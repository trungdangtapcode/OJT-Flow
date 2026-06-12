"""Google OAuth sign-in and backend session orchestration."""

from __future__ import annotations

import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from ojtflow.application.ports import AuthRepository, IdentityProvider, SessionCache
from ojtflow.core.contracts.auth import (
    AuthenticatedSession,
    ServiceAccountRecord,
    SessionRecord,
    UserRecord,
)
from ojtflow.core.errors import OJTFlowError
from ojtflow.core.ids import new_id


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
        service_account_token_ttl_seconds: int,
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
        self.service_account_token_ttl_seconds = service_account_token_ttl_seconds

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
            authenticated = _session_from_cache_payload(cached)
            if authenticated is None:
                self.cache.delete_session(token_hash)
            elif authenticated.session.revoked_at is not None:
                self.cache.delete_session(token_hash)
                return None
            elif authenticated.session.expires_at <= _now():
                self.cache.delete_session(token_hash)
                return None
            else:
                return authenticated

        authenticated = self.repository.get_active_session(token_hash, _now())
        if not authenticated:
            return None

        ttl_seconds = max(1, int((authenticated.session.expires_at - _now()).total_seconds()))
        self.cache.set_session(token_hash, _session_payload(authenticated), ttl_seconds)
        self.repository.touch_session(token_hash)
        return authenticated

    def create_service_account_identity(
        self,
        *,
        organization_id: str,
        slug: str,
        display_name: str,
        role_key: str,
        created_by_user_id: str,
    ) -> ServiceAccountRecord:
        """Create an automation identity without issuing a bearer token."""

        account_id = new_id("svc")
        display_name = display_name.strip()
        if not display_name:
            raise OJTFlowError("Service account display name is required.")
        return self.repository.create_service_account(
            account_id=account_id,
            organization_id=organization_id,
            slug=_normalize_service_account_slug(slug),
            display_name=display_name,
            role_key=role_key,
            created_by_user_id=created_by_user_id,
        )

    def issue_service_account_token(
        self,
        *,
        service_account: ServiceAccountRecord,
        token_ttl_seconds: int | None = None,
    ) -> dict[str, Any]:
        """Issue a one-time bearer token for an existing service account."""

        ttl_seconds = token_ttl_seconds or self.service_account_token_ttl_seconds
        if ttl_seconds <= 0:
            raise OJTFlowError("Service account token TTL must be positive.")
        raw_token = f"ojt_sa_{secrets.token_urlsafe(48)}"
        token_hash = _hash_token(raw_token)
        expires_at = _now() + timedelta(seconds=ttl_seconds)
        session = self.repository.create_session(
            user_id=service_account.user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        authenticated = AuthenticatedSession(
            user=UserRecord(
                user_id=service_account.user_id,
                google_sub=f"service-account:{service_account.account_id}",
                email=_service_account_email(service_account.slug, service_account.account_id),
                email_verified=True,
                display_name=service_account.display_name,
                avatar_url=None,
                created_at=service_account.created_at,
                updated_at=service_account.updated_at,
                last_login_at=None,
            ),
            session=session,
            identity_type="service_account",
            service_account=service_account,
        )
        self.cache.set_session(token_hash, _session_payload(authenticated), ttl_seconds)
        return {
            "token_type": "bearer",
            "access_token": raw_token,
            "expires_at": expires_at.isoformat(),
            "service_account": service_account,
            "session": session,
        }

    def list_service_accounts(self, *, organization_id: str) -> list[ServiceAccountRecord]:
        """List service accounts for an organization workspace."""

        return self.repository.list_service_accounts(organization_id=organization_id)

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


def _public_service_account(account: ServiceAccountRecord | None) -> dict[str, Any] | None:
    if account is None:
        return None
    return {
        "account_id": account.account_id,
        "user_id": account.user_id,
        "organization_id": account.organization_id,
        "slug": account.slug,
        "display_name": account.display_name,
        "role_key": account.role_key,
        "status": account.status,
        "created_by_user_id": account.created_by_user_id,
        "created_at": account.created_at.isoformat(),
        "updated_at": account.updated_at.isoformat(),
        "last_used_at": account.last_used_at.isoformat()
        if account.last_used_at
        else None,
    }


def _public_session(session: SessionRecord) -> dict[str, Any]:
    return {
        "session_id": session.session_id,
        "expires_at": session.expires_at.isoformat(),
        "last_seen_at": session.last_seen_at.isoformat() if session.last_seen_at else None,
    }


def auth_session_response(authenticated: AuthenticatedSession) -> dict[str, Any]:
    return {
        "identity_type": authenticated.identity_type,
        "user": _public_user(authenticated.user),
        "session": _public_session(authenticated.session),
        "service_account": _public_service_account(authenticated.service_account),
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
        "identity_type": authenticated.identity_type,
        "service_account": _service_account_payload(authenticated.service_account),
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
        identity_type=payload.get("identity_type", "user"),
        service_account=_service_account_from_payload(payload.get("service_account")),
    )


def _service_account_payload(
    account: ServiceAccountRecord | None,
) -> dict[str, Any] | None:
    if account is None:
        return None
    return {
        "account_id": account.account_id,
        "user_id": account.user_id,
        "organization_id": account.organization_id,
        "slug": account.slug,
        "display_name": account.display_name,
        "role_key": account.role_key,
        "status": account.status,
        "created_by_user_id": account.created_by_user_id,
        "created_at": account.created_at.isoformat(),
        "updated_at": account.updated_at.isoformat(),
        "last_used_at": account.last_used_at.isoformat()
        if account.last_used_at
        else None,
    }


def _service_account_from_payload(payload: dict[str, Any] | None) -> ServiceAccountRecord | None:
    if not payload:
        return None
    return ServiceAccountRecord(
        account_id=payload["account_id"],
        user_id=payload["user_id"],
        organization_id=payload["organization_id"],
        slug=payload["slug"],
        display_name=payload["display_name"],
        role_key=payload["role_key"],
        status=payload["status"],
        created_by_user_id=payload["created_by_user_id"],
        created_at=_parse_datetime(payload["created_at"]),
        updated_at=_parse_datetime(payload["updated_at"]),
        last_used_at=_parse_optional_datetime(payload.get("last_used_at")),
    )


def _session_from_cache_payload(payload: dict[str, Any]) -> AuthenticatedSession | None:
    try:
        return _session_from_payload(payload)
    except (KeyError, TypeError, ValueError):
        return None


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _parse_optional_datetime(value: str | None) -> datetime | None:
    return _parse_datetime(value) if value else None


def _normalize_service_account_slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not normalized:
        raise OJTFlowError("Service account slug is required.")
    return normalized


def _service_account_email(slug: str, account_id: str) -> str:
    return f"{slug}.{account_id}@service-account.ojtflow.local"
