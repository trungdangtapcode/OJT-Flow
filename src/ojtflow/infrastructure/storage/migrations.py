"""SQL migration runner for Postgres."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from ojtflow.config import get_settings
from ojtflow.core.errors import OJTFlowError

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover
    psycopg = None
    dict_row = None


@dataclass(frozen=True)
class Migration:
    version: str
    name: str
    path: Path
    sql: str
    checksum: str


class PostgresMigrator:
    """Applies SQL migrations from the repository migration folder."""

    def __init__(self, dsn: str, migrations_dir: Path | None = None) -> None:
        self.dsn = dsn
        self.migrations_dir = migrations_dir or get_settings().resolved_migrations_dir

    def apply(self) -> list[str]:
        """Apply pending migrations and return applied versions."""

        if psycopg is None:
            raise OJTFlowError(
                "Postgres migrations require psycopg. Install project dependencies first."
            )
        migrations = self.load_migrations()
        applied: list[str] = []
        with psycopg.connect(self.dsn, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                self._ensure_migration_table(cursor)
                known = self._known_migrations(cursor)
                for migration in migrations:
                    if migration.version in known:
                        if known[migration.version] != migration.checksum:
                            raise OJTFlowError(
                                f"Migration checksum mismatch for {migration.version}. "
                                "Do not edit applied migrations; create a new one."
                            )
                        continue
                    cursor.execute(migration.sql)
                    cursor.execute(
                        """
                        insert into ojtflow.schema_migrations(version, name, checksum)
                        values (%s, %s, %s)
                        """,
                        (migration.version, migration.name, migration.checksum),
                    )
                    applied.append(migration.version)
            connection.commit()
        return applied

    def load_migrations(self) -> list[Migration]:
        """Load migrations in filename order."""

        if not self.migrations_dir.is_dir():
            raise OJTFlowError(f"Postgres migrations directory not found: {self.migrations_dir}")

        migrations: list[Migration] = []
        seen_versions: set[str] = set()
        for path in sorted(self.migrations_dir.glob("*.sql")):
            version, name = _parse_migration_name(path)
            if version in seen_versions:
                raise OJTFlowError(
                    f"Duplicate migration version {version} in {self.migrations_dir}"
                )
            seen_versions.add(version)
            sql = path.read_text(encoding="utf-8")
            migrations.append(
                Migration(
                    version=version,
                    name=name,
                    path=path,
                    sql=sql,
                    checksum=sha256(sql.encode("utf-8")).hexdigest(),
                )
            )
        if not migrations:
            raise OJTFlowError(f"No Postgres migration files found in {self.migrations_dir}")
        return migrations

    def _ensure_migration_table(self, cursor) -> None:
        cursor.execute("create schema if not exists ojtflow")
        cursor.execute(
            """
            create table if not exists ojtflow.schema_migrations (
                version text primary key,
                name text not null,
                checksum text not null,
                applied_at timestamptz not null default now()
            )
            """
        )

    def _known_migrations(self, cursor) -> dict[str, str]:
        cursor.execute("select version, checksum from ojtflow.schema_migrations")
        return {row["version"]: row["checksum"] for row in cursor.fetchall()}


def _parse_migration_name(path: Path) -> tuple[str, str]:
    stem = path.stem
    if "_" not in stem:
        raise OJTFlowError(f"Invalid migration filename: {path.name}")
    version, name = stem.split("_", 1)
    if not version.isdigit() or len(version) != 3:
        raise OJTFlowError(f"Invalid migration version: {path.name}")
    if not name:
        raise OJTFlowError(f"Invalid migration name: {path.name}")
    return version, name
