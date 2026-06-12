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
    audit_event_like_count: int = 0
    covered_scope_count: int = 0
    partial_scope_count: int = 0
    unavailable_scope_count: int = 0
    includes_raw_payloads: bool = False


AuditEventLikeCategory = Literal[
    "workflow_event",
    "review_event",
    "auth_event",
    "tool_execution",
    "setting_change",
    "source_ingestion",
    "generic_audit_record",
]


class AuditEventLikeAgent(ContractModel):
    """FHIR AuditEvent-like actor entry."""

    who: str
    type: str
    requestor: bool = False
    role: str | None = None


class AuditEventLikeSource(ContractModel):
    """FHIR AuditEvent-like event source."""

    observer: str = "ojtflow"
    type: str = "application"


class AuditEventLikeEntity(ContractModel):
    """FHIR AuditEvent-like entity reference without raw payload data."""

    what: str
    type: str
    role: str | None = None
    detail: dict[str, Any] = Field(default_factory=dict)


class AuditEventLikeRecord(ContractModel):
    """FHIR AuditEvent-like projection for workflow and generic audit records."""

    audit_event_id: str = Field(default_factory=lambda: new_id("audevt"))
    resourceType: Literal["AuditEvent"] = "AuditEvent"
    category: AuditEventLikeCategory
    action: Literal["C", "R", "U", "D", "E"] = "E"
    recorded: str
    outcome: Literal["success", "minor_failure", "serious_failure"] = "success"
    outcome_desc: str | None = None
    workflow_id: str | None = None
    request_id: str | None = None
    source_event_ref: str | None = None
    source_record_ref: str | None = None
    agent: list[AuditEventLikeAgent] = Field(default_factory=list)
    source: AuditEventLikeSource = Field(default_factory=AuditEventLikeSource)
    entity: list[AuditEventLikeEntity] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


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
    audit_events_like: list[AuditEventLikeRecord] = Field(default_factory=list)
