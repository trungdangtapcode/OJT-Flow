import json

from ojtflow.config import clear_settings_cache, get_settings
from ojtflow.interfaces.api.routes.runtime import _secret_health


def test_runtime_secret_health_never_exposes_secret_values(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("OJT_GOOGLE_CLIENT_ID", "client-id-value")
    monkeypatch.setenv("OJT_GOOGLE_CLIENT_SECRET", "client-secret-value")
    monkeypatch.setenv("OJT_OPENAI_API_KEY", "sk-secret-openai-value")
    clear_settings_cache()

    try:
        settings = get_settings()
        health = _secret_health(settings)
    finally:
        clear_settings_cache()

    payload = json.dumps(health)
    assert health["secret_values_exposed"] is False
    assert "OJT_GOOGLE_CLIENT_SECRET" in payload
    assert "client-secret-value" not in payload
    assert "sk-secret-openai-value" not in payload
    assert "client-id-value" not in payload
    assert all("env_vars" in check for check in health["checks"])
