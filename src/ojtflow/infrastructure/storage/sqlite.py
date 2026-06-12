"""SQLite and local-file storage adapters for backend v0."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

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
from ojtflow.core.contracts.graph import GraphContextRecord
from ojtflow.core.contracts.jobs import BackgroundJob, JobError, JobProgress, JobType
from ojtflow.core.contracts.retrieval import (
    RetrievalActiveLearningCandidate,
    RetrievalActiveLearningCandidateUpdate,
    RetrievalActiveLearningCandidateWrite,
    RetrievalActiveLearningPriority,
    RetrievalActiveLearningSourceKind,
    RetrievalActiveLearningStatus,
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
        self.uploads_dir = self.data_dir / "uploads"
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
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

                create table if not exists audit_records (
                    audit_id text primary key,
                    owner_user_id text,
                    workflow_id text,
                    assistant_session_id text,
                    assistant_message_id text,
                    request_id text,
                    action text not null,
                    actor_id text not null,
                    actor_type text not null,
                    status text not null,
                    input_hash text,
                    output_hash text,
                    chain_scope text,
                    chain_sequence integer,
                    previous_record_hash text,
                    record_hash text,
                    hash_algorithm text,
                    chain_status text not null default 'pending',
                    workflow_event_refs text not null,
                    metadata_json text not null,
                    timestamp text not null,
                    record_json text not null
                );

                create index if not exists idx_audit_records_owner_timestamp
                    on audit_records(owner_user_id, timestamp desc);

                create index if not exists idx_audit_records_workflow_timestamp
                    on audit_records(workflow_id, timestamp desc);

                create index if not exists idx_audit_records_session_timestamp
                    on audit_records(assistant_session_id, timestamp desc);

                create index if not exists idx_audit_records_chain_scope_sequence
                    on audit_records(chain_scope, chain_sequence desc);

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

                create table if not exists uploaded_artifacts (
                    artifact_id text primary key,
                    owner_user_id text not null,
                    filename text not null,
                    mime_type text not null,
                    extension text not null,
                    byte_size integer not null,
                    sha256 text not null,
                    source text not null,
                    storage_ref text not null,
                    dataset_id text,
                    duplicate_of_artifact_id text,
                    retention_policy_json text not null,
                    metadata_json text not null,
                    created_at text not null,
                    check (byte_size >= 0)
                );

                create index if not exists idx_uploaded_artifacts_owner_created
                    on uploaded_artifacts(owner_user_id, created_at desc);

                create index if not exists idx_uploaded_artifacts_owner_hash
                    on uploaded_artifacts(owner_user_id, sha256, byte_size);

                create table if not exists document_parse_traces (
                    trace_id text primary key,
                    artifact_id text not null references uploaded_artifacts(artifact_id)
                        on delete cascade,
                    owner_user_id text not null,
                    job_id text,
                    trace_json text not null,
                    created_at text not null,
                    completed_at text
                );

                create index if not exists idx_document_parse_traces_artifact_created
                    on document_parse_traces(owner_user_id, artifact_id, created_at desc);

                create table if not exists artifact_access_events (
                    event_id text primary key,
                    artifact_id text not null references uploaded_artifacts(artifact_id)
                        on delete cascade,
                    owner_user_id text not null,
                    actor_user_id text not null,
                    action text not null,
                    request_id text,
                    event_json text not null,
                    created_at text not null,
                    check (action in ('download', 'export_metadata', 'view_metadata'))
                );

                create index if not exists idx_artifact_access_events_artifact_created
                    on artifact_access_events(owner_user_id, artifact_id, created_at desc);

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
                    check (value in (
                        'relevant',
                        'partial',
                        'irrelevant',
                        'not_relevant',
                        'unsafe',
                        'stale',
                        'source_policy_blocked'
                    )),
                    check (rating >= 0 and rating <= 3)
                );

                create index if not exists idx_retrieval_judgments_owner_updated
                    on retrieval_relevance_judgments(owner_user_id, updated_at desc);

                create index if not exists idx_retrieval_judgments_owner_query
                    on retrieval_relevance_judgments(owner_user_id, query_hash, updated_at desc);

                create table if not exists retrieval_active_learning_candidates (
                    candidate_id text primary key,
                    owner_user_id text not null,
                    candidate_key text not null,
                    query_hash text not null,
                    query_text text not null,
                    source_kind text not null,
                    trigger_reason text not null,
                    priority text not null,
                    status text not null,
                    evidence_id text,
                    source_id text,
                    source_type text,
                    source_version text,
                    run_id text,
                    workflow_id text,
                    judgment_id text,
                    claim_id text,
                    support_status text,
                    suggested_expected_evidence_ids_json text not null,
                    suggested_filters_json text not null,
                    benchmark_metadata_json text not null,
                    metadata_json text not null,
                    reviewer_user_id text,
                    reviewer_note text,
                    reviewed_at text,
                    created_at text not null,
                    updated_at text not null,
                    unique(owner_user_id, candidate_key),
                    check (source_kind in (
                        'low_confidence_retrieval',
                        'unsupported_claim',
                        'reviewer_correction',
                        'weak_support',
                        'negative_judgment'
                    )),
                    check (priority in ('low', 'normal', 'high', 'critical')),
                    check (status in ('open', 'accepted', 'rejected', 'promoted', 'archived')),
                    check (support_status is null or support_status in (
                        'strong',
                        'partial',
                        'weak',
                        'unsupported'
                    ))
                );

                create index if not exists idx_active_learning_owner_status_updated
                    on retrieval_active_learning_candidates(owner_user_id, status, updated_at desc);

                create index if not exists idx_active_learning_owner_kind_updated
                    on retrieval_active_learning_candidates(owner_user_id, source_kind, updated_at desc);

                create table if not exists graph_contexts (
                    graph_id text primary key,
                    owner_user_id text,
                    workflow_id text,
                    request_id text,
                    search_signature text,
                    query_text text not null,
                    resource_type text,
                    fields_json text not null,
                    node_count integer not null,
                    edge_count integer not null,
                    triple_count integer not null,
                    graph_json text not null,
                    record_json text not null,
                    created_at text not null,
                    check (node_count >= 0),
                    check (edge_count >= 0),
                    check (triple_count >= 0)
                );

                create index if not exists idx_graph_contexts_owner_created
                    on graph_contexts(owner_user_id, created_at desc);

                create index if not exists idx_graph_contexts_workflow_created
                    on graph_contexts(workflow_id, created_at desc);

                create table if not exists assistant_chat_sessions (
                    session_id text primary key,
                    owner_user_id text not null,
                    title text not null,
                    message_count integer not null default 0,
                    archived_at text,
                    created_at text not null,
                    updated_at text not null
                );

                create index if not exists idx_assistant_sessions_owner_updated
                    on assistant_chat_sessions(owner_user_id, updated_at desc);

                create index if not exists idx_assistant_sessions_owner_archived
                    on assistant_chat_sessions(owner_user_id, archived_at, updated_at desc);

                create table if not exists assistant_chat_messages (
                    message_id text primary key,
                    session_id text not null references assistant_chat_sessions(session_id)
                        on delete cascade,
                    owner_user_id text not null,
                    role text not null,
                    content text not null,
                    workflow_refs_json text not null default '[]',
                    payload_json text not null,
                    created_at text not null,
                    check (role in ('user', 'assistant', 'system', 'tool'))
                );

                create index if not exists idx_assistant_messages_session_created
                    on assistant_chat_messages(session_id, created_at, message_id);

                create table if not exists assistant_stream_replays (
                    stream_id text primary key,
                    session_id text not null references assistant_chat_sessions(session_id)
                        on delete cascade,
                    owner_user_id text not null,
                    status text not null,
                    events_json text not null,
                    created_at text not null,
                    completed_at text not null,
                    check (status in ('completed', 'failed', 'cancelled'))
                );

                create index if not exists idx_assistant_stream_replays_session_created
                    on assistant_stream_replays(session_id, created_at, stream_id);

                create table if not exists assistant_memory_preferences (
                    owner_user_id text not null,
                    key text not null,
                    value_json text not null,
                    category text not null,
                    source text not null,
                    policy_version text not null,
                    created_at text not null,
                    updated_at text not null,
                    primary key (owner_user_id, key),
                    check (source in ('user', 'system', 'admin'))
                );

                create index if not exists idx_assistant_memory_owner_updated
                    on assistant_memory_preferences(owner_user_id, updated_at desc);

                create table if not exists background_jobs (
                    job_id text primary key,
                    owner_user_id text not null,
                    job_type text not null,
                    status text not null,
                    input_json text not null,
                    output_json text not null,
                    error_json text,
                    progress_json text not null,
                    attempts integer not null,
                    max_attempts integer not null,
                    created_at text not null,
                    updated_at text not null,
                    started_at text,
                    completed_at text,
                    check (
                        job_type in (
                            'retrieval_reindex',
                            'file_parse',
                            'ocr_extract',
                            'embedding_reindex',
                            'external_ingest',
                            'export_package'
                        )
                    ),
                    check (status in ('queued', 'running', 'succeeded', 'failed', 'cancelled')),
                    check (attempts >= 0),
                    check (max_attempts >= 1)
                );

                create index if not exists idx_background_jobs_owner_updated
                    on background_jobs(owner_user_id, updated_at desc);

                create index if not exists idx_background_jobs_owner_status
                    on background_jobs(owner_user_id, status, updated_at desc);
                """
            )
            self._ensure_audit_record_columns(connection)
            self._ensure_retrieval_judgment_value_constraint(connection)
            columns = {
                row["name"]
                for row in connection.execute("pragma table_info(workflows)").fetchall()
            }
            if "owner_user_id" not in columns:
                connection.execute("alter table workflows add column owner_user_id text")
            message_columns = {
                row["name"]
                for row in connection.execute(
                    "pragma table_info(assistant_chat_messages)"
                ).fetchall()
            }
            if "workflow_refs_json" not in message_columns:
                connection.execute(
                    """
                    alter table assistant_chat_messages
                    add column workflow_refs_json text not null default '[]'
                    """
                )
            connection.execute(
                """
                create index if not exists idx_workflows_owner_updated
                    on workflows(owner_user_id, updated_at desc)
                """
            )
            connection.execute(
                """
                create index if not exists idx_audit_records_chain_scope_sequence
                    on audit_records(chain_scope, chain_sequence desc)
                """
            )

    def _ensure_retrieval_judgment_value_constraint(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        row = connection.execute(
            """
            select sql
            from sqlite_master
            where type = 'table' and name = 'retrieval_relevance_judgments'
            """
        ).fetchone()
        sql = str(row["sql"] if row else "")
        if "source_policy_blocked" in sql:
            return
        connection.executescript(
            """
            alter table retrieval_relevance_judgments
                rename to retrieval_relevance_judgments_old_value_labels;

            create table retrieval_relevance_judgments (
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
                check (value in (
                    'relevant',
                    'partial',
                    'irrelevant',
                    'not_relevant',
                    'unsafe',
                    'stale',
                    'source_policy_blocked'
                )),
                check (rating >= 0 and rating <= 3)
            );

            insert into retrieval_relevance_judgments (
                judgment_id, owner_user_id, query_hash, query_text,
                evidence_id, source_id, source_type, source_version, run_id,
                search_signature, value, rating, metadata_json, created_at, updated_at
            )
            select
                judgment_id, owner_user_id, query_hash, query_text,
                evidence_id, source_id, source_type, source_version, run_id,
                search_signature, value, rating, metadata_json, created_at, updated_at
            from retrieval_relevance_judgments_old_value_labels;

            drop table retrieval_relevance_judgments_old_value_labels;

            create index if not exists idx_retrieval_judgments_owner_updated
                on retrieval_relevance_judgments(owner_user_id, updated_at desc);

            create index if not exists idx_retrieval_judgments_owner_query
                on retrieval_relevance_judgments(owner_user_id, query_hash, updated_at desc);
            """
        )

    def _ensure_audit_record_columns(self, connection: sqlite3.Connection) -> None:
        existing = {
            row["name"]
            for row in connection.execute("pragma table_info(audit_records)").fetchall()
        }
        additions = {
            "assistant_message_id": "text",
            "actor_type": "text not null default 'system'",
            "input_hash": "text",
            "output_hash": "text",
            "chain_scope": "text",
            "chain_sequence": "integer",
            "previous_record_hash": "text",
            "record_hash": "text",
            "hash_algorithm": "text",
            "chain_status": "text not null default 'pending'",
            "workflow_event_refs": "text not null default '[]'",
            "metadata_json": "text not null default '{}'",
        }
        for column, definition in additions.items():
            if column not in existing:
                connection.execute(
                    f"alter table audit_records add column {column} {definition}"
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

    def list_records(self, limit: int = 1000) -> list[DatasetRecord]:
        with self.backbone.connect() as connection:
            rows = connection.execute(
                """
                select dataset_id, workflow_id, source_kind, declared_format,
                       detected_format, byte_size, sha256, storage_ref
                from datasets
                order by created_at desc, dataset_id desc
                limit ?
                """,
                (max(0, min(limit, 10_000)),),
            ).fetchall()
        return [_sqlite_dataset_record_from_row(row) for row in rows]


class SQLiteUploadedArtifactRepository:
    """SQLite-backed uploaded artifact metadata with local file bytes."""

    def __init__(self, backbone: SQLiteBackboneStore) -> None:
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
            connection.execute(
                """
                insert into uploaded_artifacts (
                    artifact_id, owner_user_id, filename, mime_type, extension,
                    byte_size, sha256, source, storage_ref, dataset_id,
                    duplicate_of_artifact_id, retention_policy_json, metadata_json,
                    created_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                _sqlite_uploaded_artifact_values(artifact),
            )
        return artifact

    def get(self, *, owner_user_id: str, artifact_id: str) -> UploadedArtifact:
        with self.backbone.connect() as connection:
            row = connection.execute(
                """
                select * from uploaded_artifacts
                where owner_user_id = ? and artifact_id = ?
                """,
                (owner_user_id, artifact_id),
            ).fetchone()
        if not row:
            raise NotFoundError(f"Uploaded artifact not found: {artifact_id}")
        return _sqlite_uploaded_artifact_from_row(row)

    def get_bytes(self, *, owner_user_id: str, artifact_id: str) -> bytes:
        artifact = self.get(owner_user_id=owner_user_id, artifact_id=artifact_id)
        path = artifact_path_from_file_ref(
            artifact.storage_ref,
            [self.backbone.uploads_dir],
        )
        return path.read_bytes()

    def list(self, *, owner_user_id: str, limit: int = 100) -> list[UploadedArtifact]:
        with self.backbone.connect() as connection:
            rows = connection.execute(
                """
                select * from uploaded_artifacts
                where owner_user_id = ?
                order by created_at desc, artifact_id desc
                limit ?
                """,
                (owner_user_id, max(1, min(limit, 500))),
            ).fetchall()
        return [_sqlite_uploaded_artifact_from_row(row) for row in rows]

    def append_trace(self, trace: ParsingPipelineTrace) -> ParsingPipelineTrace:
        self.get(owner_user_id=trace.owner_user_id, artifact_id=trace.artifact_id)
        with self.backbone.connect() as connection:
            connection.execute(
                """
                insert into document_parse_traces (
                    trace_id, artifact_id, owner_user_id, job_id, trace_json,
                    created_at, completed_at
                ) values (?, ?, ?, ?, ?, ?, ?)
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
        return trace

    def list_traces(
        self,
        *,
        owner_user_id: str,
        artifact_id: str,
    ) -> list[ParsingPipelineTrace]:
        self.get(owner_user_id=owner_user_id, artifact_id=artifact_id)
        with self.backbone.connect() as connection:
            rows = connection.execute(
                """
                select trace_json from document_parse_traces
                where owner_user_id = ? and artifact_id = ?
                order by created_at desc, trace_id desc
                """,
                (owner_user_id, artifact_id),
            ).fetchall()
        return [ParsingPipelineTrace.model_validate_json(row["trace_json"]) for row in rows]

    def append_access_event(self, event: ArtifactAccessEvent) -> ArtifactAccessEvent:
        self.get(owner_user_id=event.owner_user_id, artifact_id=event.artifact_id)
        with self.backbone.connect() as connection:
            connection.execute(
                """
                insert into artifact_access_events (
                    event_id, artifact_id, owner_user_id, actor_user_id, action,
                    request_id, event_json, created_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?)
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
        return event

    def list_access_events(
        self,
        *,
        owner_user_id: str,
        artifact_id: str,
    ) -> list[ArtifactAccessEvent]:
        self.get(owner_user_id=owner_user_id, artifact_id=artifact_id)
        with self.backbone.connect() as connection:
            rows = connection.execute(
                """
                select event_json from artifact_access_events
                where owner_user_id = ? and artifact_id = ?
                order by created_at desc, event_id desc
                """,
                (owner_user_id, artifact_id),
            ).fetchall()
        return [ArtifactAccessEvent.model_validate_json(row["event_json"]) for row in rows]

    def _canonical_for_hash(
        self,
        *,
        owner_user_id: str,
        sha256: str,
        byte_size: int,
    ) -> UploadedArtifact | None:
        with self.backbone.connect() as connection:
            row = connection.execute(
                """
                select * from uploaded_artifacts
                where owner_user_id = ?
                  and sha256 = ?
                  and byte_size = ?
                  and duplicate_of_artifact_id is null
                order by created_at asc, artifact_id asc
                limit 1
                """,
                (owner_user_id, sha256, byte_size),
            ).fetchone()
        return _sqlite_uploaded_artifact_from_row(row) if row else None


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


class SQLiteAuditRepository:
    """Append-only SQLite generic audit record repository."""

    def __init__(self, backbone: SQLiteBackboneStore) -> None:
        self.backbone = backbone

    def append(self, record: AuditRecord) -> AuditRecord:
        with self.backbone.connect() as connection:
            previous = self._latest_scoped_record(connection, record)
            linked = link_audit_record(record, previous)
            connection.execute(
                """
                insert into audit_records (
                    audit_id, owner_user_id, workflow_id, assistant_session_id,
                    assistant_message_id, request_id, action, actor_id, actor_type,
                    status, input_hash, output_hash, chain_scope, chain_sequence,
                    previous_record_hash, record_hash, hash_algorithm, chain_status,
                    workflow_event_refs, metadata_json, timestamp, record_json
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    linked.timestamp,
                    linked.model_dump_json(),
                ),
            )
        return linked

    def _latest_scoped_record(
        self,
        connection: sqlite3.Connection,
        record: AuditRecord,
    ) -> AuditRecord | None:
        if record.owner_user_id is None:
            where = "owner_user_id is null"
            params: tuple[object, ...] = ()
        else:
            where = "owner_user_id = ?"
            params = (record.owner_user_id,)
        row = connection.execute(
            f"""
            select record_json from audit_records
            where {where}
            order by coalesce(chain_sequence, 0) desc, timestamp desc, audit_id desc
            limit 1
            """,
            params,
        ).fetchone()
        if row is None:
            return None
        return AuditRecord.model_validate_json(row["record_json"])

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
            clauses.append("owner_user_id = ?")
            params.append(owner_user_id)
        if action is not None:
            clauses.append("action = ?")
            params.append(action)
        if workflow_id is not None:
            clauses.append("workflow_id = ?")
            params.append(workflow_id)
        if assistant_session_id is not None:
            clauses.append("assistant_session_id = ?")
            params.append(assistant_session_id)
        params.append(max(1, min(limit, 1000)))
        where = f"where {' and '.join(clauses)}" if clauses else ""
        with self.backbone.connect() as connection:
            rows = connection.execute(
                f"""
                select record_json from audit_records
                {where}
                order by timestamp desc, audit_id desc
                limit ?
                """,
                tuple(params),
            ).fetchall()
        return [AuditRecord.model_validate_json(row["record_json"]) for row in rows]


class SQLiteGraphRepository:
    """SQLite Graph-NER context repository."""

    def __init__(self, backbone: SQLiteBackboneStore) -> None:
        self.backbone = backbone

    def save_context(self, record: GraphContextRecord) -> GraphContextRecord:
        with self.backbone.connect() as connection:
            connection.execute(
                """
                insert into graph_contexts (
                    graph_id, owner_user_id, workflow_id, request_id,
                    search_signature, query_text, resource_type, fields_json,
                    node_count, edge_count, triple_count, graph_json,
                    record_json, created_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(graph_id) do update set
                    owner_user_id = excluded.owner_user_id,
                    workflow_id = excluded.workflow_id,
                    request_id = excluded.request_id,
                    search_signature = excluded.search_signature,
                    query_text = excluded.query_text,
                    resource_type = excluded.resource_type,
                    fields_json = excluded.fields_json,
                    node_count = excluded.node_count,
                    edge_count = excluded.edge_count,
                    triple_count = excluded.triple_count,
                    graph_json = excluded.graph_json,
                    record_json = excluded.record_json,
                    created_at = excluded.created_at
                """,
                (
                    record.graph_id,
                    record.owner_user_id,
                    record.workflow_id,
                    record.request_id,
                    record.search_signature,
                    record.query,
                    record.resource_type,
                    json.dumps(record.fields),
                    record.node_count,
                    record.edge_count,
                    record.triple_count,
                    json.dumps(record.graph_context),
                    record.model_dump_json(),
                    record.created_at,
                ),
            )
        return record

    def list_contexts(
        self,
        *,
        owner_user_id: str | None,
        workflow_id: str | None = None,
        limit: int = 100,
    ) -> list[GraphContextRecord]:
        clauses: list[str] = []
        params: list[object] = []
        if owner_user_id is not None:
            clauses.append("owner_user_id = ?")
            params.append(owner_user_id)
        if workflow_id is not None:
            clauses.append("workflow_id = ?")
            params.append(workflow_id)
        where = f"where {' and '.join(clauses)}" if clauses else ""
        params.append(max(1, min(limit, 1000)))
        with self.backbone.connect() as connection:
            rows = connection.execute(
                f"""
                select record_json from graph_contexts
                {where}
                order by created_at desc, graph_id desc
                limit ?
                """,
                tuple(params),
            ).fetchall()
        return [GraphContextRecord.model_validate_json(row["record_json"]) for row in rows]


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


class SQLiteRetrievalActiveLearningRepository:
    """SQLite-backed active-learning queue for retrieval benchmark candidates."""

    def __init__(self, backbone: SQLiteBackboneStore) -> None:
        self.backbone = backbone

    def upsert(
        self,
        *,
        owner_user_id: str,
        query_hash: str,
        candidate_key: str,
        write: RetrievalActiveLearningCandidateWrite,
    ) -> RetrievalActiveLearningCandidate:
        now = utc_now().isoformat()
        with self.backbone.connect() as connection:
            existing = connection.execute(
                """
                select candidate_id, status, reviewer_user_id, reviewer_note, reviewed_at, created_at
                from retrieval_active_learning_candidates
                where owner_user_id = ? and candidate_key = ?
                """,
                (owner_user_id, candidate_key),
            ).fetchone()
            candidate_id = existing["candidate_id"] if existing else new_id("alc")
            status = existing["status"] if existing else "open"
            created_at = existing["created_at"] if existing else now
            connection.execute(
                """
                insert into retrieval_active_learning_candidates (
                    candidate_id, owner_user_id, candidate_key, query_hash, query_text,
                    source_kind, trigger_reason, priority, status, evidence_id, source_id,
                    source_type, source_version, run_id, workflow_id, judgment_id, claim_id,
                    support_status, suggested_expected_evidence_ids_json,
                    suggested_filters_json, benchmark_metadata_json, metadata_json,
                    reviewer_user_id, reviewer_note, reviewed_at, created_at, updated_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(owner_user_id, candidate_key) do update set
                    query_text = excluded.query_text,
                    source_kind = excluded.source_kind,
                    trigger_reason = excluded.trigger_reason,
                    priority = excluded.priority,
                    evidence_id = excluded.evidence_id,
                    source_id = excluded.source_id,
                    source_type = excluded.source_type,
                    source_version = excluded.source_version,
                    run_id = excluded.run_id,
                    workflow_id = excluded.workflow_id,
                    judgment_id = excluded.judgment_id,
                    claim_id = excluded.claim_id,
                    support_status = excluded.support_status,
                    suggested_expected_evidence_ids_json = excluded.suggested_expected_evidence_ids_json,
                    suggested_filters_json = excluded.suggested_filters_json,
                    benchmark_metadata_json = excluded.benchmark_metadata_json,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                (
                    candidate_id,
                    owner_user_id,
                    candidate_key,
                    query_hash,
                    write.query,
                    write.source_kind,
                    write.trigger_reason,
                    write.priority,
                    status,
                    write.evidence_id,
                    write.source_id,
                    write.source_type.value if write.source_type else None,
                    write.source_version,
                    write.run_id,
                    write.workflow_id,
                    write.judgment_id,
                    write.claim_id,
                    write.support_status,
                    _json_dump(write.suggested_expected_evidence_ids),
                    _json_dump(write.suggested_filters),
                    _json_dump(write.benchmark_metadata),
                    _json_dump(write.metadata),
                    existing["reviewer_user_id"] if existing else None,
                    existing["reviewer_note"] if existing else None,
                    existing["reviewed_at"] if existing else None,
                    created_at,
                    now,
                ),
            )
            row = connection.execute(
                """
                select *
                from retrieval_active_learning_candidates
                where owner_user_id = ? and candidate_key = ?
                """,
                (owner_user_id, candidate_key),
            ).fetchone()
        return _sqlite_active_learning_candidate_from_row(row)

    def list(
        self,
        *,
        owner_user_id: str,
        status: RetrievalActiveLearningStatus | None = None,
        source_kind: RetrievalActiveLearningSourceKind | None = None,
        priority: RetrievalActiveLearningPriority | None = None,
        query_hash: str | None = None,
        limit: int = 500,
    ) -> list[RetrievalActiveLearningCandidate]:
        clauses = ["owner_user_id = ?"]
        params: list[object] = [owner_user_id]
        if status is not None:
            clauses.append("status = ?")
            params.append(status)
        if source_kind is not None:
            clauses.append("source_kind = ?")
            params.append(source_kind)
        if priority is not None:
            clauses.append("priority = ?")
            params.append(priority)
        if query_hash is not None:
            clauses.append("query_hash = ?")
            params.append(query_hash)
        params.append(max(1, min(limit, 1000)))
        with self.backbone.connect() as connection:
            rows = connection.execute(
                f"""
                select *
                from retrieval_active_learning_candidates
                where {' and '.join(clauses)}
                order by updated_at desc, candidate_id asc
                limit ?
                """,
                tuple(params),
            ).fetchall()
        return [_sqlite_active_learning_candidate_from_row(row) for row in rows]

    def update(
        self,
        *,
        owner_user_id: str,
        candidate_id: str,
        reviewer_user_id: str | None,
        update: RetrievalActiveLearningCandidateUpdate,
    ) -> RetrievalActiveLearningCandidate:
        now = utc_now().isoformat()
        assignments = ["updated_at = ?"]
        params: list[object] = [now]
        if update.status is not None:
            assignments.extend(["status = ?", "reviewed_at = ?", "reviewer_user_id = ?"])
            params.extend([update.status, now, reviewer_user_id])
        if update.priority is not None:
            assignments.append("priority = ?")
            params.append(update.priority)
        if update.reviewer_note is not None:
            assignments.append("reviewer_note = ?")
            params.append(update.reviewer_note)
        if update.benchmark_metadata is not None:
            assignments.append("benchmark_metadata_json = ?")
            params.append(_json_dump(update.benchmark_metadata))
        if update.metadata is not None:
            assignments.append("metadata_json = ?")
            params.append(_json_dump(update.metadata))
        params.extend([owner_user_id, candidate_id])
        with self.backbone.connect() as connection:
            cursor = connection.execute(
                f"""
                update retrieval_active_learning_candidates
                set {', '.join(assignments)}
                where owner_user_id = ? and candidate_id = ?
                """,
                tuple(params),
            )
            if cursor.rowcount == 0:
                raise NotFoundError(
                    f"Retrieval active-learning candidate not found: {candidate_id}"
                )
            row = connection.execute(
                """
                select *
                from retrieval_active_learning_candidates
                where owner_user_id = ? and candidate_id = ?
                """,
                (owner_user_id, candidate_id),
            ).fetchone()
        return _sqlite_active_learning_candidate_from_row(row)


class SQLiteAssistantSessionRepository:
    """SQLite-backed user Assistant chat sessions."""

    def __init__(self, backbone: SQLiteBackboneStore) -> None:
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
            connection.execute(
                """
                insert into assistant_chat_sessions (
                    session_id, owner_user_id, title, message_count,
                    archived_at, created_at, updated_at
                ) values (?, ?, ?, ?, ?, ?, ?)
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
        return session

    def list_sessions(
        self,
        *,
        owner_user_id: str,
        include_archived: bool = False,
        limit: int = 100,
        q: str | None = None,
    ) -> list[AssistantChatSessionSummary]:
        clauses = ["owner_user_id = ?"]
        params: list[object] = [owner_user_id]
        if not include_archived:
            clauses.append("archived_at is null")
        if q:
            pattern = _sqlite_like_pattern(q)
            clauses.append(
                """
                (
                    title like ? escape '\\'
                    or exists (
                        select 1 from assistant_chat_messages message
                        where message.session_id = assistant_chat_sessions.session_id
                          and message.owner_user_id = assistant_chat_sessions.owner_user_id
                          and message.content like ? escape '\\'
                    )
                )
                """
            )
            params.extend([pattern, pattern])
        params.append(max(1, min(limit, 500)))
        with self.backbone.connect() as connection:
            rows = connection.execute(
                f"""
                select * from assistant_chat_sessions
                where {' and '.join(clauses)}
                order by updated_at desc, session_id asc
                limit ?
                """,
                tuple(params),
            ).fetchall()
        return [_sqlite_assistant_session_from_row(row) for row in rows]

    def get_session(
        self,
        *,
        owner_user_id: str,
        session_id: str,
    ) -> AssistantChatSessionDetail:
        with self.backbone.connect() as connection:
            session_row = connection.execute(
                """
                select * from assistant_chat_sessions
                where owner_user_id = ? and session_id = ?
                """,
                (owner_user_id, session_id),
            ).fetchone()
            if not session_row:
                raise NotFoundError(f"Assistant chat session not found: {session_id}")
            message_rows = connection.execute(
                """
                select * from assistant_chat_messages
                where owner_user_id = ? and session_id = ?
                order by created_at, message_id
                """,
                (owner_user_id, session_id),
            ).fetchall()
        return AssistantChatSessionDetail(
            session=_sqlite_assistant_session_from_row(session_row),
            messages=[_sqlite_assistant_message_from_row(row) for row in message_rows],
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
            cursor = connection.execute(
                """
                update assistant_chat_sessions
                set title = ?, updated_at = ?
                where owner_user_id = ? and session_id = ?
                """,
                (title, now, owner_user_id, session_id),
            )
            if cursor.rowcount == 0:
                raise NotFoundError(f"Assistant chat session not found: {session_id}")
        return self.get_session(owner_user_id=owner_user_id, session_id=session_id).session

    def archive_session(
        self,
        *,
        owner_user_id: str,
        session_id: str,
    ) -> AssistantChatSessionSummary:
        now = utc_now().isoformat()
        with self.backbone.connect() as connection:
            cursor = connection.execute(
                """
                update assistant_chat_sessions
                set archived_at = coalesce(archived_at, ?), updated_at = ?
                where owner_user_id = ? and session_id = ?
                """,
                (now, now, owner_user_id, session_id),
            )
            if cursor.rowcount == 0:
                raise NotFoundError(f"Assistant chat session not found: {session_id}")
        return self.get_session(owner_user_id=owner_user_id, session_id=session_id).session

    def delete_session(self, *, owner_user_id: str, session_id: str) -> None:
        with self.backbone.connect() as connection:
            cursor = connection.execute(
                """
                delete from assistant_chat_sessions
                where owner_user_id = ? and session_id = ?
                """,
                (owner_user_id, session_id),
            )
        if cursor.rowcount == 0:
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
            session_row = connection.execute(
                """
                select session_id from assistant_chat_sessions
                where owner_user_id = ? and session_id = ?
                """,
                (owner_user_id, session_id),
            ).fetchone()
            if not session_row:
                raise NotFoundError(f"Assistant chat session not found: {session_id}")
            connection.execute(
                """
                insert into assistant_chat_messages (
                    message_id, session_id, owner_user_id, role,
                    content, workflow_refs_json, payload_json, created_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message.message_id,
                    message.session_id,
                    message.owner_user_id,
                    message.role,
                    message.content,
                    _json_dump(message.workflow_refs),
                    _json_dump(message.payload),
                    message.created_at,
                ),
            )
            connection.execute(
                """
                update assistant_chat_sessions
                set message_count = message_count + 1, updated_at = ?
                where owner_user_id = ? and session_id = ?
                """,
                (now, owner_user_id, session_id),
            )
        return message

    def append_stream_replay(self, *, replay: AssistantStreamReplay) -> AssistantStreamReplay:
        with self.backbone.connect() as connection:
            session_row = connection.execute(
                """
                select session_id from assistant_chat_sessions
                where owner_user_id = ? and session_id = ?
                """,
                (replay.owner_user_id, replay.session_id),
            ).fetchone()
            if not session_row:
                raise NotFoundError(
                    f"Assistant chat session not found: {replay.session_id}"
                )
            connection.execute(
                """
                insert into assistant_stream_replays (
                    stream_id, session_id, owner_user_id, status,
                    events_json, created_at, completed_at
                ) values (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    replay.stream_id,
                    replay.session_id,
                    replay.owner_user_id,
                    replay.status,
                    json.dumps(replay.events, separators=(",", ":"), sort_keys=True),
                    replay.created_at,
                    replay.completed_at,
                ),
            )
        return replay

    def list_stream_replays(
        self,
        *,
        owner_user_id: str,
        session_id: str,
    ) -> list[AssistantStreamReplay]:
        with self.backbone.connect() as connection:
            session_row = connection.execute(
                """
                select session_id from assistant_chat_sessions
                where owner_user_id = ? and session_id = ?
                """,
                (owner_user_id, session_id),
            ).fetchone()
            if not session_row:
                raise NotFoundError(f"Assistant chat session not found: {session_id}")
            rows = connection.execute(
                """
                select * from assistant_stream_replays
                where owner_user_id = ? and session_id = ?
                order by created_at, stream_id
                """,
                (owner_user_id, session_id),
            ).fetchall()
        return [_sqlite_assistant_stream_replay_from_row(row) for row in rows]


class SQLiteAssistantMemoryRepository:
    """SQLite-backed Assistant preference memory."""

    def __init__(self, backbone: SQLiteBackboneStore) -> None:
        self.backbone = backbone

    def list_preferences(
        self,
        *,
        owner_user_id: str,
    ) -> list[AssistantMemoryPreference]:
        with self.backbone.connect() as connection:
            rows = connection.execute(
                """
                select * from assistant_memory_preferences
                where owner_user_id = ?
                order by key
                """,
                (owner_user_id,),
            ).fetchall()
        return [_sqlite_assistant_memory_preference_from_row(row) for row in rows]

    def upsert_preference(
        self,
        *,
        preference: AssistantMemoryPreference,
    ) -> AssistantMemoryPreference:
        with self.backbone.connect() as connection:
            connection.execute(
                """
                insert into assistant_memory_preferences (
                    owner_user_id, key, value_json, category, source,
                    policy_version, created_at, updated_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(owner_user_id, key) do update set
                    value_json = excluded.value_json,
                    category = excluded.category,
                    source = excluded.source,
                    policy_version = excluded.policy_version,
                    updated_at = excluded.updated_at
                """,
                (
                    preference.owner_user_id,
                    preference.key,
                    _json_dump(preference.value),
                    preference.category,
                    preference.source,
                    preference.policy_version,
                    preference.created_at,
                    preference.updated_at,
                ),
            )
        return preference

    def delete_preference(self, *, owner_user_id: str, key: str) -> None:
        with self.backbone.connect() as connection:
            connection.execute(
                """
                delete from assistant_memory_preferences
                where owner_user_id = ? and key = ?
                """,
                (owner_user_id, key),
            )


class SQLiteBackgroundJobRepository:
    """SQLite-backed background job state."""

    def __init__(self, backbone: SQLiteBackboneStore) -> None:
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
            connection.execute(
                """
                insert into background_jobs (
                    job_id, owner_user_id, job_type, status, input_json,
                    output_json, error_json, progress_json, attempts, max_attempts,
                    created_at, updated_at, started_at, completed_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                _sqlite_job_values(job),
            )
        return job

    def get(self, *, owner_user_id: str, job_id: str) -> BackgroundJob:
        with self.backbone.connect() as connection:
            row = connection.execute(
                """
                select * from background_jobs
                where owner_user_id = ? and job_id = ?
                """,
                (owner_user_id, job_id),
            ).fetchone()
        if not row:
            raise NotFoundError(f"Background job not found: {job_id}")
        return _sqlite_background_job_from_row(row)

    def list(
        self,
        *,
        owner_user_id: str,
        status: str | None = None,
        job_type: str | None = None,
        limit: int = 100,
    ) -> list[BackgroundJob]:
        clauses = ["owner_user_id = ?"]
        params: list[object] = [owner_user_id]
        if status:
            clauses.append("status = ?")
            params.append(status)
        if job_type:
            clauses.append("job_type = ?")
            params.append(job_type)
        params.append(max(1, min(limit, 500)))
        with self.backbone.connect() as connection:
            rows = connection.execute(
                f"""
                select * from background_jobs
                where {' and '.join(clauses)}
                order by updated_at desc, job_id desc
                limit ?
                """,
                tuple(params),
            ).fetchall()
        return [_sqlite_background_job_from_row(row) for row in rows]

    def mark_running(self, *, owner_user_id: str, job_id: str) -> BackgroundJob:
        job = self.get(owner_user_id=owner_user_id, job_id=job_id)
        now = utc_now().isoformat()
        job.status = "running"
        job.attempts += 1
        job.started_at = job.started_at or now
        job.updated_at = now
        return self._replace(job)

    def mark_succeeded(
        self,
        *,
        owner_user_id: str,
        job_id: str,
        output: dict,
    ) -> BackgroundJob:
        job = self.get(owner_user_id=owner_user_id, job_id=job_id)
        now = utc_now().isoformat()
        job.status = "succeeded"
        job.output = output
        job.error = None
        job.progress.current = job.progress.total or 1
        job.progress.total = job.progress.total or 1
        job.progress.message = "Completed."
        job.completed_at = now
        job.updated_at = now
        return self._replace(job)

    def mark_failed(
        self,
        *,
        owner_user_id: str,
        job_id: str,
        error: JobError,
    ) -> BackgroundJob:
        job = self.get(owner_user_id=owner_user_id, job_id=job_id)
        now = utc_now().isoformat()
        job.status = "failed"
        job.error = error
        job.progress.message = error.message
        job.completed_at = now
        job.updated_at = now
        return self._replace(job)

    def mark_cancelled(
        self,
        *,
        owner_user_id: str,
        job_id: str,
        error: JobError,
    ) -> BackgroundJob:
        job = self.get(owner_user_id=owner_user_id, job_id=job_id)
        now = utc_now().isoformat()
        job.status = "cancelled"
        job.error = error
        job.progress.message = error.message
        job.completed_at = now
        job.updated_at = now
        return self._replace(job)

    def _replace(self, job: BackgroundJob) -> BackgroundJob:
        with self.backbone.connect() as connection:
            connection.execute(
                """
                update background_jobs
                set status = ?, output_json = ?, error_json = ?, progress_json = ?,
                    attempts = ?, updated_at = ?, started_at = ?, completed_at = ?
                where owner_user_id = ? and job_id = ?
                """,
                (
                    job.status,
                    _json_dump(job.output),
                    job.error.model_dump_json() if job.error else None,
                    job.progress.model_dump_json(),
                    job.attempts,
                    job.updated_at,
                    job.started_at,
                    job.completed_at,
                    job.owner_user_id,
                    job.job_id,
                ),
            )
        return job


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


def _sqlite_active_learning_candidate_from_row(row) -> RetrievalActiveLearningCandidate:
    return RetrievalActiveLearningCandidate(
        candidate_id=row["candidate_id"],
        owner_user_id=row["owner_user_id"],
        candidate_key=row["candidate_key"],
        query_hash=row["query_hash"],
        query=row["query_text"],
        source_kind=row["source_kind"],
        trigger_reason=row["trigger_reason"],
        priority=row["priority"],
        status=row["status"],
        evidence_id=row["evidence_id"],
        source_id=row["source_id"],
        source_type=row["source_type"],
        source_version=row["source_version"],
        run_id=row["run_id"],
        workflow_id=row["workflow_id"],
        judgment_id=row["judgment_id"],
        claim_id=row["claim_id"],
        support_status=row["support_status"],
        suggested_expected_evidence_ids=_json_load_list(
            row["suggested_expected_evidence_ids_json"]
        ),
        suggested_filters=_json_load(row["suggested_filters_json"]),
        benchmark_metadata=_json_load(row["benchmark_metadata_json"]),
        metadata=_json_load(row["metadata_json"]),
        reviewer_user_id=row["reviewer_user_id"],
        reviewer_note=row["reviewer_note"],
        reviewed_at=row["reviewed_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _sqlite_dataset_record_from_row(row) -> DatasetRecord:
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


def _sqlite_uploaded_artifact_values(artifact: UploadedArtifact) -> tuple[object, ...]:
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
        _json_dump(artifact.metadata),
        artifact.created_at,
    )


def _sqlite_uploaded_artifact_from_row(row) -> UploadedArtifact:
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
        retention_policy=_json_load(row["retention_policy_json"]),
        metadata=_json_load(row["metadata_json"]),
        created_at=row["created_at"],
    )


def _sqlite_job_values(job: BackgroundJob) -> tuple[object, ...]:
    return (
        job.job_id,
        job.owner_user_id,
        job.job_type,
        job.status,
        _json_dump(job.input),
        _json_dump(job.output),
        job.error.model_dump_json() if job.error else None,
        job.progress.model_dump_json(),
        job.attempts,
        job.max_attempts,
        job.created_at,
        job.updated_at,
        job.started_at,
        job.completed_at,
    )


def _sqlite_background_job_from_row(row) -> BackgroundJob:
    return BackgroundJob(
        job_id=row["job_id"],
        owner_user_id=row["owner_user_id"],
        job_type=row["job_type"],
        status=row["status"],
        input=_json_load(row["input_json"]),
        output=_json_load(row["output_json"]),
        error=JobError.model_validate_json(row["error_json"]) if row["error_json"] else None,
        progress=_job_progress_from_json(row["progress_json"]),
        attempts=int(row["attempts"]),
        max_attempts=int(row["max_attempts"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        started_at=row["started_at"],
        completed_at=row["completed_at"],
    )


def _sqlite_assistant_session_from_row(row) -> AssistantChatSessionSummary:
    return AssistantChatSessionSummary(
        session_id=row["session_id"],
        owner_user_id=row["owner_user_id"],
        title=row["title"],
        message_count=int(row["message_count"]),
        archived_at=row["archived_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _sqlite_assistant_message_from_row(row) -> AssistantChatMessage:
    payload = _json_load(row["payload_json"])
    return AssistantChatMessage(
        message_id=row["message_id"],
        session_id=row["session_id"],
        owner_user_id=row["owner_user_id"],
        role=row["role"],
        content=row["content"],
        workflow_refs=_json_load_list(
            row["workflow_refs_json"] if "workflow_refs_json" in row.keys() else None
        ),
        payload=payload,
        phi_classification=payload.get("phi_classification"),
        created_at=row["created_at"],
    )


def _sqlite_assistant_stream_replay_from_row(row) -> AssistantStreamReplay:
    events = json.loads(row["events_json"]) if row["events_json"] else []
    return AssistantStreamReplay(
        stream_id=row["stream_id"],
        session_id=row["session_id"],
        owner_user_id=row["owner_user_id"],
        status=row["status"],
        events=events if isinstance(events, list) else [],
        created_at=row["created_at"],
        completed_at=row["completed_at"],
    )


def _sqlite_assistant_memory_preference_from_row(row) -> AssistantMemoryPreference:
    return AssistantMemoryPreference(
        owner_user_id=row["owner_user_id"],
        key=row["key"],
        value=json.loads(row["value_json"]),
        category=row["category"],
        source=row["source"],
        policy_version=row["policy_version"],
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


def _json_load_list(value: str | None) -> list[str]:
    if not value:
        return []
    loaded = json.loads(value)
    if not isinstance(loaded, list):
        return []
    return [item for item in loaded if isinstance(item, str)]


def _job_progress_from_json(value: str):
    return JobProgress.model_validate_json(value)


def _sqlite_like_pattern(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"
