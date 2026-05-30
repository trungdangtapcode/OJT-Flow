from pathlib import Path

from ojtflow.infrastructure.storage.migrations import PostgresMigrator


ROOT = Path(__file__).resolve().parents[1]


def test_postgres_migration_files_are_loaded_in_order() -> None:
    migrations = PostgresMigrator(
        "postgresql://unused",
        ROOT / "sql/postgres/migrations",
    ).load_migrations()

    assert [migration.version for migration in migrations] == ["001", "002", "003", "004"]
    assert migrations[0].name == "backend_v0"
    assert migrations[1].name == "retrieval_v0"
    assert migrations[2].name == "auth_google_sessions"
    assert migrations[3].name == "evidence_retrieval_source_types"
    assert all(len(migration.checksum) == 64 for migration in migrations)


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
