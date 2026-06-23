"""Tests for Keycloak OIDC sign-in, workspace creation, and invitations."""

from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from ojtflow.application.governance_service import GovernanceService
from ojtflow.core.contracts.auth import AuthenticatedSession, SessionRecord, UserRecord
from ojtflow.core.errors import OJTFlowError, PolicyBlockedError
from ojtflow.infrastructure.auth.keycloak import KeycloakOIDCClient
from ojtflow.infrastructure.governance_defaults import load_workspace_defaults
from ojtflow.infrastructure.governance_rbac import load_rbac_policy
from ojtflow.infrastructure.storage.governance_memory import InMemoryGovernanceRepository
from ojtflow.interfaces.api.routes import governance


ROOT = Path(__file__).resolve().parents[1]


def _user(user_id: str, email: str) -> UserRecord:
    now = datetime.now(timezone.utc)
    return UserRecord(
        user_id=user_id,
        google_sub=f"kc-{user_id}",
        email=email,
        email_verified=True,
        display_name=user_id,
        avatar_url=None,
        created_at=now,
        updated_at=now,
        last_login_at=now,
        identity_provider="keycloak",
    )


def _session(user: UserRecord) -> AuthenticatedSession:
    now = datetime.now(timezone.utc)
    return AuthenticatedSession(
        user=user,
        session=SessionRecord(
            session_id=f"ses-{user.user_id}",
            user_id=user.user_id,
            token_hash="hash",
            created_at=now,
            expires_at=now,
            revoked_at=None,
            last_seen_at=now,
        ),
    )


def _service(repository=None) -> GovernanceService:
    return GovernanceService(
        repository or InMemoryGovernanceRepository(),
        defaults=load_workspace_defaults(ROOT / "knowledge"),
        rbac_policy=load_rbac_policy(ROOT / "knowledge"),
        invitation_ttl_seconds=3600,
    )


# --------------------------------------------------------------------------- #
# Keycloak OIDC client
# --------------------------------------------------------------------------- #


def _keycloak_client() -> KeycloakOIDCClient:
    return KeycloakOIDCClient(
        base_url="https://kc.example/",
        realm="ojtflow",
        client_id="ojtflow-api",
        client_secret="secret",
    )


def test_keycloak_authorization_url_targets_realm_auth_endpoint() -> None:
    client = _keycloak_client()
    url = client.authorization_url(redirect_uri="https://app/cb", state="xyz")
    assert url.startswith(
        "https://kc.example/realms/ojtflow/protocol/openid-connect/auth?"
    )
    assert "client_id=ojtflow-api" in url
    assert "state=xyz" in url
    assert "scope=openid+email+profile" in url


