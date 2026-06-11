"""API dependency assembly."""

from __future__ import annotations

from functools import lru_cache
from urllib.parse import urlparse

from fastapi import Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ojtflow.application.auth_service import AuthService
from ojtflow.application.assistant_service import AssistantService
from ojtflow.application.assistant_session_service import AssistantSessionService
from ojtflow.application.background_job_service import BackgroundJobService
from ojtflow.application.assistant_tools import OJTFlowToolExecutor
from ojtflow.application.document_intake_service import DocumentIntakeService
from ojtflow.application.medical_evidence_service import MedicalEvidenceService
from ojtflow.application.retrieval_judgment_service import RetrievalJudgmentService
from ojtflow.application.workflow_service import WorkflowService
from ojtflow.config import Settings, get_settings
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.core.errors import AuthenticationError
from ojtflow.infrastructure.auth.google import GoogleOAuthClient
from ojtflow.infrastructure.cache.session_cache import InMemorySessionCache, RedisSessionCache
from ojtflow.infrastructure.assistant.policies import load_assistant_tool_permission_policies
from ojtflow.infrastructure.llm.openai import OpenAIResponsesPlanner
from ojtflow.infrastructure.retrieval.embeddings import build_embedding_provider
from ojtflow.infrastructure.retrieval.evaluation_policy import (
    load_retrieval_evaluation_policy,
)
from ojtflow.infrastructure.retrieval.llamaindex_adapter import LlamaIndexRetrievalRepository
from ojtflow.infrastructure.retrieval.postgres import PostgresRetrievalRepository
from ojtflow.infrastructure.retrieval.reranking import build_reranker
from ojtflow.infrastructure.retrieval.rule_packs import retrieval_rule_packs
from ojtflow.infrastructure.retrieval.static import StaticKnowledgeRepository
from ojtflow.infrastructure.retrieval.static import StaticRetrievalRepository
from ojtflow.infrastructure.extraction.document import LocalDocumentExtractor
from ojtflow.infrastructure.storage.auth_memory import InMemoryAuthRepository
from ojtflow.infrastructure.storage.auth_postgres import PostgresAuthRepository
from ojtflow.infrastructure.storage.auth_sqlite import SQLiteAuthRepository
from ojtflow.infrastructure.storage.in_memory import (
    InMemoryAssistantSessionRepository,
    InMemoryUploadedArtifactRepository,
    InMemoryBackgroundJobRepository,
    InMemoryDatasetStore,
    InMemoryEventRepository,
    InMemoryRetrievalJudgmentRepository,
    InMemoryWorkflowRepository,
)
from ojtflow.infrastructure.storage.postgres import (
    PostgresAssistantSessionRepository,
    PostgresUploadedArtifactRepository,
    PostgresBackboneStore,
    PostgresBackgroundJobRepository,
    PostgresDatasetStore,
    PostgresEventRepository,
    PostgresRetrievalJudgmentRepository,
    PostgresWorkflowRepository,
)
from ojtflow.infrastructure.storage.sqlite import (
    SQLiteAssistantSessionRepository,
    SQLiteUploadedArtifactRepository,
    SQLiteBackboneStore,
    SQLiteBackgroundJobRepository,
    SQLiteDatasetStore,
    SQLiteEventRepository,
    SQLiteRetrievalJudgmentRepository,
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
    embedding_provider = build_embedding_provider(settings)
    reranker = build_reranker(settings)
    if settings.storage_backend == "memory":
        datasets = InMemoryDatasetStore()
        workflows = InMemoryWorkflowRepository()
        events = InMemoryEventRepository()
        retrieval = _build_retrieval_repository(
            settings,
            knowledge_root,
            embedding_provider,
            reranker,
        )
    elif settings.storage_backend == "sqlite":
        backbone = SQLiteBackboneStore(
            settings.resolved_database_path,
            settings.resolved_data_dir,
        )
        datasets = SQLiteDatasetStore(backbone)
        workflows = SQLiteWorkflowRepository(backbone)
        events = SQLiteEventRepository(backbone)
        retrieval = _build_retrieval_repository(
            settings,
            knowledge_root,
            embedding_provider,
            reranker,
        )
    elif settings.storage_backend == "postgres":
        backbone = PostgresBackboneStore(
            settings.postgres_dsn,
            settings.resolved_data_dir,
        )
        datasets = PostgresDatasetStore(backbone)
        workflows = PostgresWorkflowRepository(backbone)
        events = PostgresEventRepository(backbone)
        retrieval = _build_retrieval_repository(
            settings,
            knowledge_root,
            embedding_provider,
            reranker,
            postgres_backbone=backbone,
        )
    else:
        raise ValueError(f"Unsupported storage backend: {settings.storage_backend}")

    return WorkflowService(
        datasets=datasets,
        workflows=workflows,
        events=events,
        knowledge=StaticKnowledgeRepository(knowledge_root),
        retrieval=retrieval,
        retrieval_rule_packs=retrieval_rule_packs(knowledge_root),
    )


@lru_cache(maxsize=1)
def _build_retrieval_judgment_service() -> RetrievalJudgmentService:
    """Build durable retrieval relevance judgment services."""

    settings = get_settings()
    if settings.storage_backend == "memory":
        repository = InMemoryRetrievalJudgmentRepository()
    elif settings.storage_backend == "sqlite":
        backbone = SQLiteBackboneStore(
            settings.resolved_database_path,
            settings.resolved_data_dir,
        )
        repository = SQLiteRetrievalJudgmentRepository(backbone)
    elif settings.storage_backend == "postgres":
        backbone = PostgresBackboneStore(
            settings.postgres_dsn,
            settings.resolved_data_dir,
        )
        repository = PostgresRetrievalJudgmentRepository(backbone)
    else:
        raise ValueError(f"Unsupported storage backend: {settings.storage_backend}")
    return RetrievalJudgmentService(
        repository,
        evaluation_policy_rules=load_retrieval_evaluation_policy(settings.resolved_knowledge_dir),
    )


def _build_retrieval_repository(
    settings: Settings,
    knowledge_root,
    embedding_provider,
    reranker,
    *,
    postgres_backbone=None,
):
    if settings.retrieval_framework == "llamaindex":
        return LlamaIndexRetrievalRepository(
            knowledge_root,
            embedding_provider=embedding_provider,
            corpus_dirs=settings.resolved_retrieval_corpus_dirs,
            chunk_max_chars=settings.retrieval_chunk_max_chars,
            chunk_overlap_chars=settings.retrieval_chunk_overlap_chars,
            candidate_multiplier=settings.retrieval_candidate_multiplier,
            min_candidates=settings.retrieval_min_candidates,
            vector_weight=settings.retrieval_vector_weight,
            bm25_weight=settings.retrieval_bm25_weight,
        )
    if postgres_backbone is not None:
        return PostgresRetrievalRepository(
            postgres_backbone,
            knowledge_root,
            embedding_provider,
            reranker=reranker,
            rerank_candidate_limit=settings.rerank_candidate_limit,
            rerank_score_weight=settings.rerank_score_weight,
            diversity_enabled=settings.retrieval_diversity_enabled,
            diversity_lambda=settings.retrieval_diversity_lambda,
            corpus_dirs=settings.resolved_retrieval_corpus_dirs,
            chunk_max_chars=settings.retrieval_chunk_max_chars,
            chunk_overlap_chars=settings.retrieval_chunk_overlap_chars,
            hnsw_ef_search=settings.retrieval_hnsw_ef_search,
        )
    return StaticRetrievalRepository(
        knowledge_root,
        embedding_provider,
        reranker=reranker,
        rerank_candidate_limit=settings.rerank_candidate_limit,
        rerank_score_weight=settings.rerank_score_weight,
        diversity_enabled=settings.retrieval_diversity_enabled,
        diversity_lambda=settings.retrieval_diversity_lambda,
        corpus_dirs=settings.resolved_retrieval_corpus_dirs,
        chunk_max_chars=settings.retrieval_chunk_max_chars,
        chunk_overlap_chars=settings.retrieval_chunk_overlap_chars,
    )


@lru_cache(maxsize=1)
def _build_medical_evidence_service() -> MedicalEvidenceService:
    return MedicalEvidenceService()


@lru_cache(maxsize=1)
def _build_assistant_service() -> AssistantService:
    settings = get_settings()
    planner = None
    if settings.llm_provider == "openai":
        planner = OpenAIResponsesPlanner(
            api_key=settings.openai_api_key,
            model=settings.llm_model,
            planning_model=settings.llm_planning_model,
            synthesis_model=settings.llm_synthesis_model,
            base_url=settings.llm_base_url,
            timeout_seconds=settings.llm_timeout_seconds,
        )
    return AssistantService(
        OJTFlowToolExecutor(
            workflow_service=_build_workflow_service(),
            medical_evidence_service=_build_medical_evidence_service(),
            tool_permission_policies=load_assistant_tool_permission_policies(
                settings.resolved_knowledge_dir
            ),
        ),
        planner=planner,
        max_tool_calls=settings.llm_max_tool_calls,
        planning_progress_interval_seconds=settings.llm_planning_progress_interval_seconds,
    )


@lru_cache(maxsize=1)
def _build_assistant_session_service() -> AssistantSessionService:
    settings = get_settings()
    if settings.storage_backend == "memory":
        repository = InMemoryAssistantSessionRepository()
    elif settings.storage_backend == "sqlite":
        backbone = SQLiteBackboneStore(
            settings.resolved_database_path,
            settings.resolved_data_dir,
        )
        repository = SQLiteAssistantSessionRepository(backbone)
    elif settings.storage_backend == "postgres":
        backbone = PostgresBackboneStore(
            settings.postgres_dsn,
            settings.resolved_data_dir,
        )
        repository = PostgresAssistantSessionRepository(backbone)
    else:
        raise ValueError(f"Unsupported storage backend: {settings.storage_backend}")
    return AssistantSessionService(repository)


@lru_cache(maxsize=1)
def _build_background_job_service() -> BackgroundJobService:
    settings = get_settings()
    if settings.storage_backend == "memory":
        repository = InMemoryBackgroundJobRepository()
    elif settings.storage_backend == "sqlite":
        backbone = SQLiteBackboneStore(
            settings.resolved_database_path,
            settings.resolved_data_dir,
        )
        repository = SQLiteBackgroundJobRepository(backbone)
    elif settings.storage_backend == "postgres":
        backbone = PostgresBackboneStore(
            settings.postgres_dsn,
            settings.resolved_data_dir,
        )
        repository = PostgresBackgroundJobRepository(backbone)
    else:
        raise ValueError(f"Unsupported storage backend: {settings.storage_backend}")
    return BackgroundJobService(repository)


@lru_cache(maxsize=1)
def _build_document_intake_service() -> DocumentIntakeService:
    settings = get_settings()
    if settings.storage_backend == "memory":
        artifacts = InMemoryUploadedArtifactRepository()
        datasets = InMemoryDatasetStore()
    elif settings.storage_backend == "sqlite":
        backbone = SQLiteBackboneStore(
            settings.resolved_database_path,
            settings.resolved_data_dir,
        )
        artifacts = SQLiteUploadedArtifactRepository(backbone)
        datasets = SQLiteDatasetStore(backbone)
    elif settings.storage_backend == "postgres":
        backbone = PostgresBackboneStore(
            settings.postgres_dsn,
            settings.resolved_data_dir,
        )
        artifacts = PostgresUploadedArtifactRepository(backbone)
        datasets = PostgresDatasetStore(backbone)
    else:
        raise ValueError(f"Unsupported storage backend: {settings.storage_backend}")
    return DocumentIntakeService(
        artifacts=artifacts,
        datasets=datasets,
        jobs=_build_background_job_service(),
        extractor=LocalDocumentExtractor(),
        product_mode=settings.product_mode,
        retention_rules=settings.artifact_retention_rules,
    )


async def get_workflow_service() -> WorkflowService:
    """Return the cached workflow service without FastAPI threadpool dispatch."""

    return _build_workflow_service()


async def get_medical_evidence_service() -> MedicalEvidenceService:
    """Return healthcare evidence service."""

    return _build_medical_evidence_service()


async def get_retrieval_judgment_service() -> RetrievalJudgmentService:
    """Return durable retrieval relevance judgment service."""

    return _build_retrieval_judgment_service()


async def get_assistant_service() -> AssistantService:
    """Return natural-language assistant service."""

    return _build_assistant_service()


async def get_assistant_session_service() -> AssistantSessionService:
    """Return persisted Assistant chat session service."""

    return _build_assistant_session_service()


async def get_background_job_service() -> BackgroundJobService:
    """Return durable background job service."""

    return _build_background_job_service()


async def get_document_intake_service() -> DocumentIntakeService:
    """Return uploaded document intake service."""

    return _build_document_intake_service()


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
    _build_retrieval_judgment_service.cache_clear()
    _build_assistant_service.cache_clear()
    _build_assistant_session_service.cache_clear()
    _build_background_job_service.cache_clear()
    _build_document_intake_service.cache_clear()
