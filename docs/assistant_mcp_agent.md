# Assistant And MCP Tool Layer

OJTFlow now has a natural-language operator layer for users who should not need
to navigate every workflow, retrieval, validation, and review screen manually.
The layer is intentionally thin: it plans tool calls, executes only allowlisted
backend tools, and returns structured results that point back to existing
workflow/retrieval artifacts.

## Research Basis

- The official MCP Python SDK exposes tools, resources, prompts, and standard
  transports such as stdio, SSE, and Streamable HTTP through FastMCP.
- OpenAI Responses API supports function/tool calling and remote MCP tooling.
  OJTFlow uses the same pattern internally: a model may propose tool calls, but
  application code executes them.
- OpenAI Agents guidance recommends server-owned orchestration when the
  application owns tools, approvals, and state. OJTFlow keeps orchestration in
  application services rather than letting model output mutate storage directly.
- MCP security guidance treats authorization and tool scoping as part of the
  server boundary. OJTFlow starts with a small allowlist and explicit write
  gates.

## Architecture

```text
User/API/MCP client
  -> AssistantService
      -> deterministic planner or OpenAIResponsesPlanner
      -> OJTFlowToolExecutor
          -> WorkflowService
          -> MedicalEvidenceService
          -> RetrievalService
```

The LLM is optional. `OJT_LLM_PROVIDER=disabled` keeps local behavior
deterministic and token-free. `OJT_LLM_PROVIDER=openai` asks the OpenAI
Responses API for a strict JSON tool plan using `OJT_LLM_PLANNING_MODEL` and
then synthesizes the final answer with `OJT_LLM_SYNTHESIS_MODEL`. Both default
to the backwards-compatible `OJT_LLM_MODEL` value. `OJT_LLM_VISION_MODEL`
controls OpenAI-compatible OCR/vision extraction for image-heavy uploads.

Operators can change non-secret planner, synthesis, vision, timeout, and
OpenAI-compatible endpoint settings from Settings -> Assistant runtime or with
`PUT /api/v1/runtime/assistant-settings`. Embedding provider/model/dimension
settings live under Settings -> Retrieval runtime because they require retrieval
reindexing. Runtime changes are stored in `OJT_RUNTIME_SETTINGS_PATH`, reload
cached services, and do not expose or accept API keys. Secrets stay in
environment/config management.

Tool execution remains deterministic:

- Unknown tool names are skipped.
- OpenAI planner output is constrained to the configured backend tool names.
- Planner-visible tool schemas set `additionalProperties=false`, require all
  declared fields, and represent optional inputs as nullable values so OpenAI
  strict structured outputs do not silently omit tool arguments.
- Tool arguments are normalized by backend code.
- Workflow ownership is enforced by the API route through authenticated user ID.
- `start_workflow` requires `execute_write_actions=true`.
- The browser Assistant must also require a one-use confirmation before sending
  `execute_write_actions=true`, using the backend tool catalog to list
  write-gated tools and approval reasons.
- Review approval/rejection tools are not exposed in v0.
- Assistant memory is limited to data-driven, policy-allowlisted operational
  preferences from `knowledge/assistant/memory_policy.json`. The API injects
  these preferences into chat planning and removes caller-provided
  `assistant_memory` context first. It must never persist raw PHI, uploaded
  content, patient identifiers, or clinical facts as memory.

## API Entry Point

`GET /api/v1/assistant/tools` returns the same server allowlist used by chat
and MCP wrappers. UI clients should use it to show available tools, permission
scope, approval requirements, and input schemas instead of hardcoding a tool
catalog.

`GET /api/v1/assistant/examples` returns starter tasks loaded from
`knowledge/assistant/examples.json`. These are visible examples, not hidden
runtime defaults: the Assistant form starts empty, and selecting an example
only fills the message/context fields for the user to edit before execution.
Do not bury demo payloads in React state or backend control flow.

`GET /api/v1/assistant/answer-templates` returns governed answer structures
loaded from `knowledge/assistant/answer_templates.json`.

`GET /api/v1/assistant/mcp/resources` returns the MCP resource catalog loaded
from `knowledge/assistant/mcp_resources.json`.

`GET /api/v1/assistant/mcp/prompts` returns the MCP prompt catalog loaded from
`knowledge/assistant/mcp_prompts.json`.

`GET /api/v1/assistant/sessions`

`POST /api/v1/assistant/sessions`

`GET /api/v1/assistant/sessions/{session_id}`

