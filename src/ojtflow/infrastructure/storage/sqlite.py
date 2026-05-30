"""SQLite and local-file storage adapters for backend v0."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from urllib.parse import unquote, urlparse

from ojtflow.core.contracts.events import WorkflowEvent
from ojtflow.core.contracts.enums import WorkflowStatus
from ojtflow.core.contracts.storage import DatasetRecord
from ojtflow.core.contracts.workflow import WorkflowState
from ojtflow.core.errors import NotFoundError
from ojtflow.core.ids import new_id
from ojtflow.data_tools.hashing import sha256_bytes, sha256_text


class SQLiteBackboneStore:
    """Owns schema initialization for the SQLite-backed repositories."""

    def __init__(self, database_path: Path | str, data_dir: Path | str) -> None:
        self.database_path = Path(database_path)
        self.data_dir = Path(data_dir)
        self.datasets_dir = self.data_dir / "datasets"
        self.outputs_dir = self.data_dir / "outputs"
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def init_schema(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                create table if not exists workflows (
                    workflow_id text primary key,
                    status text not null,
                    schema_version text not null,
                    review_id text,
                    state_json text not null,
                    created_at text not null,
                    updated_at text not null
                );

                create index if not exists idx_workflows_review_id
                    on workflows(review_id);

                create table if not exists workflow_events (
                    event_id text primary key,
                    workflow_id text not null,
                    timestamp text not null,
                    actor_type text not null,
                    actor_id text not null,
                    event_type text not null,
                    severity text not null,
                    summary text not null,
                    event_json text not null
                );

                create index if not exists idx_workflow_events_workflow_id
                    on workflow_events(workflow_id, timestamp);

                create table if not exists datasets (
                    dataset_id text primary key,
                    workflow_id text,
                    source_kind text not null,
                    declared_format text,
                    detected_format text,
                    byte_size integer not null,
                    sha256 text not null,
                    storage_ref text not null unique,
                    created_at text default current_timestamp
                );
                """
            )


class SQLiteDatasetStore:
    """Stores text artifacts as files and metadata in SQLite."""

    def __init__(self, backbone: SQLiteBackboneStore) -> None:
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
            connection.execute(
                """
                insert into datasets (
                    dataset_id, workflow_id, source_kind, declared_format,
                    detected_format, byte_size, sha256, storage_ref
                ) values (?, ?, ?, ?, ?, ?, ?, ?)
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
        directory = self.backbone.datasets_dir
        path = directory / f"{dataset_id}{suffix or '.bin'}"
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
            connection.execute(
                """
                insert into datasets (
                    dataset_id, workflow_id, source_kind, declared_format,
                    detected_format, byte_size, sha256, storage_ref
                ) values (?, ?, ?, ?, ?, ?, ?, ?)
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
        return record

    def get_text(self, storage_ref: str) -> str:
        parsed = urlparse(storage_ref)
        if parsed.scheme != "file":
            raise NotFoundError(f"Unsupported dataset storage ref: {storage_ref}")
        path = Path(unquote(parsed.path))
        if not path.exists():
            raise NotFoundError(f"Dataset file not found: {storage_ref}")
        return path.read_text(encoding="utf-8")


class SQLiteWorkflowRepository:
    """Persists versioned WorkflowState JSON in SQLite."""

    def __init__(self, backbone: SQLiteBackboneStore) -> None:
        self.backbone = backbone

    def save(self, workflow: WorkflowState) -> None:
        review_id = workflow.review.review_id if workflow.review else None
        with self.backbone.connect() as connection:
            connection.execute(
                """
                insert into workflows (
                    workflow_id, status, schema_version, review_id,
                    state_json, created_at, updated_at
                ) values (?, ?, ?, ?, ?, ?, ?)
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

    def get(self, workflow_id: str) -> WorkflowState:
        with self.backbone.connect() as connection:
            row = connection.execute(
                "select state_json from workflows where workflow_id = ?",
                (workflow_id,),
            ).fetchone()
        if not row:
            raise NotFoundError(f"Workflow not found: {workflow_id}")
        return WorkflowState.model_validate_json(row["state_json"])

    def find_by_review_id(self, review_id: str) -> WorkflowState:
        with self.backbone.connect() as connection:
            row = connection.execute(
                "select state_json from workflows where review_id = ?",
                (review_id,),
            ).fetchone()
        if not row:
            raise NotFoundError(f"Review not found: {review_id}")
        return WorkflowState.model_validate_json(row["state_json"])

    def list(
        self,
        status: WorkflowStatus | None = None,
        limit: int = 50,
    ) -> list[WorkflowState]:
        limit = max(1, min(limit, 200))
        params: tuple[object, ...]
        if status:
            sql = """
                select state_json from workflows
                where status = ?
                order by updated_at desc
                limit ?
            """
            params = (status.value, limit)
        else:
            sql = """
                select state_json from workflows
                order by updated_at desc
                limit ?
            """
            params = (limit,)
        with self.backbone.connect() as connection:
            rows = connection.execute(sql, params).fetchall()
        return [WorkflowState.model_validate_json(row["state_json"]) for row in rows]


class SQLiteEventRepository:
    """Append-only SQLite event repository."""

    def __init__(self, backbone: SQLiteBackboneStore) -> None:
        self.backbone = backbone

    def append(self, event: WorkflowEvent) -> None:
        with self.backbone.connect() as connection:
            connection.execute(
                """
                insert into workflow_events (
                    event_id, workflow_id, timestamp, actor_type, actor_id,
                    event_type, severity, summary, event_json
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    event.model_dump_json(),
                ),
            )

    def list_for_workflow(self, workflow_id: str) -> list[WorkflowEvent]:
        with self.backbone.connect() as connection:
            rows = connection.execute(
                """
                select event_json from workflow_events
                where workflow_id = ?
                order by timestamp, event_id
                """,
                (workflow_id,),
            ).fetchall()
        return [WorkflowEvent.model_validate_json(row["event_json"]) for row in rows]
