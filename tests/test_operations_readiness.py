from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from ojtflow.config import clear_settings_cache
from ojtflow.core.contracts.auth import AuthenticatedSession, SessionRecord, UserRecord
from ojtflow.interfaces.api.app import create_app
from ojtflow.interfaces.api.deps import get_governance_service, require_authentication
from ojtflow.infrastructure.operations import (
    load_deployment_smoke_plan,
    load_load_smoke_plan,
    load_observability_dashboard,
    load_performance_budgets,
    load_release_gates,
)


ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_ROOT = ROOT / "knowledge"


class AllowAllGovernance:
    def require_permission(self, *, user: UserRecord, permission_scope: str) -> None:
        del user, permission_scope


async def _authenticated_dependency() -> AuthenticatedSession:
    now = datetime.now(timezone.utc)
    user = UserRecord(
        user_id="usr_ops",
        google_sub="google-usr_ops",
        email="ops@example.com",
        email_verified=True,
        display_name="Ops User",
        avatar_url=None,
        created_at=now,
        updated_at=now,
        last_login_at=now,
    )
    return AuthenticatedSession(
        user=user,
        session=SessionRecord(
            session_id="ses_ops",
            user_id=user.user_id,
            token_hash="hash",
            created_at=now,
            expires_at=now,
            revoked_at=None,
            last_seen_at=now,
        ),
    )


def test_operations_catalogs_cover_month8_release_readiness_scope() -> None:
    budgets = load_performance_budgets(KNOWLEDGE_ROOT)
    smoke_plan = load_load_smoke_plan(KNOWLEDGE_ROOT)
    dashboard = load_observability_dashboard(KNOWLEDGE_ROOT)
    gates = load_release_gates(KNOWLEDGE_ROOT)
    deployment = load_deployment_smoke_plan(KNOWLEDGE_ROOT)

    assert {metric.surface for metric in budgets.metrics} >= {
        "workflow_create",
        "retrieval_search",
        "assistant_stream",
        "upload_parse",
        "reindex",
        "runtime_readiness",
    }
    assert any(metric.percentile == "p50" for metric in budgets.metrics)
    assert any(metric.percentile == "p95" for metric in budgets.metrics)
    assert {scenario.scenario_id for scenario in smoke_plan.scenarios} >= {
        "workflow_create",
        "retrieval_search",
        "assistant_stream",
        "upload_parse",
        "reindex",
        "runtime_readiness",
    }
    assert {panel.panel_id for panel in dashboard.panels} >= {
        "api_health",
        "workflow_throughput",
        "assistant_streaming",
        "retrieval_quality",
        "background_jobs",
        "governance_security",
        "llm_cost",
    }
    assert {gate.gate_id for gate in gates.gates} >= {
        "backend_tests",
        "migration_manifest",
        "frontend_build",
        "no_raw_phi_log_scan",
        "retrieval_eval",
        "performance_smoke",
        "docker_build",
        "repo_hygiene",
        "playwright_smoke",
        "browser_e2e",
        "deployment_smoke",
    }
    assert {target.target_id for target in deployment.targets} >= {
        "frontend",
        "api_public_health",
        "api_authenticated_readiness",
    }
    assert any("OJT_SMOKE_BEARER_TOKEN" in item for item in deployment.required_env)


@pytest.mark.asyncio
async def test_operations_runtime_endpoints_return_envelopes(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    app = create_app()
    app.dependency_overrides[require_authentication] = _authenticated_dependency
    app.dependency_overrides[get_governance_service] = lambda: AllowAllGovernance()
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        budgets = await client.get("/api/v1/runtime/performance-budgets")
        smoke = await client.get("/api/v1/runtime/load-smoke-plan")
        dashboard = await client.get("/api/v1/runtime/observability-dashboard")
        gates = await client.get("/api/v1/runtime/release-gates")
        deployment = await client.get("/api/v1/runtime/deployment-smoke-plan")

    responses = [budgets, smoke, dashboard, gates, deployment]
    assert all(response.status_code == 200 for response in responses)
    assert budgets.json()["data"]["catalog_id"] == "ojtflow_performance_budgets_v0"
    assert smoke.json()["data"]["plan_id"] == "ojtflow_load_smoke_v0"
    assert dashboard.json()["data"]["dashboard_id"] == "ojtflow_observability_dashboard_v0"
    assert gates.json()["data"]["catalog_id"] == "ojtflow_release_gates_v0"
    assert deployment.json()["data"]["plan_id"] == "ojtflow_deployment_smoke_v0"


def test_ci_and_release_check_include_performance_smoke_gate() -> None:
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    release_check = (ROOT / "scripts/release-check.sh").read_text(encoding="utf-8")

    assert "Run performance smoke" in ci
    assert "scripts/performance-smoke.py --mode asgi --json" in ci
    assert "Check Postgres migration manifest" in ci
    assert "python scripts/check-migrations.py" in ci
    assert "Check repo hygiene" in ci
    assert "git diff --check" in ci
    assert "Playwright smoke" in ci
    assert "npm run e2e:smoke" in ci
    assert "Performance smoke" in release_check
    assert "scripts/performance-smoke.py\" --mode asgi" in release_check
    assert "Postgres migration manifest" in release_check
    assert "scripts/check-migrations.py" in release_check