`PATCH /api/v1/assistant/sessions/{session_id}`

`POST /api/v1/assistant/sessions/{session_id}/archive`

`DELETE /api/v1/assistant/sessions/{session_id}`

`POST /api/v1/assistant/sessions/{session_id}/messages`

Assistant sessions are persisted through the same storage backend as workflows:
memory for tests, SQLite for local single-file development, and Postgres for
production-like Docker/runtime deployments. Sessions are scoped by authenticated
user ID. A session stores title, archive state, message count, timestamps, and
ordered messages. Messages store role (`user`, `assistant`, `system`, or
`tool`), content, explicit `workflow_refs`, and a structured payload for tool
calls, stream events, context snapshots, or final assistant responses. The
service also extracts common workflow reference fields from nested payloads as a
fallback, so tool outputs that include `workflow_id` become linkable in chat
history. The API returns sanitized session/message contracts only; it does not
expose session tokens or auth material.

Sessions created with the placeholder title `New chat` are renamed by the
backend when the first user message is appended. Generated titles are
operational summaries such as validation, evidence search, workflow inspection,
conversion, or FHIR profiling; they avoid copying raw uploaded data, patient
identifiers, SSNs, emails, or file content into the chat rail.

Session listing accepts `q` to search session titles and persisted message
content server-side within the authenticated user's boundary. The browser
sidebar uses this query instead of relying on browser-only history.

`POST /api/v1/assistant/chat`

`POST /api/v1/assistant/chat/stream`

The browser Assistant uses the streaming route. It sends the same request
payload as `/assistant/chat`, then receives server-sent events for planning,
tool start, data-driven `tool_progress` stages, tool completion, warnings,
answer synthesis, answer text deltas, and the final `AssistantResponse`.
Progress stage copy lives in `knowledge/assistant/tool_progress_policies.json`
and is also exposed through the MCP resource catalog as
`ojtflow://assistant/tool-progress-policies`. Mid-stream failures are emitted
as structured `error` events because the HTTP status may already be committed.
Client disconnects and explicit stop actions are persisted as stream replay
status `cancelled` with a cancellation event when the backend can record it;
they are not reported as successful completions.
In OpenAI mode, synthesis calls the OpenAI Responses API with `stream: true`
and forwards `response.output_text.delta` chunks to the UI so users see the
answer as it is generated.

Failed tool recovery is carried through `context.assistant_recovery`. A
`retry_tool` action includes the original `tool_name` and `arguments`, and the
backend bypasses LLM planning to execute that exact allowlisted tool call
through the normal permission gates. A `continue_after_failure` action records
the failed tool summaries and returns a deterministic continuation without
executing another backend tool, so unresolved failures remain visible instead
of being silently treated as fixed.

```json
{
  "message": "Validate this lab CSV and explain the issues with trusted evidence.",
  "context": {
    "data": "date,patient_id,lab_name,value,unit\n2026/01/02,P002,HbA1c,,\n",
    "input_format": "csv",
    "schema_id": "lab_result_v1",
    "fields": ["date", "patient_id", "lab_name", "value", "unit"],
    "clinical_domain": "laboratory"
  },
  "execute_write_actions": false
}
```

The response includes mode (`deterministic` or `llm`), model, synthesized
operator findings, compact evidence summaries, raw tool calls, suggestions, and
warnings. Feature clients should render `findings` and `evidence_summary`
first, then expose raw tool output only as supporting detail.
When evidence comes from retrieval hits, `evidence_summary[].match_explanation`
preserves the backend per-hit audit object so chat and MCP clients can show why
the evidence matched without parsing the full retrieval package.
When a retrieval tool returns backend `interpretation`, the Assistant surfaces
it as a `Retrieval interpretation` finding and includes it in model context for
OpenAI synthesis. This keeps chat explanations aligned with the Retrieval page:
status, top evidence/source IDs, score driver, support status, bucket coverage,
warnings, and next action come from the backend retrieval package rather than
browser-only wording.
When a retrieval tool returns backend `recommended_actions[]`, the Assistant
surfaces the top actions as `findings` with title `Recommended search action`
and as concise `suggestions`. This lets chat users see corrective retrieval
steps such as applying a policy/schema filter or broadening the query without
opening raw retrieval JSON.
When a retrieval tool returns backend `remediation_summary`, the Assistant also
surfaces it as a `Retrieval remediation` finding and a `Next retrieval step`
suggestion. When backend `interpretation.next_action_*` is present, that
interpretation action is shown before the remediation fallback. This keeps chat,
MCP, and Retrieval UI behavior aligned around the same backend-owned next step.
For direct retrieval-only deterministic
answers, the top-level assistant message also prefers that remediation summary,
so the first visible sentence tells the user what to do next instead of only
reporting that evidence was retrieved. Validation-first answers continue to lead
with validation findings.

