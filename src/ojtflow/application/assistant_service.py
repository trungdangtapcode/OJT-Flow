"""Natural-language assistant over OJTFlow services."""

from __future__ import annotations

import json
import re
from typing import Any

from ojtflow.application.assistant_tools import OJTFlowToolExecutor
from ojtflow.application.ports import AssistantPlanner
from ojtflow.core.contracts.assistant import (
    AssistantEvidenceSummary,
    AssistantFinding,
    AssistantPlan,
    AssistantResponse,
    AssistantToolPlan,
    AssistantToolSpec,
)


class AssistantService:
    """Plan and execute allowlisted OJTFlow tools from a user message."""

    def __init__(
        self,
        tool_executor: OJTFlowToolExecutor,
        *,
        planner: AssistantPlanner | None = None,
        max_tool_calls: int = 4,
    ) -> None:
        self.tool_executor = tool_executor
        self.planner = planner
        self.max_tool_calls = max_tool_calls

    @property
    def tool_specs(self) -> list[AssistantToolSpec]:
        """Return the backend allowlist visible to assistant and MCP clients."""

        return self.tool_executor.tool_specs

    async def chat(
        self,
        *,
        message: str,
        context: dict[str, Any] | None = None,
        execute_write_actions: bool = False,
        owner_user_id: str | None = None,
    ) -> AssistantResponse:
        """Plan a small tool sequence and execute it through the backend allowlist."""

        clean_context = context or {}
        plan = await self._plan(message=message, context=clean_context)
        tool_results = [
            self.tool_executor.execute(
                tool_call,
                execute_write_actions=execute_write_actions,
                owner_user_id=owner_user_id,
            )
            for tool_call in plan.tool_calls[: self.max_tool_calls]
        ]
        warnings = [*plan.warnings]
        if len(plan.tool_calls) > self.max_tool_calls:
            warnings.append(
                f"Assistant plan had {len(plan.tool_calls)} tool call(s); "
                f"only the first {self.max_tool_calls} were executed."
            )
        findings = _findings(tool_results)
        evidence_summary = _evidence_summary(tool_results)
        return AssistantResponse(
            message=_assistant_message(plan.message, tool_results, findings),
            mode="llm" if self.planner else "deterministic",
            model=self.planner.model_name if self.planner else None,
            findings=findings,
            evidence_summary=evidence_summary,
            tool_calls=tool_results,
            suggestions=_suggestions(tool_results),
            warnings=warnings,
        )

    async def _plan(self, *, message: str, context: dict[str, Any]) -> AssistantPlan:
        if self.planner:
            return await self.planner.plan(
                message=message,
                context=context,
                tools=self.tool_executor.tool_specs,
                max_tool_calls=self.max_tool_calls,
            )
        return _deterministic_plan(message, context)


