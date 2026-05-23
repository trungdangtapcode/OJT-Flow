"""Tool allowlists for role-scoped agent access."""

from __future__ import annotations

DEFAULT_AGENT_TOOL_ALLOWLIST: dict[str, set[str]] = {
    "parser_agent": {"detect_format", "parse_data", "profile_data"},
    "schema_agent": {"infer_schema", "compare_schema", "search_context"},
    "validation_agent": {"validate_schema", "detect_anomalies"},
    "transformation_agent": {"convert_data", "apply_transformation_plan"},
    "retrieval_agent": {"search_context"},
    "explanation_agent": {"build_explanation"},
    "safety_agent": {"scan_prompt_injection", "scan_sensitive_fields"},
    "review_agent": {"request_review", "record_review_decision"},
}


def is_tool_allowed(agent_id: str, tool_name: str) -> bool:
    """Return whether an agent may call a tool."""

    return tool_name in DEFAULT_AGENT_TOOL_ALLOWLIST.get(agent_id, set())

