"""Natural-language assistant route."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse

from ojtflow.application.assistant_memory_service import (
    AssistantMemoryService,
    merge_assistant_memory_context,
)
from ojtflow.application.assistant_session_service import AssistantSessionService
from ojtflow.application.assistant_service import AssistantService
from ojtflow.config import Settings
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.core.contracts.assistant import AssistantAnswerTemplate
from ojtflow.core.contracts.mcp import (
    McpPromptCatalog,
    McpRemoteDeploymentPolicy,
    McpResourceCatalog,
)
from ojtflow.core.ids import new_id
from ojtflow.core.time import utc_now
from ojtflow.infrastructure.assistant_templates import load_assistant_answer_templates
from ojtflow.infrastructure.assistant_examples import load_assistant_examples
from ojtflow.infrastructure.mcp_catalogs import (
    load_mcp_prompt_catalog,
    load_mcp_remote_deployment_policy,
    load_mcp_resource_catalog,
)
from ojtflow.interfaces.api.deps import (
    get_api_settings,
    get_assistant_memory_service,
    get_assistant_service,
    get_assistant_session_service,
    require_authentication,
)
from ojtflow.interfaces.api.limits import enforce_inline_json_limit
from ojtflow.interfaces.api.responses import ok
from ojtflow.interfaces.api.schemas import (
    AssistantChatRequest,
    AssistantMemoryPreferenceRequest,
    AssistantSessionCreateRequest,
    AssistantSessionMessageRequest,
    AssistantSessionRenameRequest,
)

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


@router.get("/assistant/answer-templates")
async def assistant_answer_templates(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Return governed Assistant answer templates visible to this user."""

    del authenticated
    templates: list[AssistantAnswerTemplate] = load_assistant_answer_templates(
        settings.resolved_knowledge_dir
    )
    return ok(templates)


