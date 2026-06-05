"""SQLite and local-file storage adapters for backend v0."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ojtflow.core.contracts.events import WorkflowEvent
from ojtflow.core.contracts.enums import WorkflowStatus
from ojtflow.core.contracts.retrieval import (
    RetrievalRelevanceJudgment,
    RetrievalRelevanceJudgmentWrite,
)
from ojtflow.core.contracts.storage import DatasetRecord
from ojtflow.core.contracts.summary import WorkflowStats, WorkflowSummaryPage
from ojtflow.core.contracts.workflow import WorkflowState
from ojtflow.core.errors import NotFoundError
from ojtflow.core.ids import new_id
from ojtflow.core.time import utc_now
from ojtflow.data_tools.hashing import sha256_bytes, sha256_text
from ojtflow.infrastructure.storage.file_refs import artifact_path_from_file_ref
from ojtflow.infrastructure.storage.summary import filter_sort_page_summaries, workflow_stats


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
                    owner_user_id text,
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

                create table if not exists retrieval_relevance_judgments (
                    judgment_id text primary key,
                    owner_user_id text not null,
                    query_hash text not null,
                    query_text text not null,
                    evidence_id text not null,
                    source_id text,
                    source_type text,
                    source_version text,
                    run_id text,
                    search_signature text,
                    value text not null,
                    rating integer not null,
                    metadata_json text not null,
                    created_at text not null,
                    updated_at text not null,
                    unique(owner_user_id, query_hash, evidence_id),
                    check (value in ('relevant', 'partial', 'not_relevant')),
                    check (rating >= 0 and rating <= 3)
                );

                create index if not exists idx_retrieval_judgments_owner_updated
                    on retrieval_relevance_judgments(owner_user_id, updated_at desc);

                create index if not exists idx_retrieval_judgments_owner_query
                    on retrieval_relevance_judgments(owner_user_id, query_hash, updated_at desc);
                """
            )
            columns = {
                row["name"]
                for row in connection.execute("pragma table_info(workflows)").fetchall()
            }
            if "owner_user_id" not in columns:
                connection.execute("alter table workflows add column owner_user_id text")
            connection.execute(
                """
                create index if not exists idx_workflows_owner_updated
                    on workflows(owner_user_id, updated_at desc)
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
        path = artifact_path_from_file_ref(
            storage_ref,
            [self.backbone.datasets_dir, self.backbone.outputs_dir],
        )
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
                    workflow_id, owner_user_id, status, schema_version, review_id,
                    state_json, created_at, updated_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?)
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
        owner_user_id: str | None = None,
    ) -> list[WorkflowState]:
        limit = max(1, min(limit, 200))
        clauses: list[str] = []
        params: list[object] = []
        if owner_user_id is not None:
            clauses.append("owner_user_id = ?")
            params.append(owner_user_id)
        if status:
            clauses.append("status = ?")
            params.append(status.value)
        where = f"where {' and '.join(clauses)}" if clauses else ""
        sql = f"""
            select state_json from workflows
            {where}
            order by updated_at desc
            limit ?
        """
        params.append(limit)
        with self.backbone.connect() as connection:
            rows = connection.execute(sql, tuple(params)).fetchall()
        return [WorkflowState.model_validate_json(row["state_json"]) for row in rows]

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
        with self.backbone.connect() as connection:
            rows = connection.execute("select state_json from workflows").fetchall()
        workflows = [WorkflowState.model_validate_json(row["state_json"]) for row in rows]
        return filter_sort_page_summaries(
            workflows,
            status=status,
            q=q,
            page=page,
            page_size=page_size,
            sort=sort,
            direction=direction,
            reviews_only=reviews_only,
            review_status=review_status,
            owner_user_id=owner_user_id,
        )

    def stats(self, owner_user_id: str | None = None) -> WorkflowStats:
        with self.backbone.connect() as connection:
            rows = connection.execute("select state_json from workflows").fetchall()
        workflows = [WorkflowState.model_validate_json(row["state_json"]) for row in rows]
        return workflow_stats(workflows, owner_user_id=owner_user_id)


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


class SQLiteRetrievalJudgmentRepository:
    """SQLite-backed user retrieval relevance judgments."""

    def __init__(self, backbone: SQLiteBackboneStore) -> None:
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
            existing = connection.execute(
                """
                select judgment_id, created_at
                from retrieval_relevance_judgments
                where owner_user_id = ? and query_hash = ? and evidence_id = ?
                """,
                (owner_user_id, query_hash, write.evidence_id),
            ).fetchone()
            judgment_id = existing["judgment_id"] if existing else new_id("rj")
            created_at = existing["created_at"] if existing else now
            connection.execute(
                """
                insert into retrieval_relevance_judgments (
                    judgment_id, owner_user_id, query_hash, query_text,
                    evidence_id, source_id, source_type, source_version, run_id,
                    search_signature, value, rating, metadata_json, created_at, updated_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(owner_user_id, query_hash, evidence_id) do update set
                    query_text = excluded.query_text,
                    source_id = excluded.source_id,
                    source_type = excluded.source_type,
                    source_version = excluded.source_version,
                    run_id = excluded.run_id,
                    search_signature = excluded.search_signature,
                    value = excluded.value,
                    rating = excluded.rating,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
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
                    _json_dump(write.metadata),
                    created_at,
                    now,
                ),
            )
            row = connection.execute(
                """
                select * from retrieval_relevance_judgments
                where owner_user_id = ? and query_hash = ? and evidence_id = ?
                """,
                (owner_user_id, query_hash, write.evidence_id),
            ).fetchone()
        return _sqlite_judgment_from_row(row)

    def list(
        self,
        *,
        owner_user_id: str,
        query_hash: str | None = None,
        run_id: str | None = None,
        evidence_id: str | None = None,
        limit: int = 500,
    ) -> list[RetrievalRelevanceJudgment]:
        clauses = ["owner_user_id = ?"]
        params: list[object] = [owner_user_id]
        if query_hash is not None:
            clauses.append("query_hash = ?")
            params.append(query_hash)
        if run_id is not None:
            clauses.append("run_id = ?")
            params.append(run_id)
        if evidence_id is not None:
            clauses.append("evidence_id = ?")
            params.append(evidence_id)
        params.append(max(1, min(limit, 1000)))
        with self.backbone.connect() as connection:
            rows = connection.execute(
                f"""
                select * from retrieval_relevance_judgments
                where {' and '.join(clauses)}
                order by updated_at desc, judgment_id asc
                limit ?
                """,
                tuple(params),
            ).fetchall()
        return [_sqlite_judgment_from_row(row) for row in rows]

    def delete(self, *, owner_user_id: str, judgment_id: str) -> None:
        with self.backbone.connect() as connection:
            cursor = connection.execute(
                """
                delete from retrieval_relevance_judgments
                where owner_user_id = ? and judgment_id = ?
                """,
                (owner_user_id, judgment_id),
            )
        if cursor.rowcount == 0:
            raise NotFoundError(f"Retrieval judgment not found: {judgment_id}")


def _sqlite_judgment_from_row(row) -> RetrievalRelevanceJudgment:
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
        metadata=_json_load(row["metadata_json"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _json_dump(value: object) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _json_load(value: str | None) -> dict:
    if not value:
        return {}
    loaded = json.loads(value)
    return loaded if isinstance(loaded, dict) else {}
