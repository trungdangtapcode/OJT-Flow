"""PostgreSQL and local-file storage adapters for backend v0."""

from __future__ import annotations

import json
from pathlib import Path

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover - exercised only when optional dependency is absent.
    psycopg = None
    dict_row = None

from ojtflow.core.audit_hash_chain import link_audit_record
from ojtflow.core.contracts.artifacts import (
    ArtifactAccessEvent,
    ArtifactRetentionPolicy,
    ParsingPipelineTrace,
    UploadedArtifact,
)
from ojtflow.core.contracts.assistant import (
    AssistantChatMessage,
    AssistantChatSessionDetail,
    AssistantChatSessionSummary,
    AssistantMemoryPreference,
    AssistantMessageRole,
    AssistantStreamReplay,
)
from ojtflow.core.contracts.audit import AuditRecord
from ojtflow.core.contracts.events import WorkflowEvent
from ojtflow.core.contracts.enums import WorkflowStatus
from ojtflow.core.contracts.jobs import BackgroundJob, JobError, JobProgress, JobType
from ojtflow.core.contracts.retrieval import (
    RetrievalRelevanceJudgment,
    RetrievalRelevanceJudgmentWrite,
)
from ojtflow.core.contracts.storage import DatasetRecord
from ojtflow.core.contracts.summary import WorkflowStats, WorkflowSummaryItem, WorkflowSummaryPage
from ojtflow.core.contracts.workflow import WorkflowState
from ojtflow.core.errors import NotFoundError, OJTFlowError
from ojtflow.core.ids import new_id
from ojtflow.core.time import utc_now
from ojtflow.data_tools.hashing import sha256_bytes, sha256_text
from ojtflow.infrastructure.storage.file_refs import artifact_path_from_file_ref
from ojtflow.infrastructure.storage.migrations import PostgresMigrator
from ojtflow.infrastructure.storage.summary import (
    clamp_page,
    clamp_page_size,
    normalize_direction,
    normalize_sort,
)


class PostgresBackboneStore:
    """Owns schema initialization for Postgres-backed repositories."""

    def __init__(self, dsn: str, data_dir: Path | str, apply_migrations: bool = True) -> None:
        if psycopg is None:
            raise OJTFlowError(
                "Postgres backend requires psycopg. Install project dependencies first."
            )
        self.dsn = dsn
        self.data_dir = Path(data_dir)
        self.datasets_dir = self.data_dir / "datasets"
        self.outputs_dir = self.data_dir / "outputs"
        self.uploads_dir = self.data_dir / "uploads"
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        if apply_migrations:
            self.init_schema()

    def connect(self):
        return psycopg.connect(self.dsn, row_factory=dict_row)

    def init_schema(self) -> None:
        PostgresMigrator(self.dsn).apply()


