"""SQLite storage for Google OAuth users and backend sessions."""

from __future__ import annotations

from datetime import datetime, timezone

from ojtflow.core.contracts.auth import (
    AuthenticatedSession,
    GoogleIdentityProfile,
    ServiceAccountRecord,
    SessionRecord,
    UserRecord,
)
from ojtflow.core.errors import OJTFlowError
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

                create table if not exists service_accounts (
                    account_id text primary key,
                    user_id text not null unique references users(user_id)
                        on delete cascade,
                    organization_id text not null,
                    slug text not null,
                    display_name text not null,
                    role_key text not null,
                    status text not null default 'active'
                        check(status in ('active', 'disabled')),
                    created_by_user_id text not null references users(user_id),
                    created_at text not null,
                    updated_at text not null,
                    last_used_at text,
                    unique(organization_id, slug)
                );

                create index if not exists idx_service_accounts_org_status
                    on service_accounts(organization_id, status, created_at);
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
        user_id = new_id("usr")
        now = _now()
        email = f"{slug}.{account_id}@service-account.ojtflow.local"
        with self.backbone.connect() as connection:
            try:
                row = connection.execute(
                    """
                    insert into users (
                        user_id, google_sub, email, email_verified,
                        display_name, avatar_url, created_at, updated_at, last_login_at
                    ) values (?, ?, ?, 1, ?, null, ?, ?, null)
                    returning
                        user_id, google_sub, email, email_verified,
                        display_name, avatar_url, created_at, updated_at, last_login_at
                    """,
                    (
                        user_id,
                        f"service-account:{account_id}",
                        email,
                        display_name,
                        now.isoformat(),
                        now.isoformat(),
                    ),
                ).fetchone()
                connection.execute(
                    """
                    insert into service_accounts (
                        account_id, user_id, organization_id, slug, display_name,
                        role_key, status, created_by_user_id, created_at, updated_at
                    ) values (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
                    """,
                    (
                        account_id,
                        row["user_id"],
                        organization_id,
                        slug,
                        display_name,
                        role_key,
                        created_by_user_id,
                        now.isoformat(),
                        now.isoformat(),
                    ),
                )
            except Exception as exc:
                if "unique" in str(exc).lower():
                    raise OJTFlowError(
                        "Service account slug already exists in organization.",
                        details={"organization_id": organization_id, "slug": slug},
                    ) from exc
                raise
        return ServiceAccountRecord(
            account_id=account_id,
            user_id=row["user_id"],
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

    def list_service_accounts(
        self,
        *,
        organization_id: str,
    ) -> list[ServiceAccountRecord]:
        with self.backbone.connect() as connection:
            rows = connection.execute(
                """
                select account_id, user_id, organization_id, slug, display_name,
                       role_key, status, created_by_user_id, created_at, updated_at,
                       last_used_at
                from service_accounts
                where organization_id = ?
                order by created_at asc, account_id asc
                """,
                (organization_id,),
            ).fetchall()
        return [_service_account_from_row(row) for row in rows]

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
                    s.expires_at, s.revoked_at, s.last_seen_at,
                    sa.account_id, sa.organization_id, sa.slug,
                    sa.display_name as service_account_display_name,
                    sa.role_key, sa.status as service_account_status,
                    sa.created_by_user_id,
                    sa.created_at as service_account_created_at,
                    sa.updated_at as service_account_updated_at,
                    sa.last_used_at
                from sessions s
                join users u on u.user_id = s.user_id
                left join service_accounts sa on sa.user_id = u.user_id
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
        service_account = _joined_service_account_from_row(row)
        if row["google_sub"].startswith("service-account:"):
            if service_account is None or service_account.status != "active":
                return None
            self._touch_service_account(service_account.account_id)
            service_account = self._service_account_by_id(service_account.account_id)
            if service_account is None:
                return None
            return AuthenticatedSession(
                user=_joined_user_from_row(row),
                session=session,
                identity_type="service_account",
                service_account=service_account,
            )
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

    def _touch_service_account(self, account_id: str) -> None:
        with self.backbone.connect() as connection:
            connection.execute(
                """
                update service_accounts
                set last_used_at = ?, updated_at = updated_at
                where account_id = ?
                """,
                (_now().isoformat(), account_id),
            )

    def _service_account_by_id(self, account_id: str) -> ServiceAccountRecord | None:
        with self.backbone.connect() as connection:
            row = connection.execute(
                """
                select account_id, user_id, organization_id, slug, display_name,
                       role_key, status, created_by_user_id, created_at, updated_at,
                       last_used_at
                from service_accounts
                where account_id = ?
                """,
                (account_id,),
            ).fetchone()
        return _service_account_from_row(row) if row else None


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


def _service_account_from_row(row) -> ServiceAccountRecord:
    return ServiceAccountRecord(
        account_id=row["account_id"],
        user_id=row["user_id"],
        organization_id=row["organization_id"],
        slug=row["slug"],
        display_name=row["display_name"],
        role_key=row["role_key"],
        status=row["status"],
        created_by_user_id=row["created_by_user_id"],
        created_at=_parse_datetime(row["created_at"]),
        updated_at=_parse_datetime(row["updated_at"]),
        last_used_at=_parse_optional_datetime(row["last_used_at"]),
    )


def _joined_service_account_from_row(row) -> ServiceAccountRecord | None:
    if row["account_id"] is None:
        return None
    return ServiceAccountRecord(
        account_id=row["account_id"],
        user_id=row["user_id"],
        organization_id=row["organization_id"],
        slug=row["slug"],
        display_name=row["service_account_display_name"],
        role_key=row["role_key"],
        status=row["service_account_status"],
        created_by_user_id=row["created_by_user_id"],
        created_at=_parse_datetime(row["service_account_created_at"]),
        updated_at=_parse_datetime(row["service_account_updated_at"]),
        last_used_at=_parse_optional_datetime(row["last_used_at"]),
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _parse_optional_datetime(value: str | None) -> datetime | None:
    return _parse_datetime(value) if value else None
