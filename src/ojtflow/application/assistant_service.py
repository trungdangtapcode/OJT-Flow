"""Natural-language assistant over OJTFlow services."""

from __future__ import annotations

import json
from typing import Any

from ojtflow.application.assistant_tools import OJTFlowToolExecutor
from ojtflow.application.ports import AssistantPlanner
from ojtflow.core.contracts.assistant import (
    AssistantPlan,
    AssistantResponse,
    AssistantToolPlan,
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
        return AssistantResponse(
            message=_assistant_message(plan.message, tool_results),
            mode="llm" if self.planner else "deterministic",
            model=self.planner.model_name if self.planner else None,
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

    tool_calls: list[AssistantToolPlan] = []
    if "start" in normalized and "workflow" in normalized and data:
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
        tool_calls.append(
            AssistantToolPlan(
                tool_name="validate_data",
                arguments={
                    "data": data,
                    "input_format": input_format,
                    "schema_id": schema_id or "lab_result_v1",
                },
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
    elif "workflow" in normalized and any(word in normalized for word in ("list", "show", "recent")):
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


def _assistant_message(seed: str, tool_results: list) -> str:
    summaries = [result.summary for result in tool_results if result.summary]
    if summaries:
        return " ".join(summaries)
    return seed or "No tool action was required."


def _suggestions(tool_results: list) -> list[str]:
    suggestions: list[str] = []
    for result in tool_results:
        if result.status == "requires_approval":
            suggestions.append("Confirm write execution by resending with execute_write_actions=true.")
        if result.tool_name == "retrieval_search" and result.status == "completed":
            suggestions.append("Open the retrieval trace to inspect source coverage and safety flags.")
        if result.tool_name == "validate_data" and result.status == "completed":
            suggestions.append("Start a governed workflow if validation issues need review-gated repair.")
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


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value not in seen:
            unique.append(value)
            seen.add(value)
    return unique