class PostgresDatasetStore:
    """Stores text artifacts as local files and metadata in Postgres."""

    def __init__(self, backbone: PostgresBackboneStore) -> None:
        self.backbone = backbone

    def put_text(
        self,
        text: str,
        workflow_id: str | None = None,
        source_kind: str = "inline",
        declared_format: str | None = None,
        detected_format: str | None = None,
    ) -> DatasetRecord:
        digest = sha256_text(text)
        dataset_id = new_id("ds")
        directory = self.backbone.outputs_dir if source_kind == "generated" else self.backbone.datasets_dir
        path = directory / f"{dataset_id}.txt"
        path.write_text(text, encoding="utf-8")
        storage_ref = path.resolve().as_uri()
        record = DatasetRecord(
            dataset_id=dataset_id,
            workflow_id=workflow_id,
            source_kind=source_kind,
            declared_format=declared_format,
            detected_format=detected_format,
            byte_size=len(text.encode("utf-8")),
            sha256=digest,
            storage_ref=storage_ref,
        )
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into ojtflow.datasets (
                        dataset_id, workflow_id, source_kind, declared_format,
                        detected_format, byte_size, sha256, storage_ref
                    ) values (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        record.dataset_id,
                        record.workflow_id,
                        record.source_kind,
                        record.declared_format,
                        record.detected_format,
                        record.byte_size,
                        record.sha256,
                        record.storage_ref,
                    ),
                )
            connection.commit()
        return record

    def put_bytes(
        self,
        data: bytes,
        workflow_id: str | None = None,
        source_kind: str = "binary",
        filename: str | None = None,
        declared_format: str | None = None,
        detected_format: str | None = None,
    ) -> DatasetRecord:
        digest = sha256_bytes(data)
        dataset_id = new_id("ds")
        suffix = Path(filename or "").suffix.lower()
        path = self.backbone.datasets_dir / f"{dataset_id}{suffix or '.bin'}"
        path.write_bytes(data)
        storage_ref = path.resolve().as_uri()
        record = DatasetRecord(
            dataset_id=dataset_id,
            workflow_id=workflow_id,
            source_kind=source_kind,
            declared_format=declared_format,
            detected_format=detected_format,
            byte_size=len(data),
            sha256=digest,
            storage_ref=storage_ref,
        )
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into ojtflow.datasets (
                        dataset_id, workflow_id, source_kind, declared_format,
                        detected_format, byte_size, sha256, storage_ref
                    ) values (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        record.dataset_id,
                        record.workflow_id,
                        record.source_kind,
                        record.declared_format,
                        record.detected_format,
                        record.byte_size,
                        record.sha256,
                        record.storage_ref,
                    ),
                )
            connection.commit()
        return record

    def get_text(self, storage_ref: str) -> str:
        path = artifact_path_from_file_ref(
            storage_ref,
            [self.backbone.datasets_dir, self.backbone.outputs_dir],
        )
        return path.read_text(encoding="utf-8")

    def list_records(self, limit: int = 1000) -> list[DatasetRecord]:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select dataset_id, workflow_id, source_kind, declared_format,
                           detected_format, byte_size, sha256, storage_ref
                    from ojtflow.datasets
                    order by created_at desc, dataset_id desc
                    limit %s
                    """,
                    (max(0, min(limit, 10_000)),),
                )
                rows = cursor.fetchall()
        return [_postgres_dataset_record_from_row(row) for row in rows]


class PostgresUploadedArtifactRepository:
    """Postgres-backed uploaded artifact metadata with local file bytes."""

    def __init__(self, backbone: PostgresBackboneStore) -> None:
        self.backbone = backbone

    def put_bytes(
        self,
        *,
        owner_user_id: str,
        filename: str,
        mime_type: str,
        data: bytes,
        source: str = "upload",
        retention_policy: ArtifactRetentionPolicy | None = None,
        metadata: dict | None = None,
    ) -> UploadedArtifact:
        digest = sha256_bytes(data)
        extension = Path(filename).suffix.lower()
        duplicate = self._canonical_for_hash(
            owner_user_id=owner_user_id,
            sha256=digest,
            byte_size=len(data),
        )
        if duplicate:
            storage_ref = duplicate.storage_ref
        else:
            storage_path = self.backbone.uploads_dir / f"{new_id('blob')}{extension or '.bin'}"
            storage_path.write_bytes(data)
            storage_ref = storage_path.resolve().as_uri()

        artifact = UploadedArtifact(
            owner_user_id=owner_user_id,
            filename=filename,
            mime_type=mime_type or "application/octet-stream",
            extension=extension,
            byte_size=len(data),
            sha256=digest,
            source=source,
            storage_ref=storage_ref,
            duplicate_of_artifact_id=duplicate.artifact_id if duplicate else None,
            retention_policy=retention_policy or ArtifactRetentionPolicy(),
            metadata=metadata or {},
        )
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into ojtflow.uploaded_artifacts (
                        artifact_id, owner_user_id, filename, mime_type, extension,
                        byte_size, sha256, source, storage_ref, dataset_id,
                        duplicate_of_artifact_id, retention_policy, metadata, created_at
                    ) values (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s::jsonb, %s::jsonb, %s::timestamptz
                    )
                    """,
                    _postgres_uploaded_artifact_values(artifact),
                )
            connection.commit()
        return artifact

    def get(self, *, owner_user_id: str, artifact_id: str) -> UploadedArtifact:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select * from ojtflow.uploaded_artifacts
                    where owner_user_id = %s and artifact_id = %s
                    """,
                    (owner_user_id, artifact_id),
                )
                row = cursor.fetchone()
        if not row:
            raise NotFoundError(f"Uploaded artifact not found: {artifact_id}")
        return _postgres_uploaded_artifact_from_row(row)

    def get_bytes(self, *, owner_user_id: str, artifact_id: str) -> bytes:
        artifact = self.get(owner_user_id=owner_user_id, artifact_id=artifact_id)
        path = artifact_path_from_file_ref(
            artifact.storage_ref,
            [self.backbone.uploads_dir],
        )
        return path.read_bytes()

    def list(self, *, owner_user_id: str, limit: int = 100) -> list[UploadedArtifact]:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select * from ojtflow.uploaded_artifacts
                    where owner_user_id = %s
                    order by created_at desc, artifact_id desc
                    limit %s
                    """,
                    (owner_user_id, max(1, min(limit, 500))),
                )
                rows = cursor.fetchall()
        return [_postgres_uploaded_artifact_from_row(row) for row in rows]

    def append_trace(self, trace: ParsingPipelineTrace) -> ParsingPipelineTrace:
        self.get(owner_user_id=trace.owner_user_id, artifact_id=trace.artifact_id)
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into ojtflow.document_parse_traces (
                        trace_id, artifact_id, owner_user_id, job_id, trace_json,
                        created_at, completed_at
                    ) values (
                        %s, %s, %s, %s, %s::jsonb, %s::timestamptz,
                        %s::timestamptz
                    )
                    """,
                    (
                        trace.trace_id,
                        trace.artifact_id,
                        trace.owner_user_id,
                        trace.job_id,
                        trace.model_dump_json(),
                        trace.started_at,
                        trace.completed_at,
                    ),
                )
            connection.commit()
        return trace

    def list_traces(
        self,
        *,
        owner_user_id: str,
        artifact_id: str,
    ) -> list[ParsingPipelineTrace]:
        self.get(owner_user_id=owner_user_id, artifact_id=artifact_id)
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select trace_json from ojtflow.document_parse_traces
                    where owner_user_id = %s and artifact_id = %s
                    order by created_at desc, trace_id desc
                    """,
                    (owner_user_id, artifact_id),
                )
                rows = cursor.fetchall()
        return [ParsingPipelineTrace.model_validate(row["trace_json"]) for row in rows]

    def append_access_event(self, event: ArtifactAccessEvent) -> ArtifactAccessEvent:
        self.get(owner_user_id=event.owner_user_id, artifact_id=event.artifact_id)
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into ojtflow.artifact_access_events (
                        event_id, artifact_id, owner_user_id, actor_user_id, action,
                        request_id, event_json, created_at
                    ) values (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::timestamptz)
                    """,
                    (
                        event.event_id,
                        event.artifact_id,
                        event.owner_user_id,
                        event.actor_user_id,
                        event.action,
                        event.request_id,
                        event.model_dump_json(),
                        event.timestamp,
                    ),
                )
            connection.commit()
        return event

    def list_access_events(
        self,
        *,
        owner_user_id: str,
        artifact_id: str,
    ) -> list[ArtifactAccessEvent]:
        self.get(owner_user_id=owner_user_id, artifact_id=artifact_id)
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select event_json from ojtflow.artifact_access_events
                    where owner_user_id = %s and artifact_id = %s
                    order by created_at desc, event_id desc
                    """,
                    (owner_user_id, artifact_id),
                )
                rows = cursor.fetchall()
        return [ArtifactAccessEvent.model_validate(row["event_json"]) for row in rows]

    def _canonical_for_hash(
        self,
        *,
        owner_user_id: str,
        sha256: str,
        byte_size: int,
    ) -> UploadedArtifact | None:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select * from ojtflow.uploaded_artifacts
                    where owner_user_id = %s
                      and sha256 = %s
                      and byte_size = %s
                      and duplicate_of_artifact_id is null
                    order by created_at asc, artifact_id asc
                    limit 1
                    """,
                    (owner_user_id, sha256, byte_size),
                )
                row = cursor.fetchone()
        return _postgres_uploaded_artifact_from_row(row) if row else None


class PostgresWorkflowRepository:
    """Persists versioned WorkflowState JSON in Postgres."""

    def __init__(self, backbone: PostgresBackboneStore) -> None:
        self.backbone = backbone

    def save(self, workflow: WorkflowState) -> None:
        review_id = workflow.review.review_id if workflow.review else None
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into ojtflow.workflows (
                        workflow_id, owner_user_id, status, schema_version, review_id,
                        state_json, created_at, updated_at
                    ) values (%s, %s, %s, %s, %s, %s::jsonb, %s::timestamptz, %s::timestamptz)
                    on conflict(workflow_id) do update set
                        owner_user_id = excluded.owner_user_id,
                        status = excluded.status,
                        schema_version = excluded.schema_version,
                        review_id = excluded.review_id,
                        state_json = excluded.state_json,
                        updated_at = excluded.updated_at
                    """,
                    (
                        workflow.workflow_id,
                        workflow.owner_user_id,
                        workflow.status.value,
                        workflow.schema_version,
                        review_id,
                        workflow.model_dump_json(),
                        workflow.created_at,
                        workflow.updated_at,
                    ),
                )
                if workflow.review:
                    cursor.execute(
                        """
                        insert into ojtflow.reviews (
                            review_id, workflow_id, status, trigger, review_json,
                            decided_by, decided_at, updated_at
                        ) values (%s, %s, %s, %s, %s::jsonb, %s, %s::timestamptz, now())
                        on conflict(review_id) do update set
                            status = excluded.status,
                            trigger = excluded.trigger,
                            review_json = excluded.review_json,
                            decided_by = excluded.decided_by,
                            decided_at = excluded.decided_at,
                            updated_at = now()
                        """,
                        (
                            workflow.review.review_id,
                            workflow.workflow_id,
                            workflow.review.status.value,
                            workflow.review.trigger,
                            workflow.review.model_dump_json(),
                            workflow.review.decided_by,
                            workflow.review.decided_at,
                        ),
                    )
                for evidence in workflow.retrieved_context:
                    cursor.execute(
                        """
                        insert into ojtflow.evidence (
                            evidence_id, workflow_id, source_type, source_id,
                            source_version, claim, confidence, trust_level, evidence_json
                        ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                        on conflict(evidence_id) do update set
                            workflow_id = excluded.workflow_id,
                            source_type = excluded.source_type,
                            source_id = excluded.source_id,
                            source_version = excluded.source_version,
                            claim = excluded.claim,
                            confidence = excluded.confidence,
                            trust_level = excluded.trust_level,
                            evidence_json = excluded.evidence_json
                        """,
                        (
                            evidence.evidence_id,
                            workflow.workflow_id,
                            evidence.source_type.value,
                            evidence.source_id,
                            evidence.source_version,
                            evidence.claim,
                            evidence.confidence,
                            evidence.trust_level.value,
                            evidence.model_dump_json(),
                        ),
                    )
            connection.commit()

    def get(self, workflow_id: str) -> WorkflowState:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "select state_json from ojtflow.workflows where workflow_id = %s",
                    (workflow_id,),
                )
                row = cursor.fetchone()
        if not row:
            raise NotFoundError(f"Workflow not found: {workflow_id}")
        return WorkflowState.model_validate(row["state_json"])

    def find_by_review_id(self, review_id: str) -> WorkflowState:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "select state_json from ojtflow.workflows where review_id = %s",
                    (review_id,),
                )
                row = cursor.fetchone()
        if not row:
            raise NotFoundError(f"Review not found: {review_id}")
        return WorkflowState.model_validate(row["state_json"])

    def list(
        self,
        status: WorkflowStatus | None = None,
        limit: int = 50,
        owner_user_id: str | None = None,
    ) -> list[WorkflowState]:
        limit = max(1, min(limit, 200))
        clauses: list[str] = []
        params: list[object] = []
        if owner_user_id is not None:
            clauses.append("owner_user_id = %s")
            params.append(owner_user_id)
        if status:
            clauses.append("status = %s")
            params.append(status.value)
        where = f"where {' and '.join(clauses)}" if clauses else ""
        params.append(limit)
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    select state_json from ojtflow.workflows
                    {where}
                    order by updated_at desc
                    limit %s
                    """,
                    tuple(params),
                )
                rows = cursor.fetchall()
        return [WorkflowState.model_validate(row["state_json"]) for row in rows]

    def list_summary(
        self,
        status: WorkflowStatus | None = None,
        q: str | None = None,
        page: int = 1,
        page_size: int = 25,
        sort: str = "updated_at",
        direction: str = "desc",
        reviews_only: bool = False,
        review_status: str | None = None,
        owner_user_id: str | None = None,
    ) -> WorkflowSummaryPage:
        page = clamp_page(page)
        page_size = clamp_page_size(page_size)
        offset = (page - 1) * page_size
        sort = normalize_sort(sort)
        direction = normalize_direction(direction)
        where, params = _summary_filters(
            status,
            q,
            reviews_only,
            review_status,
            owner_user_id,
        )
        sort_sql = {
            "updated_at": "updated_at",
            "created_at": "created_at",
            "status": "status",
            "workflow_id": "workflow_id",
            "issue_count": "issue_count",
            "evidence_count": "evidence_count",
        }[sort]

        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"select count(*) as total from ({_summary_projection_sql()}) s {where}",
                    params,
                )
                total = int(cursor.fetchone()["total"])
                cursor.execute(
                    f"""
                    select * from ({_summary_projection_sql()}) s
                    {where}
                    order by {sort_sql} {direction}, workflow_id asc
                    limit %s offset %s
                    """,
                    (*params, page_size, offset),
                )
                rows = cursor.fetchall()

        return WorkflowSummaryPage(
            items=[_summary_item_from_row(row) for row in rows],
            page=page,
            page_size=page_size,
            total=total,
        )

    def stats(self, owner_user_id: str | None = None) -> WorkflowStats:
        where, params = _summary_filters(
            status=None,
            q=None,
            reviews_only=False,
            review_status=None,
            owner_user_id=owner_user_id,
        )
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    select status, count(*) as total
                    from ojtflow.workflows
                    {where}
                    group by status
                    """,
                    params,
                )
                by_status = {row["status"]: int(row["total"]) for row in cursor.fetchall()}
                cursor.execute(
                    f"""
                    select
                        count(*) as total,
                        count(*) filter (where review_id is not null) as review_gated,
                        count(*) filter (where review_status = 'pending') as pending_reviews,
                        coalesce(avg(issue_count), 0) as average_issue_count
                    from ({_summary_projection_sql()}) s
                    {where}
                    """,
                    params,
                )
                row = cursor.fetchone()
        return WorkflowStats(
            total=int(row["total"]),
            by_status=by_status,
            pending_reviews=int(row["pending_reviews"]),
            failed=by_status.get(WorkflowStatus.FAILED.value, 0),
            completed=by_status.get(WorkflowStatus.COMPLETED.value, 0),
            review_gated=int(row["review_gated"]),
            average_issue_count=round(float(row["average_issue_count"]), 2),
        )


