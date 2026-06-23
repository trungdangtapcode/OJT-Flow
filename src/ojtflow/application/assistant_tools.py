"""Allowlisted assistant tool execution over application services."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Callable

from ojtflow.application.medical_evidence_service import MedicalEvidenceService
from ojtflow.application.workflow_service import WorkflowService
from ojtflow.core.contracts.assistant import (
    AssistantToolPlan,
    AssistantToolResult,
    AssistantToolSpec,
)
from ojtflow.core.contracts.enums import (
    DataFormat,
    EvidenceSourceType,
    ToolPermission,
    WorkflowStatus,
)
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
        description=(
            "Profile FHIR-like JSON and emit resource/schema evidence. Use only when "
            "the submitted data is JSON with a FHIR resourceType or Bundle shape; do "
            "not use for PDF/OCR/plain text content."
        ),
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
    "generate_mapping_draft": AssistantToolSpec(
        name="generate_mapping_draft",
        description=(
            "Create a review-gated mapping and transformation draft without "
            "executing conversion."
        ),
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
                "mapping_goal": {"type": ["string", "null"]},
                "source_fields": {"type": "array", "items": {"type": "string"}},
                "target_fields": {"type": "array", "items": {"type": "string"}},
                "evidence_ids": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["instruction", "data"],
            "additionalProperties": False,
        },
    ),
    "create_review_task": AssistantToolSpec(
        name="create_review_task",
        description=(
            "Create a durable human-review task for unresolved data quality, "
            "terminology, evidence, or workflow decisions."
        ),
        permission_scope=ToolPermission.REVIEW_WRITE.value,
        requires_approval=True,
        input_schema={
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "data": {"type": ["string", "null"]},
                "input_format": {"type": ["string", "null"]},
                "schema_id": {"type": ["string", "null"]},
                "review_focus": {"type": ["string", "null"]},
                "source_workflow_id": {"type": ["string", "null"]},
                "source_turn_id": {"type": ["string", "null"]},
                "issue_kinds": {"type": "array", "items": {"type": "string"}},
                "evidence_ids": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["question"],
            "additionalProperties": False,
        },
    ),
}


def _apply_tool_permission_policies(
    specs: dict[str, AssistantToolSpec],
    policies: Mapping[str, Mapping[str, Any]],
) -> dict[str, AssistantToolSpec]:
    unknown_tools = sorted(set(policies) - set(specs))
    if unknown_tools:
        raise ValueError(
            "Assistant tool permission policy references unknown tool(s): "
            + ", ".join(unknown_tools)
        )
    merged: dict[str, AssistantToolSpec] = {}
    for name, spec in specs.items():
        policy = dict(policies.get(name) or {})
        merged[name] = spec.model_copy(update=policy)
    return merged


class OJTFlowToolExecutor:
    """Execute assistant/MCP tool calls through existing service boundaries."""

    def __init__(
        self,
        workflow_service: WorkflowService,
        medical_evidence_service: MedicalEvidenceService,
        tool_permission_policies: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> None:
        self.workflow_service = workflow_service
        self.medical_evidence_service = medical_evidence_service
        self._tool_specs = _apply_tool_permission_policies(
            ASSISTANT_TOOL_SPECS,
            tool_permission_policies or {},
        )
        self._handlers: dict[
            str,
            Callable[[dict[str, Any], str | None, str | None], dict[str, Any]],
        ] = {
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
            "generate_mapping_draft": self._generate_mapping_draft,
            "create_review_task": self._create_review_task,
        }

    @property
    def tool_specs(self) -> list[AssistantToolSpec]:
        return list(self._tool_specs.values())

    def execute(
        self,
        plan: AssistantToolPlan,
        *,
        execute_write_actions: bool = False,
        owner_user_id: str | None = None,
        request_id: str | None = None,
    ) -> AssistantToolResult:
        spec = self._tool_specs.get(plan.tool_name)
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
            output = self._handlers[plan.tool_name](
                plan.arguments,
                owner_user_id,
                request_id,
            )
            if output.get("assistant_tool_status") == "skipped":
                return AssistantToolResult(
                    tool_name=plan.tool_name,
                    status="skipped",
                    arguments=plan.arguments,
                    output=output,
                    summary=str(output.get("message") or "Tool was skipped."),
                    error=str(output.get("code") or "not_applicable"),
                    requires_approval=spec.requires_approval,
                )
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
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Execute one tool and return a JSON-ready result for MCP wrappers."""

        result = self.execute(
            AssistantToolPlan(tool_name=tool_name, arguments=arguments or {}),
            execute_write_actions=execute_write_actions,
            owner_user_id=owner_user_id,
            request_id=request_id,
        )
        return result.model_dump(mode="json")

    def _retrieval_search(
        self,
        args: dict[str, Any],
        owner_user_id: str | None,
        request_id: str | None,
    ) -> dict:
        filters = {
            key: value
            for key, value in {
                "clinical_domain": _clinical_domain_filter(args.get("clinical_domain")),
                "standard_system": _standard_system_filter(args.get("standard_system")),
                "source_type": _source_type_filter(args.get("source_type")),
                "source_id": _source_id_filter(args.get("source_id")),
                "trust_level": _trust_level_filter(args.get("trust_level")),
            }.items()
            if value
        }
        query = RetrievalQuery(
            query=_required_str(args, "query"),
            top_k=_bounded_int(args.get("top_k"), default=5, minimum=1, maximum=20),
            schema_id=_optional_str(args.get("schema_id")),
            fields=_str_list(args.get("fields")),
            filters=filters,
        )
        package = self.workflow_service.search_retrieval(
            query,
            owner_user_id=owner_user_id,
            request_id=request_id,
        )
        relaxed_filters = _relaxed_retrieval_filters(filters)
        if not package.evidence and relaxed_filters != filters:
            package = self.workflow_service.search_retrieval(
                query.model_copy(update={"filters": relaxed_filters}),
                owner_user_id=owner_user_id,
                request_id=request_id,
            )
        return package.model_dump(mode="json")

    def _validate_data(
        self,
        args: dict[str, Any],
        owner_user_id: str | None,
        request_id: str | None,
    ) -> dict:
        del owner_user_id
        del request_id
        return self.workflow_service.validate_data(
            data=_required_str(args, "data"),
            declared_format=_optional_data_format(args.get("input_format")),
            schema_id=_optional_str(args.get("schema_id")) or "lab_result_v1",
        )

    def _validate_with_evidence(
        self,
        args: dict[str, Any],
        owner_user_id: str | None,
        request_id: str | None,
    ) -> dict:
        validation = self._validate_data(args, owner_user_id, request_id)
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
                "source_type": _source_type_filter(args.get("source_type")),
                "source_id": _optional_str(args.get("source_id")),
                "trust_level": "approved",
            },
            owner_user_id,
            request_id,
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

    def _convert_data(
        self,
        args: dict[str, Any],
        owner_user_id: str | None,
        request_id: str | None,
    ) -> dict:
        del owner_user_id
        del request_id
        return self.workflow_service.convert_data(
            data=_required_str(args, "data"),
            declared_format=_optional_data_format(args.get("input_format")),
            target_format=_data_format(args.get("target_format"), default=DataFormat.JSON),
        )

    def _fhir_profile(
        self,
        args: dict[str, Any],
        owner_user_id: str | None,
        request_id: str | None,
    ) -> dict:
        del owner_user_id
        del request_id
        data = _required_str(args, "data")
        if not _looks_like_json(data):
            return _skipped_fhir_profile(
                "FHIR_PROFILE_NOT_JSON",
                "FHIR profile skipped: the submitted content is not JSON.",
                "Input is plain text, CSV, OCR text, or another non-JSON format.",
            )
        try:
            return self.medical_evidence_service.profile_fhir_like(data)
        except OJTFlowError as exc:
            if not _is_json_parse_error(exc):
                raise
            return _skipped_fhir_profile(
                "FHIR_PROFILE_INVALID_JSON",
                "FHIR profile skipped: the submitted JSON could not be parsed.",
                str(exc),
            )

    def _list_workflows(
        self,
        args: dict[str, Any],
        owner_user_id: str | None,
        request_id: str | None,
    ) -> dict:
        del request_id
        status = _optional_workflow_status(args.get("status"))
        workflows = self.workflow_service.list_workflows(
            status=status,
            limit=_bounded_int(args.get("limit"), default=10, minimum=1, maximum=100),
            owner_user_id=owner_user_id,
        )
        return {"items": [workflow.model_dump(mode="json") for workflow in workflows]}

    def _list_reviews(
        self,
        args: dict[str, Any],
        owner_user_id: str | None,
        request_id: str | None,
    ) -> dict:
        del request_id
        reviews = self.workflow_service.list_reviews(
            status=_optional_str(args.get("status")) or "pending",
            limit=_bounded_int(args.get("limit"), default=10, minimum=1, maximum=100),
            owner_user_id=owner_user_id,
        )
        return {"items": [workflow.model_dump(mode="json") for workflow in reviews]}

    def _get_workflow(
        self,
        args: dict[str, Any],
        owner_user_id: str | None,
        request_id: str | None,
    ) -> dict:
        del request_id
        workflow = self.workflow_service.get_workflow(
            _required_str(args, "workflow_id"),
            owner_user_id=owner_user_id,
        )
        return workflow.model_dump(mode="json")

    def _workflow_summary(
        self,
        args: dict[str, Any],
        owner_user_id: str | None,
        request_id: str | None,
    ) -> dict:
        workflow = self._get_workflow(args, owner_user_id, request_id)
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

    def _start_workflow(
        self,
        args: dict[str, Any],
        owner_user_id: str | None,
        request_id: str | None,
    ) -> dict:
        workflow = self.workflow_service.start_workflow(
            instruction=_required_str(args, "instruction"),
            data=_required_str(args, "data"),
            declared_format=_optional_data_format(args.get("input_format")),
            target_format=_data_format(args.get("target_format"), default=DataFormat.JSON),
            schema_id=_optional_str(args.get("schema_id")) or "lab_result_v1",
            require_human_review=bool(args.get("require_human_review", True)),
            owner_user_id=owner_user_id,
            request_id=request_id,
        )
        return workflow.model_dump(mode="json")

    def _create_review_task(
        self,
        args: dict[str, Any],
        owner_user_id: str | None,
        request_id: str | None,
    ) -> dict:
        source_context = {
            "source_workflow_id": _optional_str(args.get("source_workflow_id")),
            "source_turn_id": _optional_str(args.get("source_turn_id")),
            "review_focus": _optional_str(args.get("review_focus")),
            "issue_kinds": _str_list(args.get("issue_kinds")),
            "evidence_ids": _str_list(args.get("evidence_ids")),
        }
        workflow = self.workflow_service.create_review_task(
            question=_required_str(args, "question"),
            proposed_action={
                key: value
                for key, value in source_context.items()
                if value not in (None, "", [])
            },
            data=_optional_str(args.get("data")),
            declared_format=_optional_data_format(args.get("input_format")),
            schema_id=_optional_str(args.get("schema_id")) or "lab_result_v1",
            source_context={
                key: value
                for key, value in source_context.items()
                if value not in (None, "", [])
            },
            owner_user_id=owner_user_id,
            request_id=request_id,
        )
        payload = workflow.model_dump(mode="json")
        payload["review_task"] = {
            "workflow_id": workflow.workflow_id,
            "review_id": workflow.review.review_id if workflow.review else None,
            "question": workflow.review.question if workflow.review else None,
            "trigger": workflow.review.trigger if workflow.review else None,
        }
        return payload

    def _generate_mapping_draft(
        self,
        args: dict[str, Any],
        owner_user_id: str | None,
        request_id: str | None,
    ) -> dict:
        workflow = self.workflow_service.create_mapping_draft(
            instruction=_required_str(args, "instruction"),
            data=_required_str(args, "data"),
            declared_format=_optional_data_format(args.get("input_format")),
            target_format=_data_format(args.get("target_format"), default=DataFormat.JSON),
            schema_id=_optional_str(args.get("schema_id")) or "lab_result_v1",
            mapping_goal=_optional_str(args.get("mapping_goal")),
            source_fields=_str_list(args.get("source_fields")),
            target_fields=_str_list(args.get("target_fields")),
            evidence_ids=_str_list(args.get("evidence_ids")),
            owner_user_id=owner_user_id,
            request_id=request_id,
        )
        payload = workflow.model_dump(mode="json")
        plan = workflow.transformation_plan
        payload["mapping_draft"] = {
            "workflow_id": workflow.workflow_id,
            "review_id": workflow.review.review_id if workflow.review else None,
            "plan_id": plan.plan_id if plan else None,
            "action_count": len(plan.actions) if plan else 0,
            "target_format": plan.target_format.value if plan else None,
        }
        return payload


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


