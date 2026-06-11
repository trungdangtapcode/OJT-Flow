"""Audit-specific contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.ids import new_id
from ojtflow.core.time import utc_now


class AuditRecord(ContractModel):
    """Security-sensitive audit record."""

    audit_id: str = Field(default_factory=lambda: new_id("aud"))
    owner_user_id: str | None = None
    workflow_id: str | None = None
    workflow_event_refs: list[str] = Field(default_factory=list)
    assistant_session_id: str | None = None
    assistant_message_id: str | None = None
    request_id: str | None = None
    timestamp: str = Field(default_factory=lambda: utc_now().isoformat())
    action: str
    actor_id: str
    actor_type: str = "system"
    status: str = "completed"
    input_hash: str | None = None
    output_hash: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
