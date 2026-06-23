"""Authentication contract records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


IdentityType = Literal["user", "service_account"]
ServiceAccountStatus = Literal["active", "disabled"]


@dataclass(frozen=True)
class GoogleIdentityProfile:
    """Identity claims returned after OIDC verification (Google or Keycloak)."""

    google_sub: str
    email: str
    email_verified: bool
    display_name: str | None = None
    avatar_url: str | None = None
    hosted_domain: str | None = None
    identity_provider: str | None = None


@dataclass(frozen=True)
class UserRecord:
    """Persisted application user."""

    user_id: str
    google_sub: str
    email: str
    email_verified: bool
    display_name: str | None
    avatar_url: str | None
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None
    identity_provider: str | None = None


@dataclass(frozen=True)
class SessionRecord:
    """Persisted backend session."""

    session_id: str
    user_id: str
    token_hash: str
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    last_seen_at: datetime | None


@dataclass(frozen=True)
class ServiceAccountRecord:
    """Automation identity owned by an organization workspace."""

    account_id: str
    user_id: str
    organization_id: str
    slug: str
    display_name: str
    role_key: str
    status: ServiceAccountStatus
    created_by_user_id: str
    created_at: datetime
    updated_at: datetime
    last_used_at: datetime | None


@dataclass(frozen=True)
class AuthenticatedSession:
    """Resolved active session with user details."""

    user: UserRecord
    session: SessionRecord
    identity_type: IdentityType = "user"
    service_account: ServiceAccountRecord | None = None