def _looks_like_json(value: str) -> bool:
    stripped = value.strip()
    if not stripped or stripped[0] not in "{[":
        return False
    try:
        json.loads(stripped)
    except json.JSONDecodeError:
        return True
    return True


def _is_json_parse_error(exc: OJTFlowError) -> bool:
    return str(exc).startswith("Invalid FHIR-like JSON:")


def _skipped_fhir_profile(code: str, message: str, issue: str) -> dict[str, Any]:
    return {
        "assistant_tool_status": "skipped",
        "code": code,
        "message": message,
        "profile": {
            "is_fhir_like": False,
            "resource_type": None,
            "resource_counts": {},
            "issues": [issue],
            "handoff_context": {
                "resource_types": [],
                "graphner_ready": False,
                "rag_query_terms": [],
            },
        },
        "evidence": [],
    }


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
    if tool_name == "generate_mapping_draft":
        draft = output.get("mapping_draft") if isinstance(output.get("mapping_draft"), dict) else {}
        return (
            f"Created mapping draft {draft.get('plan_id') or ''} "
            f"for workflow {output.get('workflow_id', '')}."
        )
    if tool_name == "create_review_task":
        review = output.get("review_task") if isinstance(output.get("review_task"), dict) else {}
        return (
            f"Created review task {review.get('review_id') or ''} "
            f"for workflow {output.get('workflow_id', '')}."
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


def _trust_level_filter(value: Any) -> str:
    normalized = (_optional_str(value) or "approved").lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "trusted": "approved",
        "trustworthy": "approved",
        "authoritative": "approved",
        "approved": "approved",
        "internal": "internal",
        "user_provided": "user_provided",
        "untrusted": "untrusted",
    }
    return aliases.get(normalized, "approved")