def _summary_projection_sql() -> str:
    return """
        select
            workflow_id,
            owner_user_id,
            status,
            state_json->>'user_instruction' as instruction,
            state_json #>> '{intent,options,schema_id}' as schema_id,
            state_json #>> '{intent,target_format}' as target_format,
            coalesce(jsonb_array_length(state_json #> '{validation_report,issues}'), 0) as issue_count,
            review_id,
            state_json #>> '{review,status}' as review_status,
            coalesce(jsonb_array_length(state_json->'retrieved_context'), 0) as evidence_count,
            created_at,
            updated_at
        from ojtflow.workflows
    """


def _summary_filters(
    status: WorkflowStatus | None,
    q: str | None,
    reviews_only: bool,
    review_status: str | None,
    owner_user_id: str | None = None,
) -> tuple[str, tuple[object, ...]]:
    clauses: list[str] = []
    params: list[object] = []
    if owner_user_id is not None:
        clauses.append("owner_user_id = %s")
        params.append(owner_user_id)
    if status:
        clauses.append("status = %s")
        params.append(status.value)
    if reviews_only:
        clauses.append("review_id is not null")
    if review_status:
        clauses.append("review_status = %s")
        params.append(review_status)
    if q and q.strip():
        clauses.append(
            """(
                workflow_id ilike %s
                or instruction ilike %s
                or coalesce(schema_id, '') ilike %s
                or coalesce(review_id, '') ilike %s
            )"""
        )
        needle = f"%{q.strip()}%"
        params.extend([needle, needle, needle, needle])
    where = f"where {' and '.join(clauses)}" if clauses else ""
    return where, tuple(params)