@router.get("/assistant/mcp/resources")
async def assistant_mcp_resources(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Return data-driven MCP resource specs visible to this user."""

    del authenticated
    catalog: McpResourceCatalog = load_mcp_resource_catalog(settings.resolved_knowledge_dir)
    return ok(catalog)


@router.get("/assistant/mcp/prompts")
async def assistant_mcp_prompts(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Return data-driven MCP prompt specs visible to this user."""

    del authenticated
    catalog: McpPromptCatalog = load_mcp_prompt_catalog(settings.resolved_knowledge_dir)
    return ok(catalog)


@router.get("/assistant/mcp/remote-policy")
async def assistant_mcp_remote_policy(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Return the data-driven remote MCP deployment readiness policy."""

    del authenticated
    policy: McpRemoteDeploymentPolicy = load_mcp_remote_deployment_policy(
        settings.resolved_knowledge_dir
    )
    return ok(policy)


@router.get("/assistant/memory-policy")
async def assistant_memory_policy(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: AssistantMemoryService = Depends(get_assistant_memory_service),
) -> dict:
    """Return the data-driven allowlist for PHI-safe Assistant memory."""

    del authenticated
    return ok(service.memory_policy())


@router.get("/assistant/memory")
async def assistant_memory(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: AssistantMemoryService = Depends(get_assistant_memory_service),
) -> dict:
    """Return the authenticated user's safe Assistant memory snapshot."""

    return ok(service.snapshot(owner_user_id=authenticated.user.user_id))


@router.put("/assistant/memory/{key}")
async def upsert_assistant_memory(
    key: str,
    request: AssistantMemoryPreferenceRequest,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: AssistantMemoryService = Depends(get_assistant_memory_service),
) -> dict:
    """Set one PHI-safe operational Assistant preference."""

    return ok(
        service.upsert_preference(
            owner_user_id=authenticated.user.user_id,
            key=key,
            value=request.value,
            source=request.source,
        )
    )


@router.delete("/assistant/memory/{key}")
async def delete_assistant_memory(
    key: str,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: AssistantMemoryService = Depends(get_assistant_memory_service),
) -> dict:
    """Delete one safe Assistant preference."""

    service.delete_preference(owner_user_id=authenticated.user.user_id, key=key)
    return ok({"deleted": True, "key": key})


@router.get("/assistant/sessions")
async def assistant_sessions(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: AssistantSessionService = Depends(get_assistant_session_service),
    include_archived: bool = False,
    limit: int = Query(default=100, ge=1, le=500),
    q: str | None = Query(default=None, max_length=160),
) -> dict:
    """List persisted Assistant chat sessions for the authenticated user."""

    return ok(
        service.list_sessions(
            owner_user_id=authenticated.user.user_id,
            include_archived=include_archived,
            limit=limit,
            q=q,
        )
    )


@router.post("/assistant/sessions")
async def create_assistant_session(
    request: AssistantSessionCreateRequest,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: AssistantSessionService = Depends(get_assistant_session_service),
) -> dict:
    """Create a persisted Assistant chat session."""

    return ok(
        service.create_session(
            owner_user_id=authenticated.user.user_id,
            title=request.title,
        )
    )


@router.get("/assistant/sessions/{session_id}")
async def get_assistant_session(
    session_id: str,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: AssistantSessionService = Depends(get_assistant_session_service),
) -> dict:
    """Return one persisted Assistant chat session and ordered messages."""

    return ok(
        service.get_session(
            owner_user_id=authenticated.user.user_id,
            session_id=session_id,
        )
    )


@router.get("/assistant/sessions/{session_id}/stream-replays")
async def get_assistant_session_stream_replays(
    session_id: str,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: AssistantSessionService = Depends(get_assistant_session_service),
) -> dict:
    """Return persisted SSE replay artifacts for one Assistant session."""

    return ok(
        service.list_stream_replays(
            owner_user_id=authenticated.user.user_id,
            session_id=session_id,
        )
    )


@router.patch("/assistant/sessions/{session_id}")
async def rename_assistant_session(
    session_id: str,
    request: AssistantSessionRenameRequest,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: AssistantSessionService = Depends(get_assistant_session_service),
) -> dict:
    """Rename a persisted Assistant chat session."""

    return ok(
        service.rename_session(
            owner_user_id=authenticated.user.user_id,
            session_id=session_id,
            title=request.title,
        )
    )


@router.post("/assistant/sessions/{session_id}/archive")
async def archive_assistant_session(
    session_id: str,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: AssistantSessionService = Depends(get_assistant_session_service),
) -> dict:
    """Archive a persisted Assistant chat session."""

    return ok(
        service.archive_session(
            owner_user_id=authenticated.user.user_id,
            session_id=session_id,
        )
    )


@router.delete("/assistant/sessions/{session_id}")
async def delete_assistant_session(
    session_id: str,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: AssistantSessionService = Depends(get_assistant_session_service),
) -> dict:
    """Delete a persisted Assistant chat session and its messages."""

    service.delete_session(
        owner_user_id=authenticated.user.user_id,
        session_id=session_id,
    )
    return ok({"deleted": True, "session_id": session_id})


@router.post("/assistant/sessions/{session_id}/messages")
async def append_assistant_session_message(
    session_id: str,
    request: AssistantSessionMessageRequest,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: AssistantSessionService = Depends(get_assistant_session_service),
) -> dict:
    """Append a persisted Assistant chat message or tool artifact."""

    return ok(
        service.append_message(
            owner_user_id=authenticated.user.user_id,
            session_id=session_id,
            role=request.role,
            content=request.content,
            workflow_refs=request.workflow_refs,
            payload=request.payload,
        )
    )


@router.post("/assistant/chat")
async def assistant_chat(
    request: AssistantChatRequest,
    http_request: Request,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: AssistantService = Depends(get_assistant_service),
    session_service: AssistantSessionService = Depends(get_assistant_session_service),
    memory_service: AssistantMemoryService = Depends(get_assistant_memory_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Use natural language to run allowlisted OJTFlow tools."""

    enforce_inline_json_limit(request, settings, field_name="assistant_request")
    session_id = request.session_id.strip() if request.session_id else None
    if session_id:
        session_service.get_session(
            owner_user_id=authenticated.user.user_id,
            session_id=session_id,
        )
    context = merge_assistant_memory_context(
        request.context,
        memory_service.assistant_context(owner_user_id=authenticated.user.user_id),
    )
    result = await service.chat(
        message=request.message,
        context=context,
        execute_write_actions=request.execute_write_actions,
        owner_user_id=authenticated.user.user_id,
        request_id=getattr(http_request.state, "request_id", None),
        assistant_session_id=session_id,
    )
    return ok(result)


@router.post("/assistant/chat/stream")
async def assistant_chat_stream(
    request: AssistantChatRequest,
    http_request: Request,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: AssistantService = Depends(get_assistant_service),
    session_service: AssistantSessionService = Depends(get_assistant_session_service),
    memory_service: AssistantMemoryService = Depends(get_assistant_memory_service),
    settings: Settings = Depends(get_api_settings),
) -> StreamingResponse:
    """Stream assistant planning, tool calls, answer deltas, and final response."""

    enforce_inline_json_limit(request, settings, field_name="assistant_request")
    session_id = request.session_id.strip() if request.session_id else None
    if session_id:
        session_service.get_session(
            owner_user_id=authenticated.user.user_id,
            session_id=session_id,
        )
    context = merge_assistant_memory_context(
        request.context,
        memory_service.assistant_context(owner_user_id=authenticated.user.user_id),
    )
    stream_id = new_id("astream")
    request_id = getattr(http_request.state, "request_id", None)

    async def events() -> AsyncIterator[str]:
        stream_events: list[dict] = []
        status = "completed"

        def record(event: dict) -> str:
            logged_event = dict(event)
            logged_event.setdefault("stream_id", stream_id)
            logged_event.setdefault("session_id", session_id)
            logged_event.setdefault("request_id", request_id)
            logged_event.setdefault("created_at", utc_now().isoformat())
            logged_event["sequence"] = len(stream_events) + 1
            stream_events.append(logged_event)
            return _sse(logged_event)

        yield record(
            {
                "type": "stream_opened",
                "message": "Assistant stream connected.",
            }
        )
        try:
            async for event in service.chat_stream(
                message=request.message,
                context=context,
                execute_write_actions=request.execute_write_actions,
                owner_user_id=authenticated.user.user_id,
                request_id=request_id,
                assistant_session_id=session_id,
            ):
                if await http_request.is_disconnected():
                    status = "cancelled"
                    record(
                        {
                            "type": "cancelled",
                            "message": "Assistant stream was cancelled by the client.",
                        }
                    )
                    break
                yield record(event)
        except asyncio.CancelledError:
            status = "cancelled"
            record(
                {
                    "type": "cancelled",
                    "message": "Assistant stream was cancelled by the client.",
                }
            )
            raise
        except Exception as exc:
            status = "failed"
            logger.exception("Assistant stream failed")
            yield record(
                {
                    "type": "error",
                    "code": exc.__class__.__name__,
                    "message": "Assistant stream failed before completion.",
                    "details": {"reason": str(exc)},
                }
            )
        finally:
            if session_id:
                try:
                    session_service.append_stream_replay(
                        owner_user_id=authenticated.user.user_id,
                        session_id=session_id,
                        stream_id=stream_id,
                        events=stream_events,
                        status=status,
                    )
                except Exception:  # pragma: no cover - replay persistence is best-effort.
                    logger.exception("Assistant stream replay persistence failed")

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