def _deterministic_plan(message: str, context: dict[str, Any]) -> AssistantPlan:
    normalized = message.lower()
    data = _context_text(context, "data")
    schema_id = _context_optional_text(context, "schema_id")
    input_format = _context_optional_text(context, "input_format")
    target_format = _context_optional_text(context, "target_format") or "json"
    fields = context.get("fields") if isinstance(context.get("fields"), list) else []
    workflow_id = _context_optional_text(
        context,
        "workflow_id",
    ) or _workflow_id_from_message(message)

    tool_calls: list[AssistantToolPlan] = []
    if workflow_id and "workflow" in normalized and any(
        word in normalized for word in ("summary", "summarize", "explain", "inspect", "status")
    ):
        tool_calls.append(
            AssistantToolPlan(
                tool_name="workflow_summary",
                arguments={"workflow_id": workflow_id},
                rationale="The user asked for an operator-ready workflow summary.",
            )
        )
    elif "start" in normalized and "workflow" in normalized and data:
        tool_calls.append(
            AssistantToolPlan(
                tool_name="start_workflow",
                arguments={
                    "instruction": context.get("instruction") or message,
                    "data": data,
                    "input_format": input_format,
                    "target_format": target_format,
                    "schema_id": schema_id or "lab_result_v1",
                    "require_human_review": bool(context.get("require_human_review", True)),
                },
                rationale="The user asked to create a workflow and supplied data.",
            )
        )
    elif ("validate" in normalized or "check" in normalized) and data:
        validation_tool = (
            "validate_with_evidence"
            if any(
                word in normalized
                for word in ("evidence", "explain", "why", "standard", "clinical", "medical")
            )
            else "validate_data"
        )
        validation_args: dict[str, Any] = {
            "data": data,
            "input_format": input_format,
            "schema_id": schema_id or "lab_result_v1",
        }
        if validation_tool == "validate_with_evidence":
            validation_args.update(
                {
                    "fields": fields,
                    "clinical_domain": context.get("clinical_domain"),
                    "standard_system": context.get("standard_system"),
                }
            )
        tool_calls.append(
            AssistantToolPlan(
                tool_name=validation_tool,
                arguments=validation_args,
                rationale="The user asked for data validation.",
            )
        )
    elif ("convert" in normalized or "transform" in normalized) and data:
        tool_calls.append(
            AssistantToolPlan(
                tool_name="convert_data",
                arguments={
                    "data": data,
                    "input_format": input_format,
                    "target_format": target_format,
                },
                rationale="The user asked for data conversion.",
            )
        )
    elif ("fhir" in normalized or "resourcetype" in normalized) and data:
        tool_calls.append(
            AssistantToolPlan(
                tool_name="fhir_profile",
                arguments={"data": data},
                rationale="The user asked for FHIR-like profiling.",
            )
        )
    elif "review" in normalized:
        tool_calls.append(
            AssistantToolPlan(
                tool_name="list_reviews",
                arguments={"status": context.get("status") or "pending", "limit": 10},
                rationale="The user asked about human reviews.",
            )
        )
    elif workflow_id and "workflow" in normalized:
        tool_calls.append(
            AssistantToolPlan(
                tool_name="get_workflow",
                arguments={"workflow_id": workflow_id},
                rationale="The user asked to inspect a specific workflow.",
            )
        )
    elif "workflow" in normalized and any(
        word in normalized for word in ("list", "show", "recent")
    ):
        tool_calls.append(
            AssistantToolPlan(
                tool_name="list_workflows",
                arguments={"status": context.get("status"), "limit": 10},
                rationale="The user asked to inspect workflows.",
            )
        )
    else:
        tool_calls.append(
            AssistantToolPlan(
                tool_name="retrieval_search",
                arguments={
                    "query": message,
                    "top_k": int(context.get("top_k") or 5),
                    "schema_id": schema_id,
                    "fields": fields,
                    "clinical_domain": context.get("clinical_domain"),
                    "standard_system": context.get("standard_system"),
                    "trust_level": context.get("trust_level") or "approved",
                },
                rationale="Default assistant action is trusted evidence retrieval.",
            )
        )

    return AssistantPlan(
        message="I planned the safest matching OJTFlow tool action.",
        tool_calls=tool_calls,
    )


def _assistant_message(
    seed: str,
    tool_results: list,
    findings: list[AssistantFinding],
) -> str:
    action_required = [finding for finding in findings if finding.severity == "action_required"]
    if action_required:
        return action_required[0].detail
    errors = [finding for finding in findings if finding.severity == "error"]
    if errors:
        return errors[0].detail
    if findings:
        return findings[0].detail
    summaries = [result.summary for result in tool_results if result.summary]
    if summaries:
        return " ".join(summaries)
    return seed or "No tool action was required."


def _findings(tool_results: list) -> list[AssistantFinding]:
    findings: list[AssistantFinding] = []
    for result in tool_results:
        if result.status == "requires_approval":
            findings.append(
                AssistantFinding(
                    title="Write action needs confirmation",
                    detail=(
                        f"{result.tool_name} is gated. Enable write execution only when "
                        "the submitted data and intended workflow action are correct."
                    ),
                    severity="action_required",
                    source_tool=result.tool_name,
                )
            )
            continue
        if result.status == "failed":
            findings.append(
                AssistantFinding(
                    title=f"{result.tool_name} failed",
                    detail=result.summary or result.error or "Tool execution failed.",
                    severity="error",
                    source_tool=result.tool_name,
                )
            )
            continue
        if result.status != "completed":
            continue

        if result.tool_name == "retrieval_search":
            findings.extend(_retrieval_findings(result.output))
        elif result.tool_name == "validate_data":
            findings.extend(_validation_findings(result.output))
        elif result.tool_name == "validate_with_evidence":
            validation = (
                result.output.get("validation")
                if isinstance(result.output.get("validation"), dict)
                else {}
            )
            retrieval = (
                result.output.get("retrieval")
                if isinstance(result.output.get("retrieval"), dict)
                else {}
            )
            findings.extend(_validation_findings(validation))
            findings.extend(_retrieval_findings(retrieval))
        elif result.tool_name == "convert_data":
            findings.extend(_conversion_findings(result.output))
        elif result.tool_name == "fhir_profile":
            findings.extend(_fhir_findings(result.output))
        elif result.tool_name in {"list_workflows", "list_reviews"}:
            findings.append(_list_finding(result.tool_name, result.output))
        elif result.tool_name == "get_workflow":
            findings.append(_workflow_finding(result.output))
        elif result.tool_name == "workflow_summary":
            findings.append(_workflow_summary_finding(result.output))
        elif result.tool_name == "start_workflow":
            findings.append(_workflow_finding(result.output, created=True))
    return findings