def _summary_item_from_row(row) -> WorkflowSummaryItem:
    return WorkflowSummaryItem(
        workflow_id=row["workflow_id"],
        owner_user_id=row["owner_user_id"],
        status=WorkflowStatus(row["status"]),
        instruction=row["instruction"] or "",
        schema_id=row["schema_id"],
        target_format=row["target_format"],
        issue_count=int(row["issue_count"]),
        review_id=row["review_id"],
        review_status=row["review_status"],
        evidence_count=int(row["evidence_count"]),
        created_at=row["created_at"].isoformat(),
        updated_at=row["updated_at"].isoformat(),
    )


class PostgresEventRepository:
    """Append-only Postgres event repository."""

    def __init__(self, backbone: PostgresBackboneStore) -> None:
        self.backbone = backbone

    def append(self, event: WorkflowEvent) -> None:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into ojtflow.workflow_events (
                        event_id, workflow_id, timestamp, actor_type, actor_id,
                        event_type, severity, summary, input_refs, output_refs, event_json
                    ) values (%s, %s, %s::timestamptz, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb)
                    """,
                    (
                        event.event_id,
                        event.workflow_id,
                        event.timestamp,
                        event.actor_type.value,
                        event.actor_id,
                        event.event_type.value,
                        event.severity.value,
                        event.summary,
                        json.dumps(event.input_refs),
                        json.dumps(event.output_refs),
                        event.model_dump_json(),
                    ),
                )
            connection.commit()

    def list_for_workflow(self, workflow_id: str) -> list[WorkflowEvent]:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select event_json from ojtflow.workflow_events
                    where workflow_id = %s
                    order by timestamp, event_id
                    """,
                    (workflow_id,),
                )
                rows = cursor.fetchall()
        return [WorkflowEvent.model_validate(row["event_json"]) for row in rows]