def _source_type_filter(value: Any) -> str | None:
    normalized = (_optional_str(value) or "").lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "data_dictionary": EvidenceSourceType.DATA_DICTIONARY.value,
        "dictionary": EvidenceSourceType.DATA_DICTIONARY.value,
        "healthcare_standard": EvidenceSourceType.HEALTHCARE_STANDARD.value,
        "healthcare_standards": EvidenceSourceType.HEALTHCARE_STANDARD.value,
        "standard": EvidenceSourceType.HEALTHCARE_STANDARD.value,
        "standards": EvidenceSourceType.HEALTHCARE_STANDARD.value,
        "schema": EvidenceSourceType.SCHEMA.value,
        "terminology": EvidenceSourceType.TERMINOLOGY_SYSTEM.value,
        "terminology_system": EvidenceSourceType.TERMINOLOGY_SYSTEM.value,
        "transformation_example": EvidenceSourceType.TRANSFORMATION_EXAMPLE.value,
        "example": EvidenceSourceType.TRANSFORMATION_EXAMPLE.value,
        "validation_report": EvidenceSourceType.VALIDATION_REPORT.value,
        "tool_output": EvidenceSourceType.TOOL_OUTPUT.value,
    }
    if normalized in aliases:
        return aliases[normalized]
    valid_values = {item.value for item in EvidenceSourceType}
    if normalized in valid_values:
        return normalized
    return None


