"""Audit-specific contracts."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.contracts.events import WorkflowEvent
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
    chain_scope: str | None = None
    chain_sequence: int | None = None
    previous_record_hash: str | None = None
    record_hash: str | None = None
    hash_algorithm: str | None = None
    chain_status: Literal["pending", "linked"] = "pending"
    metadata: dict[str, Any] = Field(default_factory=dict)


AuditExportScope = Literal[
    "workflows",
    "reviews",
    "assistant_tool_calls",
    "auth_events",
    "setting_changes",
    "source_ingestion",
]
AuditExportCoverageStatus = Literal["covered", "partial", "not_available"]


class AuditExportFilters(ContractModel):
    """Filters used to create an audit export package."""

    action: str | None = None
    workflow_id: str | None = None
    assistant_session_id: str | None = None
    limit: int = 100
    include_workflow_events: bool = True


class AuditExportCoverageItem(ContractModel):
    """Coverage statement for one audit domain in the export package."""

    scope: AuditExportScope
    status: AuditExportCoverageStatus
    record_count: int = 0
    event_count: int = 0
    description: str
    limitations: list[str] = Field(default_factory=list)


class AuditExportSummary(ContractModel):
    """Machine-readable export summary for UI and compliance tooling."""

    record_count: int = 0
    workflow_event_count: int = 0
    covered_scope_count: int = 0
    partial_scope_count: int = 0
    unavailable_scope_count: int = 0
    includes_raw_payloads: bool = False


class AuditExportPackage(ContractModel):
    """Owner-scoped JSON audit export package."""

    export_id: str = Field(default_factory=lambda: new_id("audexp"))
    generated_at: str = Field(default_factory=lambda: utc_now().isoformat())
    owner_user_id: str
    export_format: Literal["json"] = "json"
    filters: AuditExportFilters
    summary: AuditExportSummary
    coverage: list[AuditExportCoverageItem]
    records: list[AuditRecord] = Field(default_factory=list)
    workflow_events: list[WorkflowEvent] = Field(default_factory=list)
