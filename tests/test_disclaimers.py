from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from ojtflow.config import clear_settings_cache
from ojtflow.core.contracts.auth import AuthenticatedSession, SessionRecord, UserRecord
from ojtflow.infrastructure.disclaimers import (
    REQUIRED_DISCLAIMER_SURFACES,
    load_disclaimer_policy,
)
from ojtflow.interfaces.api.app import create_app
from ojtflow.interfaces.api.deps import require_authentication


ROOT = Path(__file__).resolve().parents[1]


def test_disclaimer_policy_covers_user_surfaces_and_clinical_boundary() -> None:
    policy = load_disclaimer_policy(ROOT / "knowledge/governance/disclaimer_policy.json")

    assert policy.version == "disclaimer_policy.v1"
    assert [surface.surface_id for surface in policy.surfaces] == list(
        REQUIRED_DISCLAIMER_SURFACES
    )
    combined_global_text = " ".join(
        [policy.intended_use, policy.non_diagnostic_statement, policy.human_review_requirement]
    ).lower()
    assert "not a diagnostic" in combined_global_text
    assert "treatment" in combined_global_text
    assert "human review" in combined_global_text
    assert policy.prohibited_uses

    for surface in policy.surfaces:
        text = " ".join(
            [
                surface.title,
                surface.message,
                surface.human_review_text,
                surface.evidence_text,
                *surface.prohibited_uses,
            ]
        ).lower()
        assert "diagnos" in text or "clinical" in text or surface.surface_id in {
            "audit",
            "settings",
            "schemas",
            "help",
        }
        assert "review" in text
        assert surface.evidence_text


async def _authenticated_dependency() -> AuthenticatedSession:
    now = datetime.now(timezone.utc)
    user = UserRecord(
        user_id="usr_disclaimer",
        google_sub="google-usr_disclaimer",
        email="disclaimer@example.com",
        email_verified=True,
        display_name="Disclaimer User",
        avatar_url=None,
        created_at=now,
        updated_at=now,
        last_login_at=now,
    )
    return AuthenticatedSession(
        user=user,
        session=SessionRecord(
            session_id="ses_disclaimer",
            user_id=user.user_id,
            token_hash="hash",
            created_at=now,
            expires_at=now,
            revoked_at=None,
            last_seen_at=now,
        ),
    )


@pytest.mark.asyncio
async def test_disclaimer_api_returns_authenticated_product_boundary(
    monkeypatch,
) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    app = create_app()
    app.dependency_overrides[require_authentication] = _authenticated_dependency
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/runtime/disclaimers")

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    policy = body["data"]
    assert policy["version"] == "disclaimer_policy.v1"
    assert "not a diagnostic" in policy["non_diagnostic_statement"].lower()
    assert len(policy["surfaces"]) == len(REQUIRED_DISCLAIMER_SURFACES)
    assert policy["surfaces"][0]["surface_id"] == "global"
    clear_settings_cache()
