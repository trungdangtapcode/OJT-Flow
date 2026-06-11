from pathlib import Path
from hashlib import sha256

import pytest

from ojtflow.config import clear_settings_cache
from ojtflow.core.errors import OJTFlowError
from ojtflow.infrastructure.storage import migrations as migrations_module
from ojtflow.infrastructure.storage.migrations import PostgresMigrator


ROOT = Path(__file__).resolve().parents[1]


def test_postgres_migration_files_are_loaded_in_order() -> None:
    migrations = PostgresMigrator(
        "postgresql://unused",
        ROOT / "sql/postgres/migrations",
    ).load_migrations()

    assert [migration.version for migration in migrations] == [
        "001",
        "002",
        "003",
        "004",
        "005",
        "006",
        "007",
        "008",
        "009",
        "010",
        "011",
        "012",
        "013",
        "014",
        "015",
    ]
    assert migrations[0].name == "backend_v0"
    assert migrations[1].name == "retrieval_v0"
    assert migrations[2].name == "auth_google_sessions"
    assert migrations[3].name == "evidence_retrieval_source_types"
    assert migrations[4].name == "workflow_owner_scope"
    assert migrations[5].name == "semantic_embedding_vector"
    assert migrations[6].name == "retrieval_relevance_judgments"
    assert migrations[7].name == "assistant_chat_sessions"
    assert migrations[8].name == "background_jobs"
    assert migrations[9].name == "assistant_stream_replays"
    assert migrations[10].name == "uploaded_artifacts"
    assert migrations[11].name == "artifact_access_events"
    assert migrations[12].name == "assistant_stream_replay_cancelled"
    assert migrations[13].name == "assistant_memory_preferences"
    assert migrations[14].name == "audit_records"
    assert all(len(migration.checksum) == 64 for migration in migrations)


def test_postgres_migration_default_directory_comes_from_settings(
    monkeypatch,
    tmp_path: Path,
) -> None:
    migrations_dir = tmp_path / "custom-migrations"
    migrations_dir.mkdir()
    (migrations_dir / "001_custom.sql").write_text("select 1;", encoding="utf-8")
    monkeypatch.setenv("OJT_MIGRATIONS_DIR", str(migrations_dir))
    clear_settings_cache()

    try:
        migrations = PostgresMigrator("postgresql://unused").load_migrations()
    finally:
        clear_settings_cache()

    assert [migration.name for migration in migrations] == ["custom"]


def test_postgres_migration_inspection_reports_pending_unknown_and_mismatched(
    monkeypatch,
    tmp_path: Path,
) -> None:
    first_sql = "select 1;"
    second_sql = "select 2;"
    (tmp_path / "001_initial.sql").write_text(first_sql, encoding="utf-8")
    (tmp_path / "002_next.sql").write_text(second_sql, encoding="utf-8")

    class FakeCursor:
        def __init__(self) -> None:
            self.query = ""

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback) -> None:
            del exc_type, exc, traceback

        def execute(self, query: str, params=None) -> None:
            del params
            self.query = query

        def fetchone(self):
            assert "to_regclass" in self.query
            return {"table_name": "ojtflow.schema_migrations"}

        def fetchall(self):
            if "information_schema.columns" in self.query:
                return [
                    {"column_name": "version"},
                    {"column_name": "name"},
                    {"column_name": "checksum"},
                    {"column_name": "applied_at"},
                    {"column_name": "duration_ms"},
                    {"column_name": "failure_reason"},
                ]
            assert "from ojtflow.schema_migrations" in self.query
            return [
                {
                    "version": "001",
                    "name": "initial",
                    "checksum": sha256(b"edited").hexdigest(),
                    "applied_at": "2026-06-11 00:00:00+00",
                    "duration_ms": 12,
                    "failure_reason": None,
                },
                {
                    "version": "999",
                    "name": "manual",
                    "checksum": "x" * 64,
                    "applied_at": "2026-06-11 00:00:00+00",
                    "duration_ms": None,
                    "failure_reason": "manual row",
                },
            ]

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback) -> None:
            del exc_type, exc, traceback

        def cursor(self):
            return FakeCursor()

    class FakePsycopg:
        @staticmethod
        def connect(dsn, row_factory=None):
            assert dsn == "postgresql://unused"
            assert row_factory is migrations_module.dict_row
            return FakeConnection()

    monkeypatch.setattr(migrations_module, "psycopg", FakePsycopg)

    report = PostgresMigrator("postgresql://unused", tmp_path).inspect_database()

    assert report["table_exists"] is True
    assert report["manifest_count"] == 2
    assert report["applied_count"] == 1
    assert report["pending_count"] == 1
    assert report["unknown_applied_count"] == 1
    assert report["checksum_mismatch_count"] == 1
    assert report["latest_available_version"] == "002"
    assert report["latest_applied_version"] == "001"
    assert report["pending_versions"] == ["002"]
    assert report["unknown_applied_versions"] == ["999"]
    assert report["checksum_mismatches"] == ["001"]
    assert report["migrations"] == [
        {
            "version": "001",
            "name": "initial",
            "checksum": sha256(b"edited").hexdigest(),
            "status": "checksum_mismatch",
            "applied_at": "2026-06-11 00:00:00+00",
            "duration_ms": 12,
            "failure_reason": None,
        },
        {
            "version": "002",
            "name": "next",
            "checksum": sha256(second_sql.encode("utf-8")).hexdigest(),
            "status": "pending",
            "applied_at": None,
            "duration_ms": None,
            "failure_reason": None,
        },
        {
            "version": "999",
            "name": "manual",
            "checksum": "x" * 64,
            "status": "unknown_applied",
            "applied_at": "2026-06-11 00:00:00+00",
            "duration_ms": None,
            "failure_reason": "manual row",
        },
    ]


