"""SQLite tenant/workspace governance repository."""

from __future__ import annotations

import json

from ojtflow.core.contracts.governance import (
    OrganizationGroupMembershipRecord,
    OrganizationGroupRecord,
    OrganizationMembershipRecord,
    OrganizationRecord,
    WorkspaceDetail,
    WorkspaceSettingsRecord,
)
from ojtflow.core.errors import NotFoundError, OJTFlowError
from ojtflow.core.time import utc_now
from ojtflow.infrastructure.storage.sqlite import SQLiteBackboneStore


class SQLiteGovernanceRepository:
    """Stores organization workspace primitives in SQLite."""

    def __init__(self, backbone: SQLiteBackboneStore) -> None:
        self.backbone = backbone
        self.init_schema()

    def init_schema(self) -> None:
        with self.backbone.connect() as connection:
            connection.executescript(
                """
                create table if not exists organizations (
                    organization_id text primary key,
                    slug text not null unique,
                    display_name text not null,
                    status text not null default 'active'
                        check(status in ('active', 'disabled')),
                    created_by_user_id text not null references users(user_id),
                    created_at text not null,
                    updated_at text not null,
                    attributes_json text not null default '{}'
                );

                create table if not exists organization_memberships (
                    membership_id text primary key,
                    organization_id text not null references organizations(organization_id)
                        on delete cascade,
                    user_id text not null references users(user_id)
                        on delete cascade,
                    role_key text not null,
                    status text not null default 'active'
                        check(status in ('active', 'disabled', 'invited')),
                    created_at text not null,
                    updated_at text not null,
                    unique(organization_id, user_id)
                );

                create index if not exists idx_org_memberships_user_status
                    on organization_memberships(user_id, status, created_at);

                create table if not exists organization_groups (
                    group_id text primary key,
                    organization_id text not null references organizations(organization_id)
                        on delete cascade,
                    slug text not null,
                    display_name text not null,
                    description text not null default '',
                    role_keys_json text not null default '[]',
                    created_at text not null,
                    updated_at text not null,
                    unique(organization_id, slug)
                );

                create index if not exists idx_org_groups_org_slug
                    on organization_groups(organization_id, slug);

                create table if not exists organization_group_memberships (
                    group_id text not null references organization_groups(group_id)
                        on delete cascade,
                    organization_id text not null references organizations(organization_id)
                        on delete cascade,
                    user_id text not null references users(user_id)
                        on delete cascade,
                    created_at text not null,
                    primary key(group_id, user_id)
                );

                create index if not exists idx_org_group_memberships_org_user
                    on organization_group_memberships(organization_id, user_id);

                create table if not exists workspace_settings (
                    organization_id text primary key references organizations(organization_id)
                        on delete cascade,
                    settings_json text not null default '{}',
                    version integer not null default 1 check(version >= 1),
                    updated_by_user_id text references users(user_id),
                    updated_at text not null
                );
                """
            )

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
        with self.backbone.connect() as connection:
            connection.execute(
                """
                insert into organizations (
                    organization_id, slug, display_name, status, created_by_user_id,
                    created_at, updated_at, attributes_json
                ) values (?, ?, ?, ?, ?, ?, ?, ?)
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
            connection.execute(
                """
                insert into organization_memberships (
                    membership_id, organization_id, user_id, role_key,
                    status, created_at, updated_at
                ) values (?, ?, ?, ?, ?, ?, ?)
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
            self._insert_group(connection, group)
            connection.execute(
                """
                insert into organization_group_memberships (
                    group_id, organization_id, user_id, created_at
                ) values (?, ?, ?, ?)
                """,
                (
                    group_membership.group_id,
                    group_membership.organization_id,
                    group_membership.user_id,
                    group_membership.created_at,
                ),
            )
            connection.execute(
                """
                insert into workspace_settings (
                    organization_id, settings_json, version,
                    updated_by_user_id, updated_at
                ) values (?, ?, ?, ?, ?)
                """,
                (
                    settings.organization_id,
                    json.dumps(settings.settings, sort_keys=True),
                    settings.version,
                    settings.updated_by_user_id,
                    settings.updated_at,
                ),
            )
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
            row = connection.execute(
                """
                update workspace_settings
                set settings_json = ?,
                    version = version + 1,
                    updated_by_user_id = ?,
                    updated_at = ?
                where organization_id = ?
                returning organization_id
                """,
                (
                    json.dumps(settings, sort_keys=True),
                    updated_by_user_id,
                    utc_now().isoformat(),
                    organization_id,
                ),
            ).fetchone()
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
                self._insert_group(connection, group)
            except Exception as exc:
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
                connection.execute(
                    """
                    insert into organization_memberships (
                        membership_id, organization_id, user_id, role_key,
                        status, created_at, updated_at
                    ) values (?, ?, ?, ?, ?, ?, ?)
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
            except Exception as exc:
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

    def _memberships_for_user(self, user_id: str) -> list[OrganizationMembershipRecord]:
        with self.backbone.connect() as connection:
            rows = connection.execute(
                """
                select membership_id, organization_id, user_id, role_key,
                       status, created_at, updated_at
                from organization_memberships
                where user_id = ?
                  and status = 'active'
                order by created_at asc, membership_id asc
                """,
                (user_id,),
            ).fetchall()
        return [_membership_from_row(row) for row in rows]

    def _membership_for_user_org(
        self,
        *,
        user_id: str,
        organization_id: str,
    ) -> OrganizationMembershipRecord:
        with self.backbone.connect() as connection:
            row = connection.execute(
                """
                select membership_id, organization_id, user_id, role_key,
                       status, created_at, updated_at
                from organization_memberships
                where user_id = ?
                  and organization_id = ?
                  and status = 'active'
                """,
                (user_id, organization_id),
            ).fetchone()
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
            organization_row = connection.execute(
                """
                select organization_id, slug, display_name, status,
                       created_by_user_id, created_at, updated_at, attributes_json
                from organizations
                where organization_id = ?
                """,
                (membership.organization_id,),
            ).fetchone()
            settings_row = connection.execute(
                """
                select organization_id, settings_json, version,
                       updated_by_user_id, updated_at
                from workspace_settings
                where organization_id = ?
                """,
                (membership.organization_id,),
            ).fetchone()
            group_rows = connection.execute(
                """
                select group_id, organization_id, slug, display_name, description,
                       role_keys_json, created_at, updated_at
                from organization_groups
                where organization_id = ?
                order by slug asc, group_id asc
                """,
                (membership.organization_id,),
            ).fetchall()
            group_membership_rows = connection.execute(
                """
                select group_id, organization_id, user_id, created_at
                from organization_group_memberships
                where organization_id = ?
                order by group_id asc, user_id asc
                """,
                (membership.organization_id,),
            ).fetchall()
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

    def _insert_group(self, connection, group: OrganizationGroupRecord) -> None:
        connection.execute(
            """
            insert into organization_groups (
                group_id, organization_id, slug, display_name, description,
                role_keys_json, created_at, updated_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?)
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
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        attributes=json.loads(row["attributes_json"] or "{}"),
    )


def _membership_from_row(row) -> OrganizationMembershipRecord:
    return OrganizationMembershipRecord(
        membership_id=row["membership_id"],
        organization_id=row["organization_id"],
        user_id=row["user_id"],
        role_key=row["role_key"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _group_from_row(row) -> OrganizationGroupRecord:
    return OrganizationGroupRecord(
        group_id=row["group_id"],
        organization_id=row["organization_id"],
        slug=row["slug"],
        display_name=row["display_name"],
        description=row["description"] or "",
        role_keys=json.loads(row["role_keys_json"] or "[]"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _group_membership_from_row(row) -> OrganizationGroupMembershipRecord:
    return OrganizationGroupMembershipRecord(
        group_id=row["group_id"],
        organization_id=row["organization_id"],
        user_id=row["user_id"],
        created_at=row["created_at"],
    )


def _settings_from_row(row) -> WorkspaceSettingsRecord:
    return WorkspaceSettingsRecord(
        organization_id=row["organization_id"],
        settings=json.loads(row["settings_json"] or "{}"),
        version=row["version"],
        updated_by_user_id=row["updated_by_user_id"],
        updated_at=row["updated_at"],
    )
