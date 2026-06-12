"""In-memory auth repository for tests and ephemeral local runs."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from threading import RLock

from ojtflow.core.contracts.auth import (
    AuthenticatedSession,
    GoogleIdentityProfile,
    ServiceAccountRecord,
    SessionRecord,
    UserRecord,
)
from ojtflow.core.errors import OJTFlowError
from ojtflow.core.ids import new_id


class InMemoryAuthRepository:
    """Stores OAuth users and hashed sessions in process memory."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._users_by_id: dict[str, UserRecord] = {}
        self._users_by_google_sub: dict[str, str] = {}
        self._sessions_by_hash: dict[str, SessionRecord] = {}
        self._service_accounts_by_id: dict[str, ServiceAccountRecord] = {}
        self._service_account_by_user_id: dict[str, str] = {}
        self._service_account_by_org_slug: dict[tuple[str, str], str] = {}

    def upsert_google_user(self, profile: GoogleIdentityProfile) -> UserRecord:
        now = _now()
        with self._lock:
            user_id = self._users_by_google_sub.get(profile.google_sub)
            if user_id:
                existing = self._users_by_id[user_id]
                user = replace(
                    existing,
                    email=profile.email,
                    email_verified=profile.email_verified,
                    display_name=profile.display_name,
                    avatar_url=profile.avatar_url,
                    updated_at=now,
                    last_login_at=now,
                )
            else:
                user = UserRecord(
                    user_id=new_id("usr"),
                    google_sub=profile.google_sub,
                    email=profile.email,
                    email_verified=profile.email_verified,
                    display_name=profile.display_name,
                    avatar_url=profile.avatar_url,
                    created_at=now,
                    updated_at=now,
                    last_login_at=now,
                )
                self._users_by_google_sub[profile.google_sub] = user.user_id
            self._users_by_id[user.user_id] = user
            return user

    def create_service_account(
        self,
        *,
        account_id: str,
        organization_id: str,
        slug: str,
        display_name: str,
        role_key: str,
        created_by_user_id: str,
    ) -> ServiceAccountRecord:
        now = _now()
        key = (organization_id, slug)
        with self._lock:
            if key in self._service_account_by_org_slug:
                raise OJTFlowError(
                    "Service account slug already exists in organization.",
                    details={"organization_id": organization_id, "slug": slug},
                )
            user = UserRecord(
                user_id=new_id("usr"),
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
            self._users_by_id[user.user_id] = user
            self._users_by_google_sub[user.google_sub] = user.user_id
            self._service_accounts_by_id[account.account_id] = account
            self._service_account_by_user_id[user.user_id] = account.account_id
            self._service_account_by_org_slug[key] = account.account_id
            return account

    def list_service_accounts(
        self,
        *,
        organization_id: str,
    ) -> list[ServiceAccountRecord]:
        with self._lock:
            return sorted(
                [
                    account
                    for account in self._service_accounts_by_id.values()
                    if account.organization_id == organization_id
                ],
                key=lambda account: (account.created_at, account.account_id),
            )

    def create_session(
        self,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> SessionRecord:
        del user_agent, ip_address
        now = _now()
        session = SessionRecord(
            session_id=new_id("ses"),
            user_id=user_id,
            token_hash=token_hash,
            created_at=now,
            expires_at=expires_at,
            revoked_at=None,
            last_seen_at=now,
        )
        with self._lock:
            self._sessions_by_hash[token_hash] = session
        return session

    def get_active_session(self, token_hash: str, now: datetime) -> AuthenticatedSession | None:
        with self._lock:
            session = self._sessions_by_hash.get(token_hash)
            if not session or session.revoked_at or session.expires_at <= now:
                return None
            user = self._users_by_id.get(session.user_id)
            if not user:
                return None
            service_account = self._service_account_for_user(user.user_id)
            if user.google_sub.startswith("service-account:"):
                if service_account is None or service_account.status != "active":
                    return None
                self._touch_service_account(service_account.account_id)
                service_account = self._service_accounts_by_id[service_account.account_id]
                return AuthenticatedSession(
                    user=user,
                    session=session,
                    identity_type="service_account",
                    service_account=service_account,
                )
            return AuthenticatedSession(user=user, session=session)

    def touch_session(self, token_hash: str) -> None:
        with self._lock:
            session = self._sessions_by_hash.get(token_hash)
            if session and not session.revoked_at:
                self._sessions_by_hash[token_hash] = replace(session, last_seen_at=_now())

    def revoke_session(self, token_hash: str) -> None:
        with self._lock:
            session = self._sessions_by_hash.get(token_hash)
            if session and not session.revoked_at:
                now = _now()
                self._sessions_by_hash[token_hash] = replace(
                    session,
                    revoked_at=now,
                    last_seen_at=now,
                )

    def _service_account_for_user(self, user_id: str) -> ServiceAccountRecord | None:
        account_id = self._service_account_by_user_id.get(user_id)
        if not account_id:
            return None
        return self._service_accounts_by_id.get(account_id)

    def _touch_service_account(self, account_id: str) -> None:
        account = self._service_accounts_by_id.get(account_id)
        if account:
            self._service_accounts_by_id[account_id] = replace(
                account,
                last_used_at=_now(),
            )


def _now() -> datetime:
    return datetime.now(timezone.utc)
