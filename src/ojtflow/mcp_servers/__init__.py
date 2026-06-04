"""OJTFlow MCP servers.

Each server wraps a deterministic service layer and exposes it as
a set of MCP tools, resources, and prompts for AI agent consumption.

Servers
-------
structured_data_server   - detect, parse, convert (JSON/YAML/CSV)
schema_validation_server - profile, validate, schema registry
rag_context_server       - knowledge retrieval and evidence search
workflow_audit_server    - workflow history, events, audit trail
human_review_server      - pending review context and briefings

Usage (stdio transport, for Claude Code):
    python -m ojtflow.mcp_servers.structured_data_server
    python -m ojtflow.mcp_servers.schema_validation_server
    python -m ojtflow.mcp_servers.rag_context_server
    python -m ojtflow.mcp_servers.workflow_audit_server
    python -m ojtflow.mcp_servers.human_review_server
"""
