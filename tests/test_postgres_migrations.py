from pathlib import Path

from ojtflow.infrastructure.storage.migrations import PostgresMigrator


ROOT = Path(__file__).resolve().parents[1]


def test_postgres_migration_files_are_loaded_in_order() -> None:
    migrations = PostgresMigrator(
        "postgresql://unused",
        ROOT / "sql/postgres/migrations",
    ).load_migrations()

    assert [migration.version for migration in migrations] == ["001"]
    assert migrations[0].name == "backend_v0"
    assert len(migrations[0].checksum) == 64


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
