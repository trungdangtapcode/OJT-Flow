from pathlib import Path

from ojtflow.application.runtime_settings_history import (
    append_runtime_setting_history,
    list_runtime_setting_history,
    rollback_runtime_settings_change,
)
from ojtflow.config import (
    clear_settings_cache,
    get_settings,
    load_runtime_settings_overrides,
    save_runtime_assistant_settings,
)


def test_runtime_setting_history_records_and_rolls_back_changes(
    monkeypatch,
    tmp_path: Path,
) -> None:
    runtime_path = tmp_path / "runtime_settings.json"
    monkeypatch.setenv("OJT_RUNTIME_SETTINGS_PATH", str(runtime_path))
    clear_settings_cache()

    try:
        settings = get_settings()
        before = load_runtime_settings_overrides(settings)
        save_runtime_assistant_settings(
            settings,
            {
                "llm_provider": "openai",
                "llm_model": "gpt-4.1-mini",
            },
        )
        after = load_runtime_settings_overrides(settings)
        entry = append_runtime_setting_history(
            settings=settings,
            surface="assistant",
            actor_id="usr_settings",
            actor_email="settings@example.com",
            reason="Enable real Assistant planning for pilot validation.",
            before=before,
            after=after,
            keys={"llm_provider", "llm_model"},
        )

        assert entry is not None
        history = list_runtime_setting_history(settings)
        assert [item.change_id for item in history] == [entry.change_id]
        assert history[0].actor_id == "usr_settings"
        assert history[0].reason == "Enable real Assistant planning for pilot validation."
        assert {change.key for change in history[0].changes} == {
            "llm_provider",
            "llm_model",
        }

        rollback = rollback_runtime_settings_change(
            settings=settings,
            change_id=entry.change_id,
            actor_id="usr_settings",
            actor_email="settings@example.com",
            reason="Rollback after pilot validation.",
        )
        rolled_back = load_runtime_settings_overrides(settings)
    finally:
        clear_settings_cache()

    assert rollback.rollback_of == entry.change_id
    assert rollback.surface == "rollback"
    assert rolled_back == {}
    assert [
        item.change_id for item in list_runtime_setting_history(settings)
    ] == [rollback.change_id, entry.change_id]
