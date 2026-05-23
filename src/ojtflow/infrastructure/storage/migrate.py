"""Command-line migration entrypoint."""

from __future__ import annotations

from ojtflow.config import get_settings
from ojtflow.infrastructure.storage.migrations import PostgresMigrator


def main() -> None:
    settings = get_settings()
    applied = PostgresMigrator(settings.postgres_dsn).apply()
    if applied:
        print("Applied migrations:", ", ".join(applied))
    else:
        print("No pending migrations")


if __name__ == "__main__":
    main()

