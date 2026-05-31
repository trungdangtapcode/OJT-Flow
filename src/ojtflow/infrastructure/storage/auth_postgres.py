"""PostgreSQL storage for Google OAuth users and backend sessions."""

from __future__ import annotations

from datetime import datetime

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover
    psycopg = None
    dict_row = None

from ojtflow.core.contracts.auth import (
    AuthenticatedSession,
    GoogleIdentityProfile,
    SessionRecord,
    UserRecord,
)
from ojtflow.core.errors import OJTFlowError
from ojtflow.core.ids import new_id
from ojtflow.infrastructure.storage.migrations import PostgresMigrator


class PostgresAuthRepository:
    """Stores app users and hashed session tokens in Postgres."""

    def __init__(self, dsn: str) -> None:
        if psycopg is None:
            raise OJTFlowError(
                "Auth storage requires psycopg. Install project dependencies first."
            )
        self.dsn = dsn
        self._schema_initialized = False

    def connect(self):
        self._ensure_schema()
        return psycopg.connect(self.dsn, row_factory=dict_row)

    def _ensure_schema(self) -> None:
        if self._schema_initialized:
            return
        PostgresMigrator(self.dsn).apply()
        self._schema_initialized = True

    def upsert_google_user(self, profile: GoogleIdentityProfile) -> UserRecord:
        """Create or update a user by stable Google subject."""

        user_id = new_id("usr")
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into ojtflow.users (
                        user_id, google_sub, email, email_verified,
                        display_name, avatar_url, last_login_at
                    ) values (%s, %s, %s, %s, %s, %s, now())
                    on conflict (google_sub) do update set
                        email = excluded.email,
                        email_verified = excluded.email_verified,
                        display_name = excluded.display_name,
                        avatar_url = excluded.avatar_url,
                        updated_at = now(),
                        last_login_at = now()
                    returning
                        user_id, google_sub, email, email_verified,
                        display_name, avatar_url, created_at, updated_at, last_login_at
                    """,
                    (
                        user_id,
                        profile.google_sub,
                        profile.email,
                        profile.email_verified,
                        profile.display_name,
                        profile.avatar_url,
                    ),
                )
                row = cursor.fetchone()
            connection.commit()
        return _user_from_row(row)

    def create_session(
        self,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> SessionRecord:
        """Create an active session for a hashed backend token."""

        session_id = new_id("ses")
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into ojtflow.sessions (
                        session_id, user_id, token_hash, expires_at,
                        user_agent, ip_address, last_seen_at
                    ) values (%s, %s, %s, %s::timestamptz, %s, %s::inet, now())
                    returning
                        session_id, user_id, token_hash, created_at,
                        expires_at, revoked_at, last_seen_at
                    """,
                    (session_id, user_id, token_hash, expires_at, user_agent, ip_address),
                )
                row = cursor.fetchone()
            connection.commit()
        return _session_from_row(row)

    def get_active_session(self, token_hash: str, now: datetime) -> AuthenticatedSession | None:
        """Return the user/session pair if the token is active."""

        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select
                        u.user_id, u.google_sub, u.email, u.email_verified,
                        u.display_name, u.avatar_url, u.created_at as user_created_at,
                        u.updated_at as user_updated_at, u.last_login_at,
                        s.session_id, s.token_hash, s.created_at as session_created_at,
                        s.expires_at, s.revoked_at, s.last_seen_at
                    from ojtflow.sessions s
                    join ojtflow.users u on u.user_id = s.user_id
                    where s.token_hash = %s
                      and s.revoked_at is null
                      and s.expires_at > %s::timestamptz
                    """,
                    (token_hash, now),
                )
                row = cursor.fetchone()
        if not row:
            return None
        return AuthenticatedSession(
            user=_joined_user_from_row(row),
            session=_joined_session_from_row(row),
        )

    def touch_session(self, token_hash: str) -> None:
        """Record recent token use for operational visibility."""

        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    update ojtflow.sessions
                    set last_seen_at = now()
                    where token_hash = %s
                      and revoked_at is null
                    """,
                    (token_hash,),
                )
            connection.commit()

    def revoke_session(self, token_hash: str) -> None:
        """Revoke a session token."""

        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    update ojtflow.sessions
                    set revoked_at = now(), last_seen_at = now()
                    where token_hash = %s
                      and revoked_at is null
                    """,
                    (token_hash,),
                )
            connection.commit()


def _user_from_row(row) -> UserRecord:
    return UserRecord(
        user_id=row["user_id"],
        google_sub=row["google_sub"],
        email=row["email"],
        email_verified=row["email_verified"],
        display_name=row["display_name"],
        avatar_url=row["avatar_url"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        last_login_at=row["last_login_at"],
    )


def _session_from_row(row) -> SessionRecord:
    return SessionRecord(
        session_id=row["session_id"],
        user_id=row["user_id"],
        token_hash=row["token_hash"],
        created_at=row["created_at"],
        expires_at=row["expires_at"],
        revoked_at=row["revoked_at"],
        last_seen_at=row["last_seen_at"],
    )


def _joined_user_from_row(row) -> UserRecord:
    return UserRecord(
        user_id=row["user_id"],
        google_sub=row["google_sub"],
        email=row["email"],
        email_verified=row["email_verified"],
        display_name=row["display_name"],
        avatar_url=row["avatar_url"],
        created_at=row["user_created_at"],
        updated_at=row["user_updated_at"],
        last_login_at=row["last_login_at"],
    )


def _joined_session_from_row(row) -> SessionRecord:
    return SessionRecord(
        session_id=row["session_id"],
        user_id=row["user_id"],
        token_hash=row["token_hash"],
        created_at=row["session_created_at"],
        expires_at=row["expires_at"],
        revoked_at=row["revoked_at"],
        last_seen_at=row["last_seen_at"],
    )
