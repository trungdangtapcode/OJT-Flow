import json
from pathlib import Path

import httpx
import pytest

from ojtflow.config import clear_settings_cache
from ojtflow.interfaces.api.app import create_app
from ojtflow.interfaces.api.rate_limit import load_rate_limit_policy


ROOT = Path(__file__).resolve().parents[1]


def test_default_rate_limit_policy_covers_f134_categories() -> None:
    policy = load_rate_limit_policy(ROOT / "knowledge/security/rate_limit_policy.json")

    assert {rule.key for rule in policy.rules} >= {
        "auth_oauth",
        "auth_session_mutation",
        "assistant_chat",
        "file_upload",
        "retrieval_search",
        "retrieval_reindex",
        "external_connectors",
    }
    assert all(rule.limit > 0 and rule.window_seconds > 0 for rule in policy.rules)


@pytest.mark.asyncio
async def test_rate_limit_middleware_returns_429_envelope(monkeypatch, tmp_path: Path) -> None:
    policy_path = tmp_path / "rate_limit_policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "version": "rate_limit_policy.v1",
                "rules": [
                    {
                        "key": "test_health",
                        "description": "Test health route limit.",
                        "methods": ["GET"],
                        "path_prefixes": ["/health"],
                        "limit": 2,
                        "window_seconds": 60,
                        "scope": "ip",
                        "enabled": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("OJT_RATE_LIMIT_BACKEND", "memory")
    monkeypatch.setenv("OJT_RATE_LIMIT_POLICY_PATH", str(policy_path))
    clear_settings_cache()

    try:
        app = create_app()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            assert (await client.get("/health")).status_code == 200
            second = await client.get("/health")
            limited = await client.get("/health")
    finally:
        clear_settings_cache()

    assert second.status_code == 200
    assert second.headers["X-RateLimit-Limit"] == "2"
    assert second.headers["X-RateLimit-Remaining"] == "0"
    assert limited.status_code == 429
    assert limited.headers["Retry-After"]
    body = limited.json()
    assert body["data"] is None
    assert body["error"]["code"] == "rate_limited"
    assert body["error"]["details"]["rule_key"] == "test_health"
    assert body["error"]["details"]["limit"] == 2
