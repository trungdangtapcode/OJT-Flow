"""Keycloak OpenID Connect infrastructure adapter.

Keycloak is the single identity authority: it hosts local email/password users and
brokers Google as a social identity provider. The application speaks OIDC only to
Keycloak through the shared :class:`IdentityProvider` port, then upserts the resolved
identity into its own ``users`` table and issues its own opaque backend session.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import httpx

from ojtflow.core.contracts.auth import GoogleIdentityProfile
from ojtflow.core.errors import OJTFlowError


class KeycloakOIDCClient:
    """Keycloak OIDC client that resolves identities via the userinfo endpoint.

    Identity claims are read from Keycloak's userinfo endpoint with the access token
    obtained from the authorization-code exchange. Keycloak has already verified the
    underlying credential (local password or federated Google), so the TLS-protected
    userinfo response is the trusted source of claims (same trust model as the Google
    adapter, which trusts Google's token verifier).
    """

    def __init__(
        self,
        base_url: str,
        realm: str,
        client_id: str,
        client_secret: str,
        timeout_seconds: float = 10.0,
        public_base_url: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        # Browser-facing base URL for the authorization redirect. In Docker the API
        # talks to Keycloak over the internal network (e.g. http://keycloak:8080)
        # while the user's browser must reach it on a published host
        # (e.g. http://localhost:18080). Defaults to base_url when not split.
        self.public_base_url = (public_base_url or base_url).rstrip("/")
        self.realm = realm
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout_seconds = timeout_seconds

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url and self.realm and self.client_id and self.client_secret)

    @property
    def _realm_root(self) -> str:
        return f"{self.base_url}/realms/{self.realm}/protocol/openid-connect"

    @property
    def _public_realm_root(self) -> str:
        return f"{self.public_base_url}/realms/{self.realm}/protocol/openid-connect"

    @property
    def auth_endpoint(self) -> str:
        return f"{self._public_realm_root}/auth"

    @property
    def token_endpoint(self) -> str:
        return f"{self._realm_root}/token"

    @property
    def userinfo_endpoint(self) -> str:
        return f"{self._realm_root}/userinfo"

    def authorization_url(self, redirect_uri: str, state: str) -> str:
        query = urlencode(
            {
                "client_id": self.client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "openid email profile",
                "state": state,
            }
        )
        return f"{self.auth_endpoint}?{query}"

    async def exchange_code_for_profile(
        self,
        code: str,
        redirect_uri: str,
    ) -> GoogleIdentityProfile:
        """Exchange an authorization code and resolve the verified Keycloak identity."""

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
                token_data = self._parse_json(token_response, context="token")
                access_token = token_data.get("access_token")
                if not isinstance(access_token, str) or not access_token:
                    raise OJTFlowError("Keycloak token response did not include an access_token.")
                userinfo_response = await client.get(
                    self.userinfo_endpoint,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                userinfo_response.raise_for_status()
                claims = self._parse_json(userinfo_response, context="userinfo")
        except httpx.HTTPStatusError as exc:
            raise OJTFlowError(f"Keycloak OAuth request failed: {exc.response.text}") from exc
        except httpx.HTTPError as exc:
            raise OJTFlowError(f"Keycloak OAuth request failed: {exc}") from exc

        return self._profile_from_claims(claims)

    def _parse_json(self, response: httpx.Response, *, context: str) -> dict[str, Any]:
        try:
            data = response.json()
        except ValueError as exc:
            raise OJTFlowError(f"Keycloak {context} response was not valid JSON.") from exc
        if not isinstance(data, dict):
            raise OJTFlowError(f"Keycloak {context} response had an unexpected shape.")
        return data

    def _profile_from_claims(self, claims: dict[str, Any]) -> GoogleIdentityProfile:
        subject = claims.get("sub")
        email = claims.get("email")
        if not subject or not email:
            raise OJTFlowError("Keycloak identity is missing required claims (sub/email).")

        email_verified = claims.get("email_verified")
        if isinstance(email_verified, str):
            email_verified = email_verified.lower() == "true"
        if not email_verified:
            raise OJTFlowError("Keycloak account email is not verified.")

        # Keycloak exposes the brokered upstream IdP alias on `identity_provider` when
        # the user authenticated through a social provider such as Google.
        identity_provider = claims.get("identity_provider") or "keycloak"
        display_name = claims.get("name") or claims.get("preferred_username")

        return GoogleIdentityProfile(
            google_sub=subject,
            email=email,
            email_verified=True,
            display_name=display_name,
            avatar_url=claims.get("picture"),
            hosted_domain=claims.get("hd"),
            identity_provider=identity_provider,
        )
