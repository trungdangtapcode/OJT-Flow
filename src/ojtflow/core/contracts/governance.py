"""Tenant, organization, and workspace governance contracts."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel, NonBlankStr


OrganizationStatus = Literal["active", "disabled"]
MembershipStatus = Literal["active", "disabled", "invited"]
RbacRiskLevel = Literal["low", "medium", "high", "critical"]


class WorkspaceDefaultGroup(ContractModel):
    """Data-driven default group created with a user's first workspace."""

    slug: NonBlankStr
    display_name: NonBlankStr
    description: str = ""
    role_keys: list[NonBlankStr] = Field(default_factory=list)


class WorkspaceDefaults(ContractModel):
    """Trusted default tenant/workspace configuration."""

    version: NonBlankStr
    default_role_key: NonBlankStr
    default_group: WorkspaceDefaultGroup
    settings: dict[str, Any] = Field(default_factory=dict)


class RbacPermissionDefinition(ContractModel):
    """One permission scope exposed by governance policy."""

    permission_scope: NonBlankStr
    label: NonBlankStr
    description: NonBlankStr
    category: NonBlankStr
    risk_level: RbacRiskLevel = "low"


class RbacRoleDefinition(ContractModel):
    """One organization role and its granted permission scopes."""

    role_key: NonBlankStr
    display_name: NonBlankStr
    description: NonBlankStr
    permission_scopes: list[NonBlankStr] = Field(default_factory=list)
    assignable: bool = True
    system_role: bool = False
    notes: list[NonBlankStr] = Field(default_factory=list)


class RbacPolicy(ContractModel):
    """Versioned role-based access-control catalog."""

    version: NonBlankStr
    permissions: list[RbacPermissionDefinition] = Field(default_factory=list)
    roles: list[RbacRoleDefinition] = Field(default_factory=list)


class OrganizationRecord(ContractModel):
    """Durable tenant/workspace organization."""

    organization_id: NonBlankStr
    slug: NonBlankStr
    display_name: NonBlankStr
    status: OrganizationStatus = "active"
    created_by_user_id: NonBlankStr
    created_at: NonBlankStr
    updated_at: NonBlankStr
    attributes: dict[str, Any] = Field(default_factory=dict)


class OrganizationMembershipRecord(ContractModel):
    """User membership in an organization with a role key."""

    membership_id: NonBlankStr
    organization_id: NonBlankStr
    user_id: NonBlankStr
    role_key: NonBlankStr
    status: MembershipStatus = "active"
    created_at: NonBlankStr
    updated_at: NonBlankStr


class OrganizationGroupRecord(ContractModel):
    """Workspace group used for future RBAC and workflow assignment."""

    group_id: NonBlankStr
    organization_id: NonBlankStr
    slug: NonBlankStr
    display_name: NonBlankStr
    description: str = ""
    role_keys: list[NonBlankStr] = Field(default_factory=list)
    created_at: NonBlankStr
    updated_at: NonBlankStr


class OrganizationGroupMembershipRecord(ContractModel):
    """User membership in a workspace group."""

    group_id: NonBlankStr
    organization_id: NonBlankStr
    user_id: NonBlankStr
    created_at: NonBlankStr


class WorkspaceSettingsRecord(ContractModel):
    """Versioned JSON workspace settings."""

    organization_id: NonBlankStr
    settings: dict[str, Any] = Field(default_factory=dict)
    version: int = Field(default=1, ge=1)
    updated_by_user_id: str | None = None
    updated_at: NonBlankStr


class WorkspaceDetail(ContractModel):
    """Current user's organization workspace view."""

    organization: OrganizationRecord
    membership: OrganizationMembershipRecord
    groups: list[OrganizationGroupRecord] = Field(default_factory=list)
    group_memberships: list[OrganizationGroupMembershipRecord] = Field(default_factory=list)
    settings: WorkspaceSettingsRecord
    effective_role_keys: list[NonBlankStr] = Field(default_factory=list)
    effective_permission_scopes: list[NonBlankStr] = Field(default_factory=list)
