"""Authentication routes for Google OAuth and backend sessions."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, Security
from fastapi.security import HTTPAuthorizationCredentials

from ojtflow.application.auth_service import AuthService, auth_session_response
from ojtflow.config import Settings
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.interfaces.api.deps import (
    bearer_scheme,
    get_api_settings,
    get_auth_service,
    require_authentication,
    session_token_from_request,
)
from ojtflow.interfaces.api.responses import ok

router = APIRouter(tags=["auth"])


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
