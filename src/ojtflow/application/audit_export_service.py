"""Audit export package assembly."""

from __future__ import annotations

from collections.abc import Sequence

from ojtflow.core.contracts.audit import (
    AuditEventLikeAgent,
    AuditEventLikeEntity,
    AuditEventLikeRecord,
    AuditEventLikeSource,
    AuditExportCoverageItem,
    AuditExportFilters,
    AuditExportPackage,
    AuditExportSummary,
    AuditRecord,
)
from ojtflow.core.contracts.events import WorkflowEvent


def build_audit_export_package(
    *,
    owner_user_id: str,
    filters: AuditExportFilters,
    records: Sequence[AuditRecord],
    workflow_events: Sequence[WorkflowEvent],
    workflow_event_limitations: Sequence[str] = (),
) -> AuditExportPackage:
    """Build an owner-scoped audit export package from persisted audit sources."""

    record_list = list(records)
    event_list = list(workflow_events)
    audit_events_like = build_audit_event_like_records(
        records=record_list,
        workflow_events=event_list,
    )
    coverage = _coverage_items(
        records=record_list,
        workflow_events=event_list,
        filters=filters,
        workflow_event_limitations=list(workflow_event_limitations),
    )
    summary = AuditExportSummary(
        record_count=len(record_list),
        workflow_event_count=len(event_list),
        audit_event_like_count=len(audit_events_like),
        covered_scope_count=sum(1 for item in coverage if item.status == "covered"),
        partial_scope_count=sum(1 for item in coverage if item.status == "partial"),
        unavailable_scope_count=sum(
            1 for item in coverage if item.status == "not_available"
        ),
        includes_raw_payloads=False,
    )
    return AuditExportPackage(
        owner_user_id=owner_user_id,
        filters=filters,
        summary=summary,
        coverage=coverage,
        records=record_list,
        workflow_events=event_list,
        audit_events_like=audit_events_like,
    )


def build_audit_event_like_records(
    *,
    records: Sequence[AuditRecord],
    workflow_events: Sequence[WorkflowEvent],
) -> list[AuditEventLikeRecord]:
    """Project generic audit and workflow events into FHIR AuditEvent-like records."""

    projected: list[AuditEventLikeRecord] = []
    projected.extend(_audit_event_like_from_workflow_event(event) for event in workflow_events)
    projected.extend(_audit_event_like_from_audit_record(record) for record in records)
    return projected


def _audit_event_like_from_workflow_event(event: WorkflowEvent) -> AuditEventLikeRecord:
    category = (
        "review_event"
        if str(event.event_type).startswith("review.")
        else "workflow_event"
    )
    entities = [
        AuditEventLikeEntity(
            what=event.workflow_id,
            type="workflow",
            role="subject",
        ),
        AuditEventLikeEntity(
            what=event.event_id,
            type="workflow_event",
            role="source",
            detail={"event_type": event.event_type.value},
        ),
    ]
    for ref in event.input_refs:
        entities.append(AuditEventLikeEntity(what=ref, type="artifact", role="input"))
    for ref in event.output_refs:
        entities.append(AuditEventLikeEntity(what=ref, type="artifact", role="output"))
    review_id = event.metadata.get("review_id")
    if isinstance(review_id, str):
        entities.append(AuditEventLikeEntity(what=review_id, type="review", role="target"))
    return AuditEventLikeRecord(
        category=category,
        action=_audit_event_action_for_workflow_event(event),
        recorded=event.timestamp,
        outcome=_audit_event_outcome_for_workflow_event(event),
        outcome_desc=event.summary,
        workflow_id=event.workflow_id,
        request_id=event.request_id,
        source_event_ref=event.event_id,
        agent=[
            AuditEventLikeAgent(
                who=event.actor_id,
                type=event.actor_type.value,
                requestor=event.actor_type.value == "user",
                role="workflow_actor",
            )
        ],
        source=AuditEventLikeSource(observer="ojtflow.workflow_events"),
        entity=entities,
        metadata={
            "event_type": event.event_type.value,
            "severity": event.severity.value,
            "metadata_keys": sorted(event.metadata),
        },
    )


