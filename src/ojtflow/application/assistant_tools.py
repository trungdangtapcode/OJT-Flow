"""Allowlisted assistant tool execution over application services."""

from __future__ import annotations

from typing import Any, Callable

from ojtflow.application.medical_evidence_service import MedicalEvidenceService
from ojtflow.application.workflow_service import WorkflowService
from ojtflow.core.contracts.assistant import (
    AssistantToolPlan,
    AssistantToolResult,
    AssistantToolSpec,
)
from ojtflow.core.contracts.enums import DataFormat, ToolPermission, WorkflowStatus
from ojtflow.core.contracts.retrieval import RetrievalQuery
from ojtflow.core.errors import OJTFlowError


ASSISTANT_TOOL_SPECS: dict[str, AssistantToolSpec] = {
    "retrieval_search": AssistantToolSpec(
        name="retrieval_search",
        description="Search trusted healthcare evidence and return retrieval trace metadata.",
        permission_scope=ToolPermission.DATA_READ.value,
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "top_k": {"type": "integer", "minimum": 1, "maximum": 20},
                "schema_id": {"type": ["string", "null"]},
                "fields": {"type": "array", "items": {"type": "string"}},
                "clinical_domain": {"type": ["string", "null"]},
                "standard_system": {"type": ["string", "null"]},
                "trust_level": {"type": ["string", "null"]},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    ),
    "validate_data": AssistantToolSpec(
        name="validate_data",
        description="Parse and validate submitted JSON, YAML, CSV, or markdown text.",
        permission_scope=ToolPermission.DATA_VALIDATE.value,
        input_schema={
            "type": "object",
            "properties": {
                "data": {"type": "string"},
                "input_format": {"type": ["string", "null"]},
                "schema_id": {"type": ["string", "null"]},
            },
            "required": ["data"],
            "additionalProperties": False,
        },
    ),
    "convert_data": AssistantToolSpec(
        name="convert_data",
        description="Convert parsed JSON, YAML, CSV, or markdown text to a target format.",
        permission_scope=ToolPermission.DATA_TRANSFORM.value,
        input_schema={
            "type": "object",
            "properties": {
                "data": {"type": "string"},
                "input_format": {"type": ["string", "null"]},
                "target_format": {"type": "string"},
            },
            "required": ["data", "target_format"],
            "additionalProperties": False,
        },
    ),
    "fhir_profile": AssistantToolSpec(
        name="fhir_profile",
        description="Profile FHIR-like JSON and emit resource/schema evidence.",
        permission_scope=ToolPermission.DATA_PROFILE.value,
        input_schema={
            "type": "object",
            "properties": {"data": {"type": "string"}},
            "required": ["data"],
            "additionalProperties": False,
        },
    ),
    "list_workflows": AssistantToolSpec(
        name="list_workflows",
        description="List workflow states visible to the current user.",
        permission_scope=ToolPermission.DATA_READ.value,
        input_schema={
            "type": "object",
            "properties": {
                "status": {"type": ["string", "null"]},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100},
            },
            "additionalProperties": False,
        },
    ),
    "list_reviews": AssistantToolSpec(
        name="list_reviews",
        description="List review-gated workflows visible to the current user.",
        permission_scope=ToolPermission.DATA_READ.value,
        input_schema={
            "type": "object",
            "properties": {
                "status": {"type": ["string", "null"]},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100},
            },
            "additionalProperties": False,
        },
    ),
    "get_workflow": AssistantToolSpec(
        name="get_workflow",
        description="Inspect one workflow state by ID.",
        permission_scope=ToolPermission.DATA_READ.value,
        input_schema={
            "type": "object",
            "properties": {"workflow_id": {"type": "string"}},
            "required": ["workflow_id"],
            "additionalProperties": False,
        },
    ),
    "start_workflow": AssistantToolSpec(
        name="start_workflow",
        description="Create a governed workflow from supplied data and instruction.",
        permission_scope=ToolPermission.DATA_TRANSFORM.value,
        requires_approval=True,
        input_schema={
            "type": "object",
            "properties": {
                "instruction": {"type": "string"},
                "data": {"type": "string"},
                "input_format": {"type": ["string", "null"]},
                "target_format": {"type": "string"},
                "schema_id": {"type": ["string", "null"]},
                "require_human_review": {"type": "boolean"},
            },
            "required": ["instruction", "data"],
            "additionalProperties": False,
        },
    ),
}


