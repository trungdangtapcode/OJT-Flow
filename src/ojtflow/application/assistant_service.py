"""Natural-language assistant over OJTFlow services."""

from __future__ import annotations

import asyncio
import json
import re
from collections.abc import AsyncIterator, Mapping
from typing import Any

from ojtflow.application.assistant_tools import OJTFlowToolExecutor
from ojtflow.application.ports import AssistantPlanner, AuditRepository
from ojtflow.application.tool_audit import append_tool_audit_record
from ojtflow.core.contracts.assistant import (
    AssistantEvidenceSummary,
    AssistantFinding,
    AssistantPlan,
    AssistantResponse,
    AssistantToolPlan,
    AssistantToolProgressStage,
    AssistantToolResult,
    AssistantToolSpec,
)
from ojtflow.core.contracts.prompt_injection import PromptInjectionPolicy
from ojtflow.core.errors import OJTFlowError
from ojtflow.core.policy.prompt_injection_policy import (
    DEFAULT_PROMPT_INJECTION_POLICY,
    assess_prompt_injection,
    assess_tool_metadata,
    tool_metadata_boundary,
    wrap_untrusted_content,
)


class AssistantService:
    """Plan and execute allowlisted OJTFlow tools from a user message."""

    def __init__(
        self,
        tool_executor: OJTFlowToolExecutor,
        *,
        planner: AssistantPlanner | None = None,
        audit_repository: AuditRepository | None = None,
        max_tool_calls: int = 4,
        planning_progress_interval_seconds: float = 2.0,
        tool_progress_stages: Mapping[str, list[AssistantToolProgressStage]] | None = None,
        prompt_injection_policy: PromptInjectionPolicy | None = None,
    ) -> None:
        self.tool_executor = tool_executor
        self.planner = planner
        self.audit_repository = audit_repository
        self.max_tool_calls = max_tool_calls
        self.planning_progress_interval_seconds = planning_progress_interval_seconds
        self.prompt_injection_policy = (
            prompt_injection_policy or DEFAULT_PROMPT_INJECTION_POLICY
        )
        self.tool_metadata_assessments = assess_tool_metadata(
            self.tool_specs,
            policy=self.prompt_injection_policy,
        )
        if self.tool_metadata_assessments:
            blocked = ", ".join(
                str(assessment.source_ref) for assessment in self.tool_metadata_assessments
            )
            raise ValueError(
                "Assistant tool metadata contains prompt-injection patterns: "
                f"{blocked}"
            )
        self.tool_progress_stages = _validated_tool_progress_stages(
            tool_progress_stages or {},
            tool_specs=self.tool_specs,
        )

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
        request_id: str | None = None,
        assistant_session_id: str | None = None,
    ) -> AssistantResponse:
        """Plan a small tool sequence and execute it through the backend allowlist."""

        clean_context = context or {}
        planning_mode = (
            "deterministic"
            if _recovery_plan(clean_context)
            else "llm"
            if self.planner
            else "deterministic"
        )
        try:
            plan = await self._plan(message=message, context=clean_context)
        except OJTFlowError as exc:
            plan = _deterministic_plan(message, clean_context)
            planning_mode = "deterministic"
            plan.warnings.append(_planning_failure_warning(exc))
        tool_results = [
            self._execute_tool_call(
                tool_call,
                execute_write_actions=execute_write_actions,
                owner_user_id=owner_user_id,
                request_id=request_id,
                assistant_session_id=assistant_session_id,
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
        synthesis_mode = "deterministic"
        message_text = _assistant_message(plan.message, tool_results, findings)
        if (
            self.planner
            and hasattr(self.planner, "synthesize")
            and not _is_continue_recovery(clean_context)
        ):
            try:
                message_text = await self.planner.synthesize(
                    message=message,
                    context=_context_for_llm(
                        clean_context,
                        message=message,
                        policy=self.prompt_injection_policy,
                    ),
                    plan=plan,
                    tool_results=_tool_results_for_llm(
                        tool_results,
                        policy=self.prompt_injection_policy,
                    ),
                    findings=[finding.model_dump(mode="json") for finding in findings],
                    evidence_summary=_evidence_summary_for_llm(
                        evidence_summary,
                        policy=self.prompt_injection_policy,
                    ),
                )
                synthesis_mode = "llm"
            except OJTFlowError as exc:
                warnings.append(f"LLM answer synthesis failed: {exc}")
        return AssistantResponse(
            message=message_text,
            mode=planning_mode,
            synthesis_mode=synthesis_mode,
            model=self.planner.model_name if self.planner else None,
            findings=findings,
            evidence_summary=evidence_summary,
            tool_calls=tool_results,
            suggestions=_suggestions(tool_results),
            warnings=warnings,
        )

    async def chat_stream(
        self,
        *,
        message: str,
        context: dict[str, Any] | None = None,
        execute_write_actions: bool = False,
        owner_user_id: str | None = None,
        request_id: str | None = None,
        assistant_session_id: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream planning, tool execution, synthesis deltas, and final response."""

        clean_context = context or {}
        planning_mode = (
            "deterministic"
            if _recovery_plan(clean_context)
            else "llm"
            if self.planner
            else "deterministic"
        )
        yield {
            "type": "planning_started",
            "mode": planning_mode,
            "model": self.planner.model_name if self.planner else None,
            "available_tool_count": len(self.tool_specs),
            "max_tool_calls": self.max_tool_calls,
            "message": "Planning the safest matching backend action.",
        }
        try:
            if self.planner:
                if hasattr(self.planner, "plan_stream"):
                    plan = None
                    async for event in self.planner.plan_stream(
                        message=message,
                        context=_context_for_planner(
                            clean_context,
                            message=message,
                            policy=self.prompt_injection_policy,
                        ),
                        tools=self.tool_specs,
                        max_tool_calls=self.max_tool_calls,
                    ):
                        if event.get("type") == "plan":
                            candidate = event.get("plan")
                            if isinstance(candidate, AssistantPlan):
                                plan = candidate
                            continue
                        if event.get("type") in {"planning_step", "planning_delta"}:
                            yield {**event, "mode": planning_mode}
                    if plan is None:
                        raise OJTFlowError("LLM planner stream ended without a plan.")
                else:
                    plan_task = asyncio.create_task(
                        self._plan(message=message, context=clean_context)
                    )
                    elapsed_seconds = 0.0
                    yield {
                        "type": "planning_step",
                        "mode": planning_mode,
                        "label": "Planner request sent",
                        "message": (
                            "Waiting for the configured LLM planner to return a "
                            "validated tool plan."
                        ),
                    }
                    try:
                        while not plan_task.done():
                            await asyncio.sleep(self.planning_progress_interval_seconds)
                            if plan_task.done():
                                break
                            elapsed_seconds += self.planning_progress_interval_seconds
                            yield {
                                "type": "planning_progress",
                                "mode": planning_mode,
                                "elapsed_seconds": round(elapsed_seconds, 2),
                                "message": (
                                    "LLM planner is still running. No backend tools "
                                    "have executed yet."
                                ),
                            }
                        plan = await plan_task
                    except BaseException:
                        if not plan_task.done():
                            plan_task.cancel()
                        raise
            else:
                yield {
                    "type": "planning_step",
                    "mode": planning_mode,
                    "label": "Deterministic planner",
                    "message": "Selecting a tool from the local rule-based planner.",
                }
                plan = await self._plan(message=message, context=clean_context)
        except OJTFlowError as exc:
            plan = _deterministic_plan(message, clean_context)
            planning_mode = "deterministic"
            plan.warnings.append(_planning_failure_warning(exc))
            yield {
                "type": "warning",
                "message": plan.warnings[-1],
                "details": exc.details,
            }
        yield {
            "type": "plan_ready",
            "mode": planning_mode,
            "plan": plan.model_dump(mode="json"),
        }

        warnings = [*plan.warnings]
        tool_results: list[AssistantToolResult] = []
        planned_tool_calls = plan.tool_calls[: self.max_tool_calls]
        for index, tool_call in enumerate(planned_tool_calls, start=1):
            yield {
                "type": "tool_started",
                "index": index,
                "tool_call": tool_call.model_dump(mode="json"),
            }
            for stage in self._tool_progress_events(
                index=index,
                tool_name=tool_call.tool_name,
                event="before_execute",
            ):
                yield stage
            result = self._execute_tool_call(
                tool_call,
                execute_write_actions=execute_write_actions,
                owner_user_id=owner_user_id,
                request_id=request_id,
                assistant_session_id=assistant_session_id,
            )
            tool_results.append(result)
            for stage in self._tool_progress_events(
                index=index,
                tool_name=tool_call.tool_name,
                event="after_execute",
            ):
                yield stage
            yield {
                "type": "tool_completed",
                "index": index,
                "tool_result": result.model_dump(mode="json"),
            }

        if len(plan.tool_calls) > self.max_tool_calls:
            warning = (
                f"Assistant plan had {len(plan.tool_calls)} tool call(s); "
                f"only the first {self.max_tool_calls} were executed."
            )
            warnings.append(warning)
            yield {"type": "warning", "message": warning}

        findings = _findings(tool_results)
        evidence_summary = _evidence_summary(tool_results)
        synthesis_mode = "deterministic"
        message_text = _assistant_message(plan.message, tool_results, findings)
        if (
            self.planner
            and hasattr(self.planner, "synthesize_stream")
            and not _is_continue_recovery(clean_context)
        ):
            yield {
                "type": "synthesis_started",
                "mode": "llm",
                "message": "Streaming the final answer from the LLM.",
            }
            chunks: list[str] = []
            try:
                async for chunk in self.planner.synthesize_stream(
                    message=message,
                    context=_context_for_llm(
                        clean_context,
                        message=message,
                        policy=self.prompt_injection_policy,
                    ),
                    plan=plan,
                    tool_results=_tool_results_for_llm(
                        tool_results,
                        policy=self.prompt_injection_policy,
                    ),
                    findings=[finding.model_dump(mode="json") for finding in findings],
                    evidence_summary=_evidence_summary_for_llm(
                        evidence_summary,
                        policy=self.prompt_injection_policy,
                    ),
                ):
                    chunks.append(chunk)
                    yield {"type": "answer_delta", "delta": chunk}
                streamed_text = "".join(chunks).strip()
                if streamed_text:
                    message_text = streamed_text
                    synthesis_mode = "llm"
            except OJTFlowError as exc:
                warning = f"LLM answer synthesis failed: {exc}"
                warnings.append(warning)
                yield {"type": "warning", "message": warning}
        elif (
            self.planner
            and hasattr(self.planner, "synthesize")
            and not _is_continue_recovery(clean_context)
        ):
            yield {
                "type": "synthesis_started",
                "mode": "llm",
                "message": "Generating the final answer from the LLM.",
            }
            try:
                message_text = await self.planner.synthesize(
                    message=message,
                    context=_context_for_llm(
                        clean_context,
                        message=message,
                        policy=self.prompt_injection_policy,
                    ),
                    plan=plan,
                    tool_results=_tool_results_for_llm(
                        tool_results,
                        policy=self.prompt_injection_policy,
                    ),
                    findings=[finding.model_dump(mode="json") for finding in findings],
                    evidence_summary=_evidence_summary_for_llm(
                        evidence_summary,
                        policy=self.prompt_injection_policy,
                    ),
                )
                synthesis_mode = "llm"
                yield {"type": "answer_delta", "delta": message_text}
            except OJTFlowError as exc:
                warning = f"LLM answer synthesis failed: {exc}"
                warnings.append(warning)
                yield {"type": "warning", "message": warning}

        response = AssistantResponse(
            message=message_text,
            mode=planning_mode,
            synthesis_mode=synthesis_mode,
            model=self.planner.model_name if self.planner else None,
            findings=findings,
            evidence_summary=evidence_summary,
            tool_calls=tool_results,
            suggestions=_suggestions(tool_results),
            warnings=warnings,
        )
        yield {
            "type": "final",
            "response": response.model_dump(mode="json"),
        }

    async def _plan(self, *, message: str, context: dict[str, Any]) -> AssistantPlan:
        recovery_plan = _recovery_plan(context)
        if recovery_plan:
            return recovery_plan
        if self.planner:
            return await self.planner.plan(
                message=message,
                context=_context_for_planner(
                    context,
                    message=message,
                    policy=self.prompt_injection_policy,
                ),
                tools=self.tool_specs,
                max_tool_calls=self.max_tool_calls,
            )
        return _deterministic_plan(message, context)

    def _execute_tool_call(
        self,
        tool_call: AssistantToolPlan,
        *,
        execute_write_actions: bool,
        owner_user_id: str | None,
        request_id: str | None,
        assistant_session_id: str | None,
    ) -> AssistantToolResult:
        result = self.tool_executor.execute(
            tool_call,
            execute_write_actions=execute_write_actions,
            owner_user_id=owner_user_id,
            request_id=request_id,
        )
        append_tool_audit_record(
            self.audit_repository,
            action_prefix="assistant",
            tool_name=tool_call.tool_name,
            arguments={
                **tool_call.arguments,
                "execute_write_actions": execute_write_actions,
            },
            output=result.model_dump(mode="json"),
            owner_user_id=owner_user_id,
            request_id=request_id,
            assistant_session_id=assistant_session_id,
            actor_type="assistant",
        )
        return result

    def _tool_progress_events(
        self,
        *,
        index: int,
        tool_name: str,
        event: str,
    ) -> list[dict[str, Any]]:
        stages = self.tool_progress_stages.get(tool_name, [])
        return [
            {
                "type": "tool_progress",
                "index": index,
                "tool_name": tool_name,
                "stage_id": stage.stage_id,
                "label": stage.label,
                "message": stage.message,
                "progress": stage.progress,
            }
            for stage in stages
            if stage.event == event
        ]


def _validated_tool_progress_stages(
    progress_stages: Mapping[str, list[AssistantToolProgressStage]],
    *,
    tool_specs: list[AssistantToolSpec],
) -> dict[str, list[AssistantToolProgressStage]]:
    known_tools = {spec.name for spec in tool_specs}
    unknown_tools = sorted(set(progress_stages) - known_tools)
    if unknown_tools:
        raise ValueError(
            "Assistant tool progress policy references unknown tool(s): "
            + ", ".join(unknown_tools)
        )
    return {tool_name: list(stages) for tool_name, stages in progress_stages.items()}


def _planning_failure_warning(exc: OJTFlowError) -> str:
    detail_parts = [
        str(value)
        for key in (
            "status_code",
            "event_type",
            "status",
            "error_code",
            "incomplete_reason",
            "message",
        )
        if (value := exc.details.get(key)) not in (None, "")
    ]
    suffix = f" ({'; '.join(detail_parts)})" if detail_parts else ""
    return f"LLM planning failed: {exc}{suffix}"


def _deterministic_plan(message: str, context: dict[str, Any]) -> AssistantPlan:
    normalized = message.lower()
    data = _context_text(context, "data")
    schema_id = _context_optional_text(context, "schema_id")
    input_format = _context_optional_text(context, "input_format")
    target_format = _context_optional_text(context, "target_format") or "json"
    fields = context.get("fields") if isinstance(context.get("fields"), list) else []
    review_task = _review_task_context(context)
    mapping_draft = _mapping_draft_context(context)
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
    elif _wants_create_review_task(normalized, review_task):
        arguments: dict[str, Any] = {
            "question": _review_task_question(message, context, review_task),
            "schema_id": (
                _optional_text(review_task.get("schema_id"))
                or schema_id
                or "lab_result_v1"
            ),
            "review_focus": (
                _optional_text(review_task.get("review_focus"))
                or _optional_text(review_task.get("focus"))
                or "Unresolved data quality or terminology decision"
            ),
            "source_workflow_id": (
                _optional_text(review_task.get("source_workflow_id")) or workflow_id
            ),
            "source_turn_id": _optional_text(review_task.get("source_turn_id")),
            "issue_kinds": _review_task_string_list(review_task.get("issue_kinds")),
            "evidence_ids": _review_task_string_list(review_task.get("evidence_ids")),
        }
        if data:
            arguments["data"] = data
        if input_format:
            arguments["input_format"] = input_format
        tool_calls.append(
            AssistantToolPlan(
                tool_name="create_review_task",
                arguments={
                    key: value
                    for key, value in arguments.items()
                    if value not in (None, "", [])
                },
                rationale=(
                    "The user asked to create a durable human-review task for "
                    "an unresolved governed data decision."
                ),
            )
        )
    elif _wants_generate_mapping_draft(normalized, mapping_draft) and data:
        arguments: dict[str, Any] = {
            "instruction": _mapping_draft_instruction(message, context, mapping_draft),
            "data": data,
            "input_format": input_format,
            "target_format": target_format,
            "schema_id": (
                _optional_text(mapping_draft.get("schema_id"))
                or schema_id
                or "lab_result_v1"
            ),
            "mapping_goal": (
                _optional_text(mapping_draft.get("mapping_goal"))
                or _optional_text(mapping_draft.get("goal"))
            ),
            "source_fields": _review_task_string_list(
                mapping_draft.get("source_fields")
            )
            or [str(field) for field in fields if isinstance(field, str)],
            "target_fields": _review_task_string_list(
                mapping_draft.get("target_fields")
            ),
            "evidence_ids": _review_task_string_list(mapping_draft.get("evidence_ids")),
        }
        tool_calls.append(
            AssistantToolPlan(
                tool_name="generate_mapping_draft",
                arguments={
                    key: value
                    for key, value in arguments.items()
                    if value not in (None, "", [])
                },
                rationale=(
                    "The user asked to draft a mapping or transformation plan "
                    "without executing conversion."
                ),
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
    elif _has_retrieval_intent(normalized, context):
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
    else:
        return AssistantPlan(
            message=(
                "I can help with governed OJTFlow operations: validate data, find "
                "trusted healthcare evidence, inspect workflows, list reviews, convert "
                "formats, or profile FHIR-like resources. Ask for one of those tasks "
                "and include data or context when needed."
            ),
            tool_calls=[],
            warnings=["No supported OJTFlow operation was detected."],
        )

    return AssistantPlan(
        message="I planned the safest matching OJTFlow tool action.",
        tool_calls=tool_calls,
    )


def _recovery_plan(context: dict[str, Any]) -> AssistantPlan | None:
    recovery = context.get("assistant_recovery")
    if not isinstance(recovery, dict):
        return None
    action = _optional_text(recovery.get("action"))
    if action == "retry_tool":
        tool_name = _optional_text(recovery.get("tool_name"))
        arguments = recovery.get("arguments")
        if not tool_name or not isinstance(arguments, dict):
            return AssistantPlan(
                message="I could not retry the failed tool because recovery metadata was incomplete.",
                tool_calls=[],
                warnings=["assistant_recovery.retry_tool requires tool_name and arguments."],
            )
        return AssistantPlan(
            message=f"Retrying failed assistant tool call: {tool_name}.",
            tool_calls=[
                AssistantToolPlan(
                    tool_name=tool_name,
                    arguments=dict(arguments),
                    rationale=(
                        "The operator requested an exact retry of a failed assistant "
                        "tool call using the original validated arguments."
                    ),
                )
            ],
        )
    if action == "continue_after_failure":
        failed_names = ", ".join(_recovery_failed_tool_names(recovery)) or "the failed tool"
        return AssistantPlan(
            message=(
                f"Continuing without retrying {failed_names}. Treat the prior failure as "
                "unresolved, preserve any successful prior outputs, and avoid destructive "
                "actions until the failed step is reviewed."
            ),
            tool_calls=[],
            warnings=["Assistant continued without re-running failed tool calls."],
        )
    return None


def _recovery_failed_tool_names(recovery: dict[str, Any]) -> list[str]:
    calls = recovery.get("failed_tool_calls")
    if not isinstance(calls, list):
        return []
    names: list[str] = []
    for call in calls:
        if isinstance(call, dict) and (name := _optional_text(call.get("tool_name"))):
            names.append(name)
    return names


def _is_continue_recovery(context: dict[str, Any]) -> bool:
    recovery = context.get("assistant_recovery")
    return (
        isinstance(recovery, dict)
        and _optional_text(recovery.get("action")) == "continue_after_failure"
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
    if findings and findings[0].title == "Trusted evidence retrieved":
        interpretation = next(
            (finding for finding in findings if finding.title == "Retrieval interpretation"),
            None,
        )
        if interpretation:
            return interpretation.detail
        remediation = next(
            (finding for finding in findings if finding.title == "Retrieval remediation"),
            None,
        )
        if remediation:
            return remediation.detail
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
        if result.status == "skipped":
            findings.append(
                AssistantFinding(
                    title=f"{result.tool_name} skipped",
                    detail=result.summary or "Tool execution was skipped.",
                    severity="warning",
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
        elif result.tool_name == "create_review_task":
            findings.append(_review_task_finding(result.output))
        elif result.tool_name == "generate_mapping_draft":
            findings.append(_mapping_draft_finding(result.output))
    return findings


def _retrieval_findings(output: dict[str, Any]) -> list[AssistantFinding]:
    evidence = _evidence_items(output)
    trace = output.get("trace") if isinstance(output.get("trace"), dict) else {}
    coverage = output.get("coverage") if isinstance(output.get("coverage"), dict) else {}
    evidence_buckets = _evidence_buckets(output)
    interpretation = _retrieval_interpretation(output)
    standard_search_plan = _standard_search_plan(output)
    search_hints = _medical_search_hints(output)
    diversity = _retrieval_diversity(output)
    remediation_summary = _remediation_summary(output)
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
    if interpretation:
        findings.append(
            AssistantFinding(
                title="Retrieval interpretation",
                detail=str(interpretation.get("summary") or "Review retrieval interpretation."),
                severity=_interpretation_severity(interpretation),
                source_tool="retrieval_search",
                source_ids=[
                    str(interpretation.get("top_source_id"))
                ]
                if interpretation.get("top_source_id")
                else [],
            )
        )
    if remediation_summary:
        findings.append(
            AssistantFinding(
                title="Retrieval remediation",
                detail=remediation_summary,
                severity="warning",
                source_tool="retrieval_search",
            )
        )
    if standard_search_plan:
        steps = standard_search_plan.get("steps")
        step_count = len(steps) if isinstance(steps, list) else 0
        findings.append(
            AssistantFinding(
                title="Healthcare search plan",
                detail=(
                    f"{standard_search_plan.get('summary') or 'Review the standards-aware search plan.'} "
                    f"Primary route: {standard_search_plan.get('primary_route') or 'unreported'}; "
                    f"{step_count} step(s)."
                ),
                severity="info",
                source_tool="retrieval_search",
            )
        )
    if search_hints:
        launchable_count = sum(1 for hint in search_hints if _search_hint_launchable(hint))
        targets = _unique_nonblank_strings(
            str(hint.get("target"))
            for hint in search_hints
            if hint.get("target")
        )
        findings.append(
            AssistantFinding(
                title="Medical search hints",
                detail=(
                    f"Generated {len(search_hints)} governed follow-up route(s)"
                    f"{f' for {', '.join(targets[:4])}' if targets else ''}; "
                    f"{launchable_count} launchable."
                ),
                severity="info",
                source_tool="retrieval_search",
            )
        )
    if diversity:
        findings.append(
            AssistantFinding(
                title="Source diversity",
                detail=(
                    f"Selected {diversity.get('selected_source_count', 0)} of "
                    f"{diversity.get('candidate_source_count', 0)} candidate source(s); "
                    f"{diversity.get('duplicate_selected_source_count', 0)} duplicate selected."
                ),
                severity="warning"
                if int(diversity.get("duplicate_selected_source_count") or 0) > 0
                else "info",
                source_tool="retrieval_search",
                source_ids=[
                    str(item.get("source_id"))
                    for item in diversity.get("selected_hits", [])
                    if isinstance(item, dict) and item.get("source_id")
                ][:5]
                if isinstance(diversity.get("selected_hits"), list)
                else [],
            )
        )
    missing_required = [
        bucket
        for bucket in evidence_buckets
        if bucket.get("required") and int(bucket.get("hit_count") or 0) == 0
    ]
    if missing_required:
        findings.append(
            AssistantFinding(
                title="Evidence pack needs attention",
                detail=(
                    "Missing required evidence bucket(s): "
                    f"{', '.join(str(bucket.get('label') or bucket.get('bucket_id')) for bucket in missing_required)}."
                ),
                severity="warning",
                source_tool="retrieval_search",
            )
        )
    for action in _recommended_actions(output)[:3]:
        findings.append(
            AssistantFinding(
                title="Recommended search action",
                detail=(
                    f"{action.get('title') or 'Review retrieval action'}: "
                    f"{action.get('description') or 'Review the retrieval package.'}"
                ),
                severity="action_required"
                if action.get("severity") == "destructive"
                else "warning",
                source_tool="retrieval_search",
                source_ids=[
                    str(evidence_id)
                    for evidence_id in action.get("evidence_ids", [])
                    if evidence_id
                ][:5]
                if isinstance(action.get("evidence_ids"), list)
                else [],
            )
        )
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


def _review_task_finding(output: dict[str, Any]) -> AssistantFinding:
    workflow_id = str(output.get("workflow_id") or "workflow")
    review = output.get("review_task") if isinstance(output.get("review_task"), dict) else {}
    review_id = str(review.get("review_id") or "review")
    question = str(review.get("question") or "Review the unresolved data decision.")
    return AssistantFinding(
        title="Review task created",
        detail=f"Created {review_id} for {workflow_id}: {question}",
        severity="warning",
        source_tool="create_review_task",
        source_ids=[value for value in (workflow_id, review_id) if value],
    )


def _mapping_draft_finding(output: dict[str, Any]) -> AssistantFinding:
    workflow_id = str(output.get("workflow_id") or "workflow")
    draft = output.get("mapping_draft") if isinstance(output.get("mapping_draft"), dict) else {}
    plan_id = str(draft.get("plan_id") or "plan")
    review_id = str(draft.get("review_id") or "review")
    action_count = draft.get("action_count")
    return AssistantFinding(
        title="Mapping draft created",
        detail=(
            f"Created review-gated mapping draft {plan_id} for {workflow_id} "
            f"with {action_count if isinstance(action_count, int) else 0} "
            f"proposed action(s). Review task: {review_id}."
        ),
        severity="warning",
        source_tool="generate_mapping_draft",
        source_ids=[value for value in (workflow_id, plan_id, review_id) if value],
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
                    evidence_id=(
                        str(item.get("evidence_id"))
                        if item.get("evidence_id") is not None
                        else None
                    ),
                    source_id=str(item.get("source_id") or "unknown"),
                    source_type=(
                        str(item.get("source_type"))
                        if item.get("source_type") is not None
                        else None
                    ),
                    claim=str(item.get("claim") or ""),
                    trust_level=str(item.get("trust_level") or "unknown"),
                    confidence=(
                        item.get("confidence")
                        if isinstance(item.get("confidence"), (int, float))
                        else None
                    ),
                    locator=(
                        item.get("locator")
                        if isinstance(item.get("locator"), dict)
                        else {}
                    ),
                    match_explanation=(
                        item.get("match_explanation")
                        if isinstance(item.get("match_explanation"), dict)
                        else {}
                    ),
                )
            )
            if len(summaries) >= 5:
                return summaries
    return summaries


def _evidence_items(output: dict[str, Any]) -> list[dict[str, Any]]:
    hits = output.get("hits")
    if isinstance(hits, list):
        items: list[dict[str, Any]] = []
        for hit in hits:
            if not isinstance(hit, dict):
                continue
            evidence = hit.get("evidence")
            if not isinstance(evidence, dict):
                continue
            item = dict(evidence)
            match_explanation = hit.get("match_explanation")
            if isinstance(match_explanation, dict):
                item["match_explanation"] = match_explanation
            items.append(item)
        if items:
            return items
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


def _recommended_actions(output: dict[str, Any]) -> list[dict[str, Any]]:
    actions = output.get("recommended_actions")
    if isinstance(actions, list):
        return [item for item in actions if isinstance(item, dict)]
    retrieval = output.get("retrieval")
    if isinstance(retrieval, dict):
        return _recommended_actions(retrieval)
    workflow = output.get("workflow")
    if isinstance(workflow, dict):
        workflow_retrieval = workflow.get("retrieval")
        if isinstance(workflow_retrieval, dict):
            return _recommended_actions(workflow_retrieval)
    return []


def _remediation_summary(output: dict[str, Any]) -> str | None:
    summary = output.get("remediation_summary")
    if isinstance(summary, str) and summary.strip():
        return summary.strip()
    handoff_context = output.get("handoff_context")
    if isinstance(handoff_context, dict):
        handoff_summary = handoff_context.get("remediation_summary")
        if isinstance(handoff_summary, str) and handoff_summary.strip():
            return handoff_summary.strip()
    retrieval = output.get("retrieval")
    if isinstance(retrieval, dict):
        return _remediation_summary(retrieval)
    workflow = output.get("workflow")
    if isinstance(workflow, dict):
        workflow_retrieval = workflow.get("retrieval")
        if isinstance(workflow_retrieval, dict):
            return _remediation_summary(workflow_retrieval)
    return None


def _retrieval_interpretation(output: dict[str, Any]) -> dict[str, Any] | None:
    interpretation = output.get("interpretation")
    if isinstance(interpretation, dict):
        return interpretation
    handoff_context = output.get("handoff_context")
    if isinstance(handoff_context, dict):
        handoff_interpretation = handoff_context.get("interpretation")
        if isinstance(handoff_interpretation, dict):
            return handoff_interpretation
    retrieval = output.get("retrieval")
    if isinstance(retrieval, dict):
        return _retrieval_interpretation(retrieval)
    workflow = output.get("workflow")
    if isinstance(workflow, dict):
        workflow_retrieval = workflow.get("retrieval")
        if isinstance(workflow_retrieval, dict):
            return _retrieval_interpretation(workflow_retrieval)
    return None


def _standard_search_plan(output: dict[str, Any]) -> dict[str, Any] | None:
    plan = output.get("standard_search_plan")
    if isinstance(plan, dict):
        return plan
    handoff_context = output.get("handoff_context")
    if isinstance(handoff_context, dict):
        handoff_plan = handoff_context.get("standard_search_plan")
        if isinstance(handoff_plan, dict):
            return handoff_plan
    retrieval = output.get("retrieval")
    if isinstance(retrieval, dict):
        return _standard_search_plan(retrieval)
    workflow = output.get("workflow")
    if isinstance(workflow, dict):
        workflow_retrieval = workflow.get("retrieval")
        if isinstance(workflow_retrieval, dict):
            return _standard_search_plan(workflow_retrieval)
    return None


def _medical_search_hints(output: dict[str, Any]) -> list[dict[str, Any]]:
    direct = output.get("search_hints")
    if isinstance(direct, list):
        return [item for item in direct if isinstance(item, dict)][:8]
    query_analysis = output.get("query_analysis")
    if isinstance(query_analysis, dict):
        hints = query_analysis.get("search_hints")
        if isinstance(hints, list):
            return [item for item in hints if isinstance(item, dict)][:8]
    handoff_context = output.get("handoff_context")
    if isinstance(handoff_context, dict):
        handoff_analysis = handoff_context.get("query_analysis")
        if isinstance(handoff_analysis, dict):
            hints = handoff_analysis.get("search_hints")
            if isinstance(hints, list):
                return [item for item in hints if isinstance(item, dict)][:8]
    retrieval = output.get("retrieval")
    if isinstance(retrieval, dict):
        hints = _medical_search_hints(retrieval)
        if hints:
            return hints
    workflow = output.get("workflow")
    if isinstance(workflow, dict):
        workflow_retrieval = workflow.get("retrieval")
        if isinstance(workflow_retrieval, dict):
            return _medical_search_hints(workflow_retrieval)
    return []


def _compact_medical_search_hints(output: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "target": hint.get("target"),
            "query": hint.get("query"),
            "url": hint.get("url"),
            "rationale": hint.get("rationale"),
            "warnings": hint.get("warnings") if isinstance(hint.get("warnings"), list) else [],
            "metadata": _compact_search_hint_metadata(hint.get("metadata")),
        }
        for hint in _medical_search_hints(output)
    ]


def _compact_search_hint_metadata(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    compact: dict[str, Any] = {}
    if "launchable" in value:
        compact["launchable"] = bool(value.get("launchable"))
    for key in ("scope_endpoints", "selected_terms", "selected_unit_candidates"):
        items = value.get(key)
        if isinstance(items, list):
            compact[key] = [item for item in items if isinstance(item, str)][:8]
    for key, limit in (("parameter_examples", 8), ("lineage_followup", 4)):
        items = value.get(key)
        if isinstance(items, list):
            compact[key] = [item for item in items if isinstance(item, dict)][:limit]
    warning = value.get("capability_warning")
    if isinstance(warning, str) and warning.strip():
        compact["capability_warning"] = warning.strip()
    return compact


def _retrieval_diversity(output: dict[str, Any]) -> dict[str, Any] | None:
    diversity = output.get("diversity")
    if isinstance(diversity, dict):
        return diversity
    handoff_context = output.get("handoff_context")
    if isinstance(handoff_context, dict):
        handoff_diversity = handoff_context.get("diversity")
        if isinstance(handoff_diversity, dict):
            return handoff_diversity
    retrieval = output.get("retrieval")
    if isinstance(retrieval, dict):
        return _retrieval_diversity(retrieval)
    workflow = output.get("workflow")
    if isinstance(workflow, dict):
        workflow_retrieval = workflow.get("retrieval")
        if isinstance(workflow_retrieval, dict):
            return _retrieval_diversity(workflow_retrieval)
    return None


def _compact_retrieval_diversity(output: dict[str, Any]) -> dict[str, Any] | None:
    diversity = _retrieval_diversity(output)
    if not diversity:
        return None
    selected_hits = diversity.get("selected_hits")
    return {
        "enabled": bool(diversity.get("enabled")),
        "selection_mode": diversity.get("selection_mode"),
        "lambda": diversity.get("lambda_value", diversity.get("lambda")),
        "candidate_source_count": diversity.get("candidate_source_count"),
        "selected_source_count": diversity.get("selected_source_count"),
        "duplicate_selected_source_count": diversity.get("duplicate_selected_source_count"),
        "selected_hits": [
            {
                "evidence_id": item.get("evidence_id"),
                "source_id": item.get("source_id"),
                "selected_rank": item.get("selected_rank"),
                "original_rank": item.get("original_rank"),
                "relevance_score": item.get("relevance_score"),
                "redundancy_score": item.get("redundancy_score"),
                "selection_score": item.get("selection_score"),
                "reason": item.get("reason"),
            }
            for item in selected_hits[:5]
            if isinstance(item, dict)
        ]
        if isinstance(selected_hits, list)
        else [],
    }


def _search_hint_launchable(hint: dict[str, Any]) -> bool:
    if hint.get("url"):
        return True
    metadata = hint.get("metadata")
    return isinstance(metadata, dict) and bool(metadata.get("launchable"))


def _interpretation_severity(interpretation: dict[str, Any]) -> str:
    status = str(interpretation.get("status") or "").lower()
    if "no_ranked" in status or "support_gaps" in status or "warning" in status:
        return "warning"
    if "blocked" in status:
        return "action_required"
    return "info"


def _context_for_llm(
    context: dict[str, Any],
    *,
    message: str,
    policy: PromptInjectionPolicy,
) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    redacted["user_message_prompt_injection"] = assess_prompt_injection(
        message,
        surface="user_message",
        source_ref="assistant_message",
        policy=policy,
    ).model_dump(mode="json")
    for key, value in context.items():
        if key == "data":
            redacted["data"] = _redacted_untrusted_content(
                str(value),
                source="uploaded_data",
                surface="uploaded_data",
                source_ref="assistant_context.data",
                policy=policy,
            )
        elif key == "attachments":
            redacted[key] = _wrap_context_value(
                value,
                surface="uploaded_document",
                source="assistant_context.attachments",
                policy=policy,
            )
        elif key == "text_snippets":
            redacted[key] = _wrap_context_value(
                value,
                surface="text_snippet",
                source="assistant_context.text_snippets",
                policy=policy,
            )
        elif key == "selected_contexts":
            redacted[key] = _wrap_context_value(
                value,
                surface="selected_context",
                source="assistant_context.selected_contexts",
                policy=policy,
            )
        else:
            redacted[key] = value
    return redacted


def _context_for_planner(
    context: dict[str, Any],
    *,
    message: str,
    policy: PromptInjectionPolicy,
) -> dict[str, Any]:
    guarded: dict[str, Any] = {}
    guarded["user_message_prompt_injection"] = assess_prompt_injection(
        message,
        surface="user_message",
        source_ref="assistant_message",
        policy=policy,
    ).model_dump(mode="json")
    guarded["prompt_injection_policy"] = {
        "version": policy.version,
        "untrusted_surfaces": list(policy.untrusted_surfaces),
        "tool_metadata_boundary": tool_metadata_boundary(policy),
    }
    for key, value in context.items():
        if key == "data" and isinstance(value, str):
            guarded[key] = _untrusted_content(
                value,
                source="uploaded_data",
                surface="uploaded_data",
                source_ref="assistant_context.data",
                policy=policy,
            )
        elif key == "attachments":
            guarded[key] = _wrap_context_value(
                value,
                surface="uploaded_document",
                source="assistant_context.attachments",
                policy=policy,
            )
        elif key == "text_snippets":
            guarded[key] = _wrap_context_value(
                value,
                surface="text_snippet",
                source="assistant_context.text_snippets",
                policy=policy,
            )
        elif key == "selected_contexts":
            guarded[key] = _wrap_context_value(
                value,
                surface="selected_context",
                source="assistant_context.selected_contexts",
                policy=policy,
            )
        else:
            guarded[key] = value
    return guarded


def _tool_results_for_llm(
    tool_results: list[AssistantToolResult],
    *,
    policy: PromptInjectionPolicy,
) -> list[dict[str, Any]]:
    return [
        {
            "tool_name": result.tool_name,
            "status": result.status,
            "summary": result.summary,
            "arguments": _arguments_for_llm(result.arguments, policy=policy),
            "error": result.error,
            "evidence": _evidence_items_for_llm(
                _evidence_items(result.output)[:5],
                policy=policy,
            ),
            "evidence_buckets": _evidence_buckets(result.output),
            "interpretation": _retrieval_interpretation(result.output),
            "standard_search_plan": _standard_search_plan(result.output),
            "medical_search_hints": _compact_medical_search_hints(result.output),
            "diversity": _compact_retrieval_diversity(result.output),
            "remediation_summary": _remediation_summary(result.output),
            "trace": _compact_mapping(result.output.get("trace")),
            "coverage": _compact_mapping(result.output.get("coverage")),
            "validation_report": _compact_mapping(result.output.get("validation_report")),
        }
        for result in tool_results
    ]


def _evidence_summary_for_llm(
    evidence_summary: list[AssistantEvidenceSummary],
    *,
    policy: PromptInjectionPolicy,
) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for evidence in evidence_summary:
        item = evidence.model_dump(mode="json")
        if isinstance(item.get("claim"), str):
            item["claim"] = _untrusted_content(
                item["claim"],
                source="retrieved_evidence_claim",
                surface="retrieved_chunk",
                source_ref=str(item.get("evidence_id") or item.get("source_id") or ""),
                policy=policy,
            )
        summaries.append(item)
    return summaries


def _arguments_for_llm(
    arguments: dict[str, Any],
    *,
    policy: PromptInjectionPolicy,
) -> dict[str, Any]:
    safe_arguments: dict[str, Any] = {}
    for key, value in arguments.items():
        if key == "data" and isinstance(value, str):
            safe_arguments[key] = _redacted_untrusted_content(
                value,
                source=f"tool_argument.{key}",
                surface="tool_argument",
                source_ref=f"tool_argument.{key}",
                policy=policy,
            )
        elif isinstance(value, str) and key in {"query", "instruction", "question"}:
            safe_arguments[key] = _untrusted_content(
                value,
                source=f"tool_argument.{key}",
                surface="tool_argument",
                source_ref=f"tool_argument.{key}",
                policy=policy,
            )
        else:
            safe_arguments[key] = value
    return safe_arguments


def _evidence_items_for_llm(
    items: list[dict[str, Any]],
    *,
    policy: PromptInjectionPolicy,
) -> list[dict[str, Any]]:
    llm_items: list[dict[str, Any]] = []
    for item in items:
        llm_item = dict(item)
        if isinstance(llm_item.get("claim"), str):
            llm_item["claim"] = _untrusted_content(
                llm_item["claim"],
                source="retrieved_evidence_claim",
                surface="retrieved_chunk",
                source_ref=str(
                    llm_item.get("evidence_id") or llm_item.get("source_id") or ""
                ),
                policy=policy,
            )
        llm_items.append(llm_item)
    return llm_items


def _untrusted_content(
    value: str,
    *,
    source: str,
    surface: str,
    source_ref: str | None = None,
    policy: PromptInjectionPolicy,
) -> dict[str, Any]:
    return wrap_untrusted_content(
        value,
        source=source,
        surface=surface,  # type: ignore[arg-type]
        source_ref=source_ref,
        policy=policy,
    )


def _redacted_untrusted_content(
    value: str,
    *,
    source: str,
    surface: str,
    source_ref: str,
    policy: PromptInjectionPolicy,
) -> dict[str, Any]:
    assessment = assess_prompt_injection(
        value,
        surface=surface,  # type: ignore[arg-type]
        source_ref=source_ref,
        policy=policy,
    )
    return {
        "source": source,
        "surface": surface,
        "redacted_content": f"<redacted {len(value)} characters>",
        "handling": assessment.handling,
        "prompt_injection_assessment": assessment.model_dump(mode="json"),
    }


def _wrap_context_value(
    value: Any,
    *,
    surface: str,
    source: str,
    policy: PromptInjectionPolicy,
) -> Any:
    if isinstance(value, str):
        return _untrusted_content(
            value,
            source=source,
            surface=surface,
            source_ref=source,
            policy=policy,
        )
    if isinstance(value, list):
        return [
            _wrap_context_value(
                item,
                surface=surface,
                source=f"{source}[{index}]",
                policy=policy,
            )
            for index, item in enumerate(value)
        ]
    if isinstance(value, dict):
        return {
            key: _wrap_context_value(
                nested,
                surface=surface,
                source=f"{source}.{key}",
                policy=policy,
            )
            for key, nested in value.items()
        }
    return value


def _compact_mapping(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {
        key: nested_value
        for key, nested_value in value.items()
        if key
        in {
            "strategy",
            "warnings",
            "safety_flags",
            "requires_review",
            "severity_summary",
            "issues",
            "standard_system",
            "query_aspects",
        }
    }


def _unique_nonblank_strings(values) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _evidence_buckets(output: dict[str, Any]) -> list[dict[str, Any]]:
    buckets = output.get("evidence_buckets")
    if isinstance(buckets, list):
        return [item for item in buckets if isinstance(item, dict)]
    retrieval = output.get("retrieval")
    if isinstance(retrieval, dict):
        return _evidence_buckets(retrieval)
    workflow = output.get("workflow")
    if isinstance(workflow, dict):
        workflow_retrieval = workflow.get("retrieval")
        if isinstance(workflow_retrieval, dict):
            return _evidence_buckets(workflow_retrieval)
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
            interpretation = _retrieval_interpretation(result.output)
            if interpretation and interpretation.get("next_action_title"):
                detail = str(interpretation.get("next_action_detail") or "").strip()
                title = str(interpretation.get("next_action_title") or "").strip()
                suggestions.append(f"{title}: {detail}" if detail else title)
            remediation_summary = _remediation_summary(result.output)
            if remediation_summary:
                suggestions.append(f"Next retrieval step: {remediation_summary}")
            for action in _recommended_actions(result.output)[:3]:
                title = str(action.get("title") or "").strip()
                description = str(action.get("description") or "").strip()
                if title:
                    suggestions.append(
                        f"{title}: {description}" if description else title
                    )
            suggestions.append(
                "Open the retrieval trace to inspect source coverage and safety flags."
            )
        if (
            result.tool_name in {"validate_data", "validate_with_evidence"}
            and result.status == "completed"
        ):
            remediation_summary = _remediation_summary(result.output)
            if remediation_summary:
                suggestions.append(f"Next retrieval step: {remediation_summary}")
            suggestions.append(
                "Start a governed workflow if validation issues need review-gated repair."
            )
        if result.tool_name == "workflow_summary" and result.status == "completed":
            for action in result.output.get("next_actions") or []:
                if isinstance(action, str):
                    suggestions.append(action)
        if result.tool_name == "create_review_task" and result.status == "completed":
            suggestions.append(
                "Open Reviews to approve, reject, clarify, or cancel the review task."
            )
        if result.tool_name == "generate_mapping_draft" and result.status == "completed":
            suggestions.append(
                "Open Reviews to inspect or edit the drafted mapping plan before execution."
            )
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


def _review_task_context(context: dict[str, Any]) -> dict[str, Any]:
    value = context.get("assistant_review_task")
    return value if isinstance(value, dict) else {}


def _mapping_draft_context(context: dict[str, Any]) -> dict[str, Any]:
    value = context.get("assistant_mapping_draft")
    return value if isinstance(value, dict) else {}


def _wants_create_review_task(
    normalized_message: str,
    review_task: dict[str, Any],
) -> bool:
    if _optional_text(review_task.get("action")) == "create_review_task":
        return True
    create_terms = ("create", "open", "raise", "file", "make", "escalate")
    review_terms = ("review task", "review ticket", "human review", "manual review")
    return any(term in normalized_message for term in create_terms) and any(
        term in normalized_message for term in review_terms
    )


def _wants_generate_mapping_draft(
    normalized_message: str,
    mapping_draft: dict[str, Any],
) -> bool:
    if _optional_text(mapping_draft.get("action")) == "generate_mapping_draft":
        return True
    draft_terms = ("mapping draft", "draft mapping", "draft transform", "transform plan")
    action_terms = ("generate", "create", "draft", "make", "prepare")
    return any(term in normalized_message for term in draft_terms) and any(
        term in normalized_message for term in action_terms
    )


def _mapping_draft_instruction(
    message: str,
    context: dict[str, Any],
    mapping_draft: dict[str, Any],
) -> str:
    return (
        _context_optional_text(context, "mapping_instruction")
        or _optional_text(mapping_draft.get("instruction"))
        or _optional_text(mapping_draft.get("question"))
        or message.strip()
        or "Draft a review-gated mapping and transformation plan."
    )


def _review_task_question(
    message: str,
    context: dict[str, Any],
    review_task: dict[str, Any],
) -> str:
    return (
        _context_optional_text(context, "review_question")
        or _optional_text(review_task.get("question"))
        or _optional_text(review_task.get("title"))
        or message.strip()
        or "Review unresolved data quality or terminology decision."
    )


def _review_task_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _optional_text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _workflow_id_from_message(message: str) -> str | None:
    match = re.search(r"\bwf_[A-Za-z0-9_-]+\b", message)
    return match.group(0) if match else None


def _has_retrieval_intent(normalized_message: str, context: dict[str, Any]) -> bool:
    if any(
        context.get(key)
        for key in ("schema_id", "fields", "clinical_domain", "standard_system")
    ):
        return True
    operation_terms = {
        "evidence",
        "standard",
        "standards",
        "search",
        "find",
        "retrieve",
        "ground",
        "explain",
        "source",
        "sources",
        "citation",
        "citations",
    }
    healthcare_terms = {
        "clinical",
        "healthcare",
        "medical",
        "fhir",
        "observation",
        "patient",
        "lab",
        "laboratory",
        "hba1c",
        "glucose",
        "unit",
        "ucum",
        "loinc",
        "snomed",
        "rxnorm",
        "pubmed",
        "mesh",
        "medication",
        "drug",
        "phi",
    }
    tokens = set(re.findall(r"[a-z0-9_]+", normalized_message))
    return bool(tokens & operation_terms) and bool(tokens & healthcare_terms)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value not in seen:
            unique.append(value)
            seen.add(value)
    return unique