def test_postgres_migration_loader_rejects_missing_directory(tmp_path: Path) -> None:
    missing_dir = tmp_path / "missing-migrations"

    with pytest.raises(OJTFlowError, match="migrations directory not found"):
        PostgresMigrator("postgresql://unused", missing_dir).load_migrations()


def test_postgres_migration_loader_rejects_empty_directory(tmp_path: Path) -> None:
    with pytest.raises(OJTFlowError, match="No Postgres migration files found"):
        PostgresMigrator("postgresql://unused", tmp_path).load_migrations()


def test_postgres_migration_loader_rejects_duplicate_versions(tmp_path: Path) -> None:
    (tmp_path / "001_initial.sql").write_text("select 1;", encoding="utf-8")
    (tmp_path / "001_duplicate.sql").write_text("select 2;", encoding="utf-8")

    with pytest.raises(OJTFlowError, match="Duplicate migration version 001"):
        PostgresMigrator("postgresql://unused", tmp_path).load_migrations()


@pytest.mark.parametrize(
    "filename",
    [
        "1_initial.sql",
        "abc_initial.sql",
        "001.sql",
        "001_.sql",
    ],
)
def test_postgres_migration_loader_rejects_invalid_filenames(
    tmp_path: Path,
    filename: str,
) -> None:
    (tmp_path / filename).write_text("select 1;", encoding="utf-8")

    with pytest.raises(OJTFlowError, match="Invalid migration"):
        PostgresMigrator("postgresql://unused", tmp_path).load_migrations()


def test_backend_v0_migration_has_industrial_tables_and_constraints() -> None:
    sql = (ROOT / "sql/postgres/migrations/001_backend_v0.sql").read_text()

    assert "create schema if not exists ojtflow" in sql
    assert "ojtflow.schema_migrations" in sql
    assert "ojtflow.workflows" in sql
    assert "ojtflow.workflow_events" in sql
    assert "ojtflow.datasets" in sql
    assert "ojtflow.reviews" in sql
    assert "ojtflow.evidence" in sql
    assert "references ojtflow.workflows(workflow_id)" in sql
    assert "using gin(state_json)" in sql
    assert "workflows_status_check" in sql
    assert "workflows_review_id_unique" in sql
    assert "datasets_sha256_check" in sql
    assert "workflow_events_event_type_check" in sql
    assert "evidence_source_type_check" in sql
    assert "evidence_trust_level_check" in sql


def test_audit_records_migration_has_correlation_and_redaction_fields() -> None:
    sql = (ROOT / "sql/postgres/migrations/015_audit_records.sql").read_text()

    assert "create table if not exists ojtflow.audit_records" in sql
    assert "owner_user_id text" in sql
    assert "workflow_id text" in sql
    assert "assistant_session_id text" in sql
    assert "request_id text" in sql
    assert "input_hash text" in sql
    assert "output_hash text" in sql
    assert "workflow_event_refs jsonb" in sql
    assert "metadata jsonb" in sql
    assert "record_json jsonb" in sql
    assert "idx_audit_records_owner_timestamp" in sql
    assert "idx_audit_records_workflow_timestamp" in sql
    assert "idx_audit_records_session_timestamp" in sql
    assert "references ojtflow.workflows(workflow_id)" in sql


def test_retrieval_v0_migration_has_search_tables_and_pgvector_fallback() -> None:
    sql = (ROOT / "sql/postgres/migrations/002_retrieval_v0.sql").read_text()

    assert "create extension if not exists vector" in sql
    assert "undefined_file" in sql
    assert "ojtflow.knowledge_documents" in sql
    assert "ojtflow.knowledge_chunks" in sql
    assert "search_vector tsvector generated always" in sql
    assert "using gin(search_vector)" in sql
    assert "using hnsw" in sql
    assert "healthcare_standard" in sql
    assert "terminology_system" in sql
    assert "uploaded_file_raw" in sql


