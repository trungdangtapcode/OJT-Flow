from pathlib import Path

import pytest
from pydantic import ValidationError

from ojtflow.config import clear_settings_cache, get_settings


REPO_ROOT = Path(__file__).resolve().parents[1]


def _env_example_values() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in (REPO_ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key] = value
    return values


def test_env_example_is_secret_safe_and_loadable(monkeypatch) -> None:
    values = _env_example_values()

    assert values["OJT_GOOGLE_CLIENT_ID"] == ""
    assert values["OJT_GOOGLE_CLIENT_SECRET"] == ""
    assert "GOC" + "SPX-" not in "\n".join(values.values())
    assert ".apps.googleusercontent.com" not in "\n".join(
        [
            values["OJT_GOOGLE_CLIENT_ID"],
            values["OJT_GOOGLE_CLIENT_SECRET"],
        ]
    )

    for key, value in values.items():
        if key.startswith("OJT_"):
            monkeypatch.setenv(key, value)
    clear_settings_cache()

    try:
        settings = get_settings()
    finally:
        clear_settings_cache()

    assert settings.storage_backend == "postgres"
    assert settings.postgres_dsn == "postgresql://ojtflow:ojtflow@localhost:5432/ojtflow"
    assert settings.redis_url == "redis://localhost:6379/0"
    assert settings.google_client_id == ""
    assert settings.google_client_secret == ""
    assert settings.google_redirect_uri == "http://localhost:8000/api/v1/auth/google/callback"
    assert settings.google_frontend_redirect_uri == "http://localhost:5173/auth/callback"
    assert settings.max_inline_data_bytes == 1048576
    assert settings.embedding_model == "deterministic-hash-v0"
    assert settings.resolved_knowledge_dir == REPO_ROOT / "knowledge"
    assert settings.resolved_migrations_dir == REPO_ROOT / "sql/postgres/migrations"


def test_runtime_resource_paths_are_configurable_and_resolved(monkeypatch, tmp_path) -> None:
    knowledge_dir = tmp_path / "knowledge"
    migrations_dir = tmp_path / "migrations"
    monkeypatch.setenv("OJT_KNOWLEDGE_DIR", str(knowledge_dir))
    monkeypatch.setenv("OJT_MIGRATIONS_DIR", str(migrations_dir))
    clear_settings_cache()

    try:
        settings = get_settings()
    finally:
        clear_settings_cache()

    assert settings.resolved_knowledge_dir == knowledge_dir
    assert settings.resolved_migrations_dir == migrations_dir


@pytest.mark.parametrize(
    "bad_database_url",
    [
        "",
        "not-a-url",
        "mysql://user:pass@localhost/ojtflow",
        "postgresql://user:pass@:5432/ojtflow",
        "postgresql://user:pass@localhost:bad-port/ojtflow",
        "postgresql://user:pass@localhost:5432",
        "postgresql://user:pass@localhost:5432/ojtflow#fragment",
    ],
)
def test_postgres_database_url_must_be_supported(monkeypatch, bad_database_url) -> None:
    monkeypatch.setenv("OJT_DATABASE_URL", bad_database_url)
    clear_settings_cache()

    try:
        with pytest.raises(ValueError, match="Invalid Postgres URL"):
            get_settings()
    finally:
        clear_settings_cache()


@pytest.mark.parametrize(
    "database_url",
    [
        " postgresql://user:pass@localhost:5432/ojtflow ",
        "postgres://user:pass@db.example.test/ojtflow",
        "postgresql://localhost/ojtflow",
    ],
)
def test_postgres_database_url_supported_values_are_accepted(
    monkeypatch,
    database_url,
) -> None:
    monkeypatch.setenv("OJT_DATABASE_URL", database_url)
    clear_settings_cache()

    try:
        settings = get_settings()
    finally:
        clear_settings_cache()

    assert settings.postgres_dsn == database_url.strip()


