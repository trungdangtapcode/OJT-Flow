"""Tenant organization and workspace orchestration."""

from __future__ import annotations

import hashlib
import re
import secrets
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any

from ojtflow.application.ports import GovernanceRepository
from ojtflow.core.contracts.auth import UserRecord
from ojtflow.core.contracts.governance import (
    OrganizationGroupMembershipRecord,
    OrganizationGroupRecord,
    OrganizationInvitationRecord,
    OrganizationInvitationView,
    OrganizationMembershipRecord,
    OrganizationRecord,
    RbacPolicy,
    RbacRoleDefinition,
    WorkspaceDefaultGroup,
    WorkspaceDefaults,
    WorkspaceDetail,
    WorkspaceSettingsRecord,
)
from ojtflow.core.errors import NotFoundError, OJTFlowError, PolicyBlockedError
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
        invitation_ttl_seconds: int = 7 * 24 * 60 * 60,
    ) -> None:
        self.repository = repository
        self.defaults = defaults
        self.rbac_policy = rbac_policy
        self.invitation_ttl_seconds = invitation_ttl_seconds
        self._roles_by_key = {role.role_key: role for role in rbac_policy.roles}
        self._permissions_by_scope = {
            permission.permission_scope: permission for permission in rbac_policy.permissions
        }
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

    def validate_assignable_role(self, role_key: str) -> str:
        """Return a normalized assignable role key from the active RBAC policy."""

        cleaned = _clean_role_keys([role_key], roles_by_key=self._roles_by_key)[0]
        role = self._roles_by_key[cleaned]
        if not role.assignable:
            raise PolicyBlockedError(
                "RBAC role is not assignable.",
                details={"role_key": cleaned},
            )
        return cleaned

    def require_permission(
        self,
        *,
        user: UserRecord,
        permission_scope: str,
    ) -> WorkspaceDetail:
        """Return the current workspace only when the user has a permission scope."""

        if permission_scope not in self._permissions_by_scope:
            raise PolicyBlockedError(
                "Required permission scope is not defined in the active RBAC policy.",
                details={"permission_scope": permission_scope},
            )
        workspace = self.get_or_create_current_workspace(user)
        if permission_scope in workspace.effective_permission_scopes:
            return workspace
        raise PolicyBlockedError(
            "Current user is not permitted to perform this operation.",
            details={
                "permission_scope": permission_scope,
                "organization_id": workspace.organization.organization_id,
                "role_keys": workspace.effective_role_keys,
            },
        )

    def require_workspace_membership(
        self,
        *,
        user: UserRecord,
        organization_id: str,
    ) -> WorkspaceDetail:
        """Return a workspace only when the user is an active member."""

        workspace = self._require_workspace(user=user, organization_id=organization_id)
        return self._with_effective_permissions(workspace, user_id=user.user_id)

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

    def create_workspace(
        self,
        *,
        user: UserRecord,
        display_name: str,
        slug: str | None = None,
    ) -> WorkspaceDetail:
        """Create a new organization workspace owned by the requesting user."""

        display_name = display_name.strip()
        if not display_name:
            raise PolicyBlockedError("Workspace display name is required.")
        now = utc_now().isoformat()
        organization = OrganizationRecord(
            organization_id=new_id("org"),
            slug=_normalize_slug(slug or display_name),
            display_name=display_name,
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
        workspace = self.repository.create_workspace(
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

    def add_organization_member(
        self,
        *,
        user: UserRecord,
        organization_id: str,
        member_user_id: str,
        role_key: str,
    ) -> WorkspaceDetail:
        """Add a user identity to an organization with an explicit role."""

        self._require_workspace(user=user, organization_id=organization_id)
        now = utc_now().isoformat()
        membership = OrganizationMembershipRecord(
            membership_id=new_id("mem"),
            organization_id=organization_id,
            user_id=member_user_id,
            role_key=self.validate_assignable_role(role_key),
            created_at=now,
            updated_at=now,
        )
        workspace = self.repository.add_membership(
            organization_id=organization_id,
            actor_user_id=user.user_id,
            membership=membership,
        )
        return self._with_effective_permissions(workspace, user_id=user.user_id)

    def invite_member(
        self,
        *,
        user: UserRecord,
        organization_id: str,
        email: str,
        role_key: str,
    ) -> tuple[OrganizationInvitationView, str]:
        """Create a workspace invitation and return its view plus the one-time token."""

        self.require_permission(user=user, permission_scope="users:write")
        self.require_workspace_membership(user=user, organization_id=organization_id)
        normalized_email = _normalize_email(email)
        validated_role = self.validate_assignable_role(role_key)
        raw_token = secrets.token_urlsafe(48)
        now = utc_now()
        invitation = OrganizationInvitationRecord(
            invitation_id=new_id("inv"),
            organization_id=organization_id,
            email=normalized_email,
            role_key=validated_role,
            status="pending",
            token_hash=_hash_token(raw_token),
            invited_by_user_id=user.user_id,
            created_at=now.isoformat(),
            expires_at=(now + timedelta(seconds=self.invitation_ttl_seconds)).isoformat(),
        )
        stored = self.repository.create_invitation(invitation=invitation)
        return _invitation_view(stored), raw_token

    def list_invitations(
        self,
        *,
        user: UserRecord,
        organization_id: str,
    ) -> list[OrganizationInvitationView]:
        """List invitations for a workspace the user can administer."""

        self.require_permission(user=user, permission_scope="users:read")
        self.require_workspace_membership(user=user, organization_id=organization_id)
        return [
            _invitation_view(invitation)
            for invitation in self.repository.list_invitations(
                organization_id=organization_id
            )
        ]

    def accept_invitation(self, *, user: UserRecord, token: str) -> WorkspaceDetail:
        """Accept a pending invitation matching the current user's email."""

        invitation = self.repository.get_invitation_by_token_hash(
            token_hash=_hash_token(token)
        )
        if invitation is None:
            raise NotFoundError("Invitation token is invalid.")
        if invitation.status != "pending":
            raise PolicyBlockedError(
                "Invitation is no longer pending.",
                details={"status": invitation.status},
            )
        if _parse_datetime(invitation.expires_at) <= _now():
            raise PolicyBlockedError("Invitation has expired.")
        if _normalize_email(user.email) != _normalize_email(invitation.email):
            raise PolicyBlockedError(
                "Invitation was issued to a different email address.",
            )
        now = utc_now().isoformat()
        membership = OrganizationMembershipRecord(
            membership_id=new_id("mem"),
            organization_id=invitation.organization_id,
            user_id=user.user_id,
            role_key=self.validate_assignable_role(invitation.role_key),
            created_at=now,
            updated_at=now,
        )
        try:
            self.repository.add_membership(
                organization_id=invitation.organization_id,
                actor_user_id=invitation.invited_by_user_id,
                membership=membership,
            )
        except OJTFlowError:
            # Already a member: still mark the invitation resolved below.
            pass
        self.repository.mark_invitation_accepted(
            invitation_id=invitation.invitation_id,
            accepted_by_user_id=user.user_id,
        )
        # Return the invitee's own workspace view with their effective permissions.
        return self.require_workspace_membership(
            user=user,
            organization_id=invitation.organization_id,
        )

    def revoke_invitation(
        self,
        *,
        user: UserRecord,
        organization_id: str,
        invitation_id: str,
    ) -> OrganizationInvitationView:
        """Revoke a pending invitation."""

        self.require_permission(user=user, permission_scope="users:write")
        self.require_workspace_membership(user=user, organization_id=organization_id)
        revoked = self.repository.revoke_invitation(
            organization_id=organization_id,
            invitation_id=invitation_id,
        )
        return _invitation_view(revoked)

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


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _normalize_email(email: str) -> str:
    normalized = (email or "").strip().lower()
    if not normalized or "@" not in normalized:
        raise PolicyBlockedError("A valid email address is required.")
    return normalized


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _invitation_view(invitation: OrganizationInvitationRecord) -> OrganizationInvitationView:
    return OrganizationInvitationView(
        invitation_id=invitation.invitation_id,
        organization_id=invitation.organization_id,
        email=invitation.email,
        role_key=invitation.role_key,
        status=invitation.status,
        invited_by_user_id=invitation.invited_by_user_id,
        created_at=invitation.created_at,
        expires_at=invitation.expires_at,
        accepted_at=invitation.accepted_at,
        accepted_by_user_id=invitation.accepted_by_user_id,
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
