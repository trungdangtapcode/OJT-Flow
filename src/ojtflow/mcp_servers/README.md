# MCP Server Scaffold

OJTFlow exposes a local MCP server for assistant-style healthcare data
operations without forcing operators through every UI screen.

The first server wraps the same allowlisted tool executor used by
`POST /api/v1/assistant/chat`:

- `assistant_chat`
- `retrieval_search`
- `validate_data`
- `validate_with_evidence`
- `convert_data`
- `fhir_profile`
- `list_workflows`
- `list_reviews`
- `get_workflow`
- `workflow_summary`
- `start_workflow`

Use `assistant_chat` for normal natural-language operation. Use
`validate_with_evidence` when the client already has a payload and wants issues
plus standards evidence. Use `workflow_summary` when the client already has a
workflow ID and wants a compact operator view.
`retrieval_search` returns the same retrieval package contract as the API,
including `quality_summary`, `recommended_actions[]`, and
`recommended_action_summary` for corrective retrieval triage.

`start_workflow` is write-capable and returns `requires_approval` unless the
caller explicitly passes `execute_write_actions=true`. The server does not
expose review approval/rejection tools in v0.

Install and run locally:

```bash
pip install -e '.[mcp]'
PYTHONPATH=src python -m ojtflow.mcp_servers.ojtflow_tools
```

The server uses the same runtime settings as the API process, including
`OJT_STORAGE_BACKEND`, `OJT_DATABASE_URL`, `OJT_KNOWLEDGE_DIR`,
`OJT_EMBEDDING_PROVIDER`, and `OJT_OPENAI_API_KEY` when configured.

Security stance for v0:

- MCP is intended for trusted local/operator use.
- Tool execution is allowlisted and typed.
- Write actions are explicit.
- Human review decisions are not exposed as MCP tools.
- The LLM planner never receives authority to execute arbitrary functions.
