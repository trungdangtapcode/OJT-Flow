# Assistant Tool Permissions v0

## Purpose

Assistant tools are still allowlisted in code, but enterprise operation needs
clear permission metadata that can be shown to users and audited. OJTFlow now
loads per-tool permission policy from:

`knowledge/assistant/tool_permission_policies.json`

The code allowlist remains the execution boundary. The data file adds:

- permission tags such as `read-only`, `write-gated`, `phi-sensitive`, and
  `retrieval`
- risk level
- approval requirement override
- approval reason

## Runtime Behavior

`GET /api/v1/assistant/tools` returns each tool with:

- `permission_scope`
- `permission_tags`
- `risk_level`
- `requires_approval`
- `approval_reason`
- JSON input schema

If the policy file references an unknown tool, service construction fails fast.
This prevents stale governance metadata from silently drifting away from the
backend allowlist.

## UI Behavior

The Assistant tool catalog displays approval state, risk level, permission
scope, tags, and approval reason. This makes write-gated or PHI-sensitive
actions visible before the user asks the Assistant to run them.

## Verification

Run:

```bash
python -m pytest tests/test_api.py::test_assistant_tools_endpoint_returns_allowlist -q
```

The test verifies that `start_workflow` exposes the expected high-risk,
write-gated metadata from the data-driven policy file.