@pytest.mark.asyncio
async def test_keycloak_exchange_resolves_identity_from_userinfo(monkeypatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return httpx.Response(200, json={"access_token": "at", "id_token": "it"})
        if request.url.path.endswith("/userinfo"):
            assert request.headers["Authorization"] == "Bearer at"
            return httpx.Response(
                200,
                json={
                    "sub": "kc-123",
                    "email": "Doctor@Example.org",
                    "email_verified": True,
                    "name": "Dr Who",
                    "identity_provider": "google",
                },
            )
        return httpx.Response(404)

    real_async_client = httpx.AsyncClient
    monkeypatch.setattr(
        "ojtflow.infrastructure.auth.keycloak.httpx.AsyncClient",
        lambda **kwargs: real_async_client(transport=httpx.MockTransport(handler)),
    )

    profile = await _keycloak_client().exchange_code_for_profile(
        code="code",
        redirect_uri="https://app/cb",
    )
    assert profile.google_sub == "kc-123"
    assert profile.email == "Doctor@Example.org"
    assert profile.identity_provider == "google"
    assert profile.display_name == "Dr Who"


@pytest.mark.asyncio
async def test_keycloak_rejects_unverified_email(monkeypatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return httpx.Response(200, json={"access_token": "at"})
        return httpx.Response(
            200,
            json={"sub": "kc-1", "email": "x@example.org", "email_verified": False},
        )

    real_async_client = httpx.AsyncClient
    monkeypatch.setattr(
        "ojtflow.infrastructure.auth.keycloak.httpx.AsyncClient",
        lambda **kwargs: real_async_client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(OJTFlowError):
        await _keycloak_client().exchange_code_for_profile(
            code="code",
            redirect_uri="https://app/cb",
        )


# --------------------------------------------------------------------------- #
# Workspace creation
# --------------------------------------------------------------------------- #


def test_create_workspace_makes_owner_membership() -> None:
    service = _service()
    user = _user("owner1", "owner1@example.org")
    workspace = service.create_workspace(user=user, display_name="Radiology Ops")
    assert workspace.organization.display_name == "Radiology Ops"
    assert workspace.organization.slug == "radiology-ops"
    assert workspace.membership.role_key == "owner"
    assert "users:write" in workspace.effective_permission_scopes


def test_create_workspace_allows_multiple_distinct_workspaces() -> None:
    repo = InMemoryGovernanceRepository()
    service = _service(repo)
    user = _user("owner2", "owner2@example.org")
    service.create_workspace(user=user, display_name="First")
    service.create_workspace(user=user, display_name="Second")
    workspaces = service.list_workspaces(user)
    assert len(workspaces) == 2


def test_create_workspace_rejects_duplicate_slug() -> None:
    repo = InMemoryGovernanceRepository()
    service = _service(repo)
    user = _user("owner3", "owner3@example.org")
    service.create_workspace(user=user, display_name="Team", slug="shared")
    with pytest.raises(OJTFlowError):
        service.create_workspace(user=user, display_name="Other", slug="shared")


# --------------------------------------------------------------------------- #
# Invitation lifecycle (service layer)
# --------------------------------------------------------------------------- #


def test_invitation_accept_creates_membership_for_matching_email() -> None:
    repo = InMemoryGovernanceRepository()
    service = _service(repo)
    owner = _user("owner4", "owner4@example.org")
    workspace = service.create_workspace(user=owner, display_name="Clinic")
    org_id = workspace.organization.organization_id

    invitation, token = service.invite_member(
        user=owner,
        organization_id=org_id,
        email="invitee@example.org",
        role_key="operator",
    )
    assert invitation.status == "pending"
    assert not hasattr(invitation, "token_hash")

    invitee = _user("invitee4", "Invitee@Example.org")
    joined = service.accept_invitation(user=invitee, token=token)
    assert joined.organization.organization_id == org_id
    assert joined.membership.role_key == "operator"

    listed = service.list_invitations(user=owner, organization_id=org_id)
    assert listed[0].status == "accepted"


def test_invitation_rejects_email_mismatch() -> None:
    repo = InMemoryGovernanceRepository()
    service = _service(repo)
    owner = _user("owner5", "owner5@example.org")
    workspace = service.create_workspace(user=owner, display_name="Clinic")
    _, token = service.invite_member(
        user=owner,
        organization_id=workspace.organization.organization_id,
        email="invitee@example.org",
        role_key="operator",
    )
    intruder = _user("intruder5", "intruder@example.org")
    with pytest.raises(PolicyBlockedError):
        service.accept_invitation(user=intruder, token=token)


def test_revoked_invitation_cannot_be_accepted() -> None:
    repo = InMemoryGovernanceRepository()
    service = _service(repo)
    owner = _user("owner6", "owner6@example.org")
    workspace = service.create_workspace(user=owner, display_name="Clinic")
    org_id = workspace.organization.organization_id
    invitation, token = service.invite_member(
        user=owner,
        organization_id=org_id,
        email="invitee@example.org",
        role_key="operator",
    )
    service.revoke_invitation(
        user=owner,
        organization_id=org_id,
        invitation_id=invitation.invitation_id,
    )
    invitee = _user("invitee6", "invitee@example.org")
    with pytest.raises(PolicyBlockedError):
        service.accept_invitation(user=invitee, token=token)


def test_expired_invitation_is_rejected() -> None:
    repo = InMemoryGovernanceRepository()
    service = GovernanceService(
        repo,
        defaults=load_workspace_defaults(ROOT / "knowledge"),
        rbac_policy=load_rbac_policy(ROOT / "knowledge"),
        invitation_ttl_seconds=-1,  # already expired on creation
    )
    owner = _user("owner7", "owner7@example.org")
    workspace = service.create_workspace(user=owner, display_name="Clinic")
    _, token = service.invite_member(
        user=owner,
        organization_id=workspace.organization.organization_id,
        email="invitee@example.org",
        role_key="operator",
    )
    invitee = _user("invitee7", "invitee@example.org")
    with pytest.raises(PolicyBlockedError):
        service.accept_invitation(user=invitee, token=token)


def test_runtime_auth_readiness_reports_keycloak_provider(monkeypatch) -> None:
    monkeypatch.setenv("OJT_AUTH_PROVIDER", "keycloak")
    monkeypatch.setenv("OJT_KEYCLOAK_BASE_URL", "http://localhost:18080")
    monkeypatch.setenv("OJT_KEYCLOAK_REALM", "ojtflow")
    monkeypatch.setenv("OJT_KEYCLOAK_CLIENT_ID", "ojtflow-api")
    monkeypatch.setenv("OJT_KEYCLOAK_CLIENT_SECRET", "secret")
    monkeypatch.setenv("OJT_GOOGLE_CLIENT_ID", "")
    monkeypatch.setenv("OJT_GOOGLE_CLIENT_SECRET", "")
    monkeypatch.setenv("OJT_EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("OJT_EMBEDDING_MODEL", "text-embedding-3-small")
    monkeypatch.setenv("OJT_EMBEDDING_DIMENSIONS", "384")
    from ojtflow.config import clear_settings_cache, get_settings
    from ojtflow.interfaces.api.routes.runtime import _auth_configuration_check

    clear_settings_cache()
    try:
        check = _auth_configuration_check(get_settings())
    finally:
        clear_settings_cache()

    assert check["status"] == "ok"
    assert check["details"]["provider"] == "keycloak"
    assert check["details"]["auth_configured"] is True
    assert check["details"]["keycloak_configured"] is True
    assert check["details"]["google_oauth_configured"] is False


@pytest.mark.asyncio
async def test_invitation_route_flow_returns_enveloped_contract(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("OJT_EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("OJT_EMBEDDING_MODEL", "text-embedding-3-small")
    monkeypatch.setenv("OJT_EMBEDDING_DIMENSIONS", "384")
    monkeypatch.setenv("OJT_FRONTEND_BASE_URL", "http://localhost:15173")
    from ojtflow.config import clear_settings_cache, get_settings

    clear_settings_cache()

    service = _service()
    owner = _user("api_owner", "api_owner@example.org")
    invitee = _user("api_invitee", "api_invitee@example.org")
    try:
        settings = get_settings()
        created = await governance.create_organization_workspace(
            governance.CreateWorkspaceRequest(display_name="API Workspace"),
            authenticated=_session(owner),
            service=service,
        )
        org_id = created["data"]["organization"]["organization_id"]

        invited = await governance.create_organization_invitation(
            org_id,
            governance.InviteMemberRequest(
                email="api_invitee@example.org",
                role_key="operator",
            ),
            authenticated=_session(owner),
            service=service,
            settings=settings,
        )
        body = invited["data"]
        token = body["token"]
        assert body["invite_url"].startswith(
            "http://localhost:15173/invite/accept?token="
        )

        accepted = await governance.accept_organization_invitation(
            governance.AcceptInvitationRequest(token=token),
            authenticated=_session(invitee),
            service=service,
        )
        assert accepted["data"]["membership"]["role_key"] == "operator"

        listed = await governance.list_organization_invitations(
            org_id,
            authenticated=_session(owner),
            service=service,
        )
        items = listed["data"]["items"]
        assert len(items) == 1
        assert items[0]["status"] == "accepted"
    finally:
        clear_settings_cache()