def test_database_url_fallback_is_validated(monkeypatch) -> None:
    monkeypatch.delenv("OJT_DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "mysql://user:pass@localhost/ojtflow")
    clear_settings_cache()

    try:
        with pytest.raises(ValueError, match="Invalid Postgres URL"):
            get_settings()
    finally:
        clear_settings_cache()


@pytest.mark.parametrize(
    ("env_var", "bad_value"),
    [
        ("OJT_GOOGLE_OAUTH_TIMEOUT_SECONDS", "0"),
        ("OJT_AUTH_SESSION_TTL_SECONDS", "0"),
        ("OJT_AUTH_STATE_TTL_SECONDS", "-1"),
        ("OJT_MAX_UPLOAD_BYTES", "0"),
        ("OJT_MAX_INLINE_DATA_BYTES", "-1"),
        ("OJT_UPLOAD_READ_CHUNK_BYTES", "0"),
    ],
)
def test_numeric_runtime_settings_must_be_positive(monkeypatch, env_var, bad_value) -> None:
    monkeypatch.setenv(env_var, bad_value)
    clear_settings_cache()

    try:
        with pytest.raises(ValidationError):
            get_settings()
    finally:
        clear_settings_cache()


def test_positive_runtime_settings_are_accepted(monkeypatch) -> None:
    monkeypatch.setenv("OJT_GOOGLE_OAUTH_TIMEOUT_SECONDS", "0.5")
    monkeypatch.setenv("OJT_AUTH_SESSION_TTL_SECONDS", "1")
    monkeypatch.setenv("OJT_AUTH_STATE_TTL_SECONDS", "1")
    monkeypatch.setenv("OJT_MAX_UPLOAD_BYTES", "1")
    monkeypatch.setenv("OJT_MAX_INLINE_DATA_BYTES", "1")
    monkeypatch.setenv("OJT_UPLOAD_READ_CHUNK_BYTES", "1")
    clear_settings_cache()

    try:
        settings = get_settings()
    finally:
        clear_settings_cache()

    assert settings.google_oauth_timeout_seconds == 0.5
    assert settings.auth_session_ttl_seconds == 1
    assert settings.auth_state_ttl_seconds == 1
    assert settings.max_upload_bytes == 1
    assert settings.max_inline_data_bytes == 1
    assert settings.upload_read_chunk_bytes == 1


@pytest.mark.parametrize(
    "bad_redis_url",
    [
        "localhost:6379",
        "http://localhost:6379/0",
        "redis://:bad-port",
        "redis://localhost:6379/0#fragment",
        "unix://",
    ],
)
def test_redis_url_must_be_a_supported_redis_url(monkeypatch, bad_redis_url) -> None:
    monkeypatch.setenv("OJT_REDIS_URL", bad_redis_url)
    clear_settings_cache()

    try:
        with pytest.raises(ValueError, match="Invalid Redis URL"):
            get_settings()
    finally:
        clear_settings_cache()


@pytest.mark.parametrize(
    "redis_url",
    [
        "",
        " redis://localhost:6379/0 ",
        "rediss://cache.example.test:6380/0",
        "unix:///tmp/redis.sock",
    ],
)
def test_redis_url_supported_values_are_accepted(monkeypatch, redis_url) -> None:
    monkeypatch.setenv("OJT_REDIS_URL", redis_url)
    clear_settings_cache()

    try:
        settings = get_settings()
    finally:
        clear_settings_cache()

    assert settings.redis_url == redis_url.strip()


@pytest.mark.parametrize("storage_backend", ["postgres", "sqlite", "memory", " POSTGRES "])
def test_storage_backend_supported_values_are_accepted(monkeypatch, storage_backend) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", storage_backend)
    clear_settings_cache()

    try:
        settings = get_settings()
    finally:
        clear_settings_cache()

    assert settings.storage_backend == storage_backend.strip().lower()


@pytest.mark.parametrize("bad_storage_backend", ["", "   ", "postgresql", "mysql", "mongo"])
def test_storage_backend_must_be_supported(monkeypatch, bad_storage_backend) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", bad_storage_backend)
    clear_settings_cache()

    try:
        with pytest.raises(ValueError, match="Invalid storage backend"):
            get_settings()
    finally:
        clear_settings_cache()


def test_upload_extensions_are_normalized_and_deduplicated(monkeypatch) -> None:
    monkeypatch.setenv("OJT_ALLOWED_UPLOAD_EXTENSIONS", " CSV , .JSON, yml, csv ")
    clear_settings_cache()

    try:
        settings = get_settings()
    finally:
        clear_settings_cache()

    assert settings.allowed_upload_extensions == (".csv", ".json", ".yml")


@pytest.mark.parametrize(
    "bad_extension",
    [".", "..", ".tar.gz", ".exe", "pdf/evil", "pdf*", "bad extension"],
)
def test_upload_extensions_must_be_supported_simple_suffixes(
    monkeypatch,
    bad_extension,
) -> None:
    monkeypatch.setenv("OJT_ALLOWED_UPLOAD_EXTENSIONS", bad_extension)
    clear_settings_cache()

    try:
        with pytest.raises(ValueError, match="Invalid upload extension"):
            get_settings()
    finally:
        clear_settings_cache()


def test_oauth_redirect_uri_settings_allow_local_http_and_https(monkeypatch) -> None:
    monkeypatch.setenv(
        "OJT_GOOGLE_REDIRECT_URI",
        " http://127.0.0.1:8000/api/v1/auth/google/callback ",
    )
    monkeypatch.setenv(
        "OJT_GOOGLE_FRONTEND_REDIRECT_URI",
        " http://[::1]:5173/auth/callback ",
    )
    monkeypatch.setenv(
        "OJT_ALLOWED_AUTH_REDIRECT_URIS",
        " https://app.example.com/auth/callback , https://app.example.com/auth/callback ",
    )
    clear_settings_cache()

    try:
        settings = get_settings()
    finally:
        clear_settings_cache()

    assert settings.google_redirect_uri == "http://127.0.0.1:8000/api/v1/auth/google/callback"
    assert settings.google_frontend_redirect_uri == "http://[::1]:5173/auth/callback"
    assert settings.allowed_auth_redirect_uris == ("https://app.example.com/auth/callback",)
    assert settings.resolved_allowed_auth_redirect_uris == {
        "http://127.0.0.1:8000/api/v1/auth/google/callback",
        "http://[::1]:5173/auth/callback",
        "https://app.example.com/auth/callback",
    }


@pytest.mark.parametrize(
    ("env_var", "bad_redirect_uri"),
    [
        ("OJT_GOOGLE_REDIRECT_URI", ""),
        ("OJT_GOOGLE_REDIRECT_URI", "   "),
        ("OJT_GOOGLE_REDIRECT_URI", "ftp://example.com/callback"),
        ("OJT_GOOGLE_REDIRECT_URI", "https://example.com/callback#fragment"),
        ("OJT_GOOGLE_REDIRECT_URI", "https://user:pass@example.com/callback"),
        ("OJT_GOOGLE_REDIRECT_URI", "http://example.com/callback"),
        ("OJT_GOOGLE_REDIRECT_URI", "/auth/callback"),
        ("OJT_GOOGLE_FRONTEND_REDIRECT_URI", "javascript:alert(1)"),
        ("OJT_ALLOWED_AUTH_REDIRECT_URIS", "https://app.example.com/auth/callback#token"),
        ("OJT_ALLOWED_AUTH_REDIRECT_URIS", "http://app.example.com/auth/callback"),
    ],
)
def test_oauth_redirect_uri_settings_reject_unsafe_values(
    monkeypatch,
    env_var,
    bad_redirect_uri,
) -> None:
    monkeypatch.setenv(env_var, bad_redirect_uri)
    clear_settings_cache()

    try:
        with pytest.raises(ValueError, match="Invalid OAuth redirect URI"):
            get_settings()
    finally:
        clear_settings_cache()


def test_google_hosted_domains_are_normalized_and_deduplicated(monkeypatch) -> None:
    monkeypatch.setenv(
        "OJT_ALLOWED_GOOGLE_HOSTED_DOMAINS",
        " Example.COM , research.example.org, example.com ",
    )
    clear_settings_cache()

    try:
        settings = get_settings()
    finally:
        clear_settings_cache()

    assert settings.allowed_google_hosted_domains == (
        "example.com",
        "research.example.org",
    )


@pytest.mark.parametrize(
    "bad_domain",
    [
        "localhost",
        "127.0.0.1",
        "https://example.com",
        "example.com/path",
        "example.com:443",
        "user@example.com",
        "*.example.com",
        ".example.com",
        "bad domain.com",
        "bad-.example.com",
        "example.com.",
    ],
)
def test_google_hosted_domains_must_be_dns_domains(monkeypatch, bad_domain) -> None:
    monkeypatch.setenv("OJT_ALLOWED_GOOGLE_HOSTED_DOMAINS", bad_domain)
    clear_settings_cache()

    try:
        with pytest.raises(ValueError, match="Invalid domain"):
            get_settings()
    finally:
        clear_settings_cache()


@pytest.mark.parametrize(
    ("configured_domain", "expected_domain"),
    [
        (" Example.COM ", "example.com"),
        (" .Example.COM ", ".example.com"),
    ],
)
def test_auth_cookie_domain_is_normalized(
    monkeypatch,
    configured_domain,
    expected_domain,
) -> None:
    monkeypatch.setenv("OJT_AUTH_COOKIE_DOMAIN", configured_domain)
    clear_settings_cache()

    try:
        settings = get_settings()
    finally:
        clear_settings_cache()

    assert settings.auth_cookie_domain == expected_domain


@pytest.mark.parametrize(
    "bad_domain",
    [
        "localhost",
        "127.0.0.1",
        "https://example.com",
        "example.com/path",
        "example.com:443",
        "user@example.com",
        "*.example.com",
        "bad domain.com",
        "bad-.example.com",
        "example.com.",
    ],
)
def test_auth_cookie_domain_must_be_dns_domain(monkeypatch, bad_domain) -> None:
    monkeypatch.setenv("OJT_AUTH_COOKIE_DOMAIN", bad_domain)
    clear_settings_cache()

    try:
        with pytest.raises(ValueError, match="Invalid domain"):
            get_settings()
    finally:
        clear_settings_cache()


def test_embedding_settings_accept_deterministic_provider(monkeypatch) -> None:
    monkeypatch.setenv("OJT_EMBEDDING_PROVIDER", " DETERMINISTIC ")
    monkeypatch.setenv("OJT_EMBEDDING_MODEL", " deterministic-hash-v0 ")
    monkeypatch.setenv("OJT_EMBEDDING_DIMENSIONS", " 64 ")
    clear_settings_cache()

    try:
        settings = get_settings()
    finally:
        clear_settings_cache()

    assert settings.embedding_provider == "deterministic"
    assert settings.embedding_model == "deterministic-hash-v0"
    assert settings.embedding_dimensions == 64


def test_embedding_settings_accept_openai_provider(monkeypatch) -> None:
    monkeypatch.setenv("OJT_EMBEDDING_PROVIDER", " OPENAI ")
    monkeypatch.setenv("OJT_EMBEDDING_MODEL", " text-embedding-3-small ")
    monkeypatch.setenv("OJT_EMBEDDING_DIMENSIONS", " 384 ")
    monkeypatch.setenv("OPENAI_API_KEY", "host-key")
    clear_settings_cache()

    try:
        settings = get_settings()
    finally:
        clear_settings_cache()

    assert settings.embedding_provider == "openai"
    assert settings.embedding_model == "text-embedding-3-small"
    assert settings.embedding_dimensions == 384
    assert settings.openai_api_key == "host-key"


@pytest.mark.parametrize("bad_provider", ["", "   ", "vertex", "sentence-transformers"])
def test_embedding_provider_must_match_implemented_adapter(monkeypatch, bad_provider) -> None:
    monkeypatch.setenv("OJT_EMBEDDING_PROVIDER", bad_provider)
    clear_settings_cache()

    try:
        with pytest.raises(ValueError, match="Invalid embedding provider"):
            get_settings()
    finally:
        clear_settings_cache()


@pytest.mark.parametrize("bad_model", ["", "   ", "hash-v1"])
def test_deterministic_embedding_model_must_match_adapter(monkeypatch, bad_model) -> None:
    monkeypatch.setenv("OJT_EMBEDDING_MODEL", bad_model)
    clear_settings_cache()

    try:
        with pytest.raises(ValueError, match="Invalid embedding model"):
            get_settings()
    finally:
        clear_settings_cache()


@pytest.mark.parametrize("bad_dimensions", ["", "   ", "0", "1", "128", "not-a-number"])
def test_deterministic_embedding_dimensions_must_match_adapter(
    monkeypatch,
    bad_dimensions,
) -> None:
    monkeypatch.setenv("OJT_EMBEDDING_DIMENSIONS", bad_dimensions)
    clear_settings_cache()

    try:
        with pytest.raises(ValueError, match="Invalid embedding dimensions"):
            get_settings()
    finally:
        clear_settings_cache()


@pytest.mark.parametrize("bad_dimensions", ["", "   ", "0", "-1", "not-a-number"])
def test_openai_embedding_dimensions_must_be_positive(monkeypatch, bad_dimensions) -> None:
    monkeypatch.setenv("OJT_EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("OJT_EMBEDDING_DIMENSIONS", bad_dimensions)
    clear_settings_cache()

    try:
        with pytest.raises(ValueError, match="Invalid embedding dimensions"):
            get_settings()
    finally:
        clear_settings_cache()


@pytest.mark.parametrize("bad_cookie_name", ["", "   ", "bad name", "bad;name", "bad,name"])
def test_auth_cookie_name_must_be_valid_http_cookie_token(
    monkeypatch,
    bad_cookie_name,
) -> None:
    monkeypatch.setenv("OJT_AUTH_COOKIE_NAME", bad_cookie_name)
    clear_settings_cache()

    try:
        with pytest.raises(ValueError, match="Invalid auth cookie name"):
            get_settings()
    finally:
        clear_settings_cache()


def test_custom_auth_cookie_name_is_accepted(monkeypatch) -> None:
    monkeypatch.setenv("OJT_AUTH_COOKIE_NAME", "ojtflow_session_v2")
    clear_settings_cache()

    try:
        settings = get_settings()
    finally:
        clear_settings_cache()

    assert settings.auth_cookie_name == "ojtflow_session_v2"


def test_runtime_docs_explain_positive_numeric_settings() -> None:
    docs = "\n".join(
        [
            (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
            (REPO_ROOT / ".env.example").read_text(encoding="utf-8"),
            (REPO_ROOT / "docs" / "api_contract_v0.md").read_text(encoding="utf-8"),
            (REPO_ROOT / "docs" / "auth_architecture.md").read_text(encoding="utf-8"),
            (REPO_ROOT / "docs" / "document_parsing_uploads.md").read_text(
                encoding="utf-8",
            ),
            (REPO_ROOT / "docs" / "retrieval_module_v0.md").read_text(encoding="utf-8"),
        ]
    )

    for setting in [
        "OJT_GOOGLE_OAUTH_TIMEOUT_SECONDS",
        "OJT_AUTH_SESSION_TTL_SECONDS",
        "OJT_AUTH_STATE_TTL_SECONDS",
        "OJT_MAX_UPLOAD_BYTES",
        "OJT_MAX_INLINE_DATA_BYTES",
        "OJT_UPLOAD_READ_CHUNK_BYTES",
    ]:
        assert setting in docs

    assert "must be positive" in docs
    assert "OAuth timeout" in docs
    assert "auth TTLs" in docs
    assert "upload limits" in docs
    assert "chunk size" in docs


def test_runtime_docs_explain_storage_backend_validation() -> None:
    docs = "\n".join(
        [
            (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
            (REPO_ROOT / ".env.example").read_text(encoding="utf-8"),
            (REPO_ROOT / "docs" / "api_contract_v0.md").read_text(encoding="utf-8"),
        ]
    )

    assert "OJT_STORAGE_BACKEND" in docs
    assert "postgres, sqlite, or memory" in docs


def test_runtime_docs_explain_resource_directory_configuration() -> None:
    docs = "\n".join(
        [
            (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
            (REPO_ROOT / ".env.example").read_text(encoding="utf-8"),
            (REPO_ROOT / "docs" / "api_contract_v0.md").read_text(encoding="utf-8"),
        ]
    )

    assert "OJT_KNOWLEDGE_DIR" in docs
    assert "OJT_MIGRATIONS_DIR" in docs
    assert "trusted healthcare knowledge" in docs
    assert "Postgres SQL migrations" in docs
    assert "installed Python package location" in docs
    assert "must exist and contain ordered `.sql` files" in docs


def test_runtime_docs_explain_upload_extension_validation() -> None:
    docs = "\n".join(
        [
            (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
            (REPO_ROOT / ".env.example").read_text(encoding="utf-8"),
            (REPO_ROOT / "docs" / "api_contract_v0.md").read_text(encoding="utf-8"),
            (REPO_ROOT / "docs" / "document_parsing_uploads.md").read_text(
                encoding="utf-8",
            ),
        ]
    )

    assert "OJT_ALLOWED_UPLOAD_EXTENSIONS" in docs
    assert "supported upload extensions" in docs
    assert ".exe" in docs


def test_runtime_docs_explain_oauth_redirect_uri_validation() -> None:
    docs = "\n".join(
        [
            (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
            (REPO_ROOT / ".env.example").read_text(encoding="utf-8"),
            (REPO_ROOT / "docs" / "api_contract_v0.md").read_text(encoding="utf-8"),
            (REPO_ROOT / "docs" / "auth_architecture.md").read_text(encoding="utf-8"),
        ]
    )

    assert "OJT_ALLOWED_AUTH_REDIRECT_URIS" in docs
    assert "Non-local HTTP callbacks must use HTTPS" in docs
    assert "fragments" in docs
    assert "user info" in docs


def test_runtime_docs_explain_auth_domain_validation() -> None:
    docs = "\n".join(
        [
            (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
            (REPO_ROOT / ".env.example").read_text(encoding="utf-8"),
            (REPO_ROOT / "docs" / "api_contract_v0.md").read_text(encoding="utf-8"),
            (REPO_ROOT / "docs" / "auth_architecture.md").read_text(encoding="utf-8"),
        ]
    )

    assert "OJT_ALLOWED_GOOGLE_HOSTED_DOMAINS" in docs
    assert "OJT_AUTH_COOKIE_DOMAIN" in docs
    assert "bare DNS domains" in docs
    assert "URLs, ports, wildcards, spaces, IP addresses, and localhost" in docs
    assert "omit OJT_AUTH_COOKIE_DOMAIN" in docs


def test_runtime_docs_explain_embedding_provider_validation() -> None:
    docs = "\n".join(
        [
            (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
            (REPO_ROOT / ".env.example").read_text(encoding="utf-8"),
            (REPO_ROOT / "docs" / "api_contract_v0.md").read_text(encoding="utf-8"),
            (REPO_ROOT / "docs" / "retrieval_module_v0.md").read_text(encoding="utf-8"),
        ]
    )

    assert "OJT_EMBEDDING_PROVIDER" in docs
    assert "OJT_EMBEDDING_PROVIDER=openai" in docs
    assert "OJT_OPENAI_API_KEY" in docs
    assert "deterministic-hash-v0" in docs
    assert "OJT_EMBEDDING_DIMENSIONS=384" in docs
    assert "vector(384)" in docs


def test_runtime_docs_explain_auth_cookie_name_validation() -> None:
    docs = "\n".join(
        [
            (REPO_ROOT / "docs" / "api_contract_v0.md").read_text(encoding="utf-8"),
            (REPO_ROOT / "docs" / "auth_architecture.md").read_text(encoding="utf-8"),
        ]
    )

    assert "OJT_AUTH_COOKIE_NAME" in docs
    assert "valid HTTP cookie token" in docs
    assert "spaces, commas, or semicolons" in docs
