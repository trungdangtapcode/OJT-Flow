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
                "source_type": {"type": ["string", "null"]},
                "source_id": {"type": ["string", "null"]},
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
    "validate_with_evidence": AssistantToolSpec(
        name="validate_with_evidence",
        description=(
            "Validate submitted healthcare data and retrieve trusted evidence that explains "
            "schema, unit, date, PHI, and interoperability issues."
        ),
        permission_scope=ToolPermission.DATA_VALIDATE.value,
        input_schema={
            "type": "object",
            "properties": {
                "data": {"type": "string"},
                "input_format": {"type": ["string", "null"]},
                "schema_id": {"type": ["string", "null"]},
                "fields": {"type": "array", "items": {"type": "string"}},
                "clinical_domain": {"type": ["string", "null"]},
                "standard_system": {"type": ["string", "null"]},
                "source_type": {"type": ["string", "null"]},
                "source_id": {"type": ["string", "null"]},
                "query": {"type": ["string", "null"]},
                "top_k": {"type": "integer", "minimum": 1, "maximum": 20},
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
    "workflow_summary": AssistantToolSpec(
        name="workflow_summary",
        description=(
            "Return an operator-ready workflow summary with status, step progress, "
            "issue counts, evidence counts, review state, and next actions."
        ),
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
            "validate_with_evidence": self._validate_with_evidence,
            "convert_data": self._convert_data,
            "fhir_profile": self._fhir_profile,
            "list_workflows": self._list_workflows,
            "list_reviews": self._list_reviews,
            "get_workflow": self._get_workflow,
            "workflow_summary": self._workflow_summary,
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
        missing_required = _missing_required_arguments(spec, plan.arguments)
        if missing_required:
            return AssistantToolResult(
                tool_name=plan.tool_name,
                status="skipped",
                arguments=plan.arguments,
                summary=(
                    f"{plan.tool_name} was skipped because required argument(s) "
                    f"were missing: {', '.join(missing_required)}."
                ),
                error="missing_required_arguments",
                requires_approval=spec.requires_approval,
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
                "source_type": _optional_str(args.get("source_type")),
                "source_id": _optional_str(args.get("source_id")),
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

    def _validate_with_evidence(self, args: dict[str, Any], owner_user_id: str | None) -> dict:
        validation = self._validate_data(args, owner_user_id)
        report = validation.get("validation_report") if isinstance(validation, dict) else {}
        issues = (
            report.get("issues")
            if isinstance(report, dict) and isinstance(report.get("issues"), list)
            else []
        )
        schema_id = _optional_str(args.get("schema_id")) or "lab_result_v1"
        fields = _str_list(args.get("fields")) or _fields_from_validation(validation)
        issue_kinds = _issue_kinds(issues)
        query = _optional_str(args.get("query")) or _validation_evidence_query(
            schema_id=schema_id,
            fields=fields,
            issue_kinds=issue_kinds,
        )
        retrieval = self._retrieval_search(
            {
                "query": query,
                "top_k": _bounded_int(args.get("top_k"), default=5, minimum=1, maximum=20),
                "schema_id": schema_id,
                "fields": fields,
                "clinical_domain": _optional_str(args.get("clinical_domain")) or "laboratory",
                "standard_system": _optional_str(args.get("standard_system")),
                "source_type": _optional_str(args.get("source_type")),
                "source_id": _optional_str(args.get("source_id")),
                "trust_level": "approved",
            },
            owner_user_id,
        )
        return {
            "validation": validation,
            "retrieval": retrieval,
            "summary": {
                "schema_id": schema_id,
                "issue_count": len(issues),
                "issue_kinds": issue_kinds,
                "evidence_count": len(retrieval.get("evidence") or []),
                "requires_review": (
                    bool(report.get("requires_review")) if isinstance(report, dict) else False
                ),
            },
        }

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

    def _workflow_summary(self, args: dict[str, Any], owner_user_id: str | None) -> dict:
        workflow = self._get_workflow(args, owner_user_id)
        steps = workflow.get("steps") if isinstance(workflow.get("steps"), list) else []
        validation_report = (
            workflow.get("validation_report")
            if isinstance(workflow.get("validation_report"), dict)
            else {}
        )
        evidence = (
            workflow.get("retrieved_context")
            if isinstance(workflow.get("retrieved_context"), list)
            else []
        )
        issues = (
            validation_report.get("issues")
            if isinstance(validation_report.get("issues"), list)
            else []
        )
        return {
            "workflow_id": workflow.get("workflow_id"),
            "status": workflow.get("status"),
            "instruction": workflow.get("user_instruction"),
            "owner_user_id": workflow.get("owner_user_id"),
            "review_id": (
                workflow.get("review", {}).get("review_id")
                if isinstance(workflow.get("review"), dict)
                else None
            ),
            "requires_review": workflow.get("status") == WorkflowStatus.NEEDS_HUMAN_REVIEW.value,
            "step_summary": {
                "total": len(steps),
                "completed": _count_step_status(steps, "completed"),
                "failed": _count_step_status(steps, "failed"),
                "running": _count_step_status(steps, "running"),
            },
            "issue_summary": {
                "total": len(issues),
                "by_kind": _count_dict(
                    issue.get("kind") for issue in issues if isinstance(issue, dict)
                ),
                "by_severity": _count_dict(
                    issue.get("severity") for issue in issues if isinstance(issue, dict)
                ),
            },
            "evidence_summary": {
                "total": len(evidence),
                "source_ids": [
                    str(item.get("source_id"))
                    for item in evidence[:5]
                    if isinstance(item, dict) and item.get("source_id")
                ],
            },
            "next_actions": _workflow_next_actions(workflow, len(issues), len(evidence)),
            "workflow": workflow,
        }

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


def _missing_required_arguments(
    spec: AssistantToolSpec,
    arguments: dict[str, Any],
) -> list[str]:
    required = spec.input_schema.get("required")
    if not isinstance(required, list):
        return []
    missing: list[str] = []
    for key in required:
        if not isinstance(key, str):
            continue
        value = arguments.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(key)
    return missing


def _tool_summary(tool_name: str, output: dict[str, Any]) -> str:
    if tool_name == "retrieval_search":
        evidence_count = len(output.get("evidence") or [])
        strategy = ((output.get("trace") or {}).get("strategy")) or "retrieval"
        return f"Retrieved {evidence_count} evidence item(s) with {strategy}."
    if tool_name == "validate_data":
        issues = ((output.get("validation_report") or {}).get("issues")) or []
        return f"Validation completed with {len(issues)} issue(s)."
    if tool_name == "validate_with_evidence":
        summary = output.get("summary") if isinstance(output.get("summary"), dict) else {}
        return (
            f"Validation plus evidence completed with {summary.get('issue_count', 0)} "
            f"issue(s) and {summary.get('evidence_count', 0)} evidence item(s)."
        )
    if tool_name == "convert_data":
        return f"Converted input to {output.get('output_format', 'requested format')}."
    if tool_name == "fhir_profile":
        profile = output.get("profile") if isinstance(output.get("profile"), dict) else {}
        resource_type = output.get("resource_type") or profile.get("resource_type")
        return f"FHIR-like profile completed for {resource_type or 'submitted data'}."
    if tool_name in {"list_workflows", "list_reviews"}:
        return f"Returned {len(output.get('items') or [])} item(s)."
    if tool_name == "get_workflow":
        return f"Loaded workflow {output.get('workflow_id', '')}."
    if tool_name == "workflow_summary":
        return (
            f"Summarized workflow {output.get('workflow_id', '')} "
            f"with status {output.get('status', 'unknown')}."
        )
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


def _fields_from_validation(validation: dict[str, Any]) -> list[str]:
    profile = validation.get("profile") if isinstance(validation.get("profile"), dict) else {}
    fields = profile.get("fields")
    if isinstance(fields, list):
        return [str(field) for field in fields if str(field).strip()]
    return []


def _issue_kinds(issues: list[Any]) -> list[str]:
    kinds: list[str] = []
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        kind = issue.get("kind")
        if isinstance(kind, str) and kind.strip() and kind not in kinds:
            kinds.append(kind.strip())
    return kinds


def _validation_evidence_query(
    *,
    schema_id: str,
    fields: list[str],
    issue_kinds: list[str],
) -> str:
    parts = [
        "healthcare data validation evidence",
        schema_id,
        "FHIR Observation",
        "LOINC UCUM ISO date patient identifier",
    ]
    if fields:
        parts.append("fields " + " ".join(fields[:8]))
    if issue_kinds:
        parts.append("issues " + " ".join(issue_kinds[:8]))
    return " ".join(parts)


def _count_step_status(steps: list[Any], status: str) -> int:
    return sum(
        1
        for step in steps
        if isinstance(step, dict) and str(step.get("status") or "").lower() == status
    )


def _count_dict(values) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        if not value:
            continue
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _workflow_next_actions(
    workflow: dict[str, Any],
    issue_count: int,
    evidence_count: int,
) -> list[str]:
    actions: list[str] = []
    if workflow.get("status") == WorkflowStatus.NEEDS_HUMAN_REVIEW.value:
        actions.append("Review and approve, edit, reject, or clarify the gated workflow.")
    if issue_count:
        actions.append("Inspect validation issues before using transformed output.")
    if evidence_count:
        actions.append("Open retrieval evidence to confirm standards and limitations.")
    if not actions:
        actions.append("Workflow is ready for downstream inspection.")
    return actions