class PostgresAuditRepository:
    """Postgres-backed generic audit record repository."""

    def __init__(self, backbone: PostgresBackboneStore) -> None:
        self.backbone = backbone

    def append(self, record: AuditRecord) -> AuditRecord:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                previous = self._latest_scoped_record(cursor, record)
                linked = link_audit_record(record, previous)
                cursor.execute(
                    """
                    insert into ojtflow.audit_records (
                        audit_id, owner_user_id, workflow_id, assistant_session_id,
                        assistant_message_id, request_id, action, actor_id,
                        actor_type, status, input_hash, output_hash,
                        chain_scope, chain_sequence, previous_record_hash,
                        record_hash, hash_algorithm, chain_status,
                        workflow_event_refs, metadata, record_json, timestamp
                    ) values (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb,
                        %s::timestamptz
                    )
                    """,
                    (
                        linked.audit_id,
                        linked.owner_user_id,
                        linked.workflow_id,
                        linked.assistant_session_id,
                        linked.assistant_message_id,
                        linked.request_id,
                        linked.action,
                        linked.actor_id,
                        linked.actor_type,
                        linked.status,
                        linked.input_hash,
                        linked.output_hash,
                        linked.chain_scope,
                        linked.chain_sequence,
                        linked.previous_record_hash,
                        linked.record_hash,
                        linked.hash_algorithm,
                        linked.chain_status,
                        json.dumps(linked.workflow_event_refs),
                        json.dumps(linked.metadata),
                        linked.model_dump_json(),
                        linked.timestamp,
                    ),
                )
            connection.commit()
        return linked

    def _latest_scoped_record(
        self,
        cursor,
        record: AuditRecord,
    ) -> AuditRecord | None:
        if record.owner_user_id is None:
            where = "owner_user_id is null"
            params: tuple[object, ...] = ()
        else:
            where = "owner_user_id = %s"
            params = (record.owner_user_id,)
        cursor.execute(
            f"""
            select record_json from ojtflow.audit_records
            where {where}
            order by chain_sequence desc nulls last, timestamp desc, audit_id desc
            limit 1
            """,
            params,
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return AuditRecord.model_validate(row["record_json"])

    def list(
        self,
        *,
        owner_user_id: str | None = None,
        action: str | None = None,
        workflow_id: str | None = None,
        assistant_session_id: str | None = None,
        limit: int = 100,
    ) -> list[AuditRecord]:
        clauses: list[str] = []
        params: list[object] = []
        if owner_user_id is not None:
            clauses.append("owner_user_id = %s")
            params.append(owner_user_id)
        if action is not None:
            clauses.append("action = %s")
            params.append(action)
        if workflow_id is not None:
            clauses.append("workflow_id = %s")
            params.append(workflow_id)
        if assistant_session_id is not None:
            clauses.append("assistant_session_id = %s")
            params.append(assistant_session_id)
        params.append(max(1, min(limit, 1000)))
        where = f"where {' and '.join(clauses)}" if clauses else ""
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    select record_json from ojtflow.audit_records
                    {where}
                    order by timestamp desc, audit_id desc
                    limit %s
                    """,
                    tuple(params),
                )
                rows = cursor.fetchall()
        return [AuditRecord.model_validate(row["record_json"]) for row in rows]


class PostgresRetrievalJudgmentRepository:
    """Postgres-backed user retrieval relevance judgments."""

    def __init__(self, backbone: PostgresBackboneStore) -> None:
        self.backbone = backbone

    def upsert(
        self,
        *,
        owner_user_id: str,
        query_hash: str,
        write: RetrievalRelevanceJudgmentWrite,
    ) -> RetrievalRelevanceJudgment:
        now = utc_now().isoformat()
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select judgment_id, created_at
                    from ojtflow.retrieval_relevance_judgments
                    where owner_user_id = %s and query_hash = %s and evidence_id = %s
                    """,
                    (owner_user_id, query_hash, write.evidence_id),
                )
                existing = cursor.fetchone()
                judgment_id = existing["judgment_id"] if existing else new_id("rj")
                created_at = existing["created_at"].isoformat() if existing else now
                cursor.execute(
                    """
                    insert into ojtflow.retrieval_relevance_judgments (
                        judgment_id, owner_user_id, query_hash, query_text,
                        evidence_id, source_id, source_type, source_version, run_id,
                        search_signature, value, rating, metadata, created_at, updated_at
                    ) values (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s::jsonb, %s::timestamptz, %s::timestamptz
                    )
                    on conflict(owner_user_id, query_hash, evidence_id) do update set
                        query_text = excluded.query_text,
                        source_id = excluded.source_id,
                        source_type = excluded.source_type,
                        source_version = excluded.source_version,
                        run_id = excluded.run_id,
                        search_signature = excluded.search_signature,
                        value = excluded.value,
                        rating = excluded.rating,
                        metadata = excluded.metadata,
                        updated_at = excluded.updated_at
                    returning *
                    """,
                    (
                        judgment_id,
                        owner_user_id,
                        query_hash,
                        write.query,
                        write.evidence_id,
                        write.source_id,
                        write.source_type.value if write.source_type else None,
                        write.source_version,
                        write.run_id,
                        write.search_signature,
                        write.value,
                        write.rating,
                        json.dumps(write.metadata),
                        created_at,
                        now,
                    ),
                )
                row = cursor.fetchone()
            connection.commit()
        return _postgres_judgment_from_row(row)

    def list(
        self,
        *,
        owner_user_id: str,
        query_hash: str | None = None,
        run_id: str | None = None,
        evidence_id: str | None = None,
        limit: int = 500,
    ) -> list[RetrievalRelevanceJudgment]:
        clauses = ["owner_user_id = %s"]
        params: list[object] = [owner_user_id]
        if query_hash is not None:
            clauses.append("query_hash = %s")
            params.append(query_hash)
        if run_id is not None:
            clauses.append("run_id = %s")
            params.append(run_id)
        if evidence_id is not None:
            clauses.append("evidence_id = %s")
            params.append(evidence_id)
        params.append(max(1, min(limit, 1000)))
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    select * from ojtflow.retrieval_relevance_judgments
                    where {' and '.join(clauses)}
                    order by updated_at desc, judgment_id asc
                    limit %s
                    """,
                    tuple(params),
                )
                rows = cursor.fetchall()
        return [_postgres_judgment_from_row(row) for row in rows]

    def delete(self, *, owner_user_id: str, judgment_id: str) -> None:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    delete from ojtflow.retrieval_relevance_judgments
                    where owner_user_id = %s and judgment_id = %s
                    """,
                    (owner_user_id, judgment_id),
                )
                deleted = cursor.rowcount
            connection.commit()
        if deleted == 0:
            raise NotFoundError(f"Retrieval judgment not found: {judgment_id}")


