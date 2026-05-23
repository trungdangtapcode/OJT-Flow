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
    workflow_id: str
    timestamp: str = Field(default_factory=lambda: utc_now().isoformat())
    action: str
    actor_id: str
    input_hash: str | None = None
    output_hash: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

