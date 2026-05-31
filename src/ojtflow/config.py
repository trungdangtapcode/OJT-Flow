"""Runtime settings for the backend scaffold."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field


DEFAULT_ALLOWED_UPLOAD_EXTENSIONS = (
    ".pdf",
    ".docx",
    ".xlsx",
    ".xls",
    ".pptx",
    ".png",
    ".jpg",
    ".jpeg",
    ".tiff",
    ".tif",
    ".bmp",
    ".gif",
    ".webp",
    ".html",
    ".htm",
    ".md",
    ".txt",
    ".csv",
    ".json",
    ".yaml",
    ".yml",
)


class Settings(BaseModel):
    """Environment-backed settings with local demo defaults."""

    storage_backend: str = Field(default="postgres", alias="OJT_STORAGE_BACKEND")
    postgres_dsn: str = Field(
        default="postgresql://ojtflow:ojtflow@localhost:5432/ojtflow",
        alias="OJT_DATABASE_URL",
    )
    database_path: Path = Field(default=Path("var/ojtflow.db"), alias="OJT_DATABASE_PATH")
    data_dir: Path = Field(default=Path("var"), alias="OJT_DATA_DIR")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="OJT_REDIS_URL")
    google_client_id: str = Field(default="", alias="OJT_GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(default="", alias="OJT_GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(
        default="http://localhost:8000/api/v1/auth/google/callback",
        alias="OJT_GOOGLE_REDIRECT_URI",
    )
    google_frontend_redirect_uri: str = Field(
        default="http://localhost:5173/auth/callback",
        alias="OJT_GOOGLE_FRONTEND_REDIRECT_URI",
    )
    allowed_auth_redirect_uris: tuple[str, ...] = Field(
        default=(),
        alias="OJT_ALLOWED_AUTH_REDIRECT_URIS",
    )
    allowed_google_hosted_domains: tuple[str, ...] = Field(
        default=(),
        alias="OJT_ALLOWED_GOOGLE_HOSTED_DOMAINS",
    )
    google_oauth_timeout_seconds: float = Field(
        default=10.0,
        alias="OJT_GOOGLE_OAUTH_TIMEOUT_SECONDS",
    )
    auth_session_ttl_seconds: int = Field(
        default=7 * 24 * 60 * 60,
        alias="OJT_AUTH_SESSION_TTL_SECONDS",
    )
    auth_state_ttl_seconds: int = Field(default=10 * 60, alias="OJT_AUTH_STATE_TTL_SECONDS")
    auth_cookie_name: str = Field(default="ojtflow_session", alias="OJT_AUTH_COOKIE_NAME")
    auth_cookie_secure: bool = Field(default=False, alias="OJT_AUTH_COOKIE_SECURE")
    auth_cookie_samesite: str = Field(default="lax", alias="OJT_AUTH_COOKIE_SAMESITE")
    auth_cookie_domain: str | None = Field(default=None, alias="OJT_AUTH_COOKIE_DOMAIN")
    max_upload_bytes: int = Field(default=25 * 1024 * 1024, alias="OJT_MAX_UPLOAD_BYTES")
    upload_read_chunk_bytes: int = Field(
        default=1024 * 1024,
        alias="OJT_UPLOAD_READ_CHUNK_BYTES",
    )
    allowed_upload_extensions: tuple[str, ...] = Field(
        default=DEFAULT_ALLOWED_UPLOAD_EXTENSIONS,
        alias="OJT_ALLOWED_UPLOAD_EXTENSIONS",
    )

    @property
    def repo_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def resolved_database_path(self) -> Path:
        return _resolve_path(self.database_path, self.repo_root)

    @property
    def resolved_data_dir(self) -> Path:
        return _resolve_path(self.data_dir, self.repo_root)

    @property
    def resolved_allowed_auth_redirect_uris(self) -> set[str]:
        return {
            uri
            for uri in (
                self.google_redirect_uri,
                self.google_frontend_redirect_uri,
                *self.allowed_auth_redirect_uris,
            )
            if uri
        }


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
        OJT_REDIS_URL=os.getenv("OJT_REDIS_URL", "redis://localhost:6379/0"),
        OJT_GOOGLE_CLIENT_ID=os.getenv("OJT_GOOGLE_CLIENT_ID", ""),
        OJT_GOOGLE_CLIENT_SECRET=os.getenv("OJT_GOOGLE_CLIENT_SECRET", ""),
        OJT_GOOGLE_REDIRECT_URI=os.getenv(
            "OJT_GOOGLE_REDIRECT_URI",
            "http://localhost:8000/api/v1/auth/google/callback",
        ),
        OJT_GOOGLE_FRONTEND_REDIRECT_URI=os.getenv(
            "OJT_GOOGLE_FRONTEND_REDIRECT_URI",
            "http://localhost:5173/auth/callback",
        ),
        OJT_ALLOWED_AUTH_REDIRECT_URIS=_parse_csv_strings(
            os.getenv("OJT_ALLOWED_AUTH_REDIRECT_URIS")
        ),
        OJT_ALLOWED_GOOGLE_HOSTED_DOMAINS=_parse_csv_strings(
            os.getenv("OJT_ALLOWED_GOOGLE_HOSTED_DOMAINS")
        ),
        OJT_GOOGLE_OAUTH_TIMEOUT_SECONDS=float(
            os.getenv("OJT_GOOGLE_OAUTH_TIMEOUT_SECONDS", "10.0")
        ),
        OJT_AUTH_SESSION_TTL_SECONDS=int(
            os.getenv("OJT_AUTH_SESSION_TTL_SECONDS", str(7 * 24 * 60 * 60))
        ),
        OJT_AUTH_STATE_TTL_SECONDS=int(os.getenv("OJT_AUTH_STATE_TTL_SECONDS", str(10 * 60))),
        OJT_AUTH_COOKIE_NAME=os.getenv("OJT_AUTH_COOKIE_NAME") or "ojtflow_session",
        OJT_AUTH_COOKIE_SECURE=_parse_bool(os.getenv("OJT_AUTH_COOKIE_SECURE"), default=False),
        OJT_AUTH_COOKIE_SAMESITE=_parse_same_site(os.getenv("OJT_AUTH_COOKIE_SAMESITE")),
        OJT_AUTH_COOKIE_DOMAIN=os.getenv("OJT_AUTH_COOKIE_DOMAIN") or None,
        OJT_MAX_UPLOAD_BYTES=int(os.getenv("OJT_MAX_UPLOAD_BYTES", str(25 * 1024 * 1024))),
        OJT_UPLOAD_READ_CHUNK_BYTES=int(
            os.getenv("OJT_UPLOAD_READ_CHUNK_BYTES", str(1024 * 1024))
        ),
        OJT_ALLOWED_UPLOAD_EXTENSIONS=_parse_extensions(
            os.getenv("OJT_ALLOWED_UPLOAD_EXTENSIONS")
        ),
    )


def clear_settings_cache() -> None:
    """Clear cached settings in tests."""

    get_settings.cache_clear()


def _parse_extensions(value: str | None) -> tuple[str, ...]:
    if not value:
        return DEFAULT_ALLOWED_UPLOAD_EXTENSIONS
    extensions: list[str] = []
    for item in value.split(","):
        normalized = item.strip().lower()
        if not normalized:
            continue
        extensions.append(normalized if normalized.startswith(".") else f".{normalized}")
    return tuple(extensions) or DEFAULT_ALLOWED_UPLOAD_EXTENSIONS


def _parse_csv_strings(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _parse_bool(value: str | None, *, default: bool) -> bool:
    if value is None or value == "":
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"Invalid boolean environment value: {value}")


def _parse_same_site(value: str | None) -> str:
    normalized = (value or "lax").strip().lower()
    if normalized in {"lax", "strict", "none"}:
        return normalized
    raise ValueError(f"Invalid SameSite environment value: {value}")
