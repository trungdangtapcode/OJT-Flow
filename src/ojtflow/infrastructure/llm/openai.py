"""OpenAI Responses API planner for the OJTFlow assistant."""

from __future__ import annotations

import json
from typing import Any

import httpx

from ojtflow.core.contracts.assistant import (
    AssistantPlan,
    AssistantToolPlan,
    AssistantToolSpec,
)
from ojtflow.core.errors import DependencyUnavailableError, ToolExecutionError


SYSTEM_PROMPT = """You are OJTFlow's healthcare data operations planner.
Choose only from the supplied tools. Prefer read/search/validate actions.
Never approve, reject, or bypass human review. Never invent workflow IDs,
schema IDs, evidence IDs, clinical codes, or output content. Prefer coarse
assistant tools such as validate_with_evidence and workflow_summary when they
fit the request. If the user asks for diagnosis, treatment, triage, or clinical
advice, use retrieval_search for source context or return no tool calls with a
warning.
Return JSON that matches the requested schema only."""


class OpenAIResponsesPlanner:
    """Plan assistant tool calls with OpenAI structured output."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str,
        timeout_seconds: float,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    @property
    def model_name(self) -> str:
        return self.model

    async def plan(
        self,
        *,
        message: str,
        context: dict,
        tools: list[AssistantToolSpec],
        max_tool_calls: int,
    ) -> AssistantPlan:
        if not self.api_key:
            raise DependencyUnavailableError(
                "OpenAI LLM planner requires OJT_OPENAI_API_KEY or OPENAI_API_KEY."
            )
        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": SYSTEM_PROMPT}],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": json.dumps(
                                {
                                    "message": message,
                                    "context": context,
                                    "available_tools": [
                                        tool.model_dump(mode="json") for tool in tools
                                    ],
                                    "max_tool_calls": max_tool_calls,
                                },
                                ensure_ascii=False,
                            ),
                        }
                    ],
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "ojtflow_assistant_plan",
                    "schema": _assistant_plan_schema(
                        max_tool_calls,
                        tool_names=[tool.name for tool in tools],
                    ),
                }
            },
        }
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                f"{self.base_url}/responses",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if response.status_code >= 400:
            raise ToolExecutionError(
                "OpenAI LLM planner request failed.",
                details={"status_code": response.status_code, "response": response.text[:1000]},
            )
        raw_text = _response_text(response.json())
        try:
            plan_payload = json.loads(raw_text)
            return AssistantPlan(
                message=str(plan_payload.get("message") or ""),
                tool_calls=[
                    AssistantToolPlan(
                        tool_name=item.get("tool_name"),
                        arguments=item.get("arguments") or {},
                        rationale=str(item.get("rationale") or ""),
                    )
                    for item in plan_payload.get("tool_calls") or []
                    if isinstance(item, dict)
                ],
                warnings=[
                    str(item)
                    for item in plan_payload.get("warnings") or []
                    if isinstance(item, str)
                ],
            )
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise ToolExecutionError(
                "OpenAI LLM planner returned an invalid assistant plan.",
                details={"response_text": raw_text[:1000]},
            ) from exc


def _assistant_plan_schema(max_tool_calls: int, *, tool_names: list[str]) -> dict[str, Any]:
    tool_name_schema: dict[str, Any] = {"type": "string"}
    if tool_names:
        tool_name_schema["enum"] = sorted(set(tool_names))
    return {
        "type": "object",
        "properties": {
            "message": {"type": "string"},
            "tool_calls": {
                "type": "array",
                "maxItems": max_tool_calls,
                "items": {
                    "type": "object",
                    "properties": {
                        "tool_name": tool_name_schema,
                        "arguments": {
                            "type": "object",
                            "additionalProperties": True,
                        },
                        "rationale": {"type": "string"},
                    },
                    "required": ["tool_name", "arguments", "rationale"],
                    "additionalProperties": False,
                },
            },
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["message", "tool_calls", "warnings"],
        "additionalProperties": False,
    }


def _response_text(payload: dict[str, Any]) -> str:
    direct = payload.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct
    for item in payload.get("output") or []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content") or []:
            if not isinstance(content, dict):
                continue
            text = content.get("text")
            if isinstance(text, str) and text.strip():
                return text
    return ""
