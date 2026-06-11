"""Use cases for persisted Assistant chat sessions."""

from __future__ import annotations

import re
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
DEFAULT_SESSION_TITLE = "New chat"
MAX_GENERATED_TITLE_CHARS = 72
WORKFLOW_REF_PAYLOAD_KEYS = frozenset(
    {"workflow_id", "workflow_ids", "workflow_ref", "workflow_refs"}
)
SENSITIVE_TITLE_PATTERNS = (
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"\b(?:patient|mrn|ssn|dob|email|phone|address)[_-]?[a-z0-9]*\b", re.I),
    re.compile(r"\bP\d{2,}\b", re.I),
)
TITLE_STOPWORDS = {
    "please",
    "this",
    "that",
    "with",
    "from",
    "into",
    "about",
    "tell",
    "show",
    "give",
    "there",
    "their",
    "your",
    "data",
}


class AssistantSessionService:
    """Manage user-owned Assistant chat sessions."""

    def __init__(self, repository: AssistantSessionRepository) -> None:
        self.repository = repository

    def create_session(
        self,
        *,
        owner_user_id: str,
        title: str = DEFAULT_SESSION_TITLE,
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
        detail_before_append = None
        if role == "user":
            detail_before_append = self.repository.get_session(
                owner_user_id=owner_user_id,
                session_id=session_id,
            )
        message = self.repository.append_message(
            owner_user_id=owner_user_id,
            session_id=session_id,
            role=role,
            content=content,
            payload=clean_payload,
            workflow_refs=_clean_workflow_refs(
                workflow_refs or _extract_workflow_refs(clean_payload)
            ),
        )
        if (
            detail_before_append
            and detail_before_append.session.message_count == 0
            and _is_default_title(detail_before_append.session.title)
        ):
            self.repository.rename_session(
                owner_user_id=owner_user_id,
                session_id=session_id,
                title=_generated_session_title(content=content, payload=clean_payload),
            )
        return message

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
        replay_status = (
            "cancelled"
            if status == "cancelled"
            else "failed"
            if status == "failed"
            else "completed"
        )
        replay = AssistantStreamReplay(
            stream_id=stream_id,
            session_id=session_id,
            owner_user_id=owner_user_id,
            status=replay_status,
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
    return clean[:120] if clean else DEFAULT_SESSION_TITLE


def _is_default_title(title: str) -> bool:
    return _clean_title(title).casefold() == DEFAULT_SESSION_TITLE.casefold()


def _generated_session_title(*, content: str, payload: dict[str, Any]) -> str:
    context = payload.get("context") if isinstance(payload.get("context"), dict) else {}
    schema_id = _context_text(context, "schema_id")
    input_format = _context_text(context, "input_format")
    source_format = _attachment_source_format(context)
    title = _intent_title(content)
    qualifiers = [
        _schema_title(schema_id),
        _format_title(input_format or source_format),
    ]
    suffix = " / ".join(part for part in qualifiers if part)
    if suffix:
        title = f"{title} / {suffix}"
    return _clean_generated_title(title)


def _intent_title(content: str) -> str:
    normalized = content.casefold()
    if any(word in normalized for word in ("validate", "check", "quality")):
        return "Validate healthcare data"
    if any(word in normalized for word in ("evidence", "standard", "ucum", "loinc", "search")):
        return "Find trusted evidence"
    if "review" in normalized:
        return "Review work queue"
    if "workflow" in normalized:
        return "Inspect workflow"
    if any(word in normalized for word in ("convert", "transform")):
        return "Convert healthcare data"
    if "fhir" in normalized or "resourcetype" in normalized:
        return "Profile FHIR resource"
    if any(word in normalized for word in ("image", "file", "attached", "extract", "ocr")):
        return "Analyze uploaded data"
    fallback = _safe_title_fragment(content)
    return fallback or "Healthcare data chat"


def _safe_title_fragment(content: str) -> str:
    first_line = content.splitlines()[0] if content.splitlines() else content
    clean = " ".join(first_line.strip().split())
    if not clean:
        return ""
    if any(pattern.search(clean) for pattern in SENSITIVE_TITLE_PATTERNS):
        return "Healthcare data chat"
    words = [
        word.strip(".,:;!?()[]{}\"'")
        for word in clean.split()
        if word.strip(".,:;!?()[]{}\"'")
    ]
    filtered = [
        word
        for word in words
        if word.casefold() not in TITLE_STOPWORDS
        and len(word) > 1
        and not any(char.isdigit() for char in word)
    ]
    fragment = " ".join(filtered[:8]) or " ".join(words[:6])
    return _clean_generated_title(fragment)


def _clean_generated_title(title: str) -> str:
    clean = _clean_title(title)
    if len(clean) <= MAX_GENERATED_TITLE_CHARS:
        return clean
    return f"{clean[: MAX_GENERATED_TITLE_CHARS - 3].rstrip()}..."


def _context_text(context: dict[str, Any], key: str) -> str:
    value = context.get(key)
    return value.strip() if isinstance(value, str) else ""


def _schema_title(schema_id: str) -> str:
    if not schema_id:
        return ""
    normalized = schema_id.replace("_", " ").replace("-", " ").strip()
    return normalized[:32]


def _format_title(input_format: str) -> str:
    normalized = input_format.strip().upper()
    return normalized[:12] if normalized else ""


def _attachment_source_format(context: dict[str, Any]) -> str:
    attachments = context.get("attachments")
    attachment = attachments[0] if isinstance(attachments, list) and attachments else None
    if not isinstance(attachment, dict):
        attachment = context.get("attachment")
    if not isinstance(attachment, dict):
        return ""
    value = attachment.get("source_format")
    return value.strip() if isinstance(value, str) else ""


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
