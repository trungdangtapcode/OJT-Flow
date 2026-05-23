# MCP Server Scaffold

The stable deterministic services should be wrapped as MCP servers after the
core contracts stop changing.

Planned servers:

- `structured-data-server`
- `schema-validation-server`
- `rag-context-server`
- `workflow-audit-server`
- `human-review-server`

Until then, the application layer calls direct Python services through ports.

