"""AI chat endpoint powered by Groq LLM with OJTFlow tool use."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ojtflow.config import Settings
from ojtflow.core.errors import OJTFlowError
from ojtflow.interfaces.api.deps import get_api_settings, require_authentication
from ojtflow.interfaces.api.responses import ok
from ojtflow.llm.gateway import chat

router = APIRouter(tags=["ai"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)


class ToolCallSummary(BaseModel):
    name: str
    arguments: dict[str, Any]


class ChatResponse(BaseModel):
    answer: str
    tool_calls: list[ToolCallSummary]
    model: str
    usage: dict[str, int]


@router.post("/ai/chat")
async def ai_chat(
    body: ChatRequest,
    settings: Settings = Depends(get_api_settings),
    _auth=Depends(require_authentication),
) -> dict:
    """Send a natural language message and get an AI response with tool use.

    The AI can call OJTFlow tools (detect_format, validate_dataset,
    convert_data, search_knowledge) to answer questions about data.
    """
    if not settings.groq_api_key:
        raise HTTPException(
            status_code=503,
            detail="GROQ_API_KEY is not configured. Set it in .env to enable AI chat.",
        )

    history = [{"role": m.role, "content": m.content} for m in body.history]

    try:
        result = chat(
            user_message=body.message,
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            history=history or None,
        )
    except Exception as exc:
        raise OJTFlowError(f"AI gateway error: {exc}") from exc

    return ok(
        ChatResponse(
            answer=result.answer,
            tool_calls=[
                ToolCallSummary(name=tc.name, arguments=tc.arguments)
                for tc in result.tool_calls
            ],
            model=result.model,
            usage=result.usage,
        ).model_dump()
    )


@router.get("/ai/status")
async def ai_status(
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Check whether the AI gateway is configured."""
    return ok(
        {
            "configured": bool(settings.groq_api_key),
            "model": settings.groq_model,
            "available_tools": [
                "detect_format",
                "profile_dataset",
                "validate_dataset",
                "convert_data",
                "search_knowledge",
            ],
        }
    )