def _retrieval_findings(output: dict[str, Any]) -> list[AssistantFinding]:
    evidence = _evidence_items(output)
    trace = output.get("trace") if isinstance(output.get("trace"), dict) else {}
    coverage = output.get("coverage") if isinstance(output.get("coverage"), dict) else {}
    findings = [
        AssistantFinding(
            title="Trusted evidence retrieved",
            detail=(
                f"Retrieved {len(evidence)} trusted evidence item(s) with "
                f"{trace.get('strategy') or 'the configured retrieval strategy'}."
            ),
            source_tool="retrieval_search",
            source_ids=[
                str(item.get("source_id"))
                for item in evidence[:5]
                if item.get("source_id")
            ],
        )
    ]
    for warning in coverage.get("warnings") or trace.get("warnings") or []:
        if isinstance(warning, str) and warning.strip():
            findings.append(
                AssistantFinding(
                    title="Coverage warning",
                    detail=warning,
                    severity="warning",
                    source_tool="retrieval_search",
                )
            )
    safety_flags = trace.get("safety_flags") if isinstance(trace, dict) else []
    if safety_flags:
        findings.append(
            AssistantFinding(
                title="Safety flags present",
                detail=f"Retrieval trace flagged: {', '.join(str(flag) for flag in safety_flags)}.",
                severity="warning",
                source_tool="retrieval_search",
            )
        )
    return findings


def _validation_findings(output: dict[str, Any]) -> list[AssistantFinding]:
    report = (
        output.get("validation_report")
        if isinstance(output.get("validation_report"), dict)
        else {}
    )
    issues = report.get("issues") if isinstance(report.get("issues"), list) else []
    requires_review = bool(report.get("requires_review"))
    if not issues:
        return [
            AssistantFinding(
                title="Validation passed",
                detail="Validation completed with no reported issues.",
                source_tool="validate_data",
            )
        ]
    kinds = _top_counts(issue.get("kind") for issue in issues if isinstance(issue, dict))
    return [
        AssistantFinding(
            title="Validation issues found",
            detail=(
                f"Validation found {len(issues)} issue(s)"
                f"{' and requires review' if requires_review else ''}: {kinds}."
            ),
            severity="warning" if requires_review else "info",
            source_tool="validate_data",
        )
    ]


def _conversion_findings(output: dict[str, Any]) -> list[AssistantFinding]:
    metadata = output.get("metadata") if isinstance(output.get("metadata"), dict) else {}
    output_format = output.get("output_format") or metadata.get("target_format") or "target format"
    lossy = bool(metadata.get("lossy"))
    return [
        AssistantFinding(
            title="Conversion completed",
            detail=(
                f"Converted input to {output_format}."
                f"{' The conversion has lossy warnings.' if lossy else ''}"
            ),
            severity="warning" if lossy else "info",
            source_tool="convert_data",
        )
    ]


def _fhir_findings(output: dict[str, Any]) -> list[AssistantFinding]:
    profile = output.get("profile") if isinstance(output.get("profile"), dict) else {}
    resource_type = (
        profile.get("resource_type")
        or output.get("resource_type")
        or "submitted resource"
    )
    issues = profile.get("issues") if isinstance(profile.get("issues"), list) else []
    return [
        AssistantFinding(
            title="FHIR-like profile completed",
            detail=_fhir_profile_detail(resource_type, len(issues)),
            severity="warning" if issues else "info",
            source_tool="fhir_profile",
        )
    ]


def _fhir_profile_detail(resource_type: str, issue_count: int) -> str:
    if issue_count:
        return f"Profiled {resource_type}. Found {issue_count} FHIR-like shape issue(s)."
    return f"Profiled {resource_type}."


def _list_finding(tool_name: str, output: dict[str, Any]) -> AssistantFinding:
    items = output.get("items") if isinstance(output.get("items"), list) else []
    label = "review" if tool_name == "list_reviews" else "workflow"
    return AssistantFinding(
        title=f"{label.title()} list loaded",
        detail=f"Loaded {len(items)} {label} item(s).",
        source_tool=tool_name,
    )


