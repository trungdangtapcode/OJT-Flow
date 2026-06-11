"""Workflow event contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.contracts.enums import ActorType, EventType, Severity
from ojtflow.core.ids import new_id
from ojtflow.core.time import utc_now


class WorkflowEvent(ContractModel):
    """Append-only event emitted by workflows, agents, and tools."""

    event_id: str = Field(default_factory=lambda: new_id("evt"))
    workflow_id: str
    request_id: str | None = None
    timestamp: str = Field(default_factory=lambda: utc_now().isoformat())
    actor_type: ActorType
    actor_id: str
    event_type: EventType
    severity: Severity = Severity.INFO
    summary: str
    input_refs: list[str] = Field(default_factory=list)
    output_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
