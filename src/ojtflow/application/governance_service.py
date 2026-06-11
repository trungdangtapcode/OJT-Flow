"""Tenant organization and workspace orchestration."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from ojtflow.application.ports import GovernanceRepository
from ojtflow.core.contracts.auth import UserRecord
from ojtflow.core.contracts.governance import (
    OrganizationGroupMembershipRecord,
    OrganizationGroupRecord,
    OrganizationMembershipRecord,
    OrganizationRecord,
    RbacPolicy,
    RbacRoleDefinition,
    WorkspaceDefaultGroup,
    WorkspaceDefaults,
    WorkspaceDetail,
    WorkspaceSettingsRecord,
)
from ojtflow.core.errors import NotFoundError
from ojtflow.core.ids import new_id
from ojtflow.core.time import utc_now


class GovernanceService:
    """Manage organization workspace primitives for authenticated users."""

    def __init__(
        self,
        repository: GovernanceRepository,
        *,
        defaults: WorkspaceDefaults,
        rbac_policy: RbacPolicy,
    ) -> None:
        self.repository = repository
        self.defaults = defaults
        self.rbac_policy = rbac_policy
        self._roles_by_key = {role.role_key: role for role in rbac_policy.roles}
        _validate_configured_roles(
            [
                defaults.default_role_key,
                *defaults.default_group.role_keys,
            ],
            roles_by_key=self._roles_by_key,
        )

    def role_policy(self) -> RbacPolicy:
        """Return the active role-based access-control catalog."""

        return self.rbac_policy

    def get_or_create_current_workspace(self, user: UserRecord) -> WorkspaceDetail:
        """Return the user's current workspace, creating a default one if needed."""

        existing = self.repository.get_current_workspace(user_id=user.user_id)
        if existing:
            return self._with_effective_permissions(existing, user_id=user.user_id)

        now = utc_now().isoformat()
        organization = OrganizationRecord(
            organization_id=new_id("org"),
            slug=_workspace_slug(user),
            display_name=_workspace_display_name(user),
            created_by_user_id=user.user_id,
            created_at=now,
            updated_at=now,
            attributes={"defaults_version": self.defaults.version},
        )
        membership = OrganizationMembershipRecord(
            membership_id=new_id("mem"),
            organization_id=organization.organization_id,
            user_id=user.user_id,
            role_key=self.defaults.default_role_key,
            created_at=now,
            updated_at=now,
        )
        group = _group_record(
            organization_id=organization.organization_id,
            default_group=self.defaults.default_group,
            now=now,
        )
        group_membership = OrganizationGroupMembershipRecord(
            group_id=group.group_id,
            organization_id=organization.organization_id,
            user_id=user.user_id,
            created_at=now,
        )
        settings = WorkspaceSettingsRecord(
            organization_id=organization.organization_id,
            settings=deepcopy(self.defaults.settings),
            version=1,
            updated_by_user_id=user.user_id,
            updated_at=now,
        )
        workspace = self.repository.create_default_workspace(
            organization=organization,
            membership=membership,
            group=group,
            group_membership=group_membership,
            settings=settings,
        )
        return self._with_effective_permissions(workspace, user_id=user.user_id)

    def list_workspaces(self, user: UserRecord) -> list[WorkspaceDetail]:
        """List workspaces visible to a user, bootstrapping the default if absent."""

        workspaces = self.repository.list_workspaces(user_id=user.user_id)
        if workspaces:
            return [
                self._with_effective_permissions(workspace, user_id=user.user_id)
                for workspace in workspaces
            ]
        return [self.get_or_create_current_workspace(user)]

    def update_workspace_settings(
        self,
        *,
        user: UserRecord,
        organization_id: str,
        patch: dict[str, Any],
    ) -> WorkspaceDetail:
        """Merge a settings patch into an existing workspace settings document."""

        current = self._require_workspace(user=user, organization_id=organization_id)
        merged = _deep_merge(current.settings.settings, patch)
        workspace = self.repository.update_workspace_settings(
            organization_id=organization_id,
            user_id=user.user_id,
            settings=merged,
            updated_by_user_id=user.user_id,
        )
        return self._with_effective_permissions(workspace, user_id=user.user_id)

    def create_group(
        self,
        *,
        user: UserRecord,
        organization_id: str,
        slug: str,
        display_name: str,
        description: str = "",
        role_keys: list[str] | None = None,
    ) -> WorkspaceDetail:
        """Create an organization group for future RBAC and assignment workflows."""

        self._require_workspace(user=user, organization_id=organization_id)
        now = utc_now().isoformat()
        group = OrganizationGroupRecord(
            group_id=new_id("grp"),
            organization_id=organization_id,
            slug=_normalize_slug(slug),
            display_name=display_name.strip(),
            description=description.strip(),
            role_keys=_clean_role_keys(role_keys or [], roles_by_key=self._roles_by_key),
            created_at=now,
            updated_at=now,
        )
        workspace = self.repository.create_group(
            organization_id=organization_id,
            user_id=user.user_id,
            group=group,
        )
        return self._with_effective_permissions(workspace, user_id=user.user_id)

    def _require_workspace(
        self,
        *,
        user: UserRecord,
        organization_id: str,
    ) -> WorkspaceDetail:
        for workspace in self.repository.list_workspaces(user_id=user.user_id):
            if workspace.organization.organization_id == organization_id:
                return workspace
        raise NotFoundError(
            "Organization workspace was not found for the current user.",
            details={"organization_id": organization_id},
        )

    def _with_effective_permissions(
        self,
        workspace: WorkspaceDetail,
        *,
        user_id: str,
    ) -> WorkspaceDetail:
        role_keys = _effective_role_keys(workspace, user_id=user_id)
        permission_scopes = _permission_scopes_for_roles(
            role_keys,
            roles_by_key=self._roles_by_key,
        )
        return workspace.model_copy(
            update={
                "effective_role_keys": role_keys,
                "effective_permission_scopes": permission_scopes,
            }
        )


