"""PostgreSQL and local-file storage adapters for backend v0."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import unquote, urlparse

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover - exercised only when optional dependency is absent.
    psycopg = None
    dict_row = None

from ojtflow.core.contracts.events import WorkflowEvent
from ojtflow.core.contracts.enums import WorkflowStatus
from ojtflow.core.contracts.storage import DatasetRecord
from ojtflow.core.contracts.workflow import WorkflowState
from ojtflow.core.errors import NotFoundError, OJTFlowError
from ojtflow.core.ids import new_id
from ojtflow.data_tools.hashing import sha256_text
from ojtflow.infrastructure.storage.migrations import PostgresMigrator


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

    def get_text(self, storage_ref: str) -> str:
        parsed = urlparse(storage_ref)
        if parsed.scheme != "file":
            raise NotFoundError(f"Unsupported dataset storage ref: {storage_ref}")
        path = Path(unquote(parsed.path))
        if not path.exists():
            raise NotFoundError(f"Dataset file not found: {storage_ref}")
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
                        workflow_id, status, schema_version, review_id,
                        state_json, created_at, updated_at
                    ) values (%s, %s, %s, %s, %s::jsonb, %s::timestamptz, %s::timestamptz)
                    on conflict(workflow_id) do update set
                        status = excluded.status,
                        schema_version = excluded.schema_version,
                        review_id = excluded.review_id,
                        state_json = excluded.state_json,
                        updated_at = excluded.updated_at
                    """,
                    (
                        workflow.workflow_id,
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
    ) -> list[WorkflowState]:
        limit = max(1, min(limit, 200))
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                if status:
                    cursor.execute(
                        """
                        select state_json from ojtflow.workflows
                        where status = %s
                        order by updated_at desc
                        limit %s
                        """,
                        (status.value, limit),
                    )
                else:
                    cursor.execute(
                        """
                        select state_json from ojtflow.workflows
                        order by updated_at desc
                        limit %s
                        """,
                        (limit,),
                    )
                rows = cursor.fetchall()
        return [WorkflowState.model_validate(row["state_json"]) for row in rows]


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
