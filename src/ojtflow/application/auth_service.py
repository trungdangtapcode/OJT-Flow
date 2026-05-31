"""Google OAuth sign-in and backend session orchestration."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from ojtflow.application.ports import AuthRepository, IdentityProvider, SessionCache
from ojtflow.core.contracts.auth import (
    AuthenticatedSession,
    SessionRecord,
    UserRecord,
)
from ojtflow.core.errors import OJTFlowError


class AuthService:
    """Creates app users and backend sessions from Google identities."""

    def __init__(
        self,
        repository: AuthRepository,
        cache: SessionCache,
        identity_provider: IdentityProvider,
        google_redirect_uri: str,
        allowed_redirect_uris: set[str] | None,
        session_ttl_seconds: int,
        state_ttl_seconds: int,
    ) -> None:
        self.repository = repository
        self.cache = cache
        self.identity_provider = identity_provider
        self.google_redirect_uri = google_redirect_uri
        self.allowed_redirect_uris = {
            uri for uri in (allowed_redirect_uris or {google_redirect_uri}) if uri
        }
        self.session_ttl_seconds = session_ttl_seconds
        self.state_ttl_seconds = state_ttl_seconds

    def google_authorization_url(self, redirect_uri: str | None = None) -> dict[str, str]:
        self._ensure_google_configured()
        selected_redirect_uri = self._select_redirect_uri(redirect_uri)
        state = secrets.token_urlsafe(32)
        self.cache.set_oauth_state(
            state,
            self.state_ttl_seconds,
            payload={"redirect_uri": selected_redirect_uri},
        )
        return {
            "authorization_url": self.identity_provider.authorization_url(
                redirect_uri=selected_redirect_uri,
                state=state,
            ),
            "state": state,
        }

    async def complete_google_login(
        self,
        code: str,
        state: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        self._ensure_google_configured()
        state_payload = self.cache.consume_oauth_state(state)
        if not state_payload:
            raise OJTFlowError("Invalid or expired OAuth state.")

        redirect_uri = self._select_redirect_uri(
            str(state_payload.get("redirect_uri") or self.google_redirect_uri)
        )
        profile = await self.identity_provider.exchange_code_for_profile(
            code=code,
            redirect_uri=redirect_uri,
        )
        user = self.repository.upsert_google_user(profile)
        raw_token = secrets.token_urlsafe(48)
        token_hash = _hash_token(raw_token)
        expires_at = _now() + timedelta(seconds=self.session_ttl_seconds)
        session = self.repository.create_session(
            user_id=user.user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        authenticated = AuthenticatedSession(user=user, session=session)
        self.cache.set_session(
            token_hash,
            _session_payload(authenticated),
            self.session_ttl_seconds,
        )
        return {
            "token_type": "bearer",
            "access_token": raw_token,
            "expires_at": expires_at.isoformat(),
            "user": _public_user(user),
        }

    def authenticate_token(self, token: str) -> AuthenticatedSession | None:
        token_hash = _hash_token(token)
        cached = self.cache.get_session(token_hash)
        if cached:
            authenticated = _session_from_payload(cached)
            if authenticated.session.expires_at <= _now():
                self.cache.delete_session(token_hash)
                return None
            return authenticated

        authenticated = self.repository.get_active_session(token_hash, _now())
        if not authenticated:
            return None

        ttl_seconds = max(1, int((authenticated.session.expires_at - _now()).total_seconds()))
        self.cache.set_session(token_hash, _session_payload(authenticated), ttl_seconds)
        self.repository.touch_session(token_hash)
        return authenticated

    def logout(self, token: str) -> None:
        token_hash = _hash_token(token)
        self.repository.revoke_session(token_hash)
        self.cache.delete_session(token_hash)

    def _ensure_google_configured(self) -> None:
        if not self.identity_provider.is_configured:
            raise OJTFlowError(
                "Google OAuth is not configured. Set OJT_GOOGLE_CLIENT_ID and "
                "OJT_GOOGLE_CLIENT_SECRET."
            )

    def _select_redirect_uri(self, redirect_uri: str | None) -> str:
        selected = redirect_uri or self.google_redirect_uri
        if selected not in self.allowed_redirect_uris:
            raise OJTFlowError("OAuth redirect URI is not allowed for this backend.")
        return selected


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _public_user(user: UserRecord) -> dict[str, Any]:
    return {
        "user_id": user.user_id,
        "email": user.email,
        "email_verified": user.email_verified,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
    }


def _public_session(session: SessionRecord) -> dict[str, Any]:
    return {
        "session_id": session.session_id,
        "expires_at": session.expires_at.isoformat(),
        "last_seen_at": session.last_seen_at.isoformat() if session.last_seen_at else None,
    }


def auth_session_response(authenticated: AuthenticatedSession) -> dict[str, Any]:
    return {
        "user": _public_user(authenticated.user),
        "session": _public_session(authenticated.session),
    }


def _session_payload(authenticated: AuthenticatedSession) -> dict[str, Any]:
    user = authenticated.user
    session = authenticated.session
    return {
        "user": {
            "user_id": user.user_id,
            "google_sub": user.google_sub,
            "email": user.email,
            "email_verified": user.email_verified,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        },
        "session": {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "token_hash": session.token_hash,
            "created_at": session.created_at.isoformat(),
            "expires_at": session.expires_at.isoformat(),
            "revoked_at": session.revoked_at.isoformat() if session.revoked_at else None,
            "last_seen_at": session.last_seen_at.isoformat() if session.last_seen_at else None,
        },
    }


def _session_from_payload(payload: dict[str, Any]) -> AuthenticatedSession:
    user = payload["user"]
    session = payload["session"]
    return AuthenticatedSession(
        user=UserRecord(
            user_id=user["user_id"],
            google_sub=user["google_sub"],
            email=user["email"],
            email_verified=user["email_verified"],
            display_name=user.get("display_name"),
            avatar_url=user.get("avatar_url"),
            created_at=_parse_datetime(user["created_at"]),
            updated_at=_parse_datetime(user["updated_at"]),
            last_login_at=_parse_optional_datetime(user.get("last_login_at")),
        ),
        session=SessionRecord(
            session_id=session["session_id"],
            user_id=session["user_id"],
            token_hash=session["token_hash"],
            created_at=_parse_datetime(session["created_at"]),
            expires_at=_parse_datetime(session["expires_at"]),
            revoked_at=_parse_optional_datetime(session.get("revoked_at")),
            last_seen_at=_parse_optional_datetime(session.get("last_seen_at")),
        ),
    )


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _parse_optional_datetime(value: str | None) -> datetime | None:
    return _parse_datetime(value) if value else None
