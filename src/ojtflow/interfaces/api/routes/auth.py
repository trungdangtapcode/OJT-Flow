"""Authentication routes for Google OAuth and backend sessions."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, Security
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import Field

from ojtflow.application.governance_service import GovernanceService
from ojtflow.application.auth_service import AuthService, auth_session_response
from ojtflow.config import Settings
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.core.contracts.base import ContractModel, NonBlankStr
from ojtflow.interfaces.api.deps import (
    bearer_scheme,
    get_api_settings,
    get_auth_service,
    get_governance_service,
    require_authentication,
    session_token_from_request,
)
from ojtflow.interfaces.api.responses import ok

router = APIRouter(tags=["auth"])


class CreateServiceAccountRequest(ContractModel):
    """Create an automation identity and return its first token once."""

    slug: NonBlankStr = Field(
        examples=["nightly-ingestion"],
        description="Stable service account slug unique inside the organization.",
    )
    display_name: NonBlankStr = Field(examples=["Nightly Ingestion"])
    role_key: NonBlankStr | None = Field(
        default=None,
        examples=["operator"],
        description="Assignable RBAC role; defaults to OJT_SERVICE_ACCOUNT_DEFAULT_ROLE_KEY.",
    )
    organization_id: NonBlankStr | None = Field(
        default=None,
        description="Defaults to the current user's active organization.",
    )
    token_ttl_seconds: int | None = Field(
        default=None,
        gt=0,
        description="Optional shorter TTL for the first issued bearer token.",
    )


@router.get("/auth/google/url")
async def google_authorization_url(
    redirect_uri: str | None = None,
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """Create a Google OAuth URL and cache the state nonce."""

    return ok(service.google_authorization_url(redirect_uri=redirect_uri))


@router.get("/auth/google/callback")
async def google_callback(
    code: str,
    state: str,
    request: Request,
    response: Response,
    include_token: bool = False,
    settings: Settings = Depends(get_api_settings),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """Complete Google OAuth, create/update the app user, and issue a session token."""

    result = await service.complete_google_login(
        code=code,
        state=state,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    _set_session_cookie(response, settings, result["access_token"])
    return ok(_login_response(result, include_token=include_token))


@router.get("/auth/me")
async def current_user(
    authenticated: AuthenticatedSession = Depends(require_authentication),
) -> dict:
    """Resolve the current backend session."""

    return ok(auth_session_response(authenticated))


@router.get("/auth/service-accounts")
async def list_service_accounts(
    organization_id: str | None = None,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: AuthService = Depends(get_auth_service),
    governance: GovernanceService = Depends(get_governance_service),
) -> dict:
    """List automation identities in an organization workspace."""

    workspace = governance.require_permission(
        user=authenticated.user,
        permission_scope="users:read",
    )
    target_organization_id = organization_id or workspace.organization.organization_id
    governance.require_workspace_membership(
        user=authenticated.user,
        organization_id=target_organization_id,
    )
    return ok(
        {
            "items": service.list_service_accounts(
                organization_id=target_organization_id,
            )
        }
    )


@router.post("/auth/service-accounts")
async def create_service_account(
    request: CreateServiceAccountRequest,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    settings: Settings = Depends(get_api_settings),
    service: AuthService = Depends(get_auth_service),
    governance: GovernanceService = Depends(get_governance_service),
) -> dict:
    """Create a service-account identity, attach it to a workspace, and issue a token."""

    workspace = governance.require_permission(
        user=authenticated.user,
        permission_scope="users:write",
    )
    organization_id = request.organization_id or workspace.organization.organization_id
    governance.require_workspace_membership(
        user=authenticated.user,
        organization_id=organization_id,
    )
    role_key = governance.validate_assignable_role(
        request.role_key or settings.service_account_default_role_key
    )
    service_account = service.create_service_account_identity(
        organization_id=organization_id,
        slug=request.slug,
        display_name=request.display_name,
        role_key=role_key,
        created_by_user_id=authenticated.user.user_id,
    )
    governance.add_organization_member(
        user=authenticated.user,
        organization_id=organization_id,
        member_user_id=service_account.user_id,
        role_key=role_key,
    )
    token = service.issue_service_account_token(
        service_account=service_account,
        token_ttl_seconds=request.token_ttl_seconds,
    )
    return ok(
        {
            "service_account": token["service_account"],
            "token_type": token["token_type"],
            "access_token": token["access_token"],
            "expires_at": token["expires_at"],
        }
    )


@router.post("/auth/logout")
async def logout(
    request: Request,
    response: Response,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    authenticated: AuthenticatedSession = Depends(require_authentication),
    settings: Settings = Depends(get_api_settings),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """Revoke the current session token."""

    del authenticated
    token = session_token_from_request(request, credentials)
    service.logout(token)
    _clear_session_cookie(response, settings)
    return ok({"status": "logged_out"})


def _set_session_cookie(response: Response, settings: Settings, token: str) -> None:
    same_site = _normalized_same_site(settings.auth_cookie_samesite)
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        max_age=settings.auth_session_ttl_seconds,
        httponly=True,
        secure=settings.effective_auth_cookie_secure,
        samesite=same_site,
        domain=settings.auth_cookie_domain,
        path="/",
    )


def _clear_session_cookie(response: Response, settings: Settings) -> None:
    same_site = _normalized_same_site(settings.auth_cookie_samesite)
    response.delete_cookie(
        key=settings.auth_cookie_name,
        secure=settings.effective_auth_cookie_secure,
        samesite=same_site,
        domain=settings.auth_cookie_domain,
        path="/",
    )


def _normalized_same_site(value: str) -> str:
    normalized = value.lower()
    if normalized not in {"lax", "strict", "none"}:
        raise ValueError(f"Unsupported auth cookie SameSite setting: {value}")
    return normalized


def _login_response(result: dict, *, include_token: bool) -> dict:
    payload = {
        "expires_at": result["expires_at"],
        "user": result["user"],
    }
    if include_token:
        payload["token_type"] = result["token_type"]
        payload["access_token"] = result["access_token"]
    return payload
