"""Tenant organization and workspace governance routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import Field

from ojtflow.application.governance_service import GovernanceService
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.core.contracts.base import ContractModel, NonBlankStr
from ojtflow.interfaces.api.deps import get_governance_service, require_authentication
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


class CreateOrganizationGroupRequest(ContractModel):
    """Create a workspace group for future RBAC and assignment workflows."""

    slug: NonBlankStr = Field(examples=["data-stewards"])
    display_name: NonBlankStr = Field(examples=["Data Stewards"])
    description: str = Field(default="", examples=["Users responsible for data quality review."])
    role_keys: list[NonBlankStr] = Field(default_factory=list, examples=[["data-steward"]])


@router.get("/organizations/current")
async def current_organization_workspace(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: GovernanceService = Depends(get_governance_service),
) -> dict:
    """Return or initialize the current user's organization workspace."""

    return ok(service.get_or_create_current_workspace(authenticated.user))


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
