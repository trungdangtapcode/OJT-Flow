"""Google OpenID Connect infrastructure adapter."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import httpx

try:
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token as google_id_token
except ImportError:  # pragma: no cover - exercised only when runtime deps are missing.
    google_requests = None
    google_id_token = None

from ojtflow.core.contracts.auth import GoogleIdentityProfile
from ojtflow.core.errors import OJTFlowError


class GoogleOAuthClient:
    """Google OpenID Connect client that verifies ID tokens with Google's verifier."""

    auth_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
    token_endpoint = "https://oauth2.googleapis.com/token"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        timeout_seconds: float = 10.0,
        allowed_hosted_domains: set[str] | None = None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout_seconds = timeout_seconds
        self.allowed_hosted_domains = {domain.lower() for domain in allowed_hosted_domains or set()}

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def authorization_url(self, redirect_uri: str, state: str) -> str:
        query = urlencode(
            {
                "client_id": self.client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "openid email profile",
                "state": state,
                "access_type": "online",
                "prompt": "select_account",
            }
        )
        return f"{self.auth_endpoint}?{query}"

    async def exchange_code_for_profile(
        self,
        code: str,
        redirect_uri: str,
    ) -> GoogleIdentityProfile:
        """Exchange an authorization code and verify the returned identity token."""

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                token_response = await client.post(
                    self.token_endpoint,
                    data={
                        "code": code,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "redirect_uri": redirect_uri,
                        "grant_type": "authorization_code",
                    },
                )
                token_response.raise_for_status()
                token_data = token_response.json()
        except httpx.HTTPStatusError as exc:
            raise OJTFlowError(f"Google OAuth request failed: {exc.response.text}") from exc
        except httpx.HTTPError as exc:
            raise OJTFlowError(f"Google OAuth request failed: {exc}") from exc

        id_token_value = token_data.get("id_token")
        if not id_token_value:
            raise OJTFlowError("Google OAuth response did not include an id_token.")
        claims = self._verify_id_token(id_token_value)
        return self._profile_from_claims(claims)

    def _verify_id_token(self, id_token_value: str) -> dict[str, Any]:
        if google_id_token is None or google_requests is None:
            raise OJTFlowError(
                "Google OAuth token verification requires google-auth. "
                "Install project dependencies before enabling Google sign-in."
            )
        try:
            claims = google_id_token.verify_oauth2_token(
                id_token_value,
                google_requests.Request(),
                self.client_id,
                clock_skew_in_seconds=30,
            )
        except ValueError as exc:
            raise OJTFlowError("Google OAuth token verification failed.") from exc
        return dict(claims)

    def _profile_from_claims(self, claims: dict[str, Any]) -> GoogleIdentityProfile:
        google_sub = claims.get("sub")
        email = claims.get("email")
        email_verified = claims.get("email_verified")
        if isinstance(email_verified, str):
            email_verified = email_verified.lower() == "true"

        if not google_sub or not email:
            raise OJTFlowError("Google OAuth token is missing required identity claims.")
        if not email_verified:
            raise OJTFlowError("Google account email is not verified.")

        hosted_domain = claims.get("hd")
        if self.allowed_hosted_domains:
            normalized_domain = str(hosted_domain or "").lower()
            if normalized_domain not in self.allowed_hosted_domains:
                raise OJTFlowError("Google account hosted domain is not allowed.")

        return GoogleIdentityProfile(
            google_sub=google_sub,
            email=email,
            email_verified=True,
            display_name=claims.get("name"),
            avatar_url=claims.get("picture"),
            hosted_domain=hosted_domain,
        )