def _clinical_domain_filter(value: Any) -> str | None:
    raw = _optional_str(value)
    if raw is None:
        return None
    lowered = raw.lower()
    if any(separator in lowered for separator in ("/", ",", ";", "|", "&")):
        return None
    normalized = lowered.replace("-", " ").replace("_", " ").strip()
    aliases = {
        "lab": "laboratory",
        "labs": "laboratory",
        "laboratory": "laboratory",
        "clinical laboratory": "laboratory",
        "laboratory medicine": "laboratory",
        "medication": "medication",
        "medications": "medication",
        "drug": "medication",
        "drugs": "medication",
        "allergy": "allergy",
        "allergies": "allergy",
        "problem list": "problem_list",
        "condition": "problem_list",
        "diagnosis": "problem_list",
        "diagnoses": "problem_list",
        "privacy": "privacy",
        "phi": "privacy",
        "literature": "literature",
        "clinical trial": "literature",
        "clinical trials": "literature",
        "analytics": "analytics",
    }
    return aliases.get(normalized)


def _standard_system_filter(value: Any) -> str | None:
    raw = _optional_str(value)
    if raw is None:
        return None
    lowered = raw.lower()
    if any(separator in lowered for separator in ("/", ",", ";", "|", "&")):
        return None
    if " and " in lowered or " or " in lowered:
        return None
    normalized = lowered.replace("-", " ").replace("_", " ").strip()
    aliases = {
        "fhir": "FHIR",
        "hl7 fhir": "FHIR",
        "hl7 fhir r4": "FHIR",
        "loinc": "LOINC",
        "ucum": "UCUM",
        "rxnorm": "RxNorm",
        "rx norm": "RxNorm",
        "snomed": "SNOMED CT",
        "snomed ct": "SNOMED CT",
        "icd10": "ICD-10-CM",
        "icd 10": "ICD-10-CM",
        "icd 10 cm": "ICD-10-CM",
        "mesh": "MeSH",
        "openfda": "openFDA",
        "clinicaltrials.gov": "ClinicalTrials.gov",
        "clinicaltrials gov": "ClinicalTrials.gov",
    }
    return aliases.get(normalized)


