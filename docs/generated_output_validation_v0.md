# Generated Output Validation v0

F128 adds a validation boundary for LLM-generated output before it is executed,
displayed, or persisted through Assistant stream replay.

## Covered Surfaces

- `assistant_plan`: generated tool plan message, tool names, and tool rationales.
- `assistant_summary`: non-streamed LLM answer text.
- `assistant_stream_summary`: streamed LLM answer text, validated cumulatively
  before each delta is emitted.
- `export_description`: generated export labels/descriptions for future export
  workflows. Current artifact/workflow exports are rule-based, but the policy
  helper is available before LLM-authored export descriptions are introduced.

## Behavior

- Assistant plans are already parsed into `AssistantPlan`; F128 adds a second
  output-validation pass that rejects prompt-injection text in generated plan
  messages/rationales and unknown tool names outside the backend allowlist.
- If an LLM plan fails validation, Assistant returns a structured error and
  does not execute a substitute plan.
- If an LLM answer fails validation, Assistant returns a structured error and
  does not substitute local answer text.
- Streaming synthesis validates the cumulative generated answer before emitting
  each delta. If validation blocks, the unsafe delta is not emitted and the
  request fails with a structured validation error.

## Contract

`GeneratedOutputValidationResult` includes:

- `surface`
- `status`: `passed`, `warning`, or `blocked`
- `issue_count`
- `issues[]` with code, severity, message, optional field, and source ref
- `policy_version`

## Verification

Run:

```bash
OJT_STORAGE_BACKEND=memory PYTHONPATH=src pytest -q tests/test_assistant_safety.py
```