def _workflow_finding(output: dict[str, Any], *, created: bool = False) -> AssistantFinding:
    workflow_id = output.get("workflow_id") or "workflow"
    status = output.get("status") or "unknown"
    return AssistantFinding(
        title="Workflow created" if created else "Workflow loaded",
        detail=f"{workflow_id} is {status}.",
        severity="warning" if status == "needs_human_review" else "info",
        source_tool="start_workflow" if created else "get_workflow",
        source_ids=[str(workflow_id)],
    )


def _workflow_summary_finding(output: dict[str, Any]) -> AssistantFinding:
    workflow_id = output.get("workflow_id") or "workflow"
    status = output.get("status") or "unknown"
    issue_summary = (
        output.get("issue_summary") if isinstance(output.get("issue_summary"), dict) else {}
    )
    evidence_summary = (
        output.get("evidence_summary")
        if isinstance(output.get("evidence_summary"), dict)
        else {}
    )
    return AssistantFinding(
        title="Workflow summary ready",
        detail=(
            f"{workflow_id} is {status}. "
            f"Issues: {issue_summary.get('total', 0)}. "
            f"Evidence items: {evidence_summary.get('total', 0)}."
        ),
        severity="warning" if output.get("requires_review") else "info",
        source_tool="workflow_summary",
        source_ids=[str(workflow_id)],
    )


def _evidence_summary(tool_results: list) -> list[AssistantEvidenceSummary]:
    summaries: list[AssistantEvidenceSummary] = []
    seen: set[str] = set()
    for result in tool_results:
        for item in _evidence_items(result.output):
            evidence_id = str(item.get("evidence_id") or item.get("source_id") or "")
            if evidence_id in seen:
                continue
            seen.add(evidence_id)
            summaries.append(
                AssistantEvidenceSummary(
                    source_id=str(item.get("source_id") or "unknown"),
                    claim=str(item.get("claim") or ""),
                    trust_level=str(item.get("trust_level") or "unknown"),
                    confidence=(
                        item.get("confidence")
                        if isinstance(item.get("confidence"), (int, float))
                        else None
                    ),
                )
            )
            if len(summaries) >= 5:
                return summaries
    return summaries


def _evidence_items(output: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = output.get("evidence")
    if isinstance(evidence, list):
        return [item for item in evidence if isinstance(item, dict)]
    retrieved_context = output.get("retrieved_context")
    if isinstance(retrieved_context, list):
        return [item for item in retrieved_context if isinstance(item, dict)]
    retrieval = output.get("retrieval")
    if isinstance(retrieval, dict):
        return _evidence_items(retrieval)
    workflow = output.get("workflow")
    if isinstance(workflow, dict):
        retrieved_context = workflow.get("retrieved_context")
        if isinstance(retrieved_context, list):
            return [item for item in retrieved_context if isinstance(item, dict)]
        workflow_retrieval = workflow.get("retrieval")
        if isinstance(workflow_retrieval, dict):
            return _evidence_items(workflow_retrieval)
    return []


def _top_counts(values) -> str:
    counts: dict[str, int] = {}
    for value in values:
        if not value:
            continue
        counts[str(value)] = counts.get(str(value), 0) + 1
    if not counts:
        return "unspecified issue types"
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ", ".join(f"{name} x{count}" for name, count in ordered[:4])


def _suggestions(tool_results: list) -> list[str]:
    suggestions: list[str] = []
    for result in tool_results:
        if result.status == "requires_approval":
            suggestions.append(
                "Confirm write execution by resending with execute_write_actions=true."
            )
        if result.tool_name == "retrieval_search" and result.status == "completed":
            suggestions.append(
                "Open the retrieval trace to inspect source coverage and safety flags."
            )
        if (
            result.tool_name in {"validate_data", "validate_with_evidence"}
            and result.status == "completed"
        ):
            suggestions.append(
                "Start a governed workflow if validation issues need review-gated repair."
            )
        if result.tool_name == "workflow_summary" and result.status == "completed":
            for action in result.output.get("next_actions") or []:
                if isinstance(action, str):
                    suggestions.append(action)
    return _dedupe(suggestions)


def _context_text(context: dict[str, Any], key: str) -> str:
    value = context.get(key)
    if isinstance(value, str) and value.strip():
        return value
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return ""


def _context_optional_text(context: dict[str, Any], key: str) -> str | None:
    value = context.get(key)
    return value.strip() if isinstance(value, str) and value.strip() else None


def _workflow_id_from_message(message: str) -> str | None:
    match = re.search(r"\bwf_[A-Za-z0-9_-]+\b", message)
    return match.group(0) if match else None


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value not in seen:
            unique.append(value)
            seen.add(value)
    return unique
