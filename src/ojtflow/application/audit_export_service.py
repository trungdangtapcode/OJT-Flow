"""Audit export package assembly."""

from __future__ import annotations

from collections.abc import Sequence

from ojtflow.core.contracts.audit import (
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
    coverage = _coverage_items(
        records=record_list,
        workflow_events=event_list,
        filters=filters,
        workflow_event_limitations=list(workflow_event_limitations),
    )
    summary = AuditExportSummary(
        record_count=len(record_list),
        workflow_event_count=len(event_list),
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
