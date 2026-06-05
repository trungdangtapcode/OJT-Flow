"""Contracts for natural-language assistant and tool orchestration."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel, NonBlankStr


AssistantToolStatus = Literal["completed", "failed", "requires_approval", "skipped"]
AssistantFindingSeverity = Literal["info", "warning", "error", "action_required"]


class AssistantToolSpec(ContractModel):
    """Model-visible tool contract for assistant planning."""

    name: str
    description: str
    permission_scope: str
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


class AssistantPlan(ContractModel):
    """Validated LLM/deterministic plan before backend execution."""

    message: str
    tool_calls: list[AssistantToolPlan] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AssistantResponse(ContractModel):
    """Public assistant response."""

    message: str
    mode: Literal["deterministic", "llm"]
    model: str | None = None
    findings: list[AssistantFinding] = Field(default_factory=list)
    evidence_summary: list[AssistantEvidenceSummary] = Field(default_factory=list)
    tool_calls: list[AssistantToolResult] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
