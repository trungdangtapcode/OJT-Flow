from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime, timezone

import pytest

from ojtflow.application.auth_service import AuthService
from ojtflow.core.contracts.auth import (
    AuthenticatedSession,
    GoogleIdentityProfile,
    ServiceAccountRecord,
    SessionRecord,
    UserRecord,
)
from ojtflow.core.errors import DependencyUnavailableError, OJTFlowError
from ojtflow.infrastructure.auth.google import GoogleOAuthClient
from ojtflow.infrastructure.cache import session_cache as cache_module


class FakeGoogleClient:
    client_id = "google-client-id"
    client_secret = "google-client-secret"

    @property
    def is_configured(self) -> bool:
        return True

    def authorization_url(self, redirect_uri: str, state: str) -> str:
        return f"https://accounts.google.com/o/oauth2/v2/auth?state={state}"

    async def exchange_code_for_profile(
        self,
        code: str,
        redirect_uri: str,
    ) -> GoogleIdentityProfile:
        assert code == "google-code"
        return GoogleIdentityProfile(
            google_sub="google-sub-1",
            email="user@example.com",
            email_verified=True,
            display_name="Example User",
            avatar_url="https://example.com/avatar.png",
        )


class FakeCache:
    def __init__(self) -> None:
        self.sessions = {}
        self.states = set()

    def set_session(self, token_hash, payload, ttl_seconds) -> None:
        self.sessions[token_hash] = payload

    def get_session(self, token_hash):
        return self.sessions.get(token_hash)

    def delete_session(self, token_hash) -> None:
        self.sessions.pop(token_hash, None)

    def set_oauth_state(self, state, ttl_seconds, payload=None) -> None:
        self.states.add((state, tuple((payload or {}).items())))

    def consume_oauth_state(self, state):
        for item in self.states:
            cached_state, payload_items = item
            if cached_state == state:
                self.states.remove(item)
                return dict(payload_items)
        return None


class FakeAuthRepository:
    def __init__(self) -> None:
        self.users = {}
        self.sessions = {}
        self.service_accounts = {}
        self.revoked = set()

    def upsert_google_user(self, profile: GoogleIdentityProfile) -> UserRecord:
        now = datetime.now(timezone.utc)
        user = UserRecord(
            user_id="usr_test",
            google_sub=profile.google_sub,
            email=profile.email,
            email_verified=profile.email_verified,
            display_name=profile.display_name,
            avatar_url=profile.avatar_url,
            created_at=now,
            updated_at=now,
            last_login_at=now,
        )
        self.users[user.user_id] = user
        return user

    def create_service_account(
        self,
        *,
        account_id,
        organization_id,
        slug,
        display_name,
        role_key,
        created_by_user_id,
    ):
        now = datetime.now(timezone.utc)
        user = UserRecord(
            user_id=f"usr_{account_id}",
            google_sub=f"service-account:{account_id}",
            email=f"{slug}.{account_id}@service-account.ojtflow.local",
            email_verified=True,
            display_name=display_name,
            avatar_url=None,
            created_at=now,
            updated_at=now,
            last_login_at=None,
        )
        account = ServiceAccountRecord(
            account_id=account_id,
            user_id=user.user_id,
            organization_id=organization_id,
            slug=slug,
            display_name=display_name,
            role_key=role_key,
            status="active",
            created_by_user_id=created_by_user_id,
            created_at=now,
            updated_at=now,
            last_used_at=None,
        )
        self.users[user.user_id] = user
        self.service_accounts[account_id] = account
        return account

    def list_service_accounts(self, *, organization_id):
        return [
            account
            for account in self.service_accounts.values()
            if account.organization_id == organization_id
        ]

    def create_session(self, user_id, token_hash, expires_at, user_agent=None, ip_address=None):
        now = datetime.now(timezone.utc)
        session = SessionRecord(
            session_id="ses_test",
            user_id=user_id,
            token_hash=token_hash,
            created_at=now,
            expires_at=expires_at,
            revoked_at=None,
            last_seen_at=now,
        )
        self.sessions[token_hash] = session
        return session

    def get_active_session(self, token_hash, now):
        if token_hash in self.revoked:
            return None
        session = self.sessions.get(token_hash)
        if not session or session.expires_at <= now:
            return None
        return AuthenticatedSession(user=self.users[session.user_id], session=session)

    def touch_session(self, token_hash) -> None:
        pass

    def revoke_session(self, token_hash) -> None:
        self.revoked.add(token_hash)


