from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from ojtflow.application.governance_service import GovernanceService
from ojtflow.core.contracts.auth import (
    AuthenticatedSession,
    GoogleIdentityProfile,
    SessionRecord,
    UserRecord,
)
from ojtflow.infrastructure.governance_defaults import load_workspace_defaults
from ojtflow.infrastructure.storage.auth_sqlite import SQLiteAuthRepository
from ojtflow.infrastructure.storage.governance_memory import InMemoryGovernanceRepository
from ojtflow.infrastructure.storage.governance_sqlite import SQLiteGovernanceRepository
from ojtflow.infrastructure.storage.sqlite import SQLiteBackboneStore
from ojtflow.interfaces.api.app import create_app
from ojtflow.interfaces.api.deps import get_governance_service, require_authentication


ROOT = Path(__file__).resolve().parents[1]


def _user(user_id: str = "usr_governance") -> UserRecord:
    now = datetime.now(timezone.utc)
    return UserRecord(
        user_id=user_id,
        google_sub=f"google-{user_id}",
        email=f"{user_id}@example.com",
        email_verified=True,
        display_name="Governance User",
        avatar_url=None,
        created_at=now,
        updated_at=now,
        last_login_at=now,
    )


def _authenticated_session() -> AuthenticatedSession:
    user = _user()
    now = datetime.now(timezone.utc)
    return AuthenticatedSession(
        user=user,
        session=SessionRecord(
            session_id="ses_governance",
            user_id=user.user_id,
            token_hash="hash",
            created_at=now,
            expires_at=now,
            revoked_at=None,
            last_seen_at=now,
        ),
    )


async def _authenticated_dependency() -> AuthenticatedSession:
    return _authenticated_session()


def _service(repository=None) -> GovernanceService:
    return GovernanceService(
        repository or InMemoryGovernanceRepository(),
        defaults=load_workspace_defaults(ROOT / "knowledge"),
    )


def test_workspace_defaults_are_data_driven() -> None:
    defaults = load_workspace_defaults(ROOT / "knowledge")

    assert defaults.version == "workspace_defaults.v1"
    assert defaults.default_role_key == "owner"
    assert defaults.default_group.slug == "owners"
    assert defaults.settings["assistant"]["write_actions_require_confirmation"] is True


def test_governance_service_bootstraps_default_workspace_once() -> None:
    service = _service()
    user = _user()

    first = service.get_or_create_current_workspace(user)
    second = service.get_or_create_current_workspace(user)

    assert first.organization.organization_id == second.organization.organization_id
    assert first.membership.role_key == "owner"
    assert first.groups[0].slug == "owners"
    assert first.group_memberships[0].user_id == user.user_id
    assert first.settings.settings["data_policy"]["allow_external_llm_for_phi"] is False


def test_governance_service_deep_merges_settings_and_creates_groups() -> None:
    service = _service()
    user = _user()
    workspace = service.get_or_create_current_workspace(user)

    updated = service.update_workspace_settings(
        user=user,
        organization_id=workspace.organization.organization_id,
        patch={"review_policy": {"low_confidence_threshold": 0.7}},
    )
    grouped = service.create_group(
        user=user,
        organization_id=workspace.organization.organization_id,
        slug="Data Stewards",
        display_name="Data Stewards",
        description="Reviews data quality decisions.",
        role_keys=["data-steward", "data-steward"],
    )

    assert updated.settings.version == 2
    assert updated.settings.settings["review_policy"]["low_confidence_threshold"] == 0.7
    assert updated.settings.settings["review_policy"]["human_review_required_for_sensitive_data"]
    assert {group.slug for group in grouped.groups} == {"owners", "data-stewards"}
    data_stewards = next(group for group in grouped.groups if group.slug == "data-stewards")
    assert data_stewards.role_keys == ["data-steward"]


def test_sqlite_governance_repository_roundtrip(tmp_path: Path) -> None:
    backbone = SQLiteBackboneStore(tmp_path / "ojtflow.db", tmp_path / "var")
    auth = SQLiteAuthRepository(backbone)
    user = auth.upsert_google_user(
        GoogleIdentityProfile(
            google_sub="google-sqlite-governance",
            email="sqlite-governance@example.com",
            email_verified=True,
            display_name="SQLite Governance",
        )
    )
    service = _service(SQLiteGovernanceRepository(backbone))

    workspace = service.get_or_create_current_workspace(user)
    loaded = service.get_or_create_current_workspace(user)

    assert loaded.organization.organization_id == workspace.organization.organization_id
    assert loaded.membership.user_id == user.user_id
    assert loaded.groups[0].slug == "owners"
    assert loaded.settings.version == 1


@pytest.mark.asyncio
async def test_governance_api_current_settings_and_group_roundtrip() -> None:
    app = create_app()
    service = _service()
    app.dependency_overrides[require_authentication] = _authenticated_dependency
    app.dependency_overrides[get_governance_service] = lambda: service

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        current_response = await client.get("/api/v1/organizations/current")
        current = current_response.json()["data"]
        organization_id = current["organization"]["organization_id"]

        settings_response = await client.patch(
            f"/api/v1/organizations/{organization_id}/settings",
            json={"settings": {"assistant": {"memory_enabled": False}}},
        )
        group_response = await client.post(
            f"/api/v1/organizations/{organization_id}/groups",
            json={
                "slug": "reviewers",
                "display_name": "Reviewers",
                "description": "Human reviewers",
                "role_keys": ["reviewer"],
            },
        )

    assert current_response.status_code == 200
    assert current["membership"]["role_key"] == "owner"
    assert settings_response.status_code == 200
    assert settings_response.json()["data"]["settings"]["settings"]["assistant"][
        "memory_enabled"
    ] is False
    assert group_response.status_code == 200
    assert {group["slug"] for group in group_response.json()["data"]["groups"]} == {
        "owners",
        "reviewers",
    }