class OJTFlowToolExecutor:
    """Execute assistant/MCP tool calls through existing service boundaries."""

    def __init__(
        self,
        workflow_service: WorkflowService,
        medical_evidence_service: MedicalEvidenceService,
    ) -> None:
        self.workflow_service = workflow_service
        self.medical_evidence_service = medical_evidence_service
        self._handlers: dict[str, Callable[[dict[str, Any], str | None], dict[str, Any]]] = {
            "retrieval_search": self._retrieval_search,
            "validate_data": self._validate_data,
            "convert_data": self._convert_data,
            "fhir_profile": self._fhir_profile,
            "list_workflows": self._list_workflows,
            "list_reviews": self._list_reviews,
            "get_workflow": self._get_workflow,
            "start_workflow": self._start_workflow,
        }

    @property
    def tool_specs(self) -> list[AssistantToolSpec]:
        return list(ASSISTANT_TOOL_SPECS.values())

    def execute(
        self,
        plan: AssistantToolPlan,
        *,
        execute_write_actions: bool = False,
        owner_user_id: str | None = None,
    ) -> AssistantToolResult:
        spec = ASSISTANT_TOOL_SPECS.get(plan.tool_name)
        if not spec:
            return AssistantToolResult(
                tool_name=plan.tool_name,
                status="skipped",
                arguments=plan.arguments,
                summary=f"Unknown tool was not executed: {plan.tool_name}",
                error="unknown_tool",
            )
        if spec.requires_approval and not execute_write_actions:
            return AssistantToolResult(
                tool_name=plan.tool_name,
                status="requires_approval",
                arguments=plan.arguments,
                summary=(
                    f"{plan.tool_name} is a write action. Resend with "
                    "execute_write_actions=true to run it."
                ),
                requires_approval=True,
            )

        try:
            output = self._handlers[plan.tool_name](plan.arguments, owner_user_id)
            return AssistantToolResult(
                tool_name=plan.tool_name,
                status="completed",
                arguments=plan.arguments,
                output=output,
                summary=_tool_summary(plan.tool_name, output),
                requires_approval=spec.requires_approval,
            )
        except OJTFlowError as exc:
            return AssistantToolResult(
                tool_name=plan.tool_name,
                status="failed",
                arguments=plan.arguments,
                summary=str(exc),
                error=exc.__class__.__name__,
                requires_approval=spec.requires_approval,
            )
        except Exception as exc:  # pragma: no cover - defensive boundary.
            return AssistantToolResult(
                tool_name=plan.tool_name,
                status="failed",
                arguments=plan.arguments,
                summary=str(exc),
                error=exc.__class__.__name__,
                requires_approval=spec.requires_approval,
            )

    def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        *,
        execute_write_actions: bool = False,
        owner_user_id: str | None = None,
    ) -> dict[str, Any]:
        """Execute one tool and return a JSON-ready result for MCP wrappers."""

        result = self.execute(
            AssistantToolPlan(tool_name=tool_name, arguments=arguments or {}),
            execute_write_actions=execute_write_actions,
            owner_user_id=owner_user_id,
        )
        return result.model_dump(mode="json")

    def _retrieval_search(self, args: dict[str, Any], owner_user_id: str | None) -> dict:
        filters = {
            key: value
            for key, value in {
                "clinical_domain": _optional_str(args.get("clinical_domain")),
                "standard_system": _optional_str(args.get("standard_system")),
                "trust_level": _optional_str(args.get("trust_level")) or "approved",
            }.items()
            if value
        }
        package = self.workflow_service.search_retrieval(
            RetrievalQuery(
                query=_required_str(args, "query"),
                top_k=_bounded_int(args.get("top_k"), default=5, minimum=1, maximum=20),
                schema_id=_optional_str(args.get("schema_id")),
                fields=_str_list(args.get("fields")),
                filters=filters,
            ),
            owner_user_id=owner_user_id,
        )
        return package.model_dump(mode="json")

    def _validate_data(self, args: dict[str, Any], owner_user_id: str | None) -> dict:
        del owner_user_id
        return self.workflow_service.validate_data(
            data=_required_str(args, "data"),
            declared_format=_optional_data_format(args.get("input_format")),
            schema_id=_optional_str(args.get("schema_id")) or "lab_result_v1",
        )

    def _convert_data(self, args: dict[str, Any], owner_user_id: str | None) -> dict:
        del owner_user_id
        return self.workflow_service.convert_data(
            data=_required_str(args, "data"),
            declared_format=_optional_data_format(args.get("input_format")),
            target_format=_data_format(args.get("target_format"), default=DataFormat.JSON),
        )

    def _fhir_profile(self, args: dict[str, Any], owner_user_id: str | None) -> dict:
        del owner_user_id
        return self.medical_evidence_service.profile_fhir_like(_required_str(args, "data"))

    def _list_workflows(self, args: dict[str, Any], owner_user_id: str | None) -> dict:
        status = _optional_workflow_status(args.get("status"))
        workflows = self.workflow_service.list_workflows(
            status=status,
            limit=_bounded_int(args.get("limit"), default=10, minimum=1, maximum=100),
            owner_user_id=owner_user_id,
        )
        return {"items": [workflow.model_dump(mode="json") for workflow in workflows]}

    def _list_reviews(self, args: dict[str, Any], owner_user_id: str | None) -> dict:
        reviews = self.workflow_service.list_reviews(
            status=_optional_str(args.get("status")) or "pending",
            limit=_bounded_int(args.get("limit"), default=10, minimum=1, maximum=100),
            owner_user_id=owner_user_id,
        )
        return {"items": [workflow.model_dump(mode="json") for workflow in reviews]}

    def _get_workflow(self, args: dict[str, Any], owner_user_id: str | None) -> dict:
        workflow = self.workflow_service.get_workflow(
            _required_str(args, "workflow_id"),
            owner_user_id=owner_user_id,
        )
        return workflow.model_dump(mode="json")

    def _start_workflow(self, args: dict[str, Any], owner_user_id: str | None) -> dict:
        workflow = self.workflow_service.start_workflow(
            instruction=_required_str(args, "instruction"),
            data=_required_str(args, "data"),
            declared_format=_optional_data_format(args.get("input_format")),
            target_format=_data_format(args.get("target_format"), default=DataFormat.JSON),
            schema_id=_optional_str(args.get("schema_id")) or "lab_result_v1",
            require_human_review=bool(args.get("require_human_review", True)),
            owner_user_id=owner_user_id,
        )
        return workflow.model_dump(mode="json")


