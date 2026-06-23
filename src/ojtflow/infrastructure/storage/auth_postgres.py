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
    ServiceAccountRecord,
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
        """Create or update a user, keyed by external subject and linked by email.

        Matches an existing account by the stable external subject first, then by
        email (so an account created via a different provider — e.g. legacy direct
        Google before Keycloak brokering — is re-linked to the new subject instead
        of colliding on the unique email constraint), and finally inserts.
        """

        returning = (
            "user_id, google_sub, email, email_verified, display_name, avatar_url, "
            "identity_provider, created_at, updated_at, last_login_at"
        )
        with self.connect() as connection:
            with connection.cursor() as cursor:
                # 1) Existing account by external subject.
                cursor.execute(
                    f"""
                    update ojtflow.users set
                        email = %s, email_verified = %s, display_name = %s,
                        avatar_url = %s,
                        identity_provider = coalesce(%s, identity_provider),
                        updated_at = now(), last_login_at = now()
                    where google_sub = %s
                    returning {returning}
                    """,
                    (
                        profile.email,
                        profile.email_verified,
                        profile.display_name,
                        profile.avatar_url,
                        profile.identity_provider,
                        profile.google_sub,
                    ),
                )
                row = cursor.fetchone()
                if row is None:
                    # 2) Existing account by email: re-link to the new subject.
                    cursor.execute(
                        f"""
                        update ojtflow.users set
                            google_sub = %s, email_verified = %s, display_name = %s,
                            avatar_url = %s,
                            identity_provider = coalesce(%s, identity_provider),
                            updated_at = now(), last_login_at = now()
                        where email = %s
                        returning {returning}
                        """,
                        (
                            profile.google_sub,
                            profile.email_verified,
                            profile.display_name,
                            profile.avatar_url,
                            profile.identity_provider,
                            profile.email,
                        ),
                    )
                    row = cursor.fetchone()
                if row is None:
                    # 3) New account.
                    cursor.execute(
                        f"""
                        insert into ojtflow.users (
                            user_id, google_sub, email, email_verified,
                            display_name, avatar_url, identity_provider, last_login_at
                        ) values (%s, %s, %s, %s, %s, %s, %s, now())
                        returning {returning}
                        """,
                        (
                            new_id("usr"),
                            profile.google_sub,
                            profile.email,
                            profile.email_verified,
                            profile.display_name,
                            profile.avatar_url,
                            profile.identity_provider,
                        ),
                    )
                    row = cursor.fetchone()
            connection.commit()
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
        """Create a service-account user and organization identity record."""

        user_id = new_id("usr")
        email = f"{slug}.{account_id}@service-account.ojtflow.local"
        with self.connect() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        insert into ojtflow.users (
                            user_id, google_sub, email, email_verified,
                            display_name, avatar_url, last_login_at
                        ) values (%s, %s, %s, true, %s, null, null)
                        returning
                            user_id, google_sub, email, email_verified,
                            display_name, avatar_url, created_at, updated_at, last_login_at
                        """,
                        (
                            user_id,
                            f"service-account:{account_id}",
                            email,
                            display_name,
                        ),
                    )
                    user_row = cursor.fetchone()
                    cursor.execute(
                        """
                        insert into ojtflow.service_accounts (
                            account_id, user_id, organization_id, slug, display_name,
                            role_key, status, created_by_user_id
                        ) values (%s, %s, %s, %s, %s, %s, 'active', %s)
                        returning
                            account_id, user_id, organization_id, slug, display_name,
                            role_key, status, created_by_user_id, created_at, updated_at,
                            last_used_at
                        """,
                        (
                            account_id,
                            user_row["user_id"],
                            organization_id,
                            slug,
                            display_name,
                            role_key,
                            created_by_user_id,
                        ),
                    )
                    row = cursor.fetchone()
                connection.commit()
            except Exception as exc:
                connection.rollback()
                if "unique" in str(exc).lower():
                    raise OJTFlowError(
                        "Service account slug already exists in organization.",
                        details={"organization_id": organization_id, "slug": slug},
                    ) from exc
                raise
        return _service_account_from_row(row)

    def list_service_accounts(
        self,
        *,
        organization_id: str,
    ) -> list[ServiceAccountRecord]:
        """List service accounts for an organization."""

        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select
                        account_id, user_id, organization_id, slug, display_name,
                        role_key, status, created_by_user_id, created_at, updated_at,
                        last_used_at
                    from ojtflow.service_accounts
                    where organization_id = %s
                    order by created_at asc, account_id asc
                    """,
                    (organization_id,),
                )
                rows = cursor.fetchall()
        return [_service_account_from_row(row) for row in rows]

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
                        u.display_name, u.avatar_url, u.identity_provider,
                        u.created_at as user_created_at,
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
                    from ojtflow.sessions s
                    join ojtflow.users u on u.user_id = s.user_id
                    left join ojtflow.service_accounts sa on sa.user_id = u.user_id
                    where s.token_hash = %s
                      and s.revoked_at is null
                      and s.expires_at > %s::timestamptz
                    """,
                    (token_hash, now),
                )
                row = cursor.fetchone()
        if not row:
            return None
        session = _joined_session_from_row(row)
        service_account = _joined_service_account_from_row(row)
        if row["google_sub"].startswith("service-account:"):
            if service_account is None or service_account.status != "active":
                return None
            service_account = self._touch_and_get_service_account(
                service_account.account_id
            )
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

    def _touch_and_get_service_account(self, account_id: str) -> ServiceAccountRecord | None:
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    update ojtflow.service_accounts
                    set last_used_at = now()
                    where account_id = %s
                    returning
                        account_id, user_id, organization_id, slug, display_name,
                        role_key, status, created_by_user_id, created_at, updated_at,
                        last_used_at
                    """,
                    (account_id,),
                )
                row = cursor.fetchone()
            connection.commit()
        return _service_account_from_row(row) if row else None

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
        identity_provider=row.get("identity_provider"),
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
        identity_provider=row.get("identity_provider"),
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
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        last_used_at=row["last_used_at"],
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
        created_at=row["service_account_created_at"],
        updated_at=row["service_account_updated_at"],
        last_used_at=row["last_used_at"],
    )