def test_auth_google_sessions_migration_has_users_and_sessions() -> None:
    sql = (ROOT / "sql/postgres/migrations/003_auth_google_sessions.sql").read_text()

    assert "ojtflow.users" in sql
    assert "ojtflow.sessions" in sql
    assert "google_sub text not null unique" in sql
    assert "token_hash text not null unique" in sql
    assert "references ojtflow.users(user_id)" in sql
    assert "sessions_token_hash_check" in sql


def test_evidence_retrieval_source_type_migration_extends_constraint() -> None:
    sql = (ROOT / "sql/postgres/migrations/004_evidence_retrieval_source_types.sql").read_text()

    assert "drop constraint if exists evidence_source_type_check" in sql
    assert "'terminology_system'" in sql
    assert "'healthcare_standard'" in sql


def test_workflow_owner_scope_migration_adds_owner_index() -> None:
    sql = (ROOT / "sql/postgres/migrations/005_workflow_owner_scope.sql").read_text()

    assert "add column if not exists owner_user_id text" in sql
    assert "idx_workflows_owner_updated" in sql
    assert "idx_workflows_owner_status_updated" in sql


def test_semantic_embedding_vector_migration_uses_384_dimensions() -> None:
    sql = (ROOT / "sql/postgres/migrations/006_semantic_embedding_vector.sql").read_text()

    assert "drop column if exists embedding" in sql
    assert "embedding vector(384)" in sql
    assert "using hnsw" in sql


def test_retrieval_relevance_judgment_migration_has_user_scoped_labels() -> None:
    sql = (ROOT / "sql/postgres/migrations/007_retrieval_relevance_judgments.sql").read_text()

    assert "ojtflow.retrieval_relevance_judgments" in sql
    assert "owner_user_id text not null" in sql
    assert "query_hash text not null" in sql
    assert "evidence_id text not null" in sql
    assert "unique (owner_user_id, query_hash, evidence_id)" in sql
    assert "retrieval_judgments_value_check" in sql
    assert "retrieval_judgments_rating_check" in sql
    assert "idx_retrieval_judgments_owner_query" in sql


def test_assistant_chat_sessions_migration_has_session_and_message_tables() -> None:
    sql = (ROOT / "sql/postgres/migrations/008_assistant_chat_sessions.sql").read_text()

    assert "ojtflow.assistant_chat_sessions" in sql
    assert "ojtflow.assistant_chat_messages" in sql
    assert "owner_user_id text not null" in sql
    assert "message_count integer not null default 0" in sql
    assert "references ojtflow.assistant_chat_sessions(session_id)" in sql
    assert "role in ('user', 'assistant', 'system', 'tool')" in sql
    assert "workflow_refs jsonb not null" in sql
    assert "assistant_chat_messages_workflow_refs_array" in sql
    assert "idx_assistant_messages_workflow_refs" in sql
    assert "payload jsonb not null" in sql
    assert "idx_assistant_sessions_owner_updated" in sql
    assert "idx_assistant_messages_session_created" in sql


def test_background_jobs_migration_has_job_table_and_indexes() -> None:
    sql = (ROOT / "sql/postgres/migrations/009_background_jobs.sql").read_text()

    assert "ojtflow.background_jobs" in sql
    assert "owner_user_id text not null" in sql
    assert "job_type text not null" in sql
    assert "status text not null" in sql
    assert "retrieval_reindex" in sql
    assert "file_parse" in sql
    assert "ocr_extract" in sql
    assert "embedding_reindex" in sql
    assert "external_ingest" in sql
    assert "export_package" in sql
    assert "idx_background_jobs_owner_updated" in sql
    assert "idx_background_jobs_owner_status" in sql


def test_assistant_stream_replays_migration_has_replay_table_and_indexes() -> None:
    sql = (ROOT / "sql/postgres/migrations/010_assistant_stream_replays.sql").read_text()

    assert "ojtflow.assistant_stream_replays" in sql
    assert "session_id text not null references ojtflow.assistant_chat_sessions" in sql
    assert "events jsonb not null" in sql
    assert "assistant_stream_replays_events_array" in sql
    assert "idx_assistant_stream_replays_session_created" in sql
    assert "idx_assistant_stream_replays_owner_created" in sql


def test_assistant_stream_replay_cancelled_migration_extends_status_constraint() -> None:
    sql = (
        ROOT
        / "sql/postgres/migrations/013_assistant_stream_replay_cancelled.sql"
    ).read_text()

    assert "drop constraint if exists assistant_stream_replays_status_check" in sql
    assert "status in ('completed', 'failed', 'cancelled')" in sql
