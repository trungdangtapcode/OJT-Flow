"""SQLite storage for Google OAuth users and backend sessions."""

from __future__ import annotations

from datetime import datetime, timezone

from ojtflow.core.contracts.auth import (
    AuthenticatedSession,
    GoogleIdentityProfile,
    SessionRecord,
    UserRecord,
)
from ojtflow.core.ids import new_id
from ojtflow.infrastructure.storage.sqlite import SQLiteBackboneStore


class SQLiteAuthRepository:
    """Stores app users and hashed session tokens in the SQLite backbone."""

    def __init__(self, backbone: SQLiteBackboneStore) -> None:
        self.backbone = backbone
        self.init_schema()

    def init_schema(self) -> None:
        with self.backbone.connect() as connection:
            connection.executescript(
                """
                create table if not exists users (
                    user_id text primary key,
                    google_sub text not null unique,
                    email text not null unique,
                    email_verified integer not null default 0,
                    display_name text,
                    avatar_url text,
                    created_at text not null,
                    updated_at text not null,
                    last_login_at text
                );

                create index if not exists idx_users_email
                    on users(email);

                create table if not exists sessions (
                    session_id text primary key,
                    user_id text not null references users(user_id)
                        on delete cascade,
                    token_hash text not null unique,
                    created_at text not null,
                    expires_at text not null,
                    revoked_at text,
                    last_seen_at text,
                    user_agent text,
                    ip_address text,
                    check(length(token_hash) = 64)
                );

                create index if not exists idx_sessions_user_id
                    on sessions(user_id);

                create index if not exists idx_sessions_token_hash
                    on sessions(token_hash);

                create index if not exists idx_sessions_active_expires_at
                    on sessions(expires_at)
                    where revoked_at is null;
                """
            )

    def upsert_google_user(self, profile: GoogleIdentityProfile) -> UserRecord:
        user_id = new_id("usr")
        now = _now()
        with self.backbone.connect() as connection:
            row = connection.execute(
                """
                insert into users (
                    user_id, google_sub, email, email_verified,
                    display_name, avatar_url, created_at, updated_at, last_login_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(google_sub) do update set
                    email = excluded.email,
                    email_verified = excluded.email_verified,
                    display_name = excluded.display_name,
                    avatar_url = excluded.avatar_url,
                    updated_at = excluded.updated_at,
                    last_login_at = excluded.last_login_at
                returning
                    user_id, google_sub, email, email_verified,
                    display_name, avatar_url, created_at, updated_at, last_login_at
                """,
                (
                    user_id,
                    profile.google_sub,
                    profile.email,
                    int(profile.email_verified),
                    profile.display_name,
                    profile.avatar_url,
                    now.isoformat(),
                    now.isoformat(),
                    now.isoformat(),
                ),
            ).fetchone()
        return _user_from_row(row)

    def create_session(
        self,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> SessionRecord:
        session_id = new_id("ses")
        now = _now()
        with self.backbone.connect() as connection:
            row = connection.execute(
                """
                insert into sessions (
                    session_id, user_id, token_hash, created_at, expires_at,
                    user_agent, ip_address, last_seen_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?)
                returning
                    session_id, user_id, token_hash, created_at,
                    expires_at, revoked_at, last_seen_at
                """,
                (
                    session_id,
                    user_id,
                    token_hash,
                    now.isoformat(),
                    expires_at.isoformat(),
                    user_agent,
                    ip_address,
                    now.isoformat(),
                ),
            ).fetchone()
        return _session_from_row(row)

    def get_active_session(self, token_hash: str, now: datetime) -> AuthenticatedSession | None:
        with self.backbone.connect() as connection:
            row = connection.execute(
                """
                select
                    u.user_id, u.google_sub, u.email, u.email_verified,
                    u.display_name, u.avatar_url, u.created_at as user_created_at,
                    u.updated_at as user_updated_at, u.last_login_at,
                    s.session_id, s.token_hash, s.created_at as session_created_at,
                    s.expires_at, s.revoked_at, s.last_seen_at
                from sessions s
                join users u on u.user_id = s.user_id
                where s.token_hash = ?
                  and s.revoked_at is null
                """,
                (token_hash,),
            ).fetchone()
        if not row:
            return None
        session = _joined_session_from_row(row)
        if session.expires_at <= now:
            return None
        return AuthenticatedSession(
            user=_joined_user_from_row(row),
            session=session,
        )

    def touch_session(self, token_hash: str) -> None:
        with self.backbone.connect() as connection:
            connection.execute(
                """
                update sessions
                set last_seen_at = ?
                where token_hash = ?
                  and revoked_at is null
                """,
                (_now().isoformat(), token_hash),
            )

    def revoke_session(self, token_hash: str) -> None:
        now = _now().isoformat()
        with self.backbone.connect() as connection:
            connection.execute(
                """
                update sessions
                set revoked_at = ?, last_seen_at = ?
                where token_hash = ?
                  and revoked_at is null
                """,
                (now, now, token_hash),
            )


def _user_from_row(row) -> UserRecord:
    return UserRecord(
        user_id=row["user_id"],
        google_sub=row["google_sub"],
        email=row["email"],
        email_verified=bool(row["email_verified"]),
        display_name=row["display_name"],
        avatar_url=row["avatar_url"],
        created_at=_parse_datetime(row["created_at"]),
        updated_at=_parse_datetime(row["updated_at"]),
        last_login_at=_parse_optional_datetime(row["last_login_at"]),
    )


def _session_from_row(row) -> SessionRecord:
    return SessionRecord(
        session_id=row["session_id"],
        user_id=row["user_id"],
        token_hash=row["token_hash"],
        created_at=_parse_datetime(row["created_at"]),
        expires_at=_parse_datetime(row["expires_at"]),
        revoked_at=_parse_optional_datetime(row["revoked_at"]),
        last_seen_at=_parse_optional_datetime(row["last_seen_at"]),
    )


def _joined_user_from_row(row) -> UserRecord:
    return UserRecord(
        user_id=row["user_id"],
        google_sub=row["google_sub"],
        email=row["email"],
        email_verified=bool(row["email_verified"]),
        display_name=row["display_name"],
        avatar_url=row["avatar_url"],
        created_at=_parse_datetime(row["user_created_at"]),
        updated_at=_parse_datetime(row["user_updated_at"]),
        last_login_at=_parse_optional_datetime(row["last_login_at"]),
    )


def _joined_session_from_row(row) -> SessionRecord:
    return SessionRecord(
        session_id=row["session_id"],
        user_id=row["user_id"],
        token_hash=row["token_hash"],
        created_at=_parse_datetime(row["session_created_at"]),
        expires_at=_parse_datetime(row["expires_at"]),
        revoked_at=_parse_optional_datetime(row["revoked_at"]),
        last_seen_at=_parse_optional_datetime(row["last_seen_at"]),
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _parse_optional_datetime(value: str | None) -> datetime | None:
    return _parse_datetime(value) if value else None