def _audit_event_like_from_audit_record(record: AuditRecord) -> AuditEventLikeRecord:
    entities = []
    if record.workflow_id:
        entities.append(
            AuditEventLikeEntity(what=record.workflow_id, type="workflow", role="subject")
        )
    for event_ref in record.workflow_event_refs:
        entities.append(
            AuditEventLikeEntity(what=event_ref, type="workflow_event", role="source")
        )
    if record.assistant_session_id:
        entities.append(
            AuditEventLikeEntity(
                what=record.assistant_session_id,
                type="assistant_session",
                role="context",
            )
        )
    if record.assistant_message_id:
        entities.append(
            AuditEventLikeEntity(
                what=record.assistant_message_id,
                type="assistant_message",
                role="context",
            )
        )
    if record.input_hash:
        entities.append(
            AuditEventLikeEntity(
                what=record.input_hash,
                type="hash",
                role="input_hash",
                detail={"algorithm": "sha256"},
            )
        )
    if record.output_hash:
        entities.append(
            AuditEventLikeEntity(
                what=record.output_hash,
                type="hash",
                role="output_hash",
                detail={"algorithm": "sha256"},
            )
        )
    return AuditEventLikeRecord(
        category=_audit_event_category_for_audit_record(record),
        action=_audit_event_action_for_audit_record(record),
        recorded=record.timestamp,
        outcome=_audit_event_outcome_for_status(record.status),
        outcome_desc=record.status,
        workflow_id=record.workflow_id,
        request_id=record.request_id,
        source_record_ref=record.audit_id,
        agent=[
            AuditEventLikeAgent(
                who=record.actor_id,
                type=record.actor_type,
                requestor=record.actor_type in {"user", "assistant", "mcp"},
                role="audit_actor",
            )
        ],
        source=AuditEventLikeSource(observer="ojtflow.audit_records"),
        entity=entities,
        metadata={
            "action": record.action,
            "status": record.status,
            "chain_scope": record.chain_scope,
            "chain_sequence": record.chain_sequence,
            "chain_status": record.chain_status,
            "metadata_keys": sorted(record.metadata),
        },
    )


def _coverage_items(
    *,
    records: list[AuditRecord],
    workflow_events: list[WorkflowEvent],
    filters: AuditExportFilters,
    workflow_event_limitations: list[str],
) -> list[AuditExportCoverageItem]:
    assistant_records = [
        record for record in records if _is_assistant_tool_record(record)
    ]
    workflow_records = [
        record
        for record in records
        if record.workflow_id or record.workflow_event_refs or _is_workflow_record(record)
    ]
    review_records = [record for record in records if _is_review_record(record)]
    review_events = [
        event for event in workflow_events if str(event.event_type).startswith("review.")
    ]
    auth_records = [record for record in records if record.action.startswith("auth.")]
    settings_records = [
        record
        for record in records
        if record.action.startswith("settings.")
        or record.action.startswith("runtime.settings.")
    ]
    source_records = [record for record in records if _is_source_ingestion_record(record)]

    workflow_limitations = list(workflow_event_limitations)
    if not filters.workflow_id:
        workflow_limitations.append(
            "Workflow event streams are included only when workflow_id is supplied."
        )

    return [
        AuditExportCoverageItem(
            scope="workflows",
            status="partial",
            record_count=len(workflow_records),
            event_count=len(workflow_events),
            description=(
                "Exports workflow-correlated generic audit records and, when "
                "workflow_id is provided, the append-only workflow event stream."
            ),
            limitations=workflow_limitations,
        ),
        AuditExportCoverageItem(
            scope="reviews",
            status="partial",
            record_count=len(review_records),
            event_count=len(review_events),
            description=(
                "Exports review-related generic audit records and review workflow "
                "events such as review.requested and review.decided."
            ),
            limitations=[
                "Review API mutations are not yet mirrored into dedicated generic audit records."
            ],
        ),
        AuditExportCoverageItem(
            scope="assistant_tool_calls",
            status="covered",
            record_count=len(assistant_records),
            event_count=0,
            description=(
                "Assistant and local MCP tool calls write sanitized generic audit "
                "records with input/output hashes and correlation metadata."
            ),
            limitations=[
                "Raw tool arguments and raw tool output are intentionally excluded."
            ],
        ),
        AuditExportCoverageItem(
            scope="auth_events",
            status="covered" if auth_records else "not_available",
            record_count=len(auth_records),
            event_count=0,
            description="Exports authentication audit records when auth producers are present.",
            limitations=(
                []
                if auth_records
                else ["Auth routes do not yet write generic audit records."]
            ),
        ),
        AuditExportCoverageItem(
            scope="setting_changes",
            status="covered" if settings_records else "not_available",
            record_count=len(settings_records),
            event_count=0,
            description="Exports runtime setting change records when settings producers are present.",
            limitations=(
                []
                if settings_records
                else ["Runtime setting routes do not yet write generic audit records."]
            ),
        ),
        AuditExportCoverageItem(
            scope="source_ingestion",
            status="partial" if source_records else "not_available",
            record_count=len(source_records),
            event_count=0,
            description=(
                "Exports source-ingestion and retrieval-reindex records when "
                "producers exist."
            ),
            limitations=(
                [
                    "Source ingestion coverage is limited to generic audit records "
                    "and does not include a full ingestion manifest snapshot."
                ]
                if source_records
                else [
                    "Source ingestion and retrieval reindex routes do not yet write "
                    "generic audit records."
                ]
            ),
        ),
    ]


