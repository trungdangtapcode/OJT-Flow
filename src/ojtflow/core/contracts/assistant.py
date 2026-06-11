"""Contracts for natural-language assistant and tool orchestration."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel, NonBlankStr
from ojtflow.core.ids import new_id
from ojtflow.core.time import utc_now


AssistantToolStatus = Literal["completed", "failed", "requires_approval", "skipped"]
AssistantFindingSeverity = Literal["info", "warning", "error", "action_required"]
AssistantMessageRole = Literal["user", "assistant", "system", "tool"]


class AssistantToolSpec(ContractModel):
    """Model-visible tool contract for assistant planning."""

    name: str
    description: str
    permission_scope: str
    permission_tags: list[str] = Field(default_factory=list)
    risk_level: str = "low"
    approval_reason: str | None = None
    requires_approval: bool = False
    input_schema: dict[str, Any] = Field(default_factory=dict)


class AssistantToolPlan(ContractModel):
    """A proposed tool call from deterministic or LLM planning."""

    tool_name: NonBlankStr
    arguments: dict[str, Any] = Field(default_factory=dict)
    rationale: str = ""


class AssistantToolResult(ContractModel):
    """Executed or skipped assistant tool call."""

    tool_name: str
    status: AssistantToolStatus
    arguments: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    summary: str = ""
    error: str | None = None
    requires_approval: bool = False


class AssistantFinding(ContractModel):
    """Operator-ready finding synthesized from tool outputs."""

    title: str
    detail: str
    severity: AssistantFindingSeverity = "info"
    source_tool: str | None = None
    source_ids: list[str] = Field(default_factory=list)


class AssistantEvidenceSummary(ContractModel):
    """Compact evidence item for assistant answers."""

    source_id: str
    claim: str
    trust_level: str
    confidence: float | None = None
    match_explanation: dict[str, Any] = Field(default_factory=dict)


class AssistantPlan(ContractModel):
    """Validated LLM/deterministic plan before backend execution."""

    message: str
    tool_calls: list[AssistantToolPlan] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AssistantExample(ContractModel):
    """Data-driven starter task for the Assistant UI."""

    example_id: NonBlankStr
    label: NonBlankStr
    description: NonBlankStr
    message: NonBlankStr
    context: dict[str, Any] = Field(default_factory=dict)


class AssistantChatSessionSummary(ContractModel):
    """Persisted Assistant chat session summary."""

    session_id: str = Field(default_factory=lambda: new_id("chat"))
    owner_user_id: str
    title: str
    message_count: int = 0
    archived_at: str | None = None
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())
    updated_at: str = Field(default_factory=lambda: utc_now().isoformat())


class AssistantChatMessage(ContractModel):
    """Persisted Assistant chat message or tool artifact."""

    message_id: str = Field(default_factory=lambda: new_id("msg"))
    session_id: str
    owner_user_id: str
    role: AssistantMessageRole
    content: str = ""
    workflow_refs: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


class AssistantStreamReplay(ContractModel):
    """Persisted SSE timeline for replay/debugging."""

    stream_id: str
    session_id: str
    owner_user_id: str
    status: Literal["completed", "failed"]
    events: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str
    completed_at: str


class AssistantChatSessionDetail(ContractModel):
    """Persisted Assistant session with ordered messages."""

    session: AssistantChatSessionSummary
    messages: list[AssistantChatMessage] = Field(default_factory=list)


class AssistantResponse(ContractModel):
    """Public assistant response."""

    message: str
    mode: Literal["deterministic", "llm"]
    synthesis_mode: Literal["deterministic", "llm"] = "deterministic"
    model: str | None = None
    findings: list[AssistantFinding] = Field(default_factory=list)
    evidence_summary: list[AssistantEvidenceSummary] = Field(default_factory=list)
    tool_calls: list[AssistantToolResult] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