def test_auth_service_google_login_session_and_logout() -> None:
    repository = FakeAuthRepository()
    cache = FakeCache()
    service = AuthService(
        repository=repository,
        cache=cache,
        identity_provider=FakeGoogleClient(),
        google_redirect_uri="http://localhost:8000/api/v1/auth/google/callback",
        allowed_redirect_uris={
            "http://localhost:8000/api/v1/auth/google/callback",
            "http://localhost:5173/auth/callback",
        },
        session_ttl_seconds=3600,
        state_ttl_seconds=600,
        service_account_token_ttl_seconds=86400,
    )

    auth_url = service.google_authorization_url(
        redirect_uri="http://localhost:5173/auth/callback",
    )
    assert auth_url["authorization_url"].startswith("https://accounts.google.com")

    login = asyncio.run(
        service.complete_google_login(
            code="google-code",
            state=auth_url["state"],
            user_agent="pytest",
            ip_address="127.0.0.1",
        )
    )
    assert login["token_type"] == "bearer"
    assert login["user"]["email"] == "user@example.com"

    authenticated = service.authenticate_token(login["access_token"])
    assert authenticated is not None
    assert authenticated.user.email == "user@example.com"

    service.logout(login["access_token"])
    assert service.authenticate_token(login["access_token"]) is None


def test_auth_service_issues_service_account_token() -> None:
    repository = FakeAuthRepository()
    service = _auth_service(repository=repository)

    account = service.create_service_account_identity(
        organization_id="org_service",
        slug="Nightly Ingestion",
        display_name="Nightly Ingestion",
        role_key="operator",
        created_by_user_id="usr_admin",
    )
    issued = service.issue_service_account_token(
        service_account=account,
        token_ttl_seconds=60,
    )
    authenticated = service.authenticate_token(issued["access_token"])

    assert issued["token_type"] == "bearer"
    assert issued["access_token"].startswith("ojt_sa_")
    assert issued["service_account"].account_id == account.account_id
    assert authenticated is not None
    assert authenticated.identity_type == "service_account"
    assert authenticated.service_account is not None
    assert authenticated.service_account.role_key == "operator"


def test_auth_service_recovers_from_malformed_cached_session() -> None:
    repository = FakeAuthRepository()
    cache = FakeCache()
    service = _auth_service(repository=repository, cache=cache)
    auth_url = service.google_authorization_url(
        redirect_uri="http://localhost:5173/auth/callback",
    )
    login = asyncio.run(
        service.complete_google_login(
            code="google-code",
            state=auth_url["state"],
        )
    )
    token_hash = _hash_test_token(login["access_token"])
    cache.sessions[token_hash] = {"not": "a valid session payload"}

    authenticated = service.authenticate_token(login["access_token"])

    assert authenticated is not None
    assert authenticated.user.email == "user@example.com"
    assert "session" in cache.sessions[token_hash]


def test_auth_service_rejects_revoked_cached_session() -> None:
    repository = FakeAuthRepository()
    cache = FakeCache()
    service = _auth_service(repository=repository, cache=cache)
    auth_url = service.google_authorization_url(
        redirect_uri="http://localhost:5173/auth/callback",
    )
    login = asyncio.run(
        service.complete_google_login(
            code="google-code",
            state=auth_url["state"],
        )
    )
    token_hash = _hash_test_token(login["access_token"])
    cache.sessions[token_hash]["session"]["revoked_at"] = datetime.now(timezone.utc).isoformat()

    assert service.authenticate_token(login["access_token"]) is None
    assert token_hash not in cache.sessions


def test_auth_service_rejects_unallowed_redirect_uri() -> None:
    service = _auth_service(
        allowed_redirect_uris={"http://localhost:5173/auth/callback"},
    )

    with pytest.raises(OJTFlowError, match="redirect URI is not allowed"):
        service.google_authorization_url(redirect_uri="https://example.com/auth/callback")


def test_auth_service_consumes_oauth_state_once() -> None:
    service = _auth_service()
    auth_url = service.google_authorization_url(redirect_uri="http://localhost:5173/auth/callback")
    asyncio.run(service.complete_google_login(code="google-code", state=auth_url["state"]))

    with pytest.raises(OJTFlowError, match="Invalid or expired OAuth state"):
        asyncio.run(service.complete_google_login(code="google-code", state=auth_url["state"]))