class PostgresAssistantSessionRepository:
    """Postgres-backed user Assistant chat sessions."""

    def __init__(self, backbone: PostgresBackboneStore) -> None:
        self.backbone = backbone

    def create_session(self, *, owner_user_id: str, title: str) -> AssistantChatSessionSummary:
        now = utc_now().isoformat()
        session = AssistantChatSessionSummary(
            owner_user_id=owner_user_id,
            title=title,
            message_count=0,
            created_at=now,
            updated_at=now,
        )
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into ojtflow.assistant_chat_sessions (
                        session_id, owner_user_id, title, message_count,
                        archived_at, created_at, updated_at
                    ) values (%s, %s, %s, %s, %s, %s::timestamptz, %s::timestamptz)
                    """,
                    (
                        session.session_id,
                        session.owner_user_id,
                        session.title,
                        session.message_count,
                        session.archived_at,
                        session.created_at,
                        session.updated_at,
                    ),
                )
            connection.commit()
        return session

    def list_sessions(
        self,
        *,
        owner_user_id: str,
        include_archived: bool = False,
        limit: int = 100,
        q: str | None = None,
    ) -> list[AssistantChatSessionSummary]:
        clauses = ["owner_user_id = %s"]
        params: list[object] = [owner_user_id]
        if not include_archived:
            clauses.append("archived_at is null")
        if q:
            pattern = _postgres_like_pattern(q)
            clauses.append(
                """
                (
                    title ilike %s escape '\\'
                    or exists (
                        select 1 from ojtflow.assistant_chat_messages message
                        where message.session_id = assistant_chat_sessions.session_id
                          and message.owner_user_id = assistant_chat_sessions.owner_user_id
                          and message.content ilike %s escape '\\'
                    )
                )
                """
            )
            params.extend([pattern, pattern])
        params.append(max(1, min(limit, 500)))
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    select * from ojtflow.assistant_chat_sessions
                    where {' and '.join(clauses)}
                    order by updated_at desc, session_id asc
                    limit %s
                    """,
                    tuple(params),
                )
                rows = cursor.fetchall()
        return [_postgres_assistant_session_from_row(row) for row in rows]

    def get_session(
        self,
        *,
        owner_user_id: str,
        session_id: str,
    ) -> AssistantChatSessionDetail:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select * from ojtflow.assistant_chat_sessions
                    where owner_user_id = %s and session_id = %s
                    """,
                    (owner_user_id, session_id),
                )
                session_row = cursor.fetchone()
                if not session_row:
                    raise NotFoundError(f"Assistant chat session not found: {session_id}")
                cursor.execute(
                    """
                    select * from ojtflow.assistant_chat_messages
                    where owner_user_id = %s and session_id = %s
                    order by created_at, message_id
                    """,
                    (owner_user_id, session_id),
                )
                message_rows = cursor.fetchall()
        return AssistantChatSessionDetail(
            session=_postgres_assistant_session_from_row(session_row),
            messages=[_postgres_assistant_message_from_row(row) for row in message_rows],
        )

    def rename_session(
        self,
        *,
        owner_user_id: str,
        session_id: str,
        title: str,
    ) -> AssistantChatSessionSummary:
        now = utc_now().isoformat()
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    update ojtflow.assistant_chat_sessions
                    set title = %s, updated_at = %s::timestamptz
                    where owner_user_id = %s and session_id = %s
                    returning *
                    """,
                    (title, now, owner_user_id, session_id),
                )
                row = cursor.fetchone()
            connection.commit()
        if not row:
            raise NotFoundError(f"Assistant chat session not found: {session_id}")
        return _postgres_assistant_session_from_row(row)

    def archive_session(
        self,
        *,
        owner_user_id: str,
        session_id: str,
    ) -> AssistantChatSessionSummary:
        now = utc_now().isoformat()
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    update ojtflow.assistant_chat_sessions
                    set archived_at = coalesce(archived_at, %s::timestamptz),
                        updated_at = %s::timestamptz
                    where owner_user_id = %s and session_id = %s
                    returning *
                    """,
                    (now, now, owner_user_id, session_id),
                )
                row = cursor.fetchone()
            connection.commit()
        if not row:
            raise NotFoundError(f"Assistant chat session not found: {session_id}")
        return _postgres_assistant_session_from_row(row)

    def delete_session(self, *, owner_user_id: str, session_id: str) -> None:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    delete from ojtflow.assistant_chat_sessions
                    where owner_user_id = %s and session_id = %s
                    """,
                    (owner_user_id, session_id),
                )
                deleted = cursor.rowcount
            connection.commit()
        if deleted == 0:
            raise NotFoundError(f"Assistant chat session not found: {session_id}")

    def append_message(
        self,
        *,
        owner_user_id: str,
        session_id: str,
        role: AssistantMessageRole,
        content: str,
        payload: dict | None = None,
        workflow_refs: list[str] | None = None,
    ) -> AssistantChatMessage:
        now = utc_now().isoformat()
        message = AssistantChatMessage(
            session_id=session_id,
            owner_user_id=owner_user_id,
            role=role,
            content=content,
            workflow_refs=workflow_refs or [],
            payload=payload or {},
            phi_classification=(payload or {}).get("phi_classification"),
            created_at=now,
        )
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select session_id from ojtflow.assistant_chat_sessions
                    where owner_user_id = %s and session_id = %s
                    """,
                    (owner_user_id, session_id),
                )
                if not cursor.fetchone():
                    raise NotFoundError(f"Assistant chat session not found: {session_id}")
                cursor.execute(
                    """
                    insert into ojtflow.assistant_chat_messages (
                        message_id, session_id, owner_user_id, role,
                        content, workflow_refs, payload, created_at
                    ) values (
                        %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::timestamptz
                    )
                    """,
                    (
                        message.message_id,
                        message.session_id,
                        message.owner_user_id,
                        message.role,
                        message.content,
                        json.dumps(message.workflow_refs),
                        json.dumps(message.payload),
                        message.created_at,
                    ),
                )
                cursor.execute(
                    """
                    update ojtflow.assistant_chat_sessions
                    set message_count = message_count + 1,
                        updated_at = %s::timestamptz
                    where owner_user_id = %s and session_id = %s
                    """,
                    (now, owner_user_id, session_id),
                )
            connection.commit()
        return message

    def append_stream_replay(self, *, replay: AssistantStreamReplay) -> AssistantStreamReplay:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select session_id from ojtflow.assistant_chat_sessions
                    where owner_user_id = %s and session_id = %s
                    """,
                    (replay.owner_user_id, replay.session_id),
                )
                if not cursor.fetchone():
                    raise NotFoundError(
                        f"Assistant chat session not found: {replay.session_id}"
                    )
                cursor.execute(
                    """
                    insert into ojtflow.assistant_stream_replays (
                        stream_id, session_id, owner_user_id, status,
                        events, created_at, completed_at
                    ) values (
                        %s, %s, %s, %s, %s::jsonb, %s::timestamptz, %s::timestamptz
                    )
                    """,
                    (
                        replay.stream_id,
                        replay.session_id,
                        replay.owner_user_id,
                        replay.status,
                        json.dumps(replay.events),
                        replay.created_at,
                        replay.completed_at,
                    ),
                )
            connection.commit()
        return replay

    def list_stream_replays(
        self,
        *,
        owner_user_id: str,
        session_id: str,
    ) -> list[AssistantStreamReplay]:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select session_id from ojtflow.assistant_chat_sessions
                    where owner_user_id = %s and session_id = %s
                    """,
                    (owner_user_id, session_id),
                )
                if not cursor.fetchone():
                    raise NotFoundError(f"Assistant chat session not found: {session_id}")
                cursor.execute(
                    """
                    select * from ojtflow.assistant_stream_replays
                    where owner_user_id = %s and session_id = %s
                    order by created_at, stream_id
                    """,
                    (owner_user_id, session_id),
                )
                rows = cursor.fetchall()
        return [_postgres_assistant_stream_replay_from_row(row) for row in rows]


class PostgresAssistantMemoryRepository:
    """Postgres-backed Assistant preference memory."""

    def __init__(self, backbone: PostgresBackboneStore) -> None:
        self.backbone = backbone

    def list_preferences(
        self,
        *,
        owner_user_id: str,
    ) -> list[AssistantMemoryPreference]:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select * from ojtflow.assistant_memory_preferences
                    where owner_user_id = %s
                    order by key
                    """,
                    (owner_user_id,),
                )
                rows = cursor.fetchall()
        return [_postgres_assistant_memory_preference_from_row(row) for row in rows]

    def upsert_preference(
        self,
        *,
        preference: AssistantMemoryPreference,
    ) -> AssistantMemoryPreference:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into ojtflow.assistant_memory_preferences (
                        owner_user_id, key, value, category, source,
                        policy_version, created_at, updated_at
                    ) values (
                        %s, %s, %s::jsonb, %s, %s, %s,
                        %s::timestamptz, %s::timestamptz
                    )
                    on conflict(owner_user_id, key) do update set
                        value = excluded.value,
                        category = excluded.category,
                        source = excluded.source,
                        policy_version = excluded.policy_version,
                        updated_at = excluded.updated_at
                    """,
                    (
                        preference.owner_user_id,
                        preference.key,
                        json.dumps(preference.value),
                        preference.category,
                        preference.source,
                        preference.policy_version,
                        preference.created_at,
                        preference.updated_at,
                    ),
                )
            connection.commit()
        return preference

    def delete_preference(self, *, owner_user_id: str, key: str) -> None:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    delete from ojtflow.assistant_memory_preferences
                    where owner_user_id = %s and key = %s
                    """,
                    (owner_user_id, key),
                )
            connection.commit()


