"""Tenant organization and workspace governance routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import Field

from urllib.parse import urlparse, urlunparse

from ojtflow.application.governance_service import GovernanceService
from ojtflow.config import Settings
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.core.contracts.base import ContractModel, NonBlankStr
from ojtflow.interfaces.api.deps import (
    get_api_settings,
    get_governance_service,
    require_authentication,
)
from ojtflow.interfaces.api.responses import ok

router = APIRouter(tags=["governance"])


class UpdateWorkspaceSettingsRequest(ContractModel):
    """Merge patch for workspace-level settings."""

    settings: dict[str, Any] = Field(
        default_factory=dict,
        examples=[
            {
                "review_policy": {"low_confidence_threshold": 0.75},
                "assistant": {"write_actions_require_confirmation": True},
            }
        ],
    )


class CreateWorkspaceRequest(ContractModel):
    """Create a new organization workspace owned by the current user."""

    display_name: NonBlankStr = Field(examples=["Radiology Operations"])
    slug: NonBlankStr | None = Field(
        default=None,
        examples=["radiology-ops"],
        description="Optional stable slug; derived from the display name when omitted.",
    )


class CreateOrganizationGroupRequest(ContractModel):
    """Create a workspace group for future RBAC and assignment workflows."""

    slug: NonBlankStr = Field(examples=["data-stewards"])
    display_name: NonBlankStr = Field(examples=["Data Stewards"])
    description: str = Field(default="", examples=["Users responsible for data quality review."])
    role_keys: list[NonBlankStr] = Field(default_factory=list, examples=[["data-steward"]])


class InviteMemberRequest(ContractModel):
    """Invite a person to join an organization workspace by email."""

    email: NonBlankStr = Field(examples=["clinician@example.org"])
    role_key: NonBlankStr = Field(examples=["operator"])


class AcceptInvitationRequest(ContractModel):
    """Accept a pending workspace invitation with its one-time token."""

    token: NonBlankStr = Field(description="The one-time invitation token from the invite link.")


@router.get("/organizations/current")
async def current_organization_workspace(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: GovernanceService = Depends(get_governance_service),
) -> dict:
    """Return or initialize the current user's organization workspace."""

    return ok(service.get_or_create_current_workspace(authenticated.user))


@router.post("/organizations")
async def create_organization_workspace(
    request: CreateWorkspaceRequest,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: GovernanceService = Depends(get_governance_service),
) -> dict:
    """Create a new organization workspace owned by the current user."""

    return ok(
        service.create_workspace(
            user=authenticated.user,
            display_name=request.display_name,
            slug=request.slug,
        )
    )


@router.get("/governance/rbac-policy")
async def governance_rbac_policy(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: GovernanceService = Depends(get_governance_service),
) -> dict:
    """Return the active role and permission policy catalog."""

    service.require_permission(user=authenticated.user, permission_scope="settings:read")
    return ok(service.role_policy())


@router.get("/organizations")
async def list_organization_workspaces(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: GovernanceService = Depends(get_governance_service),
) -> dict:
    """List organization workspaces visible to the current user."""

    return ok({"items": service.list_workspaces(authenticated.user)})


@router.patch("/organizations/{organization_id}/settings")
async def update_organization_workspace_settings(
    organization_id: str,
    request: UpdateWorkspaceSettingsRequest,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: GovernanceService = Depends(get_governance_service),
) -> dict:
    """Merge workspace-level settings for the current organization."""

    service.require_permission(user=authenticated.user, permission_scope="settings:write")
    return ok(
        service.update_workspace_settings(
            user=authenticated.user,
            organization_id=organization_id,
            patch=request.settings,
        )
    )


@router.post("/organizations/{organization_id}/groups")
async def create_organization_group(
    organization_id: str,
    request: CreateOrganizationGroupRequest,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: GovernanceService = Depends(get_governance_service),
) -> dict:
    """Create a group inside an organization workspace."""

    service.require_permission(user=authenticated.user, permission_scope="users:write")
    return ok(
        service.create_group(
            user=authenticated.user,
            organization_id=organization_id,
            slug=request.slug,
            display_name=request.display_name,
            description=request.description,
            role_keys=request.role_keys,
        )
    )


@router.post("/organizations/{organization_id}/invitations")
async def create_organization_invitation(
    organization_id: str,
    request: InviteMemberRequest,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: GovernanceService = Depends(get_governance_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Create a workspace invitation and return a shareable accept link."""

    invitation, token = service.invite_member(
        user=authenticated.user,
        organization_id=organization_id,
        email=request.email,
        role_key=request.role_key,
    )
    return ok(
        {
            "invitation": invitation,
            "invite_url": _invite_url(settings, token),
            "token": token,
        }
    )


@router.get("/organizations/{organization_id}/invitations")
async def list_organization_invitations(
    organization_id: str,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: GovernanceService = Depends(get_governance_service),
) -> dict:
    """List invitations for an organization workspace."""

    return ok(
        {
            "items": service.list_invitations(
                user=authenticated.user,
                organization_id=organization_id,
            )
        }
    )


@router.post("/invitations/accept")
async def accept_organization_invitation(
    request: AcceptInvitationRequest,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: GovernanceService = Depends(get_governance_service),
) -> dict:
    """Accept a pending invitation matching the current user's email."""

    return ok(
        service.accept_invitation(user=authenticated.user, token=request.token)
    )


@router.post("/organizations/{organization_id}/invitations/{invitation_id}/revoke")
async def revoke_organization_invitation(
    organization_id: str,
    invitation_id: str,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: GovernanceService = Depends(get_governance_service),
) -> dict:
    """Revoke a pending workspace invitation."""

    return ok(
        service.revoke_invitation(
            user=authenticated.user,
            organization_id=organization_id,
            invitation_id=invitation_id,
        )
    )


def _invite_url(settings: Settings, token: str) -> str:
    """Build a frontend accept link for an invitation token."""

    base = settings.frontend_base_url
    if not base:
        # Fall back to the frontend origin used for OAuth redirects.
        parsed = urlparse(settings.google_frontend_redirect_uri)
        if parsed.scheme and parsed.netloc:
            base = urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))
    base = base.rstrip("/")
    return f"{base}/invite/accept?token={token}" if base else f"/invite/accept?token={token}"