def _is_assistant_tool_record(record: AuditRecord) -> bool:
    return record.action.startswith("assistant.tool.") or record.action.startswith(
        "mcp.tool."
    )


def _is_workflow_record(record: AuditRecord) -> bool:
    return record.action.startswith("workflow.") or record.action.startswith(
        "mcp.tool.start_workflow"
    )


def _is_review_record(record: AuditRecord) -> bool:
    if record.action.startswith("review.") or ".review." in record.action:
        return True
    return bool(record.metadata.get("review_id"))


def _is_source_ingestion_record(record: AuditRecord) -> bool:
    prefixes = (
        "source.",
        "ingestion.",
        "retrieval.reindex",
        "retrieval.source.",
        "jobs.retrieval_reindex",
    )
    return record.action.startswith(prefixes)


def _audit_event_category_for_audit_record(record: AuditRecord) -> str:
    if _is_assistant_tool_record(record):
        return "tool_execution"
    if _is_review_record(record):
        return "review_event"
    if record.action.startswith("auth."):
        return "auth_event"
    if record.action.startswith("settings.") or record.action.startswith(
        "runtime.settings."
    ):
        return "setting_change"
    if _is_source_ingestion_record(record):
        return "source_ingestion"
    return "generic_audit_record"


def _audit_event_action_for_workflow_event(event: WorkflowEvent) -> str:
    event_type = event.event_type.value
    if event_type.endswith(".created") or event_type == "review.requested":
        return "C"
    if event_type in {"review.decided", "transformation.completed"}:
        return "U"
    return "E"


def _audit_event_action_for_audit_record(record: AuditRecord) -> str:
    action = record.action.lower()
    if any(token in action for token in (".create", ".created", "login", "callback")):
        return "C"
    if any(token in action for token in (".update", ".rollback", ".approve", ".decide")):
        return "U"
    if any(token in action for token in (".delete", ".revoke", "logout")):
        return "D"
    if any(token in action for token in (".read", ".list", ".get", ".export")):
        return "R"
    return "E"


def _audit_event_outcome_for_workflow_event(event: WorkflowEvent) -> str:
    if event.severity.value in {"error", "critical"}:
        return "serious_failure"
    if event.severity.value == "warning":
        return "minor_failure"
    return "success"


def _audit_event_outcome_for_status(status: str) -> str:
    normalized = status.lower()
    if normalized in {"failed", "error", "rejected", "cancelled"}:
        return "serious_failure"
    if normalized in {"warning", "requires_approval", "partial"}:
        return "minor_failure"
    return "success"
