"""Runtime settings for the backend scaffold."""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from ipaddress import ip_address
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field, model_validator


EmbeddingProvider = Literal["deterministic", "openai", "huggingface"]
LLMProvider = Literal["disabled", "openai"]
ProductMode = Literal["local_dev", "demo", "pilot", "production"]
RetrievalFramework = Literal["custom", "llamaindex"]
RerankProvider = Literal["none", "huggingface"]
StorageBackend = Literal["postgres", "sqlite", "memory"]
RuntimeSettingsPayload = dict[str, str | int | float | bool]
RuntimeRetrievalSettingsPayload = RuntimeSettingsPayload
RuntimeAssistantSettingsPayload = RuntimeSettingsPayload
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
COOKIE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9!#$%&'*+\-.^_`|~]+$")
DNS_LABEL_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
UPLOAD_EXTENSION_PATTERN = re.compile(r"^\.[a-z0-9][a-z0-9-]{0,15}$")
ALLOWED_STORAGE_BACKENDS: tuple[StorageBackend, ...] = ("postgres", "sqlite", "memory")
ALLOWED_PRODUCT_MODES: tuple[ProductMode, ...] = (
    "local_dev",
    "demo",
    "pilot",
    "production",
)
ALLOWED_EMBEDDING_PROVIDERS: tuple[EmbeddingProvider, ...] = (
    "deterministic",
    "openai",
    "huggingface",
)
ALLOWED_LLM_PROVIDERS: tuple[LLMProvider, ...] = ("disabled", "openai")
ALLOWED_RERANK_PROVIDERS: tuple[RerankProvider, ...] = ("none", "huggingface")
ALLOWED_RETRIEVAL_FRAMEWORKS: tuple[RetrievalFramework, ...] = ("custom", "llamaindex")
DETERMINISTIC_EMBEDDING_MODEL = "deterministic-hash-v0"
DETERMINISTIC_EMBEDDING_DIMENSIONS = 64
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
OPENAI_EMBEDDING_DIMENSIONS = 384
OPENAI_EMBEDDING_BASE_URL = "https://api.openai.com/v1"
OPENAI_LLM_MODEL = "chat-latest"
OPENAI_VISION_MODEL = "gpt-4.1-mini"
HUGGINGFACE_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
HUGGINGFACE_EMBEDDING_DIMENSIONS = 384
HUGGINGFACE_RERANK_MODEL = "BAAI/bge-reranker-base"
DEFAULT_HF_EMBEDDING_CACHE_DIR = Path("var/huggingface")
DEFAULT_RETRIEVAL_CORPUS_DIRS = (Path("knowledge/corpus"),)
DEFAULT_RETRIEVAL_HNSW_EF_SEARCH = 100
DEFAULT_STORAGE_BACKEND: StorageBackend = "postgres"
DEFAULT_POSTGRES_DSN = "postgresql://ojtflow:ojtflow@localhost:5432/ojtflow"
DEFAULT_DATABASE_PATH = Path("var/ojtflow.db")
DEFAULT_DATA_DIR = Path("var")
DEFAULT_RUNTIME_SETTINGS_PATH = Path("var/runtime_settings.json")
DEFAULT_KNOWLEDGE_DIR = Path("knowledge")
DEFAULT_MIGRATIONS_DIR = Path("sql/postgres/migrations")
DEFAULT_REDIS_URL = "redis://localhost:6379/0"
DEFAULT_GOOGLE_REDIRECT_URI = "http://localhost:8000/api/v1/auth/google/callback"
DEFAULT_GOOGLE_FRONTEND_REDIRECT_URI = "http://localhost:5173/auth/callback"
LOCAL_OAUTH_REDIRECT_HOSTS = {"localhost", "127.0.0.1", "::1"}
RUNTIME_RETRIEVAL_SETTING_ALIASES = {
    "embedding_provider": "OJT_EMBEDDING_PROVIDER",
    "embedding_model": "OJT_EMBEDDING_MODEL",
    "embedding_dimensions": "OJT_EMBEDDING_DIMENSIONS",
    "retrieval_framework": "OJT_RETRIEVAL_FRAMEWORK",
    "retrieval_candidate_multiplier": "OJT_RETRIEVAL_CANDIDATE_MULTIPLIER",
    "retrieval_min_candidates": "OJT_RETRIEVAL_MIN_CANDIDATES",
    "retrieval_vector_weight": "OJT_RETRIEVAL_VECTOR_WEIGHT",
    "retrieval_bm25_weight": "OJT_RETRIEVAL_BM25_WEIGHT",
    "retrieval_diversity_enabled": "OJT_RETRIEVAL_DIVERSITY_ENABLED",
    "retrieval_diversity_lambda": "OJT_RETRIEVAL_DIVERSITY_LAMBDA",
    "retrieval_hnsw_ef_search": "OJT_RETRIEVAL_HNSW_EF_SEARCH",
}
RUNTIME_ASSISTANT_SETTING_ALIASES = {
    "llm_provider": "OJT_LLM_PROVIDER",
    "llm_model": "OJT_LLM_MODEL",
    "llm_planning_model": "OJT_LLM_PLANNING_MODEL",
    "llm_synthesis_model": "OJT_LLM_SYNTHESIS_MODEL",
    "llm_vision_model": "OJT_LLM_VISION_MODEL",
    "llm_base_url": "OJT_LLM_BASE_URL",
    "llm_timeout_seconds": "OJT_LLM_TIMEOUT_SECONDS",
    "llm_max_tool_calls": "OJT_LLM_MAX_TOOL_CALLS",
    "llm_planning_progress_interval_seconds": "OJT_LLM_PLANNING_PROGRESS_INTERVAL_SECONDS",
    "external_openai_llm_enabled": "OJT_EXTERNAL_OPENAI_LLM_ENABLED",
    "external_openai_llm_allow_phi": "OJT_EXTERNAL_OPENAI_LLM_ALLOW_PHI",
    "external_openai_ocr_enabled": "OJT_EXTERNAL_OPENAI_OCR_ENABLED",
    "external_openai_ocr_allow_phi": "OJT_EXTERNAL_OPENAI_OCR_ALLOW_PHI",
    "external_openai_ocr_allow_unknown": "OJT_EXTERNAL_OPENAI_OCR_ALLOW_UNKNOWN",
    "external_openai_embeddings_enabled": "OJT_EXTERNAL_OPENAI_EMBEDDINGS_ENABLED",
    "external_openai_embeddings_allow_phi": "OJT_EXTERNAL_OPENAI_EMBEDDINGS_ALLOW_PHI",
    "external_medical_search_enabled": "OJT_EXTERNAL_MEDICAL_SEARCH_ENABLED",
    "external_medical_search_allow_phi": "OJT_EXTERNAL_MEDICAL_SEARCH_ALLOW_PHI",
}
RUNTIME_SETTING_ALIASES = {
    **RUNTIME_RETRIEVAL_SETTING_ALIASES,
    **RUNTIME_ASSISTANT_SETTING_ALIASES,
}


