#!/usr/bin/env python3
"""Validate the Postgres migration manifest without connecting to a database."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ojtflow.core.errors import OJTFlowError  # noqa: E402
from ojtflow.infrastructure.storage.migrations import PostgresMigrator  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate ordered Postgres SQL migration files.",
    )
    parser.add_argument(
        "--migrations-dir",
        default="sql/postgres/migrations",
        help="Path to Postgres migration SQL directory.",
    )
    parser.add_argument(
        "--allow-gaps",
        action="store_true",
        help="Allow numeric version gaps. By default versions must be contiguous.",
    )
    args = parser.parse_args()

    migrations_dir = _resolve_path(args.migrations_dir)
    try:
        migrations = PostgresMigrator(
            "postgresql://manifest-only/unused",
            migrations_dir=migrations_dir,
        ).load_migrations()
    except OJTFlowError as exc:
        print(f"migration_manifest_error: {exc}", file=sys.stderr)
        return 1

    versions = [migration.version for migration in migrations]
    if not args.allow_gaps:
        expected = [f"{index:03d}" for index in range(1, len(versions) + 1)]
        if versions != expected:
            print(
                "migration_manifest_error: versions must be contiguous from 001; "
                f"expected {expected}, got {versions}",
                file=sys.stderr,
            )
            return 1

    duplicate_checksums = _duplicate_checksums(migrations)
    if duplicate_checksums:
        print(
            "migration_manifest_error: duplicate SQL checksums for versions "
            + ", ".join(duplicate_checksums),
            file=sys.stderr,
        )
        return 1

    print(
        "Migration manifest OK: "
        f"{len(migrations)} file(s), latest={versions[-1]}, "
        f"dir={_display_path(migrations_dir)}"
    )
    return 0


def _duplicate_checksums(migrations) -> list[str]:
    by_checksum: dict[str, list[str]] = {}
    for migration in migrations:
        by_checksum.setdefault(migration.checksum, []).append(migration.version)
    return [
        "/".join(versions)
        for versions in by_checksum.values()
        if len(versions) > 1
    ]


def _resolve_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
