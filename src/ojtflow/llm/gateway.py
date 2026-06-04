"""Groq LLM Gateway with agentic tool-use loop.

Flow:
  1. User message → Groq with tool definitions
  2. Groq returns tool_calls → execute Python functions
  3. Send results back to Groq → Groq writes final answer
  4. Return answer + tool call trace to caller
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from groq import Groq

from ojtflow.llm.tools import TOOL_DEFINITIONS, execute_tool

SYSTEM_PROMPT = """\
You are OJTFlow AI, a healthcare data assistant.
You help users understand, validate, and convert structured healthcare data (CSV, JSON, YAML).

Rules:
- Always use tools to work with data — never guess field names or values.
- When validating data, report all issues clearly with their severity.
- If PHI (patient data) is detected, warn the user before proceeding.
- Only cite evidence from the search_knowledge tool — never invent clinical facts.
- Be concise. Lead with the key finding, then details.
- Respond in the same language as the user.
"""

MAX_TOOL_ROUNDS = 5


@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any]
    result: str


@dataclass
class GatewayResponse:
    answer: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)


def chat(
    user_message: str,
    api_key: str,
    model: str = "llama-3.3-70b-versatile",
    history: list[dict[str, Any]] | None = None,
) -> GatewayResponse:
    """Send a message to Groq and execute any tool calls it makes.

    Args:
        user_message: The user's message.
        api_key: Groq API key.
        model: Groq model to use.
        history: Optional prior conversation messages for multi-turn chat.

    Returns:
        GatewayResponse with the final answer and tool call trace.
    """
    client = Groq(api_key=api_key)

    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    tool_calls_trace: list[ToolCall] = []
    final_model = model
    final_usage: dict[str, int] = {}

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            temperature=0.2,
        )

        choice = response.choices[0]
        final_model = response.model
        if response.usage:
            final_usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        # No more tool calls — return the text answer
        if choice.finish_reason == "stop" or not choice.message.tool_calls:
            return GatewayResponse(
                answer=choice.message.content or "",
                tool_calls=tool_calls_trace,
                model=final_model,
                usage=final_usage,
            )

        # Execute each tool call and collect results
        assistant_msg: dict[str, Any] = {
            "role": "assistant",
            "content": choice.message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in choice.message.tool_calls
            ],
        }
        messages.append(assistant_msg)

        for tc in choice.message.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            result = execute_tool(tc.function.name, args)

            tool_calls_trace.append(
                ToolCall(name=tc.function.name, arguments=args, result=result)
            )

            messages.append(
                {"role": "tool", "tool_call_id": tc.id, "content": result}
            )

    # Exceeded MAX_TOOL_ROUNDS — return whatever we have
    return GatewayResponse(
        answer="(max tool rounds exceeded — partial response)",
        tool_calls=tool_calls_trace,
        model=final_model,
        usage=final_usage,
    )
