"""Natural-language assistant route."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ojtflow.application.assistant_service import AssistantService
from ojtflow.config import Settings
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.interfaces.api.deps import (
    get_api_settings,
    get_assistant_service,
    require_authentication,
)
from ojtflow.interfaces.api.limits import enforce_inline_json_limit
from ojtflow.interfaces.api.responses import ok
from ojtflow.interfaces.api.schemas import AssistantChatRequest

router = APIRouter(tags=["assistant"])


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
