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
Responses API for a JSON tool plan using `OJT_LLM_MODEL` and
`OJT_OPENAI_API_KEY` or `OPENAI_API_KEY`.

Tool execution remains deterministic:

- Unknown tool names are skipped.
- Tool arguments are normalized by backend code.
- Workflow ownership is enforced by the API route through authenticated user ID.
- `start_workflow` requires `execute_write_actions=true`.
- Review approval/rejection tools are not exposed in v0.

## API Entry Point

`POST /api/v1/assistant/chat`

```json
{
  "message": "Find trusted evidence for HbA1c CSV rows with missing units.",
  "context": {
    "schema_id": "lab_result_v1",
    "fields": ["lab_name", "value", "unit"],
    "clinical_domain": "laboratory"
  },
  "execute_write_actions": false
}
```

The response includes mode (`deterministic` or `llm`), model, tool calls,
summaries, suggestions, and warnings.

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

- `retrieval_search`
- `validate_data`
- `convert_data`
- `fhir_profile`
- `list_workflows`
- `list_reviews`
- `get_workflow`
- `start_workflow`

The MCP server is for trusted local/operator use in v0. For remote enterprise
deployment, add OAuth/resource-indicator authorization, per-user tool scoping,
rate limits, and audit correlation IDs before exposing it outside the local
runtime.

## Extension Path

1. Add conversation persistence keyed by user/session.
2. Add a second LLM synthesis step over tool outputs with citation constraints.
3. Add tool-call audit events for assistant and MCP invocations.
4. Add remote MCP authorization and per-user owner scoping.
5. Add eval fixtures for natural-language commands and tool selection quality.
