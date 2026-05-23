"""Deterministic tool registry metadata before MCP wrapping."""

from __future__ import annotations

from ojtflow.core.contracts.enums import ToolPermission
from ojtflow.core.contracts.tools import ToolSpec


TOOL_SPECS: list[ToolSpec] = [
    ToolSpec(
        name="detect_format",
        input_model="FormatDetectionInput",
        output_model="FormatDetection",
        permission_scope=ToolPermission.DATA_READ,
        allowed_agents=["parser_agent"],
    ),
    ToolSpec(
        name="parse_data",
        input_model="ParseDataInput",
        output_model="ParsedData",
        permission_scope=ToolPermission.DATA_READ,
        allowed_agents=["parser_agent"],
    ),
    ToolSpec(
        name="profile_data",
        input_model="ParsedData",
        output_model="DataProfile",
        permission_scope=ToolPermission.DATA_PROFILE,
        allowed_agents=["parser_agent"],
    ),
    ToolSpec(
        name="validate_schema",
        input_model="ParsedData + DataProfile + Schema",
        output_model="ValidationReport",
        permission_scope=ToolPermission.DATA_VALIDATE,
        allowed_agents=["validation_agent"],
    ),
    ToolSpec(
        name="convert_data",
        input_model="ParsedData + TransformationPlan",
        output_model="TransformationOutput",
        permission_scope=ToolPermission.DATA_TRANSFORM,
        allowed_agents=["transformation_agent"],
        requires_approval=True,
    ),
]


def tool_specs_json() -> list[dict]:
    """Return JSON-ready tool metadata for handoff contexts."""

    return [spec.model_dump(mode="json") for spec in TOOL_SPECS]

