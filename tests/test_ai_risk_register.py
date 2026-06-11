from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from ojtflow.config import clear_settings_cache
from ojtflow.core.contracts.auth import AuthenticatedSession, SessionRecord, UserRecord
from ojtflow.infrastructure.ai_risk_register import load_ai_risk_register
from ojtflow.interfaces.api.app import create_app
from ojtflow.interfaces.api.deps import get_governance_service, require_authentication


ROOT = Path(__file__).resolve().parents[1]


def test_ai_risk_register_covers_nist_functions_and_required_governance_fields() -> None:
    register = load_ai_risk_register(
        ROOT / "knowledge/governance/ai_risk_register.json"
    )

    assert register.version == "ai_risk_register.v1"
    assert "NIST AI RMF 1.0" in " ".join(register.standard_refs)
    assert register.intended_system_use
    assert register.prohibited_uses
    assert register.risks
    covered_functions = {
        function
        for risk in register.risks
        for function in risk.nist_ai_rmf_functions
    }
    assert covered_functions == {"GOVERN", "MAP", "MEASURE", "MANAGE"}
    assert all(risk.intended_use for risk in register.risks)
    assert all(risk.limitation for risk in register.risks)
    assert all(risk.monitoring_signals for risk in register.risks)
    assert all(risk.human_oversight for risk in register.risks)
    assert all(risk.controls for risk in register.risks)


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
        user_id="usr_ai_risk",
        google_sub="google-usr_ai_risk",
        email="risk@example.com",
        email_verified=True,
        display_name="Risk Admin",
        avatar_url=None,
        created_at=now,
        updated_at=now,
        last_login_at=now,
    )
    return AuthenticatedSession(
        user=user,
        session=SessionRecord(
            session_id="ses_ai_risk",
            user_id=user.user_id,
            token_hash="hash",
            created_at=now,
            expires_at=now,
            revoked_at=None,
            last_seen_at=now,
        ),
    )


@pytest.mark.asyncio
async def test_ai_risk_register_api_returns_admin_visible_governance_register(
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
        response = await client.get("/api/v1/runtime/ai-risk-register")

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    register = body["data"]
    assert register["version"] == "ai_risk_register.v1"
    assert register["intended_system_use"]
    assert register["prohibited_uses"]
    assert register["risks"][0]["monitoring_signals"]
    assert register["risks"][0]["human_oversight"]
    assert governance.permission_scopes == ["admin:read"]
    clear_settings_cache()
