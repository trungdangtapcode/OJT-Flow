# MCP Resources And Prompts v0

## Purpose

OJTFlow exposes MCP resources and prompts from trusted data instead of hidden
Python-only definitions.

Catalogs:

- `knowledge/assistant/mcp_resources.json`
- `knowledge/assistant/mcp_prompts.json`
- `knowledge/assistant/remote_mcp_deployment_policy.json`

API:

- `GET /api/v1/assistant/mcp/resources`
- `GET /api/v1/assistant/mcp/prompts`
- `GET /api/v1/assistant/mcp/remote-policy`

Local MCP server:

```bash
PYTHONPATH=src python -m ojtflow.mcp_servers.ojtflow_tools
```

## Resource Catalog

Resources expose read-only operational context such as:

- Assistant tool allowlist
- Assistant answer templates
- Assistant starter examples
- Remote MCP deployment policy
- Retrieval strategy catalog
- Source trust policies
- Retrieval search presets
- Retrieval search options
- Recent workflow queue
- Pending review queue
- Schema catalog
- Knowledge source inventory

Each resource declares URI, title, description, provider key, permission scope,
tags, and roadmap references. Unknown provider keys fail server creation so a
catalog typo cannot silently publish an empty resource.

## Prompt Catalog

Prompts cover standard healthcare data tasks:

- validate lab CSV with trusted evidence
- profile FHIR-like resource
- find UCUM/unit evidence
- inspect pending reviews
- summarize workflow
- prepare export review

Prompts are templates with declared arguments, recommended backend tools,
evidence requirements, write-action policy, tags, and roadmap references.

The local MCP server registers these prompts at startup. Prompt rendering uses
explicit placeholder substitution for declared arguments only.

## Remote MCP Policy

Remote MCP is blocked by policy in v0. The remote policy resource states the
required OAuth protected-resource metadata, resource indicator, per-user
scoping, rate-limit, audit, and tool-manifest controls that must pass before a
streamable HTTP/SSE MCP endpoint is exposed outside trusted local operation.

## Security Boundary

These catalogs do not grant tool execution authority by themselves. Tool
execution still goes through `OJTFlowToolExecutor`, the allowlisted tool
registry, per-tool permission metadata, and write gates.

## Verification

Run:

```bash
python -m pytest tests/test_api.py::test_assistant_mcp_catalog_endpoints_return_data_driven_contracts -q
python -m pytest tests/test_mcp_remote_policy.py -q
python -m py_compile src/ojtflow/mcp_servers/ojtflow_tools.py
```
