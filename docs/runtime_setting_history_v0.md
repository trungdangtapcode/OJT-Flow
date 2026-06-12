# Runtime Setting History v0

Runtime retrieval and Assistant settings are stored as operator-managed
overrides in `OJT_RUNTIME_SETTINGS_PATH`. F132 adds an append-only JSONL history
file beside that settings file:

```text
var/runtime_settings.json
var/runtime_settings.history.jsonl
```

Each history entry records:

- `change_id`
- `changed_at`
- `surface`: `retrieval`, `assistant`, or `rollback`
- `actor_id`
- `actor_email`
- `reason`
- `rollback_of`
- `changes[]` with key, old value, old-value presence, new value, and new-value presence

## Update Flow

`PUT /api/v1/runtime/retrieval-settings` and
`PUT /api/v1/runtime/assistant-settings` accept optional `change_reason`.
The routes load current overrides, persist and validate the update, compute the
diff, append a history entry, clear cached services, and return the entry in the
response.

## Rollback Flow

`POST /api/v1/runtime/settings-history/rollback` restores the old values from a
history entry. If the original change created a new override, rollback removes
that override. The rollback itself is appended as a new history entry with
`surface="rollback"` and `rollback_of=<original change_id>`.

## Limits

This v0 history is file-backed because runtime settings are file-backed. If
runtime settings move to Postgres later, the same contract can be backed by a
database table without changing the public API shape.
