"""Natural-language assistant route."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from ojtflow.application.assistant_service import AssistantService
from ojtflow.config import Settings
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.infrastructure.assistant_examples import load_assistant_examples
from ojtflow.interfaces.api.deps import (
    get_api_settings,
    get_assistant_service,
    require_authentication,
)
from ojtflow.interfaces.api.limits import enforce_inline_json_limit
from ojtflow.interfaces.api.responses import ok
from ojtflow.interfaces.api.schemas import AssistantChatRequest

router = APIRouter(tags=["assistant"])
logger = logging.getLogger(__name__)


@router.get("/assistant/tools")
async def assistant_tools(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: AssistantService = Depends(get_assistant_service),
) -> dict:
    """Return the allowlisted assistant/MCP tools visible to this user."""

    del authenticated
    return ok(service.tool_specs)


@router.get("/assistant/examples")
async def assistant_examples(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Return data-driven Assistant starter examples visible to this user."""

    del authenticated
    return ok(load_assistant_examples(settings.resolved_knowledge_dir))


@router.post("/assistant/chat")
async def assistant_chat(
    request: AssistantChatRequest,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: AssistantService = Depends(get_assistant_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Use natural language to run allowlisted OJTFlow tools."""

    enforce_inline_json_limit(request, settings, field_name="assistant_request")
    result = await service.chat(
        message=request.message,
        context=request.context,
        execute_write_actions=request.execute_write_actions,
        owner_user_id=authenticated.user.user_id,
    )
    return ok(result)


@router.post("/assistant/chat/stream")
async def assistant_chat_stream(
    request: AssistantChatRequest,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: AssistantService = Depends(get_assistant_service),
    settings: Settings = Depends(get_api_settings),
) -> StreamingResponse:
    """Stream assistant planning, tool calls, answer deltas, and final response."""

    enforce_inline_json_limit(request, settings, field_name="assistant_request")

    async def events() -> AsyncIterator[str]:
        yield _sse(
            {
                "type": "stream_opened",
                "message": "Assistant stream connected.",
            }
        )
        try:
            async for event in service.chat_stream(
                message=request.message,
                context=request.context,
                execute_write_actions=request.execute_write_actions,
                owner_user_id=authenticated.user.user_id,
            ):
                yield _sse(event)
        except Exception as exc:
            logger.exception("Assistant stream failed")
            yield _sse(
                {
                    "type": "error",
                    "code": exc.__class__.__name__,
                    "message": "Assistant stream failed before completion.",
                    "details": {"reason": str(exc)},
                }
            )

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def _sse(event: dict) -> str:
    return (
        f"event: {event.get('type', 'message')}\n"
        f"data: {json.dumps(event, ensure_ascii=False, separators=(',', ':'))}\n\n"
    )
