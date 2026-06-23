"""Natural-language assistant over OJTFlow services."""

from __future__ import annotations

import asyncio
import re
import unicodedata
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
from ojtflow.core.errors import DependencyUnavailableError, OJTFlowError
from ojtflow.core.policy.prompt_injection_policy import (
    DEFAULT_PROMPT_INJECTION_POLICY,
    assess_prompt_injection,
    assess_tool_metadata,
    tool_metadata_boundary,
    wrap_untrusted_content,
)
from ojtflow.core.policy.generated_output_policy import (
    validate_assistant_plan_output,
    validate_generated_text_output,
    validation_warning,
)

ASSISTANT_INTENT_TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9_./%-]*", re.IGNORECASE)
ASSISTANT_HEALTHCARE_INTENT_TOKENS = frozenset(
    {
        "a1c",
        "allergy",
        "benh",
        "blood",
        "clinical",
        "code",
        "condition",
        "diagnosis",
        "don",
        "duong",
        "effective",
        "fhir",
        "glucose",
        "hba1c",
        "hl7",
        "huyet",
        "lab",
        "laboratory",
        "loinc",
        "medication",
        "nghiem",
        "observation",
        "patient",
        "phi",
        "result",
        "rxnorm",
        "snomed",
        "test",
        "ucum",
        "unit",
        "value",
        "vi",
        "xet",
    }
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
            "recovery"
            if _recovery_plan(clean_context)
            else "llm"
            if self.planner
            else "unavailable"
        )
        plan = await self._plan(message=message, context=clean_context)
        plan = _suppress_out_of_domain_grounded_retrieval(
            plan,
            message=message,
            context=clean_context,
        )
        plan = _suppress_display_only_attachment_tools(
            plan,
            message=message,
            context=clean_context,
        )
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
        if not self.planner or not hasattr(self.planner, "synthesize"):
            raise DependencyUnavailableError(
                "Real LLM answer synthesis is not configured.",
                details={"code": "LLM_NOT_CONFIGURED"},
            )
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
        validation = validate_generated_text_output(
            message_text,
            surface="assistant_summary",
            source_ref=request_id,
        )
        if validation.status == "blocked":
            raise OJTFlowError(
                "LLM answer synthesis failed validation.",
                details={"validation": validation.model_dump(mode="json")},
            )
        synthesis_mode = "llm"
        warnings.extend(_generated_output_warnings(validation))
        message_text = _grounded_refusal_when_no_evidence(
            message_text,
            user_message=message,
            evidence_summary=evidence_summary,
        )
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
            "recovery"
            if _recovery_plan(clean_context)
            else "llm"
            if self.planner
            else "unavailable"
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
                plan = await self._plan(message=message, context=clean_context)
        except OJTFlowError:
            raise
        plan = self._validated_generated_plan(plan)
        plan = _suppress_out_of_domain_grounded_retrieval(
            plan,
            message=message,
            context=clean_context,
        )
        plan = _suppress_display_only_attachment_tools(
            plan,
            message=message,
            context=clean_context,
        )
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
        synthesis_mode = "llm"
        message_text = ""
        if (
            self.planner
            and hasattr(self.planner, "synthesize_stream")
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
                    candidate_text = "".join([*chunks, chunk]).strip()
                    validation = validate_generated_text_output(
                        candidate_text,
                        surface="assistant_stream_summary",
                        source_ref=request_id,
                    )
                    if validation.status == "blocked":
                        raise OJTFlowError(
                            "LLM answer synthesis failed validation.",
                            details={"validation": validation.model_dump(mode="json")},
                        )
                    warnings.extend(_generated_output_warnings(validation))
                    chunks.append(chunk)
                    yield {"type": "answer_delta", "delta": chunk}
                streamed_text = "".join(chunks).strip()
                if streamed_text:
                    validation = validate_generated_text_output(
                        streamed_text,
                        surface="assistant_stream_summary",
                        source_ref=request_id,
                    )
                    if validation.status == "blocked":
                        raise OJTFlowError(
                            "LLM answer synthesis failed validation.",
                            details={"validation": validation.model_dump(mode="json")},
                        )
                    else:
                        message_text = streamed_text
                        synthesis_mode = "llm"
                        warnings.extend(_generated_output_warnings(validation))
                else:
                    raise OJTFlowError("LLM answer synthesis returned an empty response.")
            except OJTFlowError:
                raise
        elif (
            self.planner
            and hasattr(self.planner, "synthesize")
        ):
            yield {
                "type": "synthesis_started",
                "mode": "llm",
                "message": "Generating the final answer from the LLM.",
            }
            try:
                candidate_text = await self.planner.synthesize(
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
                validation = validate_generated_text_output(
                    candidate_text,
                    surface="assistant_summary",
                    source_ref=request_id,
                )
                if validation.status == "blocked":
                    raise OJTFlowError(
                        "LLM answer synthesis failed validation.",
                        details={"validation": validation.model_dump(mode="json")},
                    )
                else:
                    message_text = candidate_text
                    synthesis_mode = "llm"
                    warnings.extend(_generated_output_warnings(validation))
                    yield {"type": "answer_delta", "delta": message_text}
            except OJTFlowError:
                raise
        else:
            raise DependencyUnavailableError(
                "Real LLM answer synthesis is not configured.",
                details={"code": "LLM_NOT_CONFIGURED"},
            )
        message_text = _grounded_refusal_when_no_evidence(
            message_text,
            user_message=message,
            evidence_summary=evidence_summary,
        )

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
            plan = await self.planner.plan(
                message=message,
                context=_context_for_planner(
                    context,
                    message=message,
                    policy=self.prompt_injection_policy,
                ),
                tools=self.tool_specs,
                max_tool_calls=self.max_tool_calls,
            )
            return self._validated_generated_plan(plan)
        raise DependencyUnavailableError(
            "Real LLM planner is not configured.",
            details={"code": "LLM_NOT_CONFIGURED"},
        )

    def _validated_generated_plan(self, plan: AssistantPlan) -> AssistantPlan:
        if not self.tool_specs:
            return plan
        validation = validate_assistant_plan_output(
            plan,
            allowed_tool_names=(spec.name for spec in self.tool_specs),
        )
        if validation.status == "blocked":
            raise OJTFlowError(
                "LLM generated plan failed validation.",
                details={"validation": validation.model_dump(mode="json")},
            )
        warnings = [*plan.warnings, *_generated_output_warnings(validation)]
        return plan.model_copy(update={"warnings": warnings})

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


def _generated_output_warnings(validation) -> list[str]:
    if validation.status == "passed":
        return []
    return [validation_warning(validation)]


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


def _suppress_out_of_domain_grounded_retrieval(
    plan: AssistantPlan,
    *,
    message: str,
    context: dict[str, Any],
) -> AssistantPlan:
    if not _requests_grounded_answer(message):
        return plan
    if _assistant_request_has_healthcare_intent(message, context):
        return plan
    if not any(tool_call.tool_name == "retrieval_search" for tool_call in plan.tool_calls):
        return plan
    return plan.model_copy(
        update={
            "tool_calls": [
                tool_call
                for tool_call in plan.tool_calls
                if tool_call.tool_name != "retrieval_search"
            ],
            "warnings": [
                *plan.warnings,
                (
                    "Grounded retrieval was suppressed because the request has no "
                    "healthcare, standards, or configured clinical context."
                ),
            ],
        }
    )


def _suppress_display_only_attachment_tools(
    plan: AssistantPlan,
    *,
    message: str,
    context: dict[str, Any],
) -> AssistantPlan:
    if not plan.tool_calls:
        return plan
    if not _has_readable_attachment_text(context):
        return plan
    if not _requests_attachment_content_display(message):
        return plan
    return plan.model_copy(
        update={
            "tool_calls": [],
            "warnings": [
                *plan.warnings,
                (
                    "Backend analysis tools were skipped because the request only "
                    "asked to display already extracted attachment text."
                ),
            ],
        }
    )


def _has_readable_attachment_text(context: dict[str, Any]) -> bool:
    attachments = context.get("attachments")
    if not isinstance(attachments, list):
        return False
    for attachment in attachments:
        if not isinstance(attachment, dict):
            continue
        text = attachment.get("text")
        if isinstance(text, str) and text.strip():
            return True
    return False


def _requests_attachment_content_display(message: str) -> bool:
    normalized = _ascii_fold(message).lower()
    display_markers = (
        "show",
        "read",
        "print",
        "display",
        "view",
        "paste",
        "copy",
        "extract text",
        "noi dung",
        "doc",
        "hien thi",
    )
    attachment_markers = (
        "pdf",
        "file",
        "document",
        "attachment",
        "upload",
        "scan",
        "image",
        "content",
        "text",
        "tai lieu",
        "tep",
        "file",
    )
    analysis_markers = (
        "json",
        "csv",
        "fhir",
        "validate",
        "profile",
        "convert",
        "mapping",
        "map",
        "schema",
        "unit",
        "loinc",
        "extract labs",
        "structured",
    )
    if any(marker in normalized for marker in analysis_markers):
        return False
    return any(marker in normalized for marker in display_markers) and any(
        marker in normalized for marker in attachment_markers
    )


def _assistant_request_has_healthcare_intent(
    message: str,
    context: dict[str, Any],
) -> bool:
    if any(
        context.get(key)
        for key in ("clinical_domain", "schema_id", "resource_type", "standard_system")
    ):
        return True
    fields = context.get("fields")
    if isinstance(fields, list) and any(str(field).strip() for field in fields):
        return True
    normalized_message = _ascii_fold(message)
    tokens = {
        match.group(0).lower()
        for match in ASSISTANT_INTENT_TOKEN_PATTERN.finditer(normalized_message)
    }
    return bool(tokens.intersection(ASSISTANT_HEALTHCARE_INTENT_TOKENS))


def _ascii_fold(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


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
    source_id_by_evidence_id = _source_ids_by_evidence_id(evidence)
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
                source_ids=_recommended_action_source_ids(
                    action,
                    source_id_by_evidence_id,
                ),
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


def _source_ids_by_evidence_id(evidence: list[dict[str, Any]]) -> dict[str, str]:
    return {
        str(item["evidence_id"]): str(item["source_id"])
        for item in evidence
        if item.get("evidence_id") and item.get("source_id")
    }


def _recommended_action_source_ids(
    action: dict[str, Any],
    source_id_by_evidence_id: dict[str, str],
) -> list[str]:
    source_ids: list[str] = []
    raw_source_ids = action.get("source_ids")
    if isinstance(raw_source_ids, list):
        source_ids.extend(str(source_id) for source_id in raw_source_ids if source_id)
    raw_evidence_ids = action.get("evidence_ids")
    if isinstance(raw_evidence_ids, list):
        source_ids.extend(
            source_id_by_evidence_id[evidence_id]
            for evidence_id in (str(value) for value in raw_evidence_ids if value)
            if evidence_id in source_id_by_evidence_id
        )
    return _unique_nonblank_strings(source_ids)[:5]


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
        _tool_result_for_llm(result, policy=policy)
        for result in tool_results
    ]


def _tool_result_for_llm(
    result: AssistantToolResult,
    *,
    policy: PromptInjectionPolicy,
) -> dict[str, Any]:
    evidence_items = _evidence_items(result.output)[:5]
    compact_result: dict[str, Any] = {
        "tool_name": result.tool_name,
        "status": result.status,
        "summary": result.summary,
        "arguments": _arguments_for_llm(result.arguments, policy=policy),
        "error": result.error,
        "evidence": _evidence_items_for_llm(evidence_items, policy=policy),
        "interpretation": _retrieval_interpretation(result.output),
        "remediation_summary": _remediation_summary(result.output),
        "trace": _compact_mapping(result.output.get("trace")),
        "coverage": _compact_mapping(result.output.get("coverage")),
        "validation_report": _compact_mapping(result.output.get("validation_report")),
    }
    if evidence_items:
        compact_result.update(
            {
                "evidence_buckets": _evidence_buckets(result.output),
                "standard_search_plan": _standard_search_plan(result.output),
                "medical_search_hints": _compact_medical_search_hints(result.output),
                "diversity": _compact_retrieval_diversity(result.output),
            }
        )
    return compact_result


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


def _grounded_refusal_when_no_evidence(
    message_text: str,
    *,
    user_message: str,
    evidence_summary: list[AssistantEvidenceSummary],
) -> str:
    if evidence_summary or not _requests_grounded_answer(user_message):
        return message_text
    lower_text = message_text.lower()
    has_refusal = "can't answer" in lower_text or "cannot answer" in lower_text
    if has_refusal and "invent" in lower_text:
        return message_text
    return (
        "I can't answer from trusted documents because no relevant retrieved evidence "
        "was found. I won't invent citations or requirements."
    )


def _requests_grounded_answer(message: str) -> bool:
    lower_message = message.lower()
    grounded_phrases = (
        "trusted document",
        "trusted documents",
        "retrieved evidence",
        "retrieved context",
        "citations",
        "cite",
        "answer only from",
        "from the evidence",
        "from evidence",
    )
    return any(phrase in lower_message for phrase in grounded_phrases)


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


def _optional_text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value not in seen:
            unique.append(value)
            seen.add(value)
    return unique