When `OJT_LLM_PROVIDER=openai`, the Assistant performs two model-backed steps:
first it asks OpenAI for a structured tool plan, then it executes backend-owned
tools, then it asks OpenAI to synthesize the final user-facing answer from a
compact tool-result digest. The synthesis prompt forbids invented evidence,
workflow IDs, clinical codes, diagnoses, treatment advice, or write execution
claims. Source-backed claims should cite returned source IDs such as
`[terminology:ucum]`. The backend redacts raw `context.data` before synthesis;
tool outputs and evidence summaries are still sent so the model can explain the
actual operation result. `AssistantResponse.mode` reports planning mode and
`AssistantResponse.synthesis_mode` reports whether the final answer was LLM or
deterministic fallback.

The Assistant UI is intended for end users who know the data task but not the
backend route names. It should present outcome-oriented starters loaded from the
assistant example registry, such as checking uploaded data, finding medical
standards, and reviewing pending work.
Unsupported small talk or non-operational text must not silently run retrieval;
the deterministic planner returns no tool calls and a warning telling the user
which governed OJTFlow operations are supported. This prevents random text from
appearing as a completed clinical evidence operation.

## MCP Entry Point

Install:

```bash
pip install -e '.[mcp]'
```

Run:

```bash
PYTHONPATH=src python -m ojtflow.mcp_servers.ojtflow_tools
```

Exposed MCP tools:

- `assistant_chat`
- `retrieval_search`
  - returns the full retrieval package, including `recommended_actions[]` and
    `recommended_action_summary`, plus `remediation_summary`
  - accepts governed source scope: `clinical_domain`, `standard_system`,
    `source_type`, `source_id`, and `trust_level`
- `validate_data`
- `validate_with_evidence`
- `convert_data`
- `fhir_profile`
- `list_workflows`
- `list_reviews`
- `get_workflow`
- `workflow_summary`
- `start_workflow`
- `create_review_task`

Use `assistant_chat` for the normal operator path. Use the lower-level tools
when an automation client already knows the exact backend operation it needs.
`validate_with_evidence` is the primary healthcare data quality tool: it runs
validation and retrieval together so the response includes both issues and
standards evidence. It accepts the same governed source scope as
`retrieval_search`; use `source_id` when the user asks for evidence from one
exact approved source such as a specific FHIR profile, schema, guideline, or
terminology entry. `workflow_summary` is the primary workflow inspection tool
for chat clients. `create_review_task` creates durable workflow/review state
for unresolved data quality, terminology, evidence, or workflow decisions and
is write-gated through the same approval controls as other write actions.

Exposed MCP resources are registered from `knowledge/assistant/mcp_resources.json`.
The v0 catalog includes read-only resources for the Assistant tool catalog,
answer templates, starter examples, retrieval strategy catalog, source trust
policies, retrieval presets, retrieval search options, recent workflows,
pending reviews, schema catalog, and knowledge source inventory. Unknown
provider keys fail server creation.

Exposed MCP prompts are registered from `knowledge/assistant/mcp_prompts.json`.
The v0 catalog includes standard tasks for validating lab CSV with evidence,
profiling FHIR-like JSON, finding UCUM/unit evidence, inspecting pending
reviews, summarizing a workflow, and preparing export review. Prompts do not
grant execution authority; tool calls still run through the allowlisted backend
executor and write gates.

Retrieval tool outputs include `support_matrix` and copy the same object into
`handoff_context.support_matrix`. Assistant and MCP clients should use it for
source-backed answer claims instead of inferring support from free text.

The MCP server is for trusted local/operator use in v0. For remote enterprise
deployment, add OAuth/resource-indicator authorization, per-user tool scoping,
rate limits, and audit correlation IDs before exposing it outside the local
runtime.

## Extension Path

1. Add retention settings and admin export for persisted sessions.
2. Add tool-call audit events for assistant and MCP invocations.
3. Add remote MCP authorization and per-user owner scoping.
4. Add eval fixtures for natural-language commands and tool selection quality.
