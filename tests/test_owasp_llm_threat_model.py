from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from ojtflow.config import clear_settings_cache
from ojtflow.core.contracts.auth import AuthenticatedSession, SessionRecord, UserRecord
from ojtflow.infrastructure.owasp_llm_threat_model import (
    REQUIRED_OWASP_LLM_CATEGORY_IDS,
    load_owasp_llm_threat_model,
)
from ojtflow.interfaces.api.app import create_app
from ojtflow.interfaces.api.deps import get_governance_service, require_authentication


ROOT = Path(__file__).resolve().parents[1]


def test_owasp_llm_threat_model_covers_all_categories_and_maps_controls() -> None:
    model = load_owasp_llm_threat_model(
        ROOT / "knowledge/security/owasp_llm_threat_model.json"
    )

    assert model.version == "owasp_llm_threat_model.v1"
    assert model.standard_ref == "OWASP Top 10 for LLM Applications 2025"
    assert [category.category_id for category in model.categories] == list(
        REQUIRED_OWASP_LLM_CATEGORY_IDS
    )
    assert all(category.monitoring_signals for category in model.categories)
    assert all(category.applicable_surfaces for category in model.categories)
    assert all(category.residual_risk_note for category in model.categories)

    for category in model.categories:
        implementation_refs = {
            ref for mitigation in category.mitigations for ref in mitigation.implementation_refs
        }
        test_refs = {ref for mitigation in category.mitigations for ref in mitigation.test_refs}
        assert implementation_refs
        assert test_refs
        assert all((ROOT / ref).exists() for ref in implementation_refs)
        assert all((ROOT / ref).exists() for ref in test_refs)


class _AllowingGovernanceService:
    def __init__(self) -> None:
        self.permission_scopes: list[str] = []

    def require_permission(self, *, user: UserRecord, permission_scope: str):
        del user
        self.permission_scopes.append(permission_scope)
        return None


async def _authenticated_dependency() -> AuthenticatedSession:
    now = datetime.now(timezone.utc)
    user = UserRecord(
        user_id="usr_owasp",
        google_sub="google-usr_owasp",
        email="owasp@example.com",
        email_verified=True,
        display_name="OWASP Admin",
        avatar_url=None,
        created_at=now,
        updated_at=now,
        last_login_at=now,
    )
    return AuthenticatedSession(
        user=user,
        session=SessionRecord(
            session_id="ses_owasp",
            user_id=user.user_id,
            token_hash="hash",
            created_at=now,
            expires_at=now,
            revoked_at=None,
            last_seen_at=now,
        ),
    )


@pytest.mark.asyncio
async def test_owasp_llm_threat_model_api_returns_admin_visible_model(
    monkeypatch,
) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    app = create_app()
    governance = _AllowingGovernanceService()
    app.dependency_overrides[require_authentication] = _authenticated_dependency
    app.dependency_overrides[get_governance_service] = lambda: governance
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/runtime/owasp-llm-threat-model")

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    model = body["data"]
    assert model["version"] == "owasp_llm_threat_model.v1"
    assert len(model["categories"]) == 10
    assert model["categories"][0]["category_id"] == "LLM01"
    assert model["categories"][-1]["category_id"] == "LLM10"
    assert model["categories"][0]["mitigations"][0]["implementation_refs"]
    assert model["categories"][0]["mitigations"][0]["test_refs"]
    assert governance.permission_scopes == ["admin:read"]
    clear_settings_cache()
