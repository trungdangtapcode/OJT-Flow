"""Agent contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.contracts.enums import AgentStatus
from ojtflow.core.contracts.evidence import Evidence
from ojtflow.core.contracts.issue import Issue


class AgentResult(ContractModel):
    """Structured response envelope for all agents."""

    status: AgentStatus
    summary: str
    data: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = None
    issues: list[Issue] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    next_recommended_action: str | None = None