def _workspace_slug(user: UserRecord) -> str:
    email_prefix = user.email.split("@", 1)[0] if "@" in user.email else user.user_id
    return f"{_normalize_slug(email_prefix)}-{_normalize_slug(user.user_id)[-10:]}"


def _workspace_display_name(user: UserRecord) -> str:
    name = (user.display_name or user.email.split("@", 1)[0] or "Workspace").strip()
    return f"{name} Workspace"


def _group_record(
    *,
    organization_id: str,
    default_group: WorkspaceDefaultGroup,
    now: str,
) -> OrganizationGroupRecord:
    return OrganizationGroupRecord(
        group_id=new_id("grp"),
        organization_id=organization_id,
        slug=_normalize_slug(default_group.slug),
        display_name=default_group.display_name,
        description=default_group.description,
        role_keys=_clean_role_keys(default_group.role_keys),
        created_at=now,
        updated_at=now,
    )


def _normalize_slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or new_id("slug")


def _clean_role_keys(
    values: list[str],
    *,
    roles_by_key: dict[str, RbacRoleDefinition] | None = None,
) -> list[str]:
    seen: set[str] = set()
    role_keys: list[str] = []
    for value in values:
        role_key = _normalize_slug(value)
        if roles_by_key is not None and role_key not in roles_by_key:
            raise NotFoundError(
                "RBAC role key was not found.",
                details={"role_key": role_key},
            )
        if role_key in seen:
            continue
        seen.add(role_key)
        role_keys.append(role_key)
    return role_keys


def _effective_role_keys(workspace: WorkspaceDetail, *, user_id: str) -> list[str]:
    group_ids_for_user = {
        membership.group_id
        for membership in workspace.group_memberships
        if membership.user_id == user_id
    }
    role_keys = [workspace.membership.role_key]
    for group in workspace.groups:
        if group.group_id not in group_ids_for_user:
            continue
        role_keys.extend(group.role_keys)
    return _unique_preserving_order(role_keys)


def _permission_scopes_for_roles(
    role_keys: list[str],
    *,
    roles_by_key: dict[str, RbacRoleDefinition],
) -> list[str]:
    permission_scopes: list[str] = []
    for role_key in role_keys:
        role = roles_by_key.get(role_key)
        if role is None:
            continue
        permission_scopes.extend(role.permission_scopes)
    return _unique_preserving_order(permission_scopes)


def _unique_preserving_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _validate_configured_roles(
    role_keys: list[str],
    *,
    roles_by_key: dict[str, RbacRoleDefinition],
) -> None:
    for role_key in _clean_role_keys(role_keys):
        if role_key not in roles_by_key:
            raise NotFoundError(
                "Configured workspace default role is not defined in RBAC policy.",
                details={"role_key": role_key},
            )


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged
