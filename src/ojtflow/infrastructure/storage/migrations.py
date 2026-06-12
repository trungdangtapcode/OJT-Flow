"""SQL migration runner for Postgres."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from time import perf_counter

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
                    started_at = perf_counter()
                    cursor.execute(migration.sql)
                    duration_ms = int((perf_counter() - started_at) * 1000)
                    cursor.execute(
                        """
                        insert into ojtflow.schema_migrations(
                            version, name, checksum, duration_ms, failure_reason
                        )
                        values (%s, %s, %s, %s, null)
                        """,
                        (
                            migration.version,
                            migration.name,
                            migration.checksum,
                            duration_ms,
                        ),
                    )
                    applied.append(migration.version)
            connection.commit()
        return applied

    def inspect_database(self) -> dict[str, object]:
        """Return a read-only migration manifest/database status report."""

        if psycopg is None:
            raise OJTFlowError(
                "Postgres migrations require psycopg. Install project dependencies first."
            )

        migrations = self.load_migrations()
        manifest_by_version = {migration.version: migration for migration in migrations}
        known: dict[str, dict[str, object]] = {}
        table_exists = False

        with psycopg.connect(self.dsn, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute("select to_regclass('ojtflow.schema_migrations') as table_name")
                table_exists = bool(cursor.fetchone()["table_name"])
                if table_exists:
                    columns = self._schema_migration_columns(cursor)
                    duration_expr = (
                        "duration_ms" if "duration_ms" in columns else "null::integer"
                    )
                    failure_expr = (
                        "failure_reason" if "failure_reason" in columns else "null::text"
                    )
                    cursor.execute(
                        f"""
                        select version, name, checksum, applied_at::text as applied_at,
                               {duration_expr} as duration_ms,
                               {failure_expr} as failure_reason
                        from ojtflow.schema_migrations
                        order by version
                        """
                    )
                    known = {row["version"]: dict(row) for row in cursor.fetchall()}

        pending_versions = [
            migration.version for migration in migrations if migration.version not in known
        ]
        unknown_applied_versions = [
            version for version in known if version not in manifest_by_version
        ]
        checksum_mismatches = [
            version
            for version, row in known.items()
            if version in manifest_by_version
            and row["checksum"] != manifest_by_version[version].checksum
        ]
        applied_versions = [
            migration.version for migration in migrations if migration.version in known
        ]

        migration_rows: list[dict[str, object]] = []
        for migration in migrations:
            row = known.get(migration.version)
            status = "pending"
            applied_at = None
            duration_ms = None
            failure_reason = None
            checksum = migration.checksum
            if row:
                applied_at = row["applied_at"]
                duration_ms = row.get("duration_ms")
                failure_reason = row.get("failure_reason")
                if migration.version in checksum_mismatches:
                    status = "checksum_mismatch"
                    checksum = row["checksum"]
                else:
                    status = "applied"
            migration_rows.append(
                {
                    "version": migration.version,
                    "name": migration.name,
                    "checksum": checksum,
                    "status": status,
                    "applied_at": applied_at,
                    "duration_ms": duration_ms,
                    "failure_reason": failure_reason,
                }
            )
        for version in unknown_applied_versions:
            row = known[version]
            migration_rows.append(
                {
                    "version": version,
                    "name": row["name"],
                    "checksum": row["checksum"],
                    "status": "unknown_applied",
                    "applied_at": row["applied_at"],
                    "duration_ms": row.get("duration_ms"),
                    "failure_reason": row.get("failure_reason"),
                }
            )

        return {
            "table_exists": table_exists,
            "manifest_count": len(migrations),
            "applied_count": len(applied_versions),
            "pending_count": len(pending_versions),
            "unknown_applied_count": len(unknown_applied_versions),
            "checksum_mismatch_count": len(checksum_mismatches),
            "latest_available_version": migrations[-1].version if migrations else None,
            "latest_applied_version": applied_versions[-1] if applied_versions else None,
            "pending_versions": pending_versions,
            "unknown_applied_versions": unknown_applied_versions,
            "checksum_mismatches": checksum_mismatches,
            "migrations": migration_rows,
        }

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
                applied_at timestamptz not null default now(),
                duration_ms integer,
                failure_reason text,
                constraint schema_migrations_duration_check check (
                    duration_ms is null or duration_ms >= 0
                )
            )
            """
        )
        cursor.execute(
            """
            alter table ojtflow.schema_migrations
            add column if not exists duration_ms integer
            """
        )
        cursor.execute(
            """
            alter table ojtflow.schema_migrations
            add column if not exists failure_reason text
            """
        )
        cursor.execute(
            """
            do $$
            begin
                alter table ojtflow.schema_migrations
                add constraint schema_migrations_duration_check
                check (duration_ms is null or duration_ms >= 0);
            exception
                when duplicate_object then null;
            end $$;
            """
        )

    def _known_migrations(self, cursor) -> dict[str, str]:
        cursor.execute("select version, checksum from ojtflow.schema_migrations")
        return {row["version"]: row["checksum"] for row in cursor.fetchall()}

    def _schema_migration_columns(self, cursor) -> set[str]:
        cursor.execute(
            """
            select column_name
            from information_schema.columns
            where table_schema = 'ojtflow'
              and table_name = 'schema_migrations'
            """
        )
        return {row["column_name"] for row in cursor.fetchall()}


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
