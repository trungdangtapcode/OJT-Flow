from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from ojtflow.application.auth_service import AuthService
from ojtflow.core.contracts.auth import (
    AuthenticatedSession,
    GoogleIdentityProfile,
    SessionRecord,
    UserRecord,
)
from ojtflow.core.errors import OJTFlowError


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


def test_auth_service_rejects_unallowed_redirect_uri() -> None:
    service = AuthService(
        repository=FakeAuthRepository(),
        cache=FakeCache(),
        identity_provider=FakeGoogleClient(),
        google_redirect_uri="http://localhost:8000/api/v1/auth/google/callback",
        allowed_redirect_uris={"http://localhost:5173/auth/callback"},
        session_ttl_seconds=3600,
        state_ttl_seconds=600,
    )

    with pytest.raises(OJTFlowError, match="redirect URI is not allowed"):
        service.google_authorization_url(redirect_uri="https://example.com/auth/callback")


def test_auth_service_consumes_oauth_state_once() -> None:
    service = AuthService(
        repository=FakeAuthRepository(),
        cache=FakeCache(),
        identity_provider=FakeGoogleClient(),
        google_redirect_uri="http://localhost:8000/api/v1/auth/google/callback",
        allowed_redirect_uris={
            "http://localhost:8000/api/v1/auth/google/callback",
            "http://localhost:5173/auth/callback",
        },
        session_ttl_seconds=3600,
        state_ttl_seconds=600,
    )
    auth_url = service.google_authorization_url(redirect_uri="http://localhost:5173/auth/callback")
    asyncio.run(service.complete_google_login(code="google-code", state=auth_url["state"]))

    with pytest.raises(OJTFlowError, match="Invalid or expired OAuth state"):
        asyncio.run(service.complete_google_login(code="google-code", state=auth_url["state"]))