def _tool_summary(tool_name: str, output: dict[str, Any]) -> str:
    if tool_name == "retrieval_search":
        evidence_count = len(output.get("evidence") or [])
        strategy = ((output.get("trace") or {}).get("strategy")) or "retrieval"
        return f"Retrieved {evidence_count} evidence item(s) with {strategy}."
    if tool_name == "validate_data":
        issues = ((output.get("validation_report") or {}).get("issues")) or []
        return f"Validation completed with {len(issues)} issue(s)."
    if tool_name == "convert_data":
        return f"Converted input to {output.get('output_format', 'requested format')}."
    if tool_name == "fhir_profile":
        resource_type = output.get("resource_type") or output.get("profile", {}).get("resource_type")
        return f"FHIR-like profile completed for {resource_type or 'submitted data'}."
    if tool_name in {"list_workflows", "list_reviews"}:
        return f"Returned {len(output.get('items') or [])} item(s)."
    if tool_name == "get_workflow":
        return f"Loaded workflow {output.get('workflow_id', '')}."
    if tool_name == "start_workflow":
        return (
            f"Created workflow {output.get('workflow_id', '')} "
            f"with status {output.get('status', 'unknown')}."
        )
    return f"{tool_name} completed."


def _required_str(args: dict[str, Any], key: str) -> str:
    value = args.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Assistant tool argument '{key}' must be a non-blank string.")
    return value


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _bounded_int(value: Any, *, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def _optional_data_format(value: Any) -> DataFormat | None:
    normalized = _optional_str(value)
    return _data_format(normalized, default=None) if normalized else None


def _data_format(value: Any, *, default: DataFormat | None) -> DataFormat:
    normalized = _optional_str(value)
    if not normalized:
        if default is None:
            raise ValueError("Data format is required.")
        return default
    return DataFormat(normalized.lower())


def _optional_workflow_status(value: Any) -> WorkflowStatus | None:
    normalized = _optional_str(value)
    return WorkflowStatus(normalized) if normalized else None