def _source_id_filter(value: Any) -> str | None:
    raw = _optional_str(value)
    if raw is None:
        return None
    normalized = raw.strip()
    if " " in normalized or ":" not in normalized:
        return None
    allowed_prefixes = {
        "catalog",
        "corpus",
        "dictionary",
        "example",
        "governance",
        "schema",
        "standard",
        "terminology",
    }
    prefix = normalized.split(":", 1)[0].lower()
    if prefix not in allowed_prefixes:
        return None
    return normalized


def _relaxed_retrieval_filters(filters: dict[str, str]) -> dict[str, str]:
    relaxed: dict[str, str] = {}
    if filters.get("clinical_domain"):
        relaxed["clinical_domain"] = filters["clinical_domain"]
    if filters.get("trust_level"):
        relaxed["trust_level"] = filters["trust_level"]
    return relaxed


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
    normalized_key = normalized.lower().replace("-", "_")
    # Assistant attachments carry extraction-source labels; validation needs parser formats.
    source_label_aliases = {
        "text": DataFormat.MARKDOWN,
        "txt": DataFormat.MARKDOWN,
        "plain_text": DataFormat.MARKDOWN,
        "plaintext": DataFormat.MARKDOWN,
        "document_text": DataFormat.MARKDOWN,
        "source_text": DataFormat.MARKDOWN,
        "ocr": DataFormat.MARKDOWN,
        "ocr_text": DataFormat.MARKDOWN,
        "pdf_ocr": DataFormat.MARKDOWN,
        "image_ocr": DataFormat.MARKDOWN,
        "scanned_pdf": DataFormat.MARKDOWN,
        "multi_context": DataFormat.MARKDOWN,
    }
    if normalized_key in source_label_aliases:
        return source_label_aliases[normalized_key]
    return DataFormat(normalized_key)


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