def test_google_oauth_client_wraps_malformed_token_json(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_google_token_response(monkeypatch, _MalformedJsonResponse())
    client = GoogleOAuthClient(client_id="client-id", client_secret="client-secret")

    with pytest.raises(OJTFlowError, match="not valid JSON"):
        asyncio.run(
            client.exchange_code_for_profile(
                code="google-code",
                redirect_uri="http://localhost:5173/auth/callback",
            )
        )


def test_google_oauth_client_rejects_unexpected_token_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_google_token_response(monkeypatch, _TokenResponse(["not", "an", "object"]))
    client = GoogleOAuthClient(client_id="client-id", client_secret="client-secret")

    with pytest.raises(OJTFlowError, match="unexpected shape"):
        asyncio.run(
            client.exchange_code_for_profile(
                code="google-code",
                redirect_uri="http://localhost:5173/auth/callback",
            )
        )


def test_google_oauth_client_requires_string_id_token(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_google_token_response(monkeypatch, _TokenResponse({"id_token": 123}))
    client = GoogleOAuthClient(client_id="client-id", client_secret="client-secret")

    with pytest.raises(OJTFlowError, match="did not include an id_token"):
        asyncio.run(
            client.exchange_code_for_profile(
                code="google-code",
                redirect_uri="http://localhost:5173/auth/callback",
            )
        )


class _TokenResponse:
    text = '{"id_token": "fake"}'

    def __init__(self, payload) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self.payload


class _MalformedJsonResponse(_TokenResponse):
    text = "{not-json"

    def __init__(self) -> None:
        super().__init__(None)

    def json(self):
        raise ValueError("invalid json")


def _install_fake_google_token_response(monkeypatch: pytest.MonkeyPatch, response) -> None:
    class _FakeAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            self.args = args
            self.kwargs = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback) -> None:
            return None

        async def post(self, *args, **kwargs):
            return response

    monkeypatch.setattr(
        "ojtflow.infrastructure.auth.google.httpx.AsyncClient",
        _FakeAsyncClient,
    )


def test_redis_session_cache_strict_mode_raises_when_redis_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_failing_redis(monkeypatch)
    cache = cache_module.RedisSessionCache(
        "redis://secret-cache.example.test:6379/0",
        allow_fallback=False,
    )

    with pytest.raises(DependencyUnavailableError) as exc_info:
        cache.set_oauth_state("state-1", 60, {"redirect_uri": "http://localhost/callback"})

    assert exc_info.value.details == {
        "dependency": "redis",
        "operation": "set_oauth_state",
        "error_type": "RedisError",
    }
    assert "secret-cache" not in str(exc_info.value.details)


def test_redis_session_cache_strict_mode_handles_missing_redis_url() -> None:
    cache = cache_module.RedisSessionCache("", allow_fallback=False)

    with pytest.raises(DependencyUnavailableError) as exc_info:
        cache.set_oauth_state("state-1", 60)

    assert exc_info.value.details == {
        "dependency": "redis",
        "operation": "set_oauth_state",
    }


def test_redis_session_cache_strict_mode_reports_client_construction_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class InvalidRedisModule:
        @staticmethod
        def from_url(*args, **kwargs):
            del args, kwargs
            raise ValueError("invalid Redis URL with secret details")

    monkeypatch.setattr(cache_module, "redis", InvalidRedisModule)
    cache = cache_module.RedisSessionCache("redis://:bad-port", allow_fallback=False)

    with pytest.raises(DependencyUnavailableError) as exc_info:
        cache.get_session("token-hash")

    assert exc_info.value.details == {
        "dependency": "redis",
        "operation": "get_session",
        "error_type": "ValueError",
    }
    assert "secret details" not in str(exc_info.value.details)


def test_redis_session_cache_fallback_mode_remains_process_local_for_development(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_failing_redis(monkeypatch)
    cache = cache_module.RedisSessionCache(
        "redis://secret-cache.example.test:6379/0",
        allow_fallback=True,
    )

    cache.set_oauth_state("state-1", 60, {"redirect_uri": "http://localhost/callback"})

    assert cache.consume_oauth_state("state-1") == {
        "redirect_uri": "http://localhost/callback"
    }


def _install_failing_redis(monkeypatch: pytest.MonkeyPatch) -> None:
    class FailingRedisClient:
        def setex(self, *args, **kwargs) -> None:
            del args, kwargs
            raise cache_module.RedisError("secret-cache.example.test refused connection")

        def getdel(self, *args, **kwargs):
            del args, kwargs
            raise cache_module.RedisError("secret-cache.example.test refused connection")

        def get(self, *args, **kwargs):
            del args, kwargs
            raise cache_module.RedisError("secret-cache.example.test refused connection")

        def delete(self, *args, **kwargs) -> None:
            del args, kwargs
            raise cache_module.RedisError("secret-cache.example.test refused connection")

    class FailingRedisModule:
        @staticmethod
        def from_url(*args, **kwargs):
            del args, kwargs
            return FailingRedisClient()

    monkeypatch.setattr(cache_module, "redis", FailingRedisModule)


def _auth_service(
    repository: FakeAuthRepository | None = None,
    cache: FakeCache | None = None,
    allowed_redirect_uris: set[str] | None = None,
) -> AuthService:
    return AuthService(
        repository=repository or FakeAuthRepository(),
        cache=cache or FakeCache(),
        identity_provider=FakeGoogleClient(),
        google_redirect_uri="http://localhost:8000/api/v1/auth/google/callback",
        allowed_redirect_uris=allowed_redirect_uris
        or {
            "http://localhost:8000/api/v1/auth/google/callback",
            "http://localhost:5173/auth/callback",
        },
        session_ttl_seconds=3600,
        state_ttl_seconds=600,
        service_account_token_ttl_seconds=86400,
    )


def _hash_test_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