class PostgresBackgroundJobRepository:
    """Postgres-backed durable background jobs."""

    def __init__(self, backbone: PostgresBackboneStore) -> None:
        self.backbone = backbone

    def create(
        self,
        *,
        owner_user_id: str,
        job_type: JobType,
        input: dict,
        max_attempts: int = 1,
    ) -> BackgroundJob:
        now = utc_now().isoformat()
        job = BackgroundJob(
            owner_user_id=owner_user_id,
            job_type=job_type,
            input=input,
            max_attempts=max_attempts,
            created_at=now,
            updated_at=now,
        )
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into ojtflow.background_jobs (
                        job_id, owner_user_id, job_type, status, input, output,
                        error, progress, attempts, max_attempts, created_at,
                        updated_at, started_at, completed_at
                    ) values (
                        %s, %s, %s, %s, %s::jsonb, %s::jsonb,
                        %s::jsonb, %s::jsonb, %s, %s, %s::timestamptz,
                        %s::timestamptz, %s::timestamptz, %s::timestamptz
                    )
                    """,
                    _postgres_job_values(job),
                )
            connection.commit()
        return job

    def get(self, *, owner_user_id: str, job_id: str) -> BackgroundJob:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select * from ojtflow.background_jobs
                    where owner_user_id = %s and job_id = %s
                    """,
                    (owner_user_id, job_id),
                )
                row = cursor.fetchone()
        if not row:
            raise NotFoundError(f"Background job not found: {job_id}")
        return _postgres_background_job_from_row(row)

    def list(
        self,
        *,
        owner_user_id: str,
        status: str | None = None,
        job_type: str | None = None,
        limit: int = 100,
    ) -> list[BackgroundJob]:
        clauses = ["owner_user_id = %s"]
        params: list[object] = [owner_user_id]
        if status:
            clauses.append("status = %s")
            params.append(status)
        if job_type:
            clauses.append("job_type = %s")
            params.append(job_type)
        params.append(max(1, min(limit, 500)))
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    select * from ojtflow.background_jobs
                    where {' and '.join(clauses)}
                    order by updated_at desc, job_id desc
                    limit %s
                    """,
                    tuple(params),
                )
                rows = cursor.fetchall()
        return [_postgres_background_job_from_row(row) for row in rows]

    def mark_running(self, *, owner_user_id: str, job_id: str) -> BackgroundJob:
        job = self.get(owner_user_id=owner_user_id, job_id=job_id)
        now = utc_now().isoformat()
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    update ojtflow.background_jobs
                    set status = 'running',
                        attempts = attempts + 1,
                        started_at = coalesce(started_at, %s::timestamptz),
                        updated_at = %s::timestamptz
                    where owner_user_id = %s and job_id = %s
                    returning *
                    """,
                    (now, now, owner_user_id, job.job_id),
                )
                row = cursor.fetchone()
            connection.commit()
        if not row:
            raise NotFoundError(f"Background job not found: {job_id}")
        return _postgres_background_job_from_row(row)

    def mark_succeeded(
        self,
        *,
        owner_user_id: str,
        job_id: str,
        output: dict,
    ) -> BackgroundJob:
        now = utc_now().isoformat()
        progress = {"current": 1, "total": 1, "message": "Completed."}
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    update ojtflow.background_jobs
                    set status = 'succeeded',
                        output = %s::jsonb,
                        error = null,
                        progress = %s::jsonb,
                        completed_at = %s::timestamptz,
                        updated_at = %s::timestamptz
                    where owner_user_id = %s and job_id = %s
                    returning *
                    """,
                    (
                        json.dumps(output),
                        json.dumps(progress),
                        now,
                        now,
                        owner_user_id,
                        job_id,
                    ),
                )
                row = cursor.fetchone()
            connection.commit()
        if not row:
            raise NotFoundError(f"Background job not found: {job_id}")
        return _postgres_background_job_from_row(row)

    def mark_failed(
        self,
        *,
        owner_user_id: str,
        job_id: str,
        error: JobError,
    ) -> BackgroundJob:
        now = utc_now().isoformat()
        progress = {"current": 0, "total": None, "message": error.message}
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    update ojtflow.background_jobs
                    set status = 'failed',
                        error = %s::jsonb,
                        progress = %s::jsonb,
                        completed_at = %s::timestamptz,
                        updated_at = %s::timestamptz
                    where owner_user_id = %s and job_id = %s
                    returning *
                    """,
                    (
                        error.model_dump_json(),
                        json.dumps(progress),
                        now,
                        now,
                        owner_user_id,
                        job_id,
                    ),
                )
                row = cursor.fetchone()
            connection.commit()
        if not row:
            raise NotFoundError(f"Background job not found: {job_id}")
        return _postgres_background_job_from_row(row)

    def mark_cancelled(
        self,
        *,
        owner_user_id: str,
        job_id: str,
        error: JobError,
    ) -> BackgroundJob:
        now = utc_now().isoformat()
        progress = {"current": 0, "total": None, "message": error.message}
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    update ojtflow.background_jobs
                    set status = 'cancelled',
                        error = %s::jsonb,
                        progress = %s::jsonb,
                        completed_at = %s::timestamptz,
                        updated_at = %s::timestamptz
                    where owner_user_id = %s and job_id = %s
                    returning *
                    """,
                    (
                        error.model_dump_json(),
                        json.dumps(progress),
                        now,
                        now,
                        owner_user_id,
                        job_id,
                    ),
                )
                row = cursor.fetchone()
            connection.commit()
        if not row:
            raise NotFoundError(f"Background job not found: {job_id}")
        return _postgres_background_job_from_row(row)


def _postgres_dataset_record_from_row(row) -> DatasetRecord:
    return DatasetRecord(
        dataset_id=row["dataset_id"],
        workflow_id=row["workflow_id"],
        source_kind=row["source_kind"],
        declared_format=row["declared_format"],
        detected_format=row["detected_format"],
        byte_size=int(row["byte_size"]),
        sha256=row["sha256"],
        storage_ref=row["storage_ref"],
    )


def _postgres_uploaded_artifact_values(artifact: UploadedArtifact) -> tuple[object, ...]:
    return (
        artifact.artifact_id,
        artifact.owner_user_id,
        artifact.filename,
        artifact.mime_type,
        artifact.extension,
        artifact.byte_size,
        artifact.sha256,
        artifact.source,
        artifact.storage_ref,
        artifact.dataset_id,
        artifact.duplicate_of_artifact_id,
        artifact.retention_policy.model_dump_json(),
        json.dumps(artifact.metadata),
        artifact.created_at,
    )


def _postgres_uploaded_artifact_from_row(row) -> UploadedArtifact:
    metadata = row["metadata"] if isinstance(row["metadata"], dict) else {}
    retention_policy = (
        row["retention_policy"] if isinstance(row["retention_policy"], dict) else {}
    )
    return UploadedArtifact(
        artifact_id=row["artifact_id"],
        owner_user_id=row["owner_user_id"],
        filename=row["filename"],
        mime_type=row["mime_type"],
        extension=row["extension"],
        byte_size=int(row["byte_size"]),
        sha256=row["sha256"],
        source=row["source"],
        storage_ref=row["storage_ref"],
        dataset_id=row["dataset_id"],
        duplicate_of_artifact_id=row["duplicate_of_artifact_id"],
        retention_policy=retention_policy,
        metadata=metadata,
        created_at=row["created_at"].isoformat(),
    )


def _postgres_job_values(job: BackgroundJob) -> tuple[object, ...]:
    return (
        job.job_id,
        job.owner_user_id,
        job.job_type,
        job.status,
        json.dumps(job.input),
        json.dumps(job.output),
        job.error.model_dump_json() if job.error else None,
        job.progress.model_dump_json(),
        job.attempts,
        job.max_attempts,
        job.created_at,
        job.updated_at,
        job.started_at,
        job.completed_at,
    )


def _postgres_background_job_from_row(row) -> BackgroundJob:
    return BackgroundJob(
        job_id=row["job_id"],
        owner_user_id=row["owner_user_id"],
        job_type=row["job_type"],
        status=row["status"],
        input=row["input"] if isinstance(row["input"], dict) else {},
        output=row["output"] if isinstance(row["output"], dict) else {},
        error=_postgres_job_error(row["error"]),
        progress=_postgres_job_progress(row["progress"]),
        attempts=int(row["attempts"]),
        max_attempts=int(row["max_attempts"]),
        created_at=row["created_at"].isoformat(),
        updated_at=row["updated_at"].isoformat(),
        started_at=row["started_at"].isoformat() if row["started_at"] else None,
        completed_at=row["completed_at"].isoformat() if row["completed_at"] else None,
    )


def _postgres_job_error(value: object) -> JobError | None:
    if not isinstance(value, dict):
        return None
    return JobError.model_validate(value)


def _postgres_job_progress(value: object) -> JobProgress:
    if not isinstance(value, dict):
        return JobProgress()
    return JobProgress.model_validate(value)


def _postgres_judgment_from_row(row) -> RetrievalRelevanceJudgment:
    metadata = row["metadata"] if isinstance(row["metadata"], dict) else {}
    return RetrievalRelevanceJudgment(
        judgment_id=row["judgment_id"],
        owner_user_id=row["owner_user_id"],
        query=row["query_text"],
        query_hash=row["query_hash"],
        evidence_id=row["evidence_id"],
        source_id=row["source_id"],
        source_type=row["source_type"],
        source_version=row["source_version"],
        run_id=row["run_id"],
        search_signature=row["search_signature"],
        value=row["value"],
        rating=int(row["rating"]),
        metadata=metadata,
        created_at=row["created_at"].isoformat(),
        updated_at=row["updated_at"].isoformat(),
    )


def _postgres_assistant_session_from_row(row) -> AssistantChatSessionSummary:
    return AssistantChatSessionSummary(
        session_id=row["session_id"],
        owner_user_id=row["owner_user_id"],
        title=row["title"],
        message_count=int(row["message_count"]),
        archived_at=row["archived_at"].isoformat() if row["archived_at"] else None,
        created_at=row["created_at"].isoformat(),
        updated_at=row["updated_at"].isoformat(),
    )


def _postgres_assistant_message_from_row(row) -> AssistantChatMessage:
    payload = row["payload"] if isinstance(row["payload"], dict) else {}
    return AssistantChatMessage(
        message_id=row["message_id"],
        session_id=row["session_id"],
        owner_user_id=row["owner_user_id"],
        role=row["role"],
        content=row["content"],
        workflow_refs=_postgres_json_list(
            row["workflow_refs"] if "workflow_refs" in row else []
        ),
        payload=payload,
        phi_classification=payload.get("phi_classification"),
        created_at=row["created_at"].isoformat(),
    )


def _postgres_assistant_stream_replay_from_row(row) -> AssistantStreamReplay:
    events = row["events"] if isinstance(row["events"], list) else []
    return AssistantStreamReplay(
        stream_id=row["stream_id"],
        session_id=row["session_id"],
        owner_user_id=row["owner_user_id"],
        status=row["status"],
        events=events,
        created_at=row["created_at"].isoformat(),
        completed_at=row["completed_at"].isoformat(),
    )


def _postgres_assistant_memory_preference_from_row(row) -> AssistantMemoryPreference:
    return AssistantMemoryPreference(
        owner_user_id=row["owner_user_id"],
        key=row["key"],
        value=row["value"],
        category=row["category"],
        source=row["source"],
        policy_version=row["policy_version"],
        created_at=row["created_at"].isoformat(),
        updated_at=row["updated_at"].isoformat(),
    )


def _postgres_json_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _postgres_like_pattern(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"
