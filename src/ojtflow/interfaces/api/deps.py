"""API dependency assembly."""

from __future__ import annotations

from functools import lru_cache
from urllib.parse import urlparse

from fastapi import Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ojtflow.application.auth_service import AuthService
from ojtflow.application.medical_evidence_service import MedicalEvidenceService
from ojtflow.application.workflow_service import WorkflowService
from ojtflow.config import Settings, get_settings
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.core.errors import AuthenticationError
from ojtflow.infrastructure.auth.google import GoogleOAuthClient
from ojtflow.infrastructure.cache.session_cache import InMemorySessionCache, RedisSessionCache
from ojtflow.infrastructure.retrieval.engine import DeterministicEmbeddingProvider
from ojtflow.infrastructure.retrieval.postgres import PostgresRetrievalRepository
from ojtflow.infrastructure.retrieval.static import StaticKnowledgeRepository
from ojtflow.infrastructure.retrieval.static import StaticRetrievalRepository
from ojtflow.infrastructure.storage.auth_memory import InMemoryAuthRepository
from ojtflow.infrastructure.storage.auth_postgres import PostgresAuthRepository
from ojtflow.infrastructure.storage.auth_sqlite import SQLiteAuthRepository
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
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@lru_cache(maxsize=1)
def _build_auth_service() -> AuthService:
    """Build Google OAuth session services."""

    settings = get_settings()
    if settings.storage_backend == "memory":
        repository = InMemoryAuthRepository()
        cache = InMemorySessionCache()
    elif settings.storage_backend == "sqlite":
        backbone = SQLiteBackboneStore(
            settings.resolved_database_path,
            settings.resolved_data_dir,
        )
        repository = SQLiteAuthRepository(backbone)
        cache = InMemorySessionCache()
    elif settings.storage_backend == "postgres":
        repository = PostgresAuthRepository(settings.postgres_dsn)
        cache = RedisSessionCache(settings.redis_url, allow_fallback=False)
    else:
        raise ValueError(f"Unsupported storage backend: {settings.storage_backend}")

    google_client = GoogleOAuthClient(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        timeout_seconds=settings.google_oauth_timeout_seconds,
        allowed_hosted_domains=set(settings.allowed_google_hosted_domains),
    )
    return AuthService(
        repository=repository,
        cache=cache,
        identity_provider=google_client,
        google_redirect_uri=settings.google_redirect_uri,
        allowed_redirect_uris=settings.resolved_allowed_auth_redirect_uris,
        session_ttl_seconds=settings.auth_session_ttl_seconds,
        state_ttl_seconds=settings.auth_state_ttl_seconds,
    )


@lru_cache(maxsize=1)
def _build_workflow_service() -> WorkflowService:
    """Build the default local service graph."""

    settings = get_settings()
    knowledge_root = settings.resolved_knowledge_dir
    embedding_provider = DeterministicEmbeddingProvider(settings.embedding_dimensions)
    if settings.storage_backend == "memory":
        datasets = InMemoryDatasetStore()
        workflows = InMemoryWorkflowRepository()
        events = InMemoryEventRepository()
        retrieval = StaticRetrievalRepository(knowledge_root, embedding_provider)
    elif settings.storage_backend == "sqlite":
        backbone = SQLiteBackboneStore(
            settings.resolved_database_path,
            settings.resolved_data_dir,
        )
        datasets = SQLiteDatasetStore(backbone)
        workflows = SQLiteWorkflowRepository(backbone)
        events = SQLiteEventRepository(backbone)
        retrieval = StaticRetrievalRepository(knowledge_root, embedding_provider)
    elif settings.storage_backend == "postgres":
        backbone = PostgresBackboneStore(
            settings.postgres_dsn,
            settings.resolved_data_dir,
        )
        datasets = PostgresDatasetStore(backbone)
        workflows = PostgresWorkflowRepository(backbone)
        events = PostgresEventRepository(backbone)
        retrieval = PostgresRetrievalRepository(backbone, knowledge_root, embedding_provider)
    else:
        raise ValueError(f"Unsupported storage backend: {settings.storage_backend}")

    return WorkflowService(
        datasets=datasets,
        workflows=workflows,
        events=events,
        knowledge=StaticKnowledgeRepository(knowledge_root),
        retrieval=retrieval,
    )


@lru_cache(maxsize=1)
def _build_medical_evidence_service() -> MedicalEvidenceService:
    return MedicalEvidenceService()


async def get_workflow_service() -> WorkflowService:
    """Return the cached workflow service without FastAPI threadpool dispatch."""

    return _build_workflow_service()


async def get_medical_evidence_service() -> MedicalEvidenceService:
    """Return healthcare evidence service."""

    return _build_medical_evidence_service()


async def get_auth_service() -> AuthService:
    """Return the cached auth service without FastAPI threadpool dispatch."""

    return _build_auth_service()


def bearer_token_from_credentials(
    credentials: HTTPAuthorizationCredentials | None,
) -> str:
    """Extract a bearer token from HTTP bearer credentials."""

    if not credentials:
        raise AuthenticationError("Missing Authorization header.")
    if credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise AuthenticationError("Expected Bearer token.")
    token = credentials.credentials.strip()
    if not token:
        raise AuthenticationError("Expected Bearer token.")
    return token


def session_token_from_request(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str:
    """Resolve a session token from bearer credentials or the configured auth cookie."""

    if credentials:
        return bearer_token_from_credentials(credentials)

    settings = get_settings()
    cookie_token = request.cookies.get(settings.auth_cookie_name)
    if cookie_token and cookie_token.strip():
        _enforce_cookie_origin(request, settings)
        return cookie_token.strip()
    raise AuthenticationError("Missing authenticated session.")


async def require_authentication(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> AuthenticatedSession:
    """Require a valid backend session token for protected routes."""

    token = session_token_from_request(request, credentials)
    service = _build_auth_service()
    authenticated = service.authenticate_token(token)
    if not authenticated:
        raise AuthenticationError("Invalid or expired session token.")
    return authenticated


def _enforce_cookie_origin(request: Request, settings: Settings) -> None:
    if request.method.upper() not in UNSAFE_METHODS:
        return

    origin = _origin_from_header(request.headers.get("origin"))
    if origin is None:
        origin = _origin_from_header(request.headers.get("referer"))
    if origin is None:
        raise AuthenticationError(
            "Cookie-authenticated write requests require a trusted Origin header."
        )

    allowed_origins = _allowed_cookie_origins(request, settings)
    if origin not in allowed_origins:
        raise AuthenticationError(
            "Cookie-authenticated write request Origin is not trusted."
        )


def _allowed_cookie_origins(request: Request, settings: Settings) -> set[str]:
    origins = {
        origin
        for origin in (
            _origin_from_header(str(request.base_url)),
            _origin_from_header(settings.google_redirect_uri),
            _origin_from_header(settings.google_frontend_redirect_uri),
            *(
                _origin_from_header(uri)
                for uri in settings.allowed_auth_redirect_uris
            ),
        )
        if origin
    }
    return origins


def _origin_from_header(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    scheme = parsed.scheme.lower()
    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return None
    try:
        parsed_port = parsed.port
    except ValueError:
        return None
    port = f":{parsed_port}" if parsed_port else ""
    return f"{scheme}://{hostname}{port}"


async def get_api_settings() -> Settings:
    """Return settings without FastAPI threadpool dispatch."""

    return get_settings()


def clear_workflow_service_cache() -> None:
    """Clear cached service graph in tests."""

    _build_workflow_service.cache_clear()
    _build_auth_service.cache_clear()
    _build_medical_evidence_service.cache_clear()
