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
For each tool call, put the tool arguments in arguments_json as a JSON object
string. Use "{}" when the tool has no arguments.
Return JSON that matches the requested schema only."""


SYNTHESIS_PROMPT = """You are OJTFlow's healthcare data operations assistant.
Answer conversationally using only the supplied backend tool results. Do not
invent evidence, workflow IDs, clinical codes, diagnoses, treatment advice, or
actions. Cite source IDs from evidence_summary or tool_results when making
claims, using bracketed source IDs. If required evidence buckets are missing,
state that limitation clearly. If a write action is gated, tell the user what
confirmation is needed; never claim it was executed."""


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
        payload = _plan_payload(
            model=self.model,
            message=message,
            context=context,
            tools=tools,
            max_tool_calls=max_tool_calls,
        )
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/responses",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise ToolExecutionError(
                "OpenAI LLM planner request failed.",
                details={"error": exc.__class__.__name__, "message": str(exc)},
            ) from exc
        if response.status_code >= 400:
            raise ToolExecutionError(
                "OpenAI LLM planner request failed.",
                details={"status_code": response.status_code, "response": response.text[:1000]},
            )
        raw_text = _response_text(response.json())
        try:
            return _assistant_plan_from_text(raw_text)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise ToolExecutionError(
                "OpenAI LLM planner returned an invalid assistant plan.",
                details={"response_text": raw_text[:1000]},
            ) from exc

    async def plan_stream(
        self,
        *,
        message: str,
        context: dict,
        tools: list[AssistantToolSpec],
        max_tool_calls: int,
    ):
        """Stream planner progress and final validated plan from OpenAI Responses API."""

        if not self.api_key:
            raise DependencyUnavailableError(
                "OpenAI LLM planner requires OJT_OPENAI_API_KEY or OPENAI_API_KEY."
            )
        yield {
            "type": "planning_step",
            "label": "Tool catalog loaded",
            "message": f"{len(tools)} allowlisted backend tool(s) available.",
        }
        payload = _plan_payload(
            model=self.model,
            message=message,
            context=context,
            tools=tools,
            max_tool_calls=max_tool_calls,
        )
        payload["stream"] = True
        yield {
            "type": "planning_step",
            "label": "Planner request sent",
            "message": (
                "OpenAI is selecting tool names and JSON arguments under the "
                "assistant plan schema."
            ),
        }
        raw_chunks: list[str] = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/responses",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                ) as response:
                    if response.status_code >= 400:
                        body = (await response.aread()).decode("utf-8", errors="replace")
                        raise ToolExecutionError(
                            "OpenAI LLM planner stream failed.",
                            details={
                                "status_code": response.status_code,
                                "response": body[:1000],
                            },
                        )
                    async for line in response.aiter_lines():
                        delta = _stream_delta_from_line(line)
                        if not delta:
                            continue
                        raw_chunks.append(delta)
                        yield {"type": "planning_delta", "delta": delta}
        except httpx.HTTPError as exc:
            raise ToolExecutionError(
                "OpenAI LLM planner stream failed.",
                details={"error": exc.__class__.__name__, "message": str(exc)},
            ) from exc

        raw_text = "".join(raw_chunks).strip()
        yield {
            "type": "planning_step",
            "label": "Plan received",
            "message": "Validating the streamed JSON tool plan before execution.",
        }
        try:
            yield {"type": "plan", "plan": _assistant_plan_from_text(raw_text)}
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise ToolExecutionError(
                "OpenAI LLM planner returned an invalid streamed assistant plan.",
                details={"response_text": raw_text[:1000]},
            ) from exc

    async def synthesize(
        self,
        *,
        message: str,
        context: dict[str, Any],
        plan: AssistantPlan,
        tool_results: list[dict[str, Any]],
        findings: list[dict[str, Any]],
        evidence_summary: list[dict[str, Any]],
    ) -> str:
        """Generate the user-facing answer from executed backend tool results."""

        if not self.api_key:
            raise DependencyUnavailableError(
                "OpenAI LLM synthesis requires OJT_OPENAI_API_KEY or OPENAI_API_KEY."
            )
        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": SYNTHESIS_PROMPT}],
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
                                    "plan": plan.model_dump(mode="json"),
                                    "tool_results": tool_results,
                                    "findings": findings,
                                    "evidence_summary": evidence_summary,
                                },
                                ensure_ascii=False,
                            ),
                        }
                    ],
                },
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/responses",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise ToolExecutionError(
                "OpenAI LLM synthesis request failed.",
                details={"error": exc.__class__.__name__, "message": str(exc)},
            ) from exc
        if response.status_code >= 400:
            raise ToolExecutionError(
                "OpenAI LLM synthesis request failed.",
                details={"status_code": response.status_code, "response": response.text[:1000]},
            )
        answer = _response_text(response.json()).strip()
        if not answer:
            raise ToolExecutionError("OpenAI LLM synthesis returned an empty answer.")
        return answer

    async def synthesize_stream(
        self,
        *,
        message: str,
        context: dict[str, Any],
        plan: AssistantPlan,
        tool_results: list[dict[str, Any]],
        findings: list[dict[str, Any]],
        evidence_summary: list[dict[str, Any]],
    ):
        """Stream the user-facing answer from OpenAI Responses API SSE events."""

        if not self.api_key:
            raise DependencyUnavailableError(
                "OpenAI LLM synthesis requires OJT_OPENAI_API_KEY or OPENAI_API_KEY."
            )
        payload = {
            "model": self.model,
            "stream": True,
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": SYNTHESIS_PROMPT}],
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
                                    "plan": plan.model_dump(mode="json"),
                                    "tool_results": tool_results,
                                    "findings": findings,
                                    "evidence_summary": evidence_summary,
                                },
                                ensure_ascii=False,
                            ),
                        }
                    ],
                },
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/responses",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                ) as response:
                    if response.status_code >= 400:
                        body = (await response.aread()).decode("utf-8", errors="replace")
                        raise ToolExecutionError(
                            "OpenAI LLM synthesis stream failed.",
                            details={
                                "status_code": response.status_code,
                                "response": body[:1000],
                            },
                        )
                    async for line in response.aiter_lines():
                        delta = _stream_delta_from_line(line)
                        if delta:
                            yield delta
        except httpx.HTTPError as exc:
            raise ToolExecutionError(
                "OpenAI LLM synthesis stream failed.",
                details={"error": exc.__class__.__name__, "message": str(exc)},
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
                        "arguments_json": {
                            "type": "string",
                            "description": (
                                "JSON object string containing arguments for the selected tool."
                            ),
                        },
                        "rationale": {"type": "string"},
                    },
                    "required": ["tool_name", "arguments_json", "rationale"],
                    "additionalProperties": False,
                },
            },
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["message", "tool_calls", "warnings"],
        "additionalProperties": False,
    }


def _plan_payload(
    *,
    model: str,
    message: str,
    context: dict,
    tools: list[AssistantToolSpec],
    max_tool_calls: int,
) -> dict[str, Any]:
    return {
        "model": model,
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


def _assistant_plan_from_text(raw_text: str) -> AssistantPlan:
    plan_payload = json.loads(raw_text)
    return AssistantPlan(
        message=str(plan_payload.get("message") or ""),
        tool_calls=[
            AssistantToolPlan(
                tool_name=item.get("tool_name"),
                arguments=_tool_arguments(item),
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


def _tool_arguments(item: dict[str, Any]) -> dict[str, Any]:
    legacy_arguments = item.get("arguments")
    if isinstance(legacy_arguments, dict):
        return legacy_arguments
    raw_arguments = item.get("arguments_json")
    if not isinstance(raw_arguments, str) or not raw_arguments.strip():
        return {}
    try:
        parsed = json.loads(raw_arguments)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


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


def _stream_delta_from_line(line: str) -> str:
    stripped = line.strip()
    if not stripped.startswith("data:"):
        return ""
    raw = stripped.removeprefix("data:").strip()
    if not raw or raw == "[DONE]":
        return ""
    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        return ""
    if event.get("type") != "response.output_text.delta":
        return ""
    delta = event.get("delta")
    return delta if isinstance(delta, str) else ""
