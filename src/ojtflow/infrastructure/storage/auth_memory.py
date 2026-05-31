"""In-memory auth repository for tests and ephemeral local runs."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from threading import RLock

from ojtflow.core.contracts.auth import (
    AuthenticatedSession,
    GoogleIdentityProfile,
    SessionRecord,
    UserRecord,
)
from ojtflow.core.ids import new_id


class InMemoryAuthRepository:
    """Stores OAuth users and hashed sessions in process memory."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._users_by_id: dict[str, UserRecord] = {}
        self._users_by_google_sub: dict[str, str] = {}
        self._sessions_by_hash: dict[str, SessionRecord] = {}

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


def _now() -> datetime:
    return datetime.now(timezone.utc)
