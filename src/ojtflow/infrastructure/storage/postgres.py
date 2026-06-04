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

from ojtflow.core.contracts.events import WorkflowEvent
from ojtflow.core.contracts.enums import WorkflowStatus
from ojtflow.core.contracts.storage import DatasetRecord
from ojtflow.core.contracts.summary import WorkflowStats, WorkflowSummaryItem, WorkflowSummaryPage
from ojtflow.core.contracts.workflow import WorkflowState
from ojtflow.core.errors import NotFoundError, OJTFlowError
from ojtflow.core.ids import new_id
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
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
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
