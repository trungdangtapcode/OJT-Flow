"""Postgres tenant/workspace governance repository."""

from __future__ import annotations

import json
from datetime import datetime

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover
    psycopg = None
    dict_row = None

from ojtflow.core.contracts.governance import (
    OrganizationGroupMembershipRecord,
    OrganizationGroupRecord,
    OrganizationInvitationRecord,
    OrganizationMembershipRecord,
    OrganizationRecord,
    WorkspaceDetail,
    WorkspaceSettingsRecord,
)
from ojtflow.core.errors import NotFoundError, OJTFlowError
from ojtflow.infrastructure.storage.postgres import PostgresBackboneStore


class PostgresGovernanceRepository:
    """Stores organization workspace primitives in Postgres."""

    def __init__(self, backbone: PostgresBackboneStore) -> None:
        if psycopg is None:
            raise OJTFlowError(
                "Postgres governance storage requires psycopg. Install dependencies first."
            )
        self.backbone = backbone

    def get_current_workspace(self, *, user_id: str) -> WorkspaceDetail | None:
        memberships = self._memberships_for_user(user_id)
        if not memberships:
            return None
        return self._workspace_for_membership(memberships[0])

    def list_workspaces(self, *, user_id: str) -> list[WorkspaceDetail]:
        return [
            self._workspace_for_membership(membership)
            for membership in self._memberships_for_user(user_id)
        ]

    def create_default_workspace(
        self,
        *,
        organization: OrganizationRecord,
        membership: OrganizationMembershipRecord,
        group: OrganizationGroupRecord,
        group_membership: OrganizationGroupMembershipRecord,
        settings: WorkspaceSettingsRecord,
    ) -> WorkspaceDetail:
        existing = self.get_current_workspace(user_id=membership.user_id)
        if existing:
            return existing
        return self._insert_workspace(
            organization=organization,
            membership=membership,
            group=group,
            group_membership=group_membership,
            settings=settings,
        )

    def create_workspace(
        self,
        *,
        organization: OrganizationRecord,
        membership: OrganizationMembershipRecord,
        group: OrganizationGroupRecord,
        group_membership: OrganizationGroupMembershipRecord,
        settings: WorkspaceSettingsRecord,
    ) -> WorkspaceDetail:
        return self._insert_workspace(
            organization=organization,
            membership=membership,
            group=group,
            group_membership=group_membership,
            settings=settings,
        )

    def _insert_workspace(
        self,
        *,
        organization: OrganizationRecord,
        membership: OrganizationMembershipRecord,
        group: OrganizationGroupRecord,
        group_membership: OrganizationGroupMembershipRecord,
        settings: WorkspaceSettingsRecord,
    ) -> WorkspaceDetail:
        with self.backbone.connect() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        insert into ojtflow.organizations (
                            organization_id, slug, display_name, status,
                            created_by_user_id, created_at, updated_at, attributes
                        ) values (
                            %s, %s, %s, %s, %s, %s::timestamptz, %s::timestamptz,
                            %s::jsonb
                        )
                        """,
                        (
                            organization.organization_id,
                            organization.slug,
                            organization.display_name,
                            organization.status,
                            organization.created_by_user_id,
                            organization.created_at,
                            organization.updated_at,
                            json.dumps(organization.attributes, sort_keys=True),
                        ),
                    )
                    cursor.execute(
                        """
                        insert into ojtflow.organization_memberships (
                            membership_id, organization_id, user_id, role_key,
                            status, created_at, updated_at
                        ) values (
                            %s, %s, %s, %s, %s, %s::timestamptz, %s::timestamptz
                        )
                        """,
                        (
                            membership.membership_id,
                            membership.organization_id,
                            membership.user_id,
                            membership.role_key,
                            membership.status,
                            membership.created_at,
                            membership.updated_at,
                        ),
                    )
                    self._insert_group(cursor, group)
                    cursor.execute(
                        """
                        insert into ojtflow.organization_group_memberships (
                            group_id, organization_id, user_id, created_at
                        ) values (%s, %s, %s, %s::timestamptz)
                        """,
                        (
                            group_membership.group_id,
                            group_membership.organization_id,
                            group_membership.user_id,
                            group_membership.created_at,
                        ),
                    )
                    cursor.execute(
                        """
                        insert into ojtflow.workspace_settings (
                            organization_id, settings_json, version,
                            updated_by_user_id, updated_at
                        ) values (%s, %s::jsonb, %s, %s, %s::timestamptz)
                        """,
                        (
                            settings.organization_id,
                            json.dumps(settings.settings, sort_keys=True),
                            settings.version,
                            settings.updated_by_user_id,
                            settings.updated_at,
                        ),
                    )
                connection.commit()
            except Exception as exc:
                connection.rollback()
                if "unique" in str(exc).lower():
                    raise OJTFlowError(
                        "Workspace slug already exists.",
                        details={"slug": organization.slug},
                    ) from exc
                raise
        return self._workspace_for_membership(membership)

    def update_workspace_settings(
        self,
        *,
        organization_id: str,
        user_id: str,
        settings: dict,
        updated_by_user_id: str,
    ) -> WorkspaceDetail:
        membership = self._membership_for_user_org(
            user_id=user_id,
            organization_id=organization_id,
        )
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    update ojtflow.workspace_settings
                    set settings_json = %s::jsonb,
                        version = version + 1,
                        updated_by_user_id = %s,
                        updated_at = now()
                    where organization_id = %s
                    returning organization_id
                    """,
                    (
                        json.dumps(settings, sort_keys=True),
                        updated_by_user_id,
                        organization_id,
                    ),
                )
                row = cursor.fetchone()
            connection.commit()
        if not row:
            raise NotFoundError("Workspace settings were not found.")
        return self._workspace_for_membership(membership)

    def create_group(
        self,
        *,
        organization_id: str,
        user_id: str,
        group: OrganizationGroupRecord,
    ) -> WorkspaceDetail:
        membership = self._membership_for_user_org(
            user_id=user_id,
            organization_id=organization_id,
        )
        with self.backbone.connect() as connection:
            try:
                with connection.cursor() as cursor:
                    self._insert_group(cursor, group)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                if "unique" in str(exc).lower():
                    raise OJTFlowError(
                        "Organization group slug already exists.",
                        details={
                            "organization_id": organization_id,
                            "slug": group.slug,
                        },
                    ) from exc
                raise
        return self._workspace_for_membership(membership)

    def add_membership(
        self,
        *,
        organization_id: str,
        actor_user_id: str,
        membership: OrganizationMembershipRecord,
    ) -> WorkspaceDetail:
        actor_membership = self._membership_for_user_org(
            user_id=actor_user_id,
            organization_id=organization_id,
        )
        with self.backbone.connect() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        insert into ojtflow.organization_memberships (
                            membership_id, organization_id, user_id, role_key,
                            status, created_at, updated_at
                        ) values (
                            %s, %s, %s, %s, %s, %s::timestamptz, %s::timestamptz
                        )
                        """,
                        (
                            membership.membership_id,
                            membership.organization_id,
                            membership.user_id,
                            membership.role_key,
                            membership.status,
                            membership.created_at,
                            membership.updated_at,
                        ),
                    )
                connection.commit()
            except Exception as exc:
                connection.rollback()
                if "unique" in str(exc).lower():
                    raise OJTFlowError(
                        "Organization membership already exists.",
                        details={
                            "organization_id": organization_id,
                            "user_id": membership.user_id,
                        },
                    ) from exc
                raise
        return self._workspace_for_membership(actor_membership)

    def create_invitation(
        self,
        *,
        invitation: OrganizationInvitationRecord,
    ) -> OrganizationInvitationRecord:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into ojtflow.organization_invitations (
                        invitation_id, organization_id, email, role_key, status,
                        token_hash, invited_by_user_id, created_at, expires_at,
                        accepted_at, accepted_by_user_id
                    ) values (
                        %s, %s, %s, %s, %s, %s, %s, %s::timestamptz, %s::timestamptz,
                        %s::timestamptz, %s
                    )
                    """,
                    (
                        invitation.invitation_id,
                        invitation.organization_id,
                        invitation.email,
                        invitation.role_key,
                        invitation.status,
                        invitation.token_hash,
                        invitation.invited_by_user_id,
                        invitation.created_at,
                        invitation.expires_at,
                        invitation.accepted_at,
                        invitation.accepted_by_user_id,
                    ),
                )
            connection.commit()
        return invitation

    def list_invitations(
        self,
        *,
        organization_id: str,
        status: str | None = None,
    ) -> list[OrganizationInvitationRecord]:
        clause = "where organization_id = %s"
        params: list = [organization_id]
        if status is not None:
            clause += " and status = %s"
            params.append(status)
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    select invitation_id, organization_id, email, role_key, status,
                           token_hash, invited_by_user_id, created_at, expires_at,
                           accepted_at, accepted_by_user_id
                    from ojtflow.organization_invitations
                    {clause}
                    order by created_at desc, invitation_id desc
                    """,
                    tuple(params),
                )
                rows = cursor.fetchall()
        return [_invitation_from_row(row) for row in rows]

    def get_invitation_by_token_hash(
        self,
        *,
        token_hash: str,
    ) -> OrganizationInvitationRecord | None:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select invitation_id, organization_id, email, role_key, status,
                           token_hash, invited_by_user_id, created_at, expires_at,
                           accepted_at, accepted_by_user_id
                    from ojtflow.organization_invitations
                    where token_hash = %s
                    """,
                    (token_hash,),
                )
                row = cursor.fetchone()
        return _invitation_from_row(row) if row else None

    def mark_invitation_accepted(
        self,
        *,
        invitation_id: str,
        accepted_by_user_id: str,
    ) -> OrganizationInvitationRecord:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    update ojtflow.organization_invitations
                    set status = 'accepted',
                        accepted_at = now(),
                        accepted_by_user_id = %s
                    where invitation_id = %s
                    returning invitation_id, organization_id, email, role_key, status,
                              token_hash, invited_by_user_id, created_at, expires_at,
                              accepted_at, accepted_by_user_id
                    """,
                    (accepted_by_user_id, invitation_id),
                )
                row = cursor.fetchone()
            connection.commit()
        if not row:
            raise NotFoundError(
                "Invitation was not found.",
                details={"invitation_id": invitation_id},
            )
        return _invitation_from_row(row)

    def revoke_invitation(
        self,
        *,
        organization_id: str,
        invitation_id: str,
    ) -> OrganizationInvitationRecord:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    update ojtflow.organization_invitations
                    set status = 'revoked'
                    where invitation_id = %s
                      and organization_id = %s
                      and status = 'pending'
                    returning invitation_id, organization_id, email, role_key, status,
                              token_hash, invited_by_user_id, created_at, expires_at,
                              accepted_at, accepted_by_user_id
                    """,
                    (invitation_id, organization_id),
                )
                row = cursor.fetchone()
            connection.commit()
        if not row:
            raise NotFoundError(
                "Pending invitation was not found.",
                details={
                    "organization_id": organization_id,
                    "invitation_id": invitation_id,
                },
            )
        return _invitation_from_row(row)

    def _memberships_for_user(self, user_id: str) -> list[OrganizationMembershipRecord]:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select membership_id, organization_id, user_id, role_key,
                           status, created_at, updated_at
                    from ojtflow.organization_memberships
                    where user_id = %s
                      and status = 'active'
                    order by created_at asc, membership_id asc
                    """,
                    (user_id,),
                )
                rows = cursor.fetchall()
        return [_membership_from_row(row) for row in rows]

    def _membership_for_user_org(
        self,
        *,
        user_id: str,
        organization_id: str,
    ) -> OrganizationMembershipRecord:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select membership_id, organization_id, user_id, role_key,
                           status, created_at, updated_at
                    from ojtflow.organization_memberships
                    where user_id = %s
                      and organization_id = %s
                      and status = 'active'
                    """,
                    (user_id, organization_id),
                )
                row = cursor.fetchone()
        if not row:
            raise NotFoundError(
                "Organization workspace was not found for the current user.",
                details={"organization_id": organization_id},
            )
        return _membership_from_row(row)

    def _workspace_for_membership(
        self,
        membership: OrganizationMembershipRecord,
    ) -> WorkspaceDetail:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select organization_id, slug, display_name, status,
                           created_by_user_id, created_at, updated_at, attributes
                    from ojtflow.organizations
                    where organization_id = %s
                    """,
                    (membership.organization_id,),
                )
                organization_row = cursor.fetchone()
                cursor.execute(
                    """
                    select organization_id, settings_json, version,
                           updated_by_user_id, updated_at
                    from ojtflow.workspace_settings
                    where organization_id = %s
                    """,
                    (membership.organization_id,),
                )
                settings_row = cursor.fetchone()
                cursor.execute(
                    """
                    select group_id, organization_id, slug, display_name,
                           description, role_keys, created_at, updated_at
                    from ojtflow.organization_groups
                    where organization_id = %s
                    order by slug asc, group_id asc
                    """,
                    (membership.organization_id,),
                )
                group_rows = cursor.fetchall()
                cursor.execute(
                    """
                    select group_id, organization_id, user_id, created_at
                    from ojtflow.organization_group_memberships
                    where organization_id = %s
                    order by group_id asc, user_id asc
                    """,
                    (membership.organization_id,),
                )
                group_membership_rows = cursor.fetchall()
        if not organization_row or not settings_row:
            raise NotFoundError("Workspace record is incomplete.")
        return WorkspaceDetail(
            organization=_organization_from_row(organization_row),
            membership=membership,
            groups=[_group_from_row(row) for row in group_rows],
            group_memberships=[
                _group_membership_from_row(row) for row in group_membership_rows
            ],
            settings=_settings_from_row(settings_row),
        )

    def _insert_group(self, cursor, group: OrganizationGroupRecord) -> None:
        cursor.execute(
            """
            insert into ojtflow.organization_groups (
                group_id, organization_id, slug, display_name, description,
                role_keys, created_at, updated_at
            ) values (
                %s, %s, %s, %s, %s, %s::jsonb, %s::timestamptz, %s::timestamptz
            )
            """,
            (
                group.group_id,
                group.organization_id,
                group.slug,
                group.display_name,
                group.description,
                json.dumps(group.role_keys, sort_keys=True),
                group.created_at,
                group.updated_at,
            ),
        )


def _organization_from_row(row) -> OrganizationRecord:
    return OrganizationRecord(
        organization_id=row["organization_id"],
        slug=row["slug"],
        display_name=row["display_name"],
        status=row["status"],
        created_by_user_id=row["created_by_user_id"],
        created_at=_iso(row["created_at"]),
        updated_at=_iso(row["updated_at"]),
        attributes=_jsonish(row["attributes"], default={}),
    )


def _membership_from_row(row) -> OrganizationMembershipRecord:
    return OrganizationMembershipRecord(
        membership_id=row["membership_id"],
        organization_id=row["organization_id"],
        user_id=row["user_id"],
        role_key=row["role_key"],
        status=row["status"],
        created_at=_iso(row["created_at"]),
        updated_at=_iso(row["updated_at"]),
    )


def _group_from_row(row) -> OrganizationGroupRecord:
    return OrganizationGroupRecord(
        group_id=row["group_id"],
        organization_id=row["organization_id"],
        slug=row["slug"],
        display_name=row["display_name"],
        description=row["description"] or "",
        role_keys=_jsonish(row["role_keys"], default=[]),
        created_at=_iso(row["created_at"]),
        updated_at=_iso(row["updated_at"]),
    )


def _group_membership_from_row(row) -> OrganizationGroupMembershipRecord:
    return OrganizationGroupMembershipRecord(
        group_id=row["group_id"],
        organization_id=row["organization_id"],
        user_id=row["user_id"],
        created_at=_iso(row["created_at"]),
    )


def _invitation_from_row(row) -> OrganizationInvitationRecord:
    return OrganizationInvitationRecord(
        invitation_id=row["invitation_id"],
        organization_id=row["organization_id"],
        email=row["email"],
        role_key=row["role_key"],
        status=row["status"],
        token_hash=row["token_hash"],
        invited_by_user_id=row["invited_by_user_id"],
        created_at=_iso(row["created_at"]),
        expires_at=_iso(row["expires_at"]),
        accepted_at=_iso(row["accepted_at"]) if row["accepted_at"] else None,
        accepted_by_user_id=row["accepted_by_user_id"],
    )


def _settings_from_row(row) -> WorkspaceSettingsRecord:
    return WorkspaceSettingsRecord(
        organization_id=row["organization_id"],
        settings=_jsonish(row["settings_json"], default={}),
        version=row["version"],
        updated_by_user_id=row["updated_by_user_id"],
        updated_at=_iso(row["updated_at"]),
    )


def _iso(value) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _jsonish(value, *, default):
    if value is None:
        return default
    if isinstance(value, str):
        return json.loads(value)
    return value
