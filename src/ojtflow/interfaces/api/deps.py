"""API dependency assembly."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ojtflow.application.auth_service import AuthService, GoogleOAuthClient
from ojtflow.application.workflow_service import WorkflowService
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.config import Settings, get_settings
from ojtflow.infrastructure.cache.session_cache import RedisSessionCache
from ojtflow.infrastructure.retrieval.static import StaticKnowledgeRepository
from ojtflow.infrastructure.storage.auth_postgres import PostgresAuthRepository
from ojtflow.infrastructure.storage.in_memory import (
    InMemoryDatasetStore,
    InMemoryEventRepository,
    InMemoryWorkflowRepository,
)
from ojtflow.infrastructure.storage.postgres import (
    PostgresBackboneStore,
    PostgresDatasetStore,
    PostgresEventRepository,
    PostgresWorkflowRepository,
)
from ojtflow.infrastructure.storage.sqlite import (
    SQLiteBackboneStore,
    SQLiteDatasetStore,
    SQLiteEventRepository,
    SQLiteWorkflowRepository,
)


bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def _build_auth_service() -> AuthService:
    """Build Google OAuth session services."""

    settings = get_settings()
    repository = PostgresAuthRepository(settings.postgres_dsn)
    cache = RedisSessionCache(settings.redis_url)
    google_client = GoogleOAuthClient(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
    )
    return AuthService(
        repository=repository,
        cache=cache,
        google_client=google_client,
        google_redirect_uri=settings.google_redirect_uri,
        allowed_redirect_uris={
            settings.google_redirect_uri,
            settings.google_frontend_redirect_uri,
        },
        session_ttl_seconds=settings.auth_session_ttl_seconds,
        state_ttl_seconds=settings.auth_state_ttl_seconds,
    )


@lru_cache(maxsize=1)
def _build_workflow_service() -> WorkflowService:
    """Build the default local service graph."""

    repo_root = Path(__file__).resolve().parents[4]
    settings = get_settings()
    if settings.storage_backend == "memory":
        datasets = InMemoryDatasetStore()
        workflows = InMemoryWorkflowRepository()
        events = InMemoryEventRepository()
    elif settings.storage_backend == "sqlite":
        backbone = SQLiteBackboneStore(
            settings.resolved_database_path,
            settings.resolved_data_dir,
        )
        datasets = SQLiteDatasetStore(backbone)
        workflows = SQLiteWorkflowRepository(backbone)
        events = SQLiteEventRepository(backbone)
    elif settings.storage_backend == "postgres":
        backbone = PostgresBackboneStore(
            settings.postgres_dsn,
            settings.resolved_data_dir,
        )
        datasets = PostgresDatasetStore(backbone)
        workflows = PostgresWorkflowRepository(backbone)
        events = PostgresEventRepository(backbone)
    else:
        raise ValueError(f"Unsupported storage backend: {settings.storage_backend}")

    return WorkflowService(
        datasets=datasets,
        workflows=workflows,
        events=events,
        knowledge=StaticKnowledgeRepository(repo_root / "knowledge"),
    )


async def get_workflow_service() -> WorkflowService:
    """Return the cached workflow service without FastAPI threadpool dispatch."""

    return _build_workflow_service()


async def get_auth_service() -> AuthService:
    """Return the cached auth service without FastAPI threadpool dispatch."""

    return _build_auth_service()


def bearer_token_from_credentials(
    credentials: HTTPAuthorizationCredentials | None,
) -> str:
    """Extract a bearer token from HTTP bearer credentials."""

    if not credentials:
        raise HTTPException(status_code=401, detail="Missing Authorization header.")
    if credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Expected Bearer token.")
    return credentials.credentials.strip()


async def require_authentication(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> AuthenticatedSession:
    """Require a valid backend session token for protected routes."""

    token = bearer_token_from_credentials(credentials)
    service = _build_auth_service()
    authenticated = service.authenticate_token(token)
    if not authenticated:
        raise HTTPException(status_code=401, detail="Invalid or expired session token.")
    return authenticated


async def get_api_settings() -> Settings:
    """Return settings without FastAPI threadpool dispatch."""

    return get_settings()


def clear_workflow_service_cache() -> None:
    """Clear cached service graph in tests."""

    _build_workflow_service.cache_clear()
    _build_auth_service.cache_clear()
