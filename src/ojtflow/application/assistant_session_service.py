"""Use cases for persisted Assistant chat sessions."""

from __future__ import annotations

from typing import Any

from ojtflow.application.ports import AssistantSessionRepository
from ojtflow.core.contracts.assistant import (
    AssistantChatMessage,
    AssistantChatSessionDetail,
    AssistantChatSessionSummary,
    AssistantMessageRole,
    AssistantStreamReplay,
)
from ojtflow.core.time import utc_now

MAX_WORKFLOW_REFS_PER_MESSAGE = 50
MAX_SESSION_SEARCH_CHARS = 160
WORKFLOW_REF_PAYLOAD_KEYS = frozenset(
    {"workflow_id", "workflow_ids", "workflow_ref", "workflow_refs"}
)


class AssistantSessionService:
    """Manage user-owned Assistant chat sessions."""

    def __init__(self, repository: AssistantSessionRepository) -> None:
        self.repository = repository

    def create_session(
        self,
        *,
        owner_user_id: str,
        title: str = "New chat",
    ) -> AssistantChatSessionSummary:
        return self.repository.create_session(
            owner_user_id=owner_user_id,
            title=_clean_title(title),
        )

    def list_sessions(
        self,
        *,
        owner_user_id: str,
        include_archived: bool = False,
        limit: int = 100,
        q: str | None = None,
    ) -> list[AssistantChatSessionSummary]:
        return self.repository.list_sessions(
            owner_user_id=owner_user_id,
            include_archived=include_archived,
            limit=limit,
            q=_clean_search_query(q),
        )

    def get_session(
        self,
        *,
        owner_user_id: str,
        session_id: str,
    ) -> AssistantChatSessionDetail:
        return self.repository.get_session(
            owner_user_id=owner_user_id,
            session_id=session_id,
        )

    def rename_session(
        self,
        *,
        owner_user_id: str,
        session_id: str,
        title: str,
    ) -> AssistantChatSessionSummary:
        return self.repository.rename_session(
            owner_user_id=owner_user_id,
            session_id=session_id,
            title=_clean_title(title),
        )

    def archive_session(
        self,
        *,
        owner_user_id: str,
        session_id: str,
    ) -> AssistantChatSessionSummary:
        return self.repository.archive_session(
            owner_user_id=owner_user_id,
            session_id=session_id,
        )

    def delete_session(self, *, owner_user_id: str, session_id: str) -> None:
        self.repository.delete_session(
            owner_user_id=owner_user_id,
            session_id=session_id,
        )

    def append_message(
        self,
        *,
        owner_user_id: str,
        session_id: str,
        role: AssistantMessageRole,
        content: str,
        payload: dict[str, Any] | None = None,
        workflow_refs: list[str] | None = None,
    ) -> AssistantChatMessage:
        clean_payload = payload or {}
        return self.repository.append_message(
            owner_user_id=owner_user_id,
            session_id=session_id,
            role=role,
            content=content,
            payload=clean_payload,
            workflow_refs=_clean_workflow_refs(
                workflow_refs or _extract_workflow_refs(clean_payload)
            ),
        )

    def append_stream_replay(
        self,
        *,
        owner_user_id: str,
        session_id: str,
        stream_id: str,
        events: list[dict[str, Any]],
        status: str,
    ) -> AssistantStreamReplay:
        completed_at = utc_now().isoformat()
        replay = AssistantStreamReplay(
            stream_id=stream_id,
            session_id=session_id,
            owner_user_id=owner_user_id,
            status="failed" if status == "failed" else "completed",
            events=events,
            created_at=_first_event_created_at(events) or completed_at,
            completed_at=completed_at,
        )
        return self.repository.append_stream_replay(replay=replay)

    def list_stream_replays(
        self,
        *,
        owner_user_id: str,
        session_id: str,
    ) -> list[AssistantStreamReplay]:
        return self.repository.list_stream_replays(
            owner_user_id=owner_user_id,
            session_id=session_id,
        )


def _clean_title(title: str) -> str:
    clean = " ".join(title.strip().split())
    return clean[:120] if clean else "New chat"


def _clean_search_query(value: str | None) -> str | None:
    if value is None:
        return None
    clean = " ".join(value.strip().split())
    return clean[:MAX_SESSION_SEARCH_CHARS] if clean else None


def _clean_workflow_refs(workflow_refs: list[str]) -> list[str]:
    refs: list[str] = []
    seen: set[str] = set()
    for value in workflow_refs:
        if not isinstance(value, str):
            continue
        ref = value.strip()
        if not ref or ref in seen:
            continue
        seen.add(ref)
        refs.append(ref)
        if len(refs) >= MAX_WORKFLOW_REFS_PER_MESSAGE:
            break
    return refs


def _extract_workflow_refs(value: Any, *, depth: int = 0) -> list[str]:
    if depth > 8:
        return []
    if isinstance(value, dict):
        refs: list[str] = []
        for key, nested in value.items():
            if key in WORKFLOW_REF_PAYLOAD_KEYS:
                refs.extend(_workflow_refs_from_value(nested))
                continue
            refs.extend(_extract_workflow_refs(nested, depth=depth + 1))
        return refs
    if isinstance(value, list):
        refs: list[str] = []
        for item in value:
            refs.extend(_extract_workflow_refs(item, depth=depth + 1))
        return refs
    return []


def _first_event_created_at(events: list[dict[str, Any]]) -> str | None:
    for event in events:
        created_at = event.get("created_at")
        if isinstance(created_at, str) and created_at:
            return created_at
    return None


def _workflow_refs_from_value(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []
