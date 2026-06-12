"""Runtime settings history and rollback support."""

from __future__ import annotations

from ojtflow.config import (
    Settings,
    RuntimeSettingsPayload,
    load_runtime_settings_overrides,
    replace_runtime_settings_overrides,
    runtime_settings_history_path,
)
from ojtflow.core.contracts.runtime import (
    RuntimeSettingChange,
    RuntimeSettingHistoryEntry,
    RuntimeSettingSurface,
)
from ojtflow.core.errors import NotFoundError


def append_runtime_setting_history(
    *,
    settings: Settings,
    surface: RuntimeSettingSurface,
    actor_id: str,
    actor_email: str | None,
    reason: str | None,
    before: RuntimeSettingsPayload,
    after: RuntimeSettingsPayload,
    keys: set[str],
    rollback_of: str | None = None,
) -> RuntimeSettingHistoryEntry | None:
    """Append a history entry for changed runtime setting keys."""

    changes = [
        RuntimeSettingChange(
            key=key,
            old_value_present=key in before,
            old_value=before.get(key),
            new_value_present=key in after,
            new_value=after.get(key),
        )
        for key in sorted(keys)
        if before.get(key) != after.get(key) or (key in before) != (key in after)
    ]
    if not changes:
        return None

    entry = RuntimeSettingHistoryEntry(
        surface=surface,
        actor_id=actor_id,
        actor_email=actor_email,
        reason=_clean_reason(reason),
        rollback_of=rollback_of,
        changes=changes,
    )
    path = runtime_settings_history_path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(entry.model_dump_json() + "\n")
    return entry


def list_runtime_setting_history(
    settings: Settings,
    *,
    limit: int = 100,
) -> list[RuntimeSettingHistoryEntry]:
    """Return most recent runtime setting history entries."""

    path = runtime_settings_history_path(settings)
    if not path.exists():
        return []
    entries: list[RuntimeSettingHistoryEntry] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entries.append(RuntimeSettingHistoryEntry.model_validate_json(line))
    entries.sort(key=lambda entry: (entry.changed_at, entry.change_id), reverse=True)
    return entries[: max(1, min(limit, 500))]


def rollback_runtime_settings_change(
    *,
    settings: Settings,
    change_id: str,
    actor_id: str,
    actor_email: str | None,
    reason: str | None,
) -> RuntimeSettingHistoryEntry:
    """Rollback a previous runtime setting change and record the rollback."""

    entries = list_runtime_setting_history(settings, limit=500)
    target = next((entry for entry in entries if entry.change_id == change_id), None)
    if target is None:
        raise NotFoundError(
            f"Runtime setting history entry not found: {change_id}",
            details={"change_id": change_id},
        )

    before = load_runtime_settings_overrides(settings)
    rolled_back = dict(before)
    rollback_keys: set[str] = set()
    for change in target.changes:
        rollback_keys.add(change.key)
        if change.old_value_present:
            rolled_back[change.key] = change.old_value
        else:
            rolled_back.pop(change.key, None)

    replace_runtime_settings_overrides(settings, rolled_back)
    after = load_runtime_settings_overrides(settings)
    rollback_entry = append_runtime_setting_history(
        settings=settings,
        surface="rollback",
        actor_id=actor_id,
        actor_email=actor_email,
        reason=reason or f"Rollback runtime settings change {change_id}.",
        before=before,
        after=after,
        keys=rollback_keys,
        rollback_of=change_id,
    )
    if rollback_entry is None:
        raise NotFoundError(
            f"Runtime setting history entry already matches current settings: {change_id}",
            details={"change_id": change_id},
        )
    return rollback_entry


def _clean_reason(reason: str | None) -> str:
    value = (reason or "No reason supplied.").strip()
    return value[:500] or "No reason supplied."
