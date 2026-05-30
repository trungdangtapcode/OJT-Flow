"""Authentication routes for Google OAuth and backend sessions."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Security
from fastapi.security import HTTPAuthorizationCredentials

from ojtflow.application.auth_service import AuthService, auth_session_response
from ojtflow.interfaces.api.deps import (
    bearer_scheme,
    bearer_token_from_credentials,
    get_auth_service,
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
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """Complete Google OAuth, create/update the app user, and issue a session token."""

    result = await service.complete_google_login(
        code=code,
        state=state,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    return ok(result)


@router.get("/auth/me")
async def current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> dict:
    """Resolve the current bearer token."""

    token = bearer_token_from_credentials(credentials)
    service = await get_auth_service()
    authenticated = service.authenticate_token(token)
    if not authenticated:
        raise HTTPException(status_code=401, detail="Invalid or expired session token.")
    return ok(auth_session_response(authenticated))


@router.post("/auth/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> dict:
    """Revoke the current bearer token."""

    token = bearer_token_from_credentials(credentials)
    service = await get_auth_service()
    service.logout(token)
    return ok({"status": "logged_out"})