class Settings(BaseModel):
    """Environment-backed settings with local demo defaults."""

    product_mode: ProductMode = Field(default="local_dev", alias="OJT_PRODUCT_MODE")
    no_mock_data: bool = Field(default=False, alias="OJT_NO_MOCK_DATA")
    audit_hash_chain_required: bool = Field(
        default=False,
        alias="OJT_AUDIT_HASH_CHAIN_REQUIRED",
    )
    storage_backend: StorageBackend = Field(
        default=DEFAULT_STORAGE_BACKEND,
        alias="OJT_STORAGE_BACKEND",
    )
    postgres_dsn: str = Field(
        default=DEFAULT_POSTGRES_DSN,
        alias="OJT_DATABASE_URL",
    )
    database_path: Path = Field(default=DEFAULT_DATABASE_PATH, alias="OJT_DATABASE_PATH")
    data_dir: Path = Field(default=DEFAULT_DATA_DIR, alias="OJT_DATA_DIR")
    knowledge_dir: Path = Field(default=DEFAULT_KNOWLEDGE_DIR, alias="OJT_KNOWLEDGE_DIR")
    migrations_dir: Path = Field(default=DEFAULT_MIGRATIONS_DIR, alias="OJT_MIGRATIONS_DIR")
    runtime_settings_path: Path = Field(
        default=DEFAULT_RUNTIME_SETTINGS_PATH,
        alias="OJT_RUNTIME_SETTINGS_PATH",
    )
    redis_url: str = Field(default=DEFAULT_REDIS_URL, alias="OJT_REDIS_URL")
    google_client_id: str = Field(default="", alias="OJT_GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(default="", alias="OJT_GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(
        default=DEFAULT_GOOGLE_REDIRECT_URI,
        alias="OJT_GOOGLE_REDIRECT_URI",
    )
    google_frontend_redirect_uri: str = Field(
        default=DEFAULT_GOOGLE_FRONTEND_REDIRECT_URI,
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
        gt=0,
    )
    auth_session_ttl_seconds: int = Field(
        default=7 * 24 * 60 * 60,
        alias="OJT_AUTH_SESSION_TTL_SECONDS",
        gt=0,
    )
    auth_state_ttl_seconds: int = Field(
        default=10 * 60,
        alias="OJT_AUTH_STATE_TTL_SECONDS",
        gt=0,
    )
    service_account_token_ttl_seconds: int = Field(
        default=90 * 24 * 60 * 60,
        alias="OJT_SERVICE_ACCOUNT_TOKEN_TTL_SECONDS",
        gt=0,
    )
    service_account_default_role_key: str = Field(
        default="operator",
        alias="OJT_SERVICE_ACCOUNT_DEFAULT_ROLE_KEY",
    )
    auth_cookie_name: str = Field(default="ojtflow_session", alias="OJT_AUTH_COOKIE_NAME")
    auth_cookie_secure: bool = Field(default=False, alias="OJT_AUTH_COOKIE_SECURE")
    auth_cookie_samesite: str = Field(default="lax", alias="OJT_AUTH_COOKIE_SAMESITE")
    auth_cookie_domain: str | None = Field(default=None, alias="OJT_AUTH_COOKIE_DOMAIN")
    max_upload_bytes: int = Field(
        default=25 * 1024 * 1024,
        alias="OJT_MAX_UPLOAD_BYTES",
        gt=0,
    )
    max_inline_data_bytes: int = Field(
        default=1 * 1024 * 1024,
        alias="OJT_MAX_INLINE_DATA_BYTES",
        gt=0,
    )
    upload_read_chunk_bytes: int = Field(
        default=1024 * 1024,
        alias="OJT_UPLOAD_READ_CHUNK_BYTES",
        gt=0,
    )
    max_batch_upload_files: int = Field(
        default=20,
        alias="OJT_MAX_BATCH_UPLOAD_FILES",
        gt=0,
        le=100,
    )
    allowed_upload_extensions: tuple[str, ...] = Field(
        default=DEFAULT_ALLOWED_UPLOAD_EXTENSIONS,
        alias="OJT_ALLOWED_UPLOAD_EXTENSIONS",
    )
    artifact_retention_rules: tuple[dict[str, object], ...] = Field(
        default=(),
        alias="OJT_ARTIFACT_RETENTION_RULES",
    )
    embedding_provider: EmbeddingProvider = Field(
        default="deterministic",
        alias="OJT_EMBEDDING_PROVIDER",
    )
    embedding_model: str = Field(
        default=DETERMINISTIC_EMBEDDING_MODEL,
        alias="OJT_EMBEDDING_MODEL",
    )
    embedding_dimensions: int = Field(
        default=DETERMINISTIC_EMBEDDING_DIMENSIONS,
        alias="OJT_EMBEDDING_DIMENSIONS",
        gt=0,
    )
    openai_api_key: str = Field(default="", alias="OJT_OPENAI_API_KEY")
    openai_embedding_base_url: str = Field(
        default=OPENAI_EMBEDDING_BASE_URL,
        alias="OJT_OPENAI_EMBEDDING_BASE_URL",
    )
    openai_embedding_timeout_seconds: float = Field(
        default=20.0,
        alias="OJT_OPENAI_EMBEDDING_TIMEOUT_SECONDS",
        gt=0,
    )
    llm_provider: LLMProvider = Field(default="disabled", alias="OJT_LLM_PROVIDER")
    llm_model: str = Field(default=OPENAI_LLM_MODEL, alias="OJT_LLM_MODEL")
    llm_planning_model: str | None = Field(default=None, alias="OJT_LLM_PLANNING_MODEL")
    llm_synthesis_model: str | None = Field(default=None, alias="OJT_LLM_SYNTHESIS_MODEL")
    llm_vision_model: str | None = Field(default=None, alias="OJT_LLM_VISION_MODEL")
    llm_base_url: str = Field(
        default=OPENAI_EMBEDDING_BASE_URL,
        alias="OJT_LLM_BASE_URL",
    )
    llm_timeout_seconds: float = Field(
        default=30.0,
        alias="OJT_LLM_TIMEOUT_SECONDS",
        gt=0,
    )
    llm_max_tool_calls: int = Field(
        default=4,
        alias="OJT_LLM_MAX_TOOL_CALLS",
        gt=0,
        le=12,
    )
    llm_planning_progress_interval_seconds: float = Field(
        default=2.0,
        alias="OJT_LLM_PLANNING_PROGRESS_INTERVAL_SECONDS",
        gt=0,
    )
    external_openai_llm_enabled: bool = Field(
        default=True,
        alias="OJT_EXTERNAL_OPENAI_LLM_ENABLED",
    )
    external_openai_llm_allow_phi: bool = Field(
        default=False,
        alias="OJT_EXTERNAL_OPENAI_LLM_ALLOW_PHI",
    )
    external_openai_ocr_enabled: bool = Field(
        default=True,
        alias="OJT_EXTERNAL_OPENAI_OCR_ENABLED",
    )
    external_openai_ocr_allow_phi: bool = Field(
        default=False,
        alias="OJT_EXTERNAL_OPENAI_OCR_ALLOW_PHI",
    )
    external_openai_ocr_allow_unknown: bool = Field(
        default=True,
        alias="OJT_EXTERNAL_OPENAI_OCR_ALLOW_UNKNOWN",
    )
    external_openai_embeddings_enabled: bool = Field(
        default=True,
        alias="OJT_EXTERNAL_OPENAI_EMBEDDINGS_ENABLED",
    )
    external_openai_embeddings_allow_phi: bool = Field(
        default=False,
        alias="OJT_EXTERNAL_OPENAI_EMBEDDINGS_ALLOW_PHI",
    )
    external_medical_search_enabled: bool = Field(
        default=True,
        alias="OJT_EXTERNAL_MEDICAL_SEARCH_ENABLED",
    )
    external_medical_search_allow_phi: bool = Field(
        default=False,
        alias="OJT_EXTERNAL_MEDICAL_SEARCH_ALLOW_PHI",
    )
    hf_embedding_device: str = Field(default="auto", alias="OJT_HF_EMBEDDING_DEVICE")
    hf_embedding_batch_size: int = Field(
        default=32,
        alias="OJT_HF_EMBEDDING_BATCH_SIZE",
        gt=0,
    )
    hf_embedding_cache_dir: Path = Field(
        default=DEFAULT_HF_EMBEDDING_CACHE_DIR,
        alias="OJT_HF_EMBEDDING_CACHE_DIR",
    )
    retrieval_corpus_dirs: tuple[Path, ...] = Field(
        default=DEFAULT_RETRIEVAL_CORPUS_DIRS,
        alias="OJT_RETRIEVAL_CORPUS_DIRS",
    )
    retrieval_chunk_max_chars: int = Field(
        default=1200,
        alias="OJT_RETRIEVAL_CHUNK_MAX_CHARS",
        gt=0,
    )
    retrieval_chunk_overlap_chars: int = Field(
        default=160,
        alias="OJT_RETRIEVAL_CHUNK_OVERLAP_CHARS",
        ge=0,
    )
    retrieval_diversity_enabled: bool = Field(
        default=True,
        alias="OJT_RETRIEVAL_DIVERSITY_ENABLED",
    )
    retrieval_diversity_lambda: float = Field(
        default=0.72,
        alias="OJT_RETRIEVAL_DIVERSITY_LAMBDA",
        ge=0,
        le=1,
    )
    retrieval_hnsw_ef_search: int = Field(
        default=DEFAULT_RETRIEVAL_HNSW_EF_SEARCH,
        alias="OJT_RETRIEVAL_HNSW_EF_SEARCH",
        ge=1,
        le=1000,
    )
    retrieval_framework: RetrievalFramework = Field(
        default="custom",
        alias="OJT_RETRIEVAL_FRAMEWORK",
    )
    retrieval_candidate_multiplier: int = Field(
        default=4,
        alias="OJT_RETRIEVAL_CANDIDATE_MULTIPLIER",
        ge=1,
        le=20,
    )
    retrieval_min_candidates: int = Field(
        default=12,
        alias="OJT_RETRIEVAL_MIN_CANDIDATES",
        ge=1,
        le=200,
    )
    retrieval_vector_weight: float = Field(
        default=0.62,
        alias="OJT_RETRIEVAL_VECTOR_WEIGHT",
        ge=0,
        le=1,
    )
    retrieval_bm25_weight: float = Field(
        default=0.38,
        alias="OJT_RETRIEVAL_BM25_WEIGHT",
        ge=0,
        le=1,
    )
    rerank_provider: RerankProvider = Field(default="none", alias="OJT_RERANK_PROVIDER")
    rerank_model: str = Field(
        default=HUGGINGFACE_RERANK_MODEL,
        alias="OJT_RERANK_MODEL",
    )
    rerank_device: str = Field(default="auto", alias="OJT_RERANK_DEVICE")
    rerank_batch_size: int = Field(default=16, alias="OJT_RERANK_BATCH_SIZE", gt=0)
    rerank_candidate_limit: int = Field(
        default=20,
        alias="OJT_RERANK_CANDIDATE_LIMIT",
        gt=0,
    )
    rerank_score_weight: float = Field(
        default=0.08,
        alias="OJT_RERANK_SCORE_WEIGHT",
        gt=0,
        le=1,
    )

    @model_validator(mode="after")
    def _normalize_llm_models(self) -> "Settings":
        if not self.llm_planning_model:
            self.llm_planning_model = self.llm_model
        if not self.llm_synthesis_model:
            self.llm_synthesis_model = self.llm_model
        if not self.llm_vision_model:
            self.llm_vision_model = (
                OPENAI_VISION_MODEL
                if self.llm_model == OPENAI_LLM_MODEL
                else self.llm_model
            )
        return self

    @model_validator(mode="after")
    def _validate_retrieval_chunking(self) -> "Settings":
        if self.retrieval_chunk_overlap_chars >= self.retrieval_chunk_max_chars:
            raise ValueError(
                "OJT_RETRIEVAL_CHUNK_OVERLAP_CHARS must be smaller than "
                "OJT_RETRIEVAL_CHUNK_MAX_CHARS"
            )
        return self

    @model_validator(mode="after")
    def _validate_retrieval_framework_weights(self) -> "Settings":
        if self.retrieval_vector_weight + self.retrieval_bm25_weight <= 0:
            raise ValueError(
                "OJT_RETRIEVAL_VECTOR_WEIGHT and OJT_RETRIEVAL_BM25_WEIGHT "
                "cannot both be zero"
            )
        return self

    @model_validator(mode="after")
    def _validate_product_mode_policy(self) -> "Settings":
        if self.product_mode in {"pilot", "production"}:
            if self.storage_backend == "memory":
                raise ValueError(
                    "OJT_STORAGE_BACKEND=memory is not allowed when "
                    "OJT_PRODUCT_MODE is pilot or production"
                )
            if self.llm_provider == "disabled":
                raise ValueError(
                    "OJT_LLM_PROVIDER=disabled is not allowed when "
                    "OJT_PRODUCT_MODE is pilot or production"
                )
        return self

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
    def resolved_knowledge_dir(self) -> Path:
        return _resolve_path(self.knowledge_dir, self.repo_root)

    @property
    def resolved_migrations_dir(self) -> Path:
        return _resolve_path(self.migrations_dir, self.repo_root)

    @property
    def resolved_runtime_settings_path(self) -> Path:
        return _resolve_path(self.runtime_settings_path, self.repo_root)

    @property
    def resolved_hf_embedding_cache_dir(self) -> Path:
        return _resolve_path(self.hf_embedding_cache_dir, self.repo_root)

    @property
    def resolved_retrieval_corpus_dirs(self) -> tuple[Path, ...]:
        return tuple(_resolve_path(path, self.repo_root) for path in self.retrieval_corpus_dirs)

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

    @property
    def effective_auth_cookie_secure(self) -> bool:
        """Return whether emitted auth cookies will include the Secure flag."""

        return self.auth_cookie_secure or self.auth_cookie_samesite.lower() == "none"

    @property
    def effective_no_mock_data(self) -> bool:
        """Return whether demo/mock data paths must be blocked."""

        return self.no_mock_data or self.product_mode in {"pilot", "production"}

    @property
    def effective_audit_hash_chain_required(self) -> bool:
        """Return whether deployment policy requires chained audit records."""

        return self.audit_hash_chain_required or self.product_mode in {
            "pilot",
            "production",
        }


def _resolve_path(path: Path, root: Path) -> Path:
    return path if path.is_absolute() else root / path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings."""

    settings_kwargs = dict(
        OJT_PRODUCT_MODE=_parse_product_mode(os.getenv("OJT_PRODUCT_MODE")),
        OJT_NO_MOCK_DATA=_parse_bool(os.getenv("OJT_NO_MOCK_DATA"), default=False),
        OJT_AUDIT_HASH_CHAIN_REQUIRED=_parse_bool(
            os.getenv("OJT_AUDIT_HASH_CHAIN_REQUIRED"),
            default=False,
        ),
        OJT_STORAGE_BACKEND=_parse_storage_backend(os.getenv("OJT_STORAGE_BACKEND")),
        OJT_DATABASE_URL=_parse_postgres_dsn(
            os.getenv(
                "OJT_DATABASE_URL",
                os.getenv("DATABASE_URL", DEFAULT_POSTGRES_DSN),
            )
        ),
        OJT_DATABASE_PATH=Path(os.getenv("OJT_DATABASE_PATH", str(DEFAULT_DATABASE_PATH))),
        OJT_DATA_DIR=Path(os.getenv("OJT_DATA_DIR", str(DEFAULT_DATA_DIR))),
        OJT_KNOWLEDGE_DIR=Path(os.getenv("OJT_KNOWLEDGE_DIR", str(DEFAULT_KNOWLEDGE_DIR))),
        OJT_MIGRATIONS_DIR=Path(
            os.getenv("OJT_MIGRATIONS_DIR", str(DEFAULT_MIGRATIONS_DIR))
        ),
        OJT_RUNTIME_SETTINGS_PATH=Path(
            os.getenv("OJT_RUNTIME_SETTINGS_PATH", str(DEFAULT_RUNTIME_SETTINGS_PATH))
        ),
        OJT_REDIS_URL=_parse_redis_url(os.getenv("OJT_REDIS_URL")),
        OJT_GOOGLE_CLIENT_ID=os.getenv("OJT_GOOGLE_CLIENT_ID", ""),
        OJT_GOOGLE_CLIENT_SECRET=os.getenv("OJT_GOOGLE_CLIENT_SECRET", ""),
        OJT_GOOGLE_REDIRECT_URI=_parse_oauth_redirect_uri(
            "OJT_GOOGLE_REDIRECT_URI",
            os.getenv("OJT_GOOGLE_REDIRECT_URI"),
            default=DEFAULT_GOOGLE_REDIRECT_URI,
        ),
        OJT_GOOGLE_FRONTEND_REDIRECT_URI=_parse_oauth_redirect_uri(
            "OJT_GOOGLE_FRONTEND_REDIRECT_URI",
            os.getenv("OJT_GOOGLE_FRONTEND_REDIRECT_URI"),
            default=DEFAULT_GOOGLE_FRONTEND_REDIRECT_URI,
        ),
        OJT_ALLOWED_AUTH_REDIRECT_URIS=_parse_oauth_redirect_uri_csv(
            "OJT_ALLOWED_AUTH_REDIRECT_URIS",
            os.getenv("OJT_ALLOWED_AUTH_REDIRECT_URIS"),
        ),
        OJT_ALLOWED_GOOGLE_HOSTED_DOMAINS=_parse_google_hosted_domains(
            os.getenv("OJT_ALLOWED_GOOGLE_HOSTED_DOMAINS")
        ),
        OJT_GOOGLE_OAUTH_TIMEOUT_SECONDS=float(
            os.getenv("OJT_GOOGLE_OAUTH_TIMEOUT_SECONDS", "10.0")
        ),
        OJT_AUTH_SESSION_TTL_SECONDS=int(
            os.getenv("OJT_AUTH_SESSION_TTL_SECONDS", str(7 * 24 * 60 * 60))
        ),
        OJT_AUTH_STATE_TTL_SECONDS=int(os.getenv("OJT_AUTH_STATE_TTL_SECONDS", str(10 * 60))),
        OJT_AUTH_COOKIE_NAME=_parse_cookie_name(os.getenv("OJT_AUTH_COOKIE_NAME")),
        OJT_AUTH_COOKIE_SECURE=_parse_bool(os.getenv("OJT_AUTH_COOKIE_SECURE"), default=False),
        OJT_AUTH_COOKIE_SAMESITE=_parse_same_site(os.getenv("OJT_AUTH_COOKIE_SAMESITE")),
        OJT_AUTH_COOKIE_DOMAIN=_parse_cookie_domain(os.getenv("OJT_AUTH_COOKIE_DOMAIN")),
        OJT_MAX_UPLOAD_BYTES=int(os.getenv("OJT_MAX_UPLOAD_BYTES", str(25 * 1024 * 1024))),
        OJT_MAX_INLINE_DATA_BYTES=int(
            os.getenv("OJT_MAX_INLINE_DATA_BYTES", str(1 * 1024 * 1024))
        ),
        OJT_UPLOAD_READ_CHUNK_BYTES=int(
            os.getenv("OJT_UPLOAD_READ_CHUNK_BYTES", str(1024 * 1024))
        ),
        OJT_MAX_BATCH_UPLOAD_FILES=int(os.getenv("OJT_MAX_BATCH_UPLOAD_FILES", "20")),
        OJT_ALLOWED_UPLOAD_EXTENSIONS=_parse_extensions(
            os.getenv("OJT_ALLOWED_UPLOAD_EXTENSIONS")
        ),
        OJT_ARTIFACT_RETENTION_RULES=_parse_json_object_list(
            os.getenv("OJT_ARTIFACT_RETENTION_RULES"),
            setting_name="OJT_ARTIFACT_RETENTION_RULES",
        ),
        OJT_EMBEDDING_PROVIDER=_parse_embedding_provider(os.getenv("OJT_EMBEDDING_PROVIDER")),
        OJT_EMBEDDING_MODEL=_parse_embedding_model(
            os.getenv("OJT_EMBEDDING_MODEL"),
            provider=os.getenv("OJT_EMBEDDING_PROVIDER"),
        ),
        OJT_EMBEDDING_DIMENSIONS=_parse_embedding_dimensions(
            os.getenv("OJT_EMBEDDING_DIMENSIONS"),
            provider=os.getenv("OJT_EMBEDDING_PROVIDER"),
            model=os.getenv("OJT_EMBEDDING_MODEL"),
        ),
        OJT_OPENAI_API_KEY=os.getenv("OJT_OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", "")),
        OJT_OPENAI_EMBEDDING_BASE_URL=_parse_openai_base_url(
            os.getenv("OJT_OPENAI_EMBEDDING_BASE_URL")
        ),
        OJT_OPENAI_EMBEDDING_TIMEOUT_SECONDS=float(
            os.getenv("OJT_OPENAI_EMBEDDING_TIMEOUT_SECONDS", "20.0")
        ),
        OJT_LLM_PROVIDER=_parse_llm_provider(os.getenv("OJT_LLM_PROVIDER")),
        OJT_LLM_MODEL=_parse_llm_model(os.getenv("OJT_LLM_MODEL")),
        OJT_LLM_PLANNING_MODEL=_parse_optional_llm_model(
            os.getenv("OJT_LLM_PLANNING_MODEL")
        ),
        OJT_LLM_SYNTHESIS_MODEL=_parse_optional_llm_model(
            os.getenv("OJT_LLM_SYNTHESIS_MODEL")
        ),
        OJT_LLM_VISION_MODEL=_parse_optional_llm_model(
            os.getenv("OJT_LLM_VISION_MODEL", os.getenv("OJT_OPENAI_VISION_MODEL"))
        ),
        OJT_LLM_BASE_URL=_parse_openai_base_url(
            os.getenv("OJT_LLM_BASE_URL"),
            setting_name="OpenAI LLM base URL",
        ),
        OJT_LLM_TIMEOUT_SECONDS=float(os.getenv("OJT_LLM_TIMEOUT_SECONDS", "30.0")),
        OJT_LLM_MAX_TOOL_CALLS=int(os.getenv("OJT_LLM_MAX_TOOL_CALLS", "4")),
        OJT_LLM_PLANNING_PROGRESS_INTERVAL_SECONDS=float(
            os.getenv("OJT_LLM_PLANNING_PROGRESS_INTERVAL_SECONDS", "2.0")
        ),
        OJT_EXTERNAL_OPENAI_LLM_ENABLED=_parse_bool(
            os.getenv("OJT_EXTERNAL_OPENAI_LLM_ENABLED"),
            default=True,
        ),
        OJT_EXTERNAL_OPENAI_LLM_ALLOW_PHI=_parse_bool(
            os.getenv("OJT_EXTERNAL_OPENAI_LLM_ALLOW_PHI"),
            default=False,
        ),
        OJT_EXTERNAL_OPENAI_OCR_ENABLED=_parse_bool(
            os.getenv("OJT_EXTERNAL_OPENAI_OCR_ENABLED"),
            default=True,
        ),
        OJT_EXTERNAL_OPENAI_OCR_ALLOW_PHI=_parse_bool(
            os.getenv("OJT_EXTERNAL_OPENAI_OCR_ALLOW_PHI"),
            default=False,
        ),
        OJT_EXTERNAL_OPENAI_OCR_ALLOW_UNKNOWN=_parse_bool(
            os.getenv("OJT_EXTERNAL_OPENAI_OCR_ALLOW_UNKNOWN"),
            default=True,
        ),
        OJT_EXTERNAL_OPENAI_EMBEDDINGS_ENABLED=_parse_bool(
            os.getenv("OJT_EXTERNAL_OPENAI_EMBEDDINGS_ENABLED"),
            default=True,
        ),
        OJT_EXTERNAL_OPENAI_EMBEDDINGS_ALLOW_PHI=_parse_bool(
            os.getenv("OJT_EXTERNAL_OPENAI_EMBEDDINGS_ALLOW_PHI"),
            default=False,
        ),
        OJT_EXTERNAL_MEDICAL_SEARCH_ENABLED=_parse_bool(
            os.getenv("OJT_EXTERNAL_MEDICAL_SEARCH_ENABLED"),
            default=True,
        ),
        OJT_EXTERNAL_MEDICAL_SEARCH_ALLOW_PHI=_parse_bool(
            os.getenv("OJT_EXTERNAL_MEDICAL_SEARCH_ALLOW_PHI"),
            default=False,
        ),
        OJT_HF_EMBEDDING_DEVICE=_parse_hf_embedding_device(
            os.getenv("OJT_HF_EMBEDDING_DEVICE")
        ),
        OJT_HF_EMBEDDING_BATCH_SIZE=int(os.getenv("OJT_HF_EMBEDDING_BATCH_SIZE", "32")),
        OJT_HF_EMBEDDING_CACHE_DIR=Path(
            os.getenv("OJT_HF_EMBEDDING_CACHE_DIR", str(DEFAULT_HF_EMBEDDING_CACHE_DIR))
        ),
        OJT_RETRIEVAL_CORPUS_DIRS=_parse_path_csv(
            os.getenv("OJT_RETRIEVAL_CORPUS_DIRS"),
            default=DEFAULT_RETRIEVAL_CORPUS_DIRS,
        ),
        OJT_RETRIEVAL_CHUNK_MAX_CHARS=int(
            os.getenv("OJT_RETRIEVAL_CHUNK_MAX_CHARS", "1200")
        ),
        OJT_RETRIEVAL_CHUNK_OVERLAP_CHARS=int(
            os.getenv("OJT_RETRIEVAL_CHUNK_OVERLAP_CHARS", "160")
        ),
        OJT_RETRIEVAL_DIVERSITY_ENABLED=_parse_bool(
            os.getenv("OJT_RETRIEVAL_DIVERSITY_ENABLED"),
            default=True,
        ),
        OJT_RETRIEVAL_DIVERSITY_LAMBDA=float(
            os.getenv("OJT_RETRIEVAL_DIVERSITY_LAMBDA", "0.72")
        ),
        OJT_RETRIEVAL_HNSW_EF_SEARCH=int(
            os.getenv("OJT_RETRIEVAL_HNSW_EF_SEARCH", str(DEFAULT_RETRIEVAL_HNSW_EF_SEARCH))
        ),
        OJT_RETRIEVAL_FRAMEWORK=_parse_retrieval_framework(
            os.getenv("OJT_RETRIEVAL_FRAMEWORK")
        ),
        OJT_RETRIEVAL_CANDIDATE_MULTIPLIER=int(
            os.getenv("OJT_RETRIEVAL_CANDIDATE_MULTIPLIER", "4")
        ),
        OJT_RETRIEVAL_MIN_CANDIDATES=int(
            os.getenv("OJT_RETRIEVAL_MIN_CANDIDATES", "12")
        ),
        OJT_RETRIEVAL_VECTOR_WEIGHT=float(
            os.getenv("OJT_RETRIEVAL_VECTOR_WEIGHT", "0.62")
        ),
        OJT_RETRIEVAL_BM25_WEIGHT=float(os.getenv("OJT_RETRIEVAL_BM25_WEIGHT", "0.38")),
        OJT_RERANK_PROVIDER=_parse_rerank_provider(os.getenv("OJT_RERANK_PROVIDER")),
        OJT_RERANK_MODEL=_parse_rerank_model(os.getenv("OJT_RERANK_MODEL")),
        OJT_RERANK_DEVICE=_parse_hf_device(
            os.getenv("OJT_RERANK_DEVICE"),
            setting_name="Hugging Face rerank device",
        ),
        OJT_RERANK_BATCH_SIZE=int(os.getenv("OJT_RERANK_BATCH_SIZE", "16")),
        OJT_RERANK_CANDIDATE_LIMIT=int(os.getenv("OJT_RERANK_CANDIDATE_LIMIT", "20")),
        OJT_RERANK_SCORE_WEIGHT=float(os.getenv("OJT_RERANK_SCORE_WEIGHT", "0.08")),
    )
    _apply_runtime_settings_overrides(settings_kwargs)
    return Settings(**settings_kwargs)


def clear_settings_cache() -> None:
    """Clear cached settings in tests."""

    get_settings.cache_clear()


def runtime_retrieval_settings(settings: Settings) -> RuntimeRetrievalSettingsPayload:
    """Return the retrieval settings that operators may change at runtime."""

    return {
        "embedding_provider": settings.embedding_provider,
        "embedding_model": settings.embedding_model,
        "embedding_dimensions": settings.embedding_dimensions,
        "retrieval_framework": settings.retrieval_framework,
        "retrieval_candidate_multiplier": settings.retrieval_candidate_multiplier,
        "retrieval_min_candidates": settings.retrieval_min_candidates,
        "retrieval_vector_weight": settings.retrieval_vector_weight,
        "retrieval_bm25_weight": settings.retrieval_bm25_weight,
        "retrieval_diversity_enabled": settings.retrieval_diversity_enabled,
        "retrieval_diversity_lambda": settings.retrieval_diversity_lambda,
        "retrieval_hnsw_ef_search": settings.retrieval_hnsw_ef_search,
    }


def runtime_assistant_settings(settings: Settings) -> RuntimeAssistantSettingsPayload:
    """Return assistant settings that operators may change at runtime."""

    return {
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "llm_planning_model": settings.llm_planning_model or settings.llm_model,
        "llm_synthesis_model": settings.llm_synthesis_model or settings.llm_model,
        "llm_vision_model": settings.llm_vision_model or OPENAI_VISION_MODEL,
        "llm_base_url": settings.llm_base_url,
        "llm_timeout_seconds": settings.llm_timeout_seconds,
        "llm_max_tool_calls": settings.llm_max_tool_calls,
        "llm_planning_progress_interval_seconds": (
            settings.llm_planning_progress_interval_seconds
        ),
        "external_openai_llm_enabled": settings.external_openai_llm_enabled,
        "external_openai_llm_allow_phi": settings.external_openai_llm_allow_phi,
        "external_openai_ocr_enabled": settings.external_openai_ocr_enabled,
        "external_openai_ocr_allow_phi": settings.external_openai_ocr_allow_phi,
        "external_openai_ocr_allow_unknown": settings.external_openai_ocr_allow_unknown,
        "external_openai_embeddings_enabled": settings.external_openai_embeddings_enabled,
        "external_openai_embeddings_allow_phi": (
            settings.external_openai_embeddings_allow_phi
        ),
        "external_medical_search_enabled": settings.external_medical_search_enabled,
        "external_medical_search_allow_phi": settings.external_medical_search_allow_phi,
    }


def save_runtime_retrieval_settings(
    settings: Settings,
    updates: RuntimeRetrievalSettingsPayload,
) -> Settings:
    """Persist runtime retrieval settings and validate the effective settings first."""

    return _save_runtime_settings(settings, updates, RUNTIME_RETRIEVAL_SETTING_ALIASES)


def save_runtime_assistant_settings(
    settings: Settings,
    updates: RuntimeAssistantSettingsPayload,
) -> Settings:
    """Persist runtime assistant settings and validate the effective settings first."""

    return _save_runtime_settings(settings, updates, RUNTIME_ASSISTANT_SETTING_ALIASES)


def runtime_settings_history_path(settings: Settings) -> Path:
    """Return the runtime setting history file path."""

    runtime_path = settings.resolved_runtime_settings_path
    return runtime_path.with_name(f"{runtime_path.stem}.history.jsonl")


def load_runtime_settings_overrides(settings: Settings) -> RuntimeSettingsPayload:
    """Return sanitized runtime settings overrides."""

    return _load_runtime_settings_overrides(settings.resolved_runtime_settings_path)


def replace_runtime_settings_overrides(
    settings: Settings,
    values: RuntimeSettingsPayload,
) -> Settings:
    """Validate and replace the full runtime settings override payload."""

    sanitized = {
        key: _coerce_runtime_setting_value(key, value)
        for key, value in values.items()
        if key in RUNTIME_SETTING_ALIASES
    }
    validated = _validate_runtime_settings(settings, sanitized)
    _write_runtime_settings_overrides(settings.resolved_runtime_settings_path, sanitized)
    return validated


def _save_runtime_settings(
    settings: Settings,
    updates: RuntimeSettingsPayload,
    allowed_aliases: dict[str, str],
) -> Settings:
    runtime_path = settings.resolved_runtime_settings_path
    merged = {
        key: value
        for key, value in _load_runtime_settings_overrides(runtime_path).items()
        if key in RUNTIME_SETTING_ALIASES
    }
    for key, value in updates.items():
        if key in allowed_aliases:
            merged[key] = _coerce_runtime_setting_value(key, value)

    validated = _validate_runtime_settings(settings, merged)
    _write_runtime_settings_overrides(runtime_path, merged)
    return validated


def _apply_runtime_settings_overrides(settings_kwargs: dict[str, object]) -> None:
    raw_path = settings_kwargs.get("OJT_RUNTIME_SETTINGS_PATH", DEFAULT_RUNTIME_SETTINGS_PATH)
    runtime_path = _resolve_path(Path(raw_path), Path(__file__).resolve().parents[2])
    for key, value in _load_runtime_settings_overrides(runtime_path).items():
        alias = RUNTIME_SETTING_ALIASES.get(key)
        if not alias:
            continue
        settings_kwargs[alias] = _coerce_runtime_setting_value(key, value)


def _validate_runtime_settings(
    settings: Settings,
    values: RuntimeSettingsPayload,
) -> Settings:
    candidate_kwargs = settings.model_dump(by_alias=True)
    for key, value in values.items():
        alias = RUNTIME_SETTING_ALIASES.get(key)
        if alias:
            candidate_kwargs[alias] = _coerce_runtime_setting_value(key, value)
    return Settings(**candidate_kwargs)


def _load_runtime_settings_overrides(path: Path) -> RuntimeSettingsPayload:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid runtime settings JSON at {path}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid runtime settings JSON at {path}: expected an object")
    payload: RuntimeSettingsPayload = {}
    for key, value in raw.items():
        if key not in RUNTIME_SETTING_ALIASES:
            continue
        payload[str(key)] = _coerce_runtime_setting_value(str(key), value)
    return payload


def _write_runtime_settings_overrides(
    path: Path,
    values: RuntimeSettingsPayload,
) -> None:
    payload = {
        key: _coerce_runtime_setting_value(key, value)
        for key, value in values.items()
        if key in RUNTIME_SETTING_ALIASES
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temp_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temp_path.replace(path)
    finally:
        try:
            if temp_path.exists():
                temp_path.unlink()
        except OSError:
            pass


def _coerce_runtime_setting_value(key: str, value: object) -> str | int | float | bool:
    if key == "llm_provider":
        if not isinstance(value, str):
            raise ValueError("llm_provider must be a string")
        return _parse_llm_provider(value)
    if key == "llm_model":
        if not isinstance(value, str):
            raise ValueError("llm_model must be a string")
        return _parse_llm_model(value)
    if key in {"llm_planning_model", "llm_synthesis_model", "llm_vision_model"}:
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string")
        return _parse_llm_model(value)
    if key == "llm_base_url":
        if not isinstance(value, str):
            raise ValueError("llm_base_url must be a string")
        return _parse_openai_base_url(value, setting_name="OpenAI LLM base URL")
    if key == "llm_timeout_seconds":
        if isinstance(value, bool):
            raise ValueError("llm_timeout_seconds must be a number")
        return float(value)
    if key == "llm_max_tool_calls":
        if isinstance(value, bool):
            raise ValueError("llm_max_tool_calls must be an integer")
        return int(value)
    if key == "llm_planning_progress_interval_seconds":
        if isinstance(value, bool):
            raise ValueError("llm_planning_progress_interval_seconds must be a number")
        return float(value)
    if key in {
        "external_openai_llm_enabled",
        "external_openai_llm_allow_phi",
        "external_openai_ocr_enabled",
        "external_openai_ocr_allow_phi",
        "external_openai_ocr_allow_unknown",
        "external_openai_embeddings_enabled",
        "external_openai_embeddings_allow_phi",
        "external_medical_search_enabled",
        "external_medical_search_allow_phi",
    }:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return _parse_bool(value, default=False)
        raise ValueError(f"{key} must be a boolean")
    if key == "embedding_provider":
        if not isinstance(value, str):
            raise ValueError("embedding_provider must be a string")
        return _parse_embedding_provider(value)
    if key == "embedding_model":
        if not isinstance(value, str):
            raise ValueError("embedding_model must be a string")
        normalized = value.strip()
        if not _valid_model_identifier(normalized):
            raise ValueError("embedding_model must be a non-blank model id")
        return normalized
    if key == "embedding_dimensions":
        if isinstance(value, bool):
            raise ValueError("embedding_dimensions must be an integer")
        parsed_dimensions = int(value)
        if parsed_dimensions <= 0:
            raise ValueError("embedding_dimensions must be greater than zero")
        return parsed_dimensions
    if key == "retrieval_framework":
        if not isinstance(value, str):
            raise ValueError("retrieval_framework must be a string")
        return _parse_retrieval_framework(value)
    if key == "retrieval_diversity_enabled":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return _parse_bool(value, default=True)
        raise ValueError("retrieval_diversity_enabled must be a boolean")
    if key in {
        "retrieval_candidate_multiplier",
        "retrieval_min_candidates",
        "retrieval_hnsw_ef_search",
    }:
        if isinstance(value, bool):
            raise ValueError(f"{key} must be an integer")
        return int(value)
    if key in {
        "retrieval_vector_weight",
        "retrieval_bm25_weight",
        "retrieval_diversity_lambda",
    }:
        if isinstance(value, bool):
            raise ValueError(f"{key} must be a number")
        return float(value)
    raise ValueError(f"Unsupported runtime setting: {key}")


def _parse_extensions(value: str | None) -> tuple[str, ...]:
    if not value:
        return DEFAULT_ALLOWED_UPLOAD_EXTENSIONS
    extensions: list[str] = []
    for item in value.split(","):
        normalized = item.strip().lower()
        if not normalized:
            continue
        extension = normalized if normalized.startswith(".") else f".{normalized}"
        if (
            not UPLOAD_EXTENSION_PATTERN.fullmatch(extension)
            or extension not in DEFAULT_ALLOWED_UPLOAD_EXTENSIONS
        ):
            supported = ", ".join(DEFAULT_ALLOWED_UPLOAD_EXTENSIONS)
            raise ValueError(
                "Invalid upload extension environment value: "
                f"{item}. Expected one of: {supported}"
            )
        if extension not in extensions:
            extensions.append(extension)
    return tuple(extensions) or DEFAULT_ALLOWED_UPLOAD_EXTENSIONS


def _parse_json_object_list(
    value: str | None,
    *,
    setting_name: str,
) -> tuple[dict[str, object], ...]:
    if not value:
        return ()
    try:
        loaded = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{setting_name} must be valid JSON") from exc
    if not isinstance(loaded, list):
        raise ValueError(f"{setting_name} must be a JSON list")
    result: list[dict[str, object]] = []
    for index, item in enumerate(loaded):
        if not isinstance(item, dict):
            raise ValueError(f"{setting_name}[{index}] must be a JSON object")
        result.append({str(key): value for key, value in item.items()})
    return tuple(result)


def _parse_oauth_redirect_uri(
    setting_name: str,
    value: str | None,
    *,
    default: str | None = None,
) -> str:
    raw = default if value is None else value.strip()
    if not raw:
        raise ValueError(f"Invalid OAuth redirect URI for {setting_name}: value is blank")

    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(
            f"Invalid OAuth redirect URI for {setting_name}: scheme must be http or https"
        )
    if not parsed.hostname:
        raise ValueError(
            f"Invalid OAuth redirect URI for {setting_name}: host is required"
        )
    if parsed.username or parsed.password:
        raise ValueError(
            f"Invalid OAuth redirect URI for {setting_name}: user info is not allowed"
        )
    if parsed.fragment:
        raise ValueError(
            f"Invalid OAuth redirect URI for {setting_name}: fragment is not allowed"
        )
    if parsed.scheme == "http" and parsed.hostname.lower() not in LOCAL_OAUTH_REDIRECT_HOSTS:
        raise ValueError(
            f"Invalid OAuth redirect URI for {setting_name}: non-local HTTP callbacks must use HTTPS"
        )
    return raw


def _parse_oauth_redirect_uri_csv(setting_name: str, value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    parsed: list[str] = []
    for item in value.split(","):
        if not item.strip():
            continue
        redirect_uri = _parse_oauth_redirect_uri(setting_name, item)
        if redirect_uri not in parsed:
            parsed.append(redirect_uri)
    return tuple(parsed)


def _parse_google_hosted_domains(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    domains: list[str] = []
    for item in value.split(","):
        if not item.strip():
            continue
        domain = _parse_dns_domain(
            "OJT_ALLOWED_GOOGLE_HOSTED_DOMAINS",
            item,
            allow_leading_dot=False,
        )
        if domain not in domains:
            domains.append(domain)
    return tuple(domains)


def _parse_cookie_domain(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    return _parse_dns_domain(
        "OJT_AUTH_COOKIE_DOMAIN",
        value,
        allow_leading_dot=True,
    )


def _parse_dns_domain(
    setting_name: str,
    value: str,
    *,
    allow_leading_dot: bool,
) -> str:
    normalized = value.strip().lower()
    if not normalized:
        raise ValueError(f"Invalid domain for {setting_name}: value is blank")
    if "://" in normalized or "/" in normalized or "\\" in normalized:
        raise ValueError(
            f"Invalid domain for {setting_name}: use a bare DNS domain, not a URL or path"
        )
    if "@" in normalized:
        raise ValueError(f"Invalid domain for {setting_name}: user info is not allowed")
    if ":" in normalized:
        raise ValueError(f"Invalid domain for {setting_name}: ports are not allowed")
    if "*" in normalized or "," in normalized or any(char.isspace() for char in normalized):
        raise ValueError(
            f"Invalid domain for {setting_name}: wildcards, commas, and spaces are not allowed"
        )
    if normalized.endswith("."):
        raise ValueError(f"Invalid domain for {setting_name}: trailing dots are not allowed")

    has_leading_dot = normalized.startswith(".")
    if has_leading_dot and not allow_leading_dot:
        raise ValueError(f"Invalid domain for {setting_name}: leading dots are not allowed")
    domain_body = normalized[1:] if has_leading_dot else normalized
    if not domain_body:
        raise ValueError(f"Invalid domain for {setting_name}: value is blank")
    if len(domain_body) > 253:
        raise ValueError(f"Invalid domain for {setting_name}: domain is too long")
    try:
        ip_address(domain_body)
    except ValueError:
        pass
    else:
        raise ValueError(f"Invalid domain for {setting_name}: IP addresses are not allowed")

    labels = domain_body.split(".")
    if len(labels) < 2:
        raise ValueError(
            f"Invalid domain for {setting_name}: use a registrable DNS domain"
        )
    for label in labels:
        if not DNS_LABEL_PATTERN.fullmatch(label):
            raise ValueError(
                f"Invalid domain for {setting_name}: each label must be a DNS label"
            )
    return f".{domain_body}" if has_leading_dot else domain_body


def _parse_bool(value: str | None, *, default: bool) -> bool:
    if value is None or value == "":
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"Invalid boolean environment value: {value}")


def _parse_redis_url(value: str | None) -> str:
    if value is None:
        return DEFAULT_REDIS_URL
    normalized = value.strip()
    if not normalized:
        return ""
    parsed = urlparse(normalized)
    if parsed.scheme not in {"redis", "rediss", "unix"}:
        raise ValueError(
            "Invalid Redis URL for OJT_REDIS_URL: scheme must be redis, rediss, or unix"
        )
    if parsed.fragment:
        raise ValueError("Invalid Redis URL for OJT_REDIS_URL: fragments are not allowed")
    if parsed.scheme in {"redis", "rediss"}:
        if not parsed.hostname:
            raise ValueError("Invalid Redis URL for OJT_REDIS_URL: host is required")
        try:
            parsed.port
        except ValueError as exc:
            raise ValueError(
                "Invalid Redis URL for OJT_REDIS_URL: port must be numeric"
            ) from exc
        return normalized
    if parsed.scheme == "unix" and not parsed.path:
        raise ValueError("Invalid Redis URL for OJT_REDIS_URL: unix socket path is required")
    return normalized


def _parse_postgres_dsn(value: str | None) -> str:
    if value is None:
        return DEFAULT_POSTGRES_DSN
    normalized = value.strip()
    if not normalized:
        raise ValueError("Invalid Postgres URL for OJT_DATABASE_URL: value is blank")
    parsed = urlparse(normalized)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise ValueError(
            "Invalid Postgres URL for OJT_DATABASE_URL: scheme must be postgres or postgresql"
        )
    if not parsed.hostname:
        raise ValueError("Invalid Postgres URL for OJT_DATABASE_URL: host is required")
    try:
        parsed.port
    except ValueError as exc:
        raise ValueError(
            "Invalid Postgres URL for OJT_DATABASE_URL: port must be numeric"
        ) from exc
    if parsed.fragment:
        raise ValueError("Invalid Postgres URL for OJT_DATABASE_URL: fragments are not allowed")
    database_name = parsed.path.lstrip("/")
    if not database_name:
        raise ValueError("Invalid Postgres URL for OJT_DATABASE_URL: database name is required")
    return normalized


def _parse_same_site(value: str | None) -> str:
    normalized = (value or "lax").strip().lower()
    if normalized in {"lax", "strict", "none"}:
        return normalized
    raise ValueError(f"Invalid SameSite environment value: {value}")


def _parse_storage_backend(value: str | None) -> StorageBackend:
    normalized = "postgres" if value is None else value.strip().lower()
    if normalized == "postgres":
        return "postgres"
    if normalized == "sqlite":
        return "sqlite"
    if normalized == "memory":
        return "memory"
    allowed = ", ".join(ALLOWED_STORAGE_BACKENDS)
    raise ValueError(
        f"Invalid storage backend environment value: {value}. Expected one of: {allowed}"
    )


def _parse_product_mode(value: str | None) -> ProductMode:
    normalized = "local_dev" if value is None else value.strip().lower().replace("-", "_")
    if normalized in {"local", "dev", "development"}:
        return "local_dev"
    if normalized in ALLOWED_PRODUCT_MODES:
        return normalized  # type: ignore[return-value]
    allowed = ", ".join(ALLOWED_PRODUCT_MODES)
    raise ValueError(
        f"Invalid product mode environment value: {value}. Expected one of: {allowed}"
    )


def _parse_embedding_provider(value: str | None) -> EmbeddingProvider:
    normalized = "deterministic" if value is None else value.strip().lower()
    if normalized == "deterministic":
        return "deterministic"
    if normalized == "openai":
        return "openai"
    if normalized in {"huggingface", "sentence-transformers", "sentence_transformers", "hf"}:
        return "huggingface"
    allowed = ", ".join(ALLOWED_EMBEDDING_PROVIDERS)
    raise ValueError(
        f"Invalid embedding provider environment value: {value}. Expected one of: {allowed}"
    )


def _parse_rerank_provider(value: str | None) -> RerankProvider:
    normalized = "none" if value is None else value.strip().lower()
    if normalized in {"", "none", "off", "disabled"}:
        return "none"
    if normalized in {"huggingface", "sentence-transformers", "sentence_transformers", "hf"}:
        return "huggingface"
    allowed = ", ".join(ALLOWED_RERANK_PROVIDERS)
    raise ValueError(
        f"Invalid rerank provider environment value: {value}. Expected one of: {allowed}"
    )


def _parse_retrieval_framework(value: str | None) -> RetrievalFramework:
    normalized = "custom" if value is None else value.strip().lower()
    if normalized in {"", "custom", "native", "ojtflow"}:
        return "custom"
    if normalized in {"llamaindex", "llama-index", "llama_index"}:
        return "llamaindex"
    allowed = ", ".join(ALLOWED_RETRIEVAL_FRAMEWORKS)
    raise ValueError(
        f"Invalid retrieval framework environment value: {value}. Expected one of: {allowed}"
    )


def _parse_llm_provider(value: str | None) -> LLMProvider:
    normalized = "disabled" if value is None else value.strip().lower()
    if normalized in {"", "none", "off", "disabled"}:
        return "disabled"
    if normalized == "openai":
        return "openai"
    allowed = ", ".join(ALLOWED_LLM_PROVIDERS)
    raise ValueError(
        f"Invalid LLM provider environment value: {value}. Expected one of: {allowed}"
    )


def _parse_llm_model(value: str | None) -> str:
    normalized = OPENAI_LLM_MODEL if value is None else value.strip()
    if _valid_model_identifier(normalized):
        return normalized
    raise ValueError(
        f"Invalid LLM model environment value: {value}. Expected a non-blank model id"
    )


def _parse_optional_llm_model(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    return _parse_llm_model(value)


def _parse_embedding_model(value: str | None, *, provider: str | None = None) -> str:
    parsed_provider = _parse_embedding_provider(provider)
    default = (
        OPENAI_EMBEDDING_MODEL
        if parsed_provider == "openai"
        else HUGGINGFACE_EMBEDDING_MODEL
        if parsed_provider == "huggingface"
        else DETERMINISTIC_EMBEDDING_MODEL
    )
    normalized = default if value is None else value.strip()
    allowed = {
        "deterministic": {DETERMINISTIC_EMBEDDING_MODEL},
        "openai": {OPENAI_EMBEDDING_MODEL, "text-embedding-3-large"},
        "huggingface": None,
    }[parsed_provider]
    if allowed is None and _valid_model_identifier(normalized):
        return normalized
    if allowed is not None and normalized in allowed:
        return normalized
    expected = (
        "a non-blank Hugging Face model id or local model path"
        if allowed is None
        else f"one of: {', '.join(sorted(allowed))}"
    )
    raise ValueError(
        "Invalid embedding model environment value: "
        f"{value}. Expected {expected}"
    )


def _parse_embedding_dimensions(
    value: str | None,
    *,
    provider: str | None = None,
    model: str | None = None,
) -> int:
    parsed_provider = _parse_embedding_provider(provider)
    parsed_model = _parse_embedding_model(model, provider=parsed_provider)
    default_dimensions = (
        OPENAI_EMBEDDING_DIMENSIONS
        if parsed_provider == "openai"
        else HUGGINGFACE_EMBEDDING_DIMENSIONS
        if parsed_provider == "huggingface"
        else DETERMINISTIC_EMBEDDING_DIMENSIONS
    )
    normalized = str(default_dimensions) if value is None else value.strip()
    try:
        dimensions = int(normalized)
    except ValueError as exc:
        raise ValueError(
            "Invalid embedding dimensions environment value: "
            f"{value}. Expected a positive integer supported by {parsed_model}"
        ) from exc
    if parsed_provider == "deterministic" and dimensions == DETERMINISTIC_EMBEDDING_DIMENSIONS:
        return dimensions
    if parsed_provider == "openai" and dimensions > 0:
        if parsed_model.startswith("text-embedding-3-"):
            return dimensions
        if dimensions == 1536:
            return dimensions
    if parsed_provider == "huggingface" and dimensions > 0:
        return dimensions
    raise ValueError(
        "Invalid embedding dimensions environment value: "
        f"{value}. Expected a positive integer supported by {parsed_model}"
    )


def _parse_rerank_model(value: str | None) -> str:
    normalized = HUGGINGFACE_RERANK_MODEL if value is None else value.strip()
    if _valid_model_identifier(normalized):
        return normalized
    raise ValueError(
        "Invalid rerank model environment value: "
        f"{value}. Expected a non-blank Hugging Face CrossEncoder model id or local path"
    )


def _parse_openai_base_url(
    value: str | None,
    *,
    setting_name: str = "OpenAI embedding base URL",
) -> str:
    raw = OPENAI_EMBEDDING_BASE_URL if value is None else value.strip().rstrip("/")
    if not raw:
        raise ValueError(f"Invalid {setting_name}: value is blank")
    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Invalid {setting_name}: scheme must be http or https")
    if not parsed.hostname:
        raise ValueError(f"Invalid {setting_name}: host is required")
    if parsed.username or parsed.password:
        raise ValueError(f"Invalid {setting_name}: user info is not allowed")
    if parsed.fragment:
        raise ValueError(f"Invalid {setting_name}: fragment is not allowed")
    return raw


def _parse_hf_embedding_device(value: str | None) -> str:
    return _parse_hf_device(value, setting_name="Hugging Face embedding device")


def _parse_hf_device(value: str | None, *, setting_name: str) -> str:
    normalized = "auto" if value is None else value.strip().lower()
    if not normalized:
        raise ValueError(f"Invalid {setting_name}: value is blank")
    if normalized in {"auto", "cpu", "cuda", "mps"}:
        return normalized
    if re.fullmatch(r"cuda:\d+", normalized):
        return normalized
    raise ValueError(
        f"Invalid {setting_name}: expected auto, cpu, cuda, cuda:N, or mps"
    )


def _parse_path_csv(value: str | None, *, default: tuple[Path, ...]) -> tuple[Path, ...]:
    if not value:
        return default
    paths: list[Path] = []
    for item in value.split(","):
        normalized = item.strip()
        if not normalized:
            continue
        paths.append(Path(normalized))
    return tuple(paths) or default


def _valid_model_identifier(value: str) -> bool:
    if not value or any(char in value for char in "\r\n\t"):
        return False
    return len(value) <= 200


def _parse_cookie_name(value: str | None) -> str:
    normalized = "ojtflow_session" if value is None else value.strip()
    if not normalized or not COOKIE_NAME_PATTERN.fullmatch(normalized):
        raise ValueError(f"Invalid auth cookie name environment value: {value}")
    return normalized
