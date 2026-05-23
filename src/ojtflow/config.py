"""Runtime settings for the backend scaffold."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Environment-backed settings with local demo defaults."""

    storage_backend: str = Field(default="postgres", alias="OJT_STORAGE_BACKEND")
    postgres_dsn: str = Field(
        default="postgresql://ojtflow:ojtflow@localhost:5432/ojtflow",
        alias="OJT_DATABASE_URL",
    )
    database_path: Path = Field(default=Path("var/ojtflow.db"), alias="OJT_DATABASE_PATH")
    data_dir: Path = Field(default=Path("var"), alias="OJT_DATA_DIR")

    @property
    def repo_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def resolved_database_path(self) -> Path:
        return _resolve_path(self.database_path, self.repo_root)

    @property
    def resolved_data_dir(self) -> Path:
        return _resolve_path(self.data_dir, self.repo_root)


def _resolve_path(path: Path, root: Path) -> Path:
    return path if path.is_absolute() else root / path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings."""

    return Settings(
        OJT_STORAGE_BACKEND=os.getenv("OJT_STORAGE_BACKEND", "postgres"),
        OJT_DATABASE_URL=os.getenv(
            "OJT_DATABASE_URL",
            os.getenv("DATABASE_URL", "postgresql://ojtflow:ojtflow@localhost:5432/ojtflow"),
        ),
        OJT_DATABASE_PATH=Path(os.getenv("OJT_DATABASE_PATH", "var/ojtflow.db")),
        OJT_DATA_DIR=Path(os.getenv("OJT_DATA_DIR", "var")),
    )


def clear_settings_cache() -> None:
    """Clear cached settings in tests."""

    get_settings.cache_clear()
