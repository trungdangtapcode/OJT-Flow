from pathlib import Path

import pytest

from ojtflow.config import clear_settings_cache
from ojtflow.core.errors import OJTFlowError
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
    ]
    assert migrations[0].name == "backend_v0"
    assert migrations[1].name == "retrieval_v0"
    assert migrations[2].name == "auth_google_sessions"
    assert migrations[3].name == "evidence_retrieval_source_types"
    assert migrations[4].name == "workflow_owner_scope"
    assert migrations[5].name == "semantic_embedding_vector"
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
