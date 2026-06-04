"""MCP server: workflow audit and history tools.

Exposes read-only access to workflow history, events, and audit records
so an AI agent can reconstruct what happened during a workflow.

Run locally:
    python -m ojtflow.mcp_servers.workflow_audit_server
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from ojtflow.config import get_settings
from ojtflow.infrastructure.storage.sqlite import (
    SQLiteBackboneStore,
    SQLiteEventRepository,
    SQLiteWorkflowRepository,
)

mcp = FastMCP(
    "ojtflow-workflow-audit",
    instructions=(
        "Read-only tools for inspecting workflow history, audit events, and step timelines. "
        "Use these to answer questions like 'what happened in this workflow?' or "
        "'which workflows are waiting for review?'. "
        "Never mutate workflow state through this server — use the OJTFlow API for that."
    ),
)


def _get_repos() -> tuple[SQLiteWorkflowRepository, SQLiteEventRepository]:
    settings = get_settings()
    backbone = SQLiteBackboneStore(
        settings.resolved_database_path,
        settings.resolved_data_dir,
    )
    return SQLiteWorkflowRepository(backbone), SQLiteEventRepository(backbone)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def list_workflows(
    status: str | None = None,
    limit: int = 10,
    offset: int = 0,
) -> dict[str, Any]:
    """List recent workflows with their current status.

    Args:
        status: Optional filter — one of 'created', 'running', 'needs_human_review',
                'completed', 'failed', 'cancelled'.
        limit: Maximum number of results (default 10, max 50).
        offset: Pagination offset.

    Returns:
        workflows: List of workflow summaries.
        total: Total count matching the filter.
    """
    limit = min(limit, 50)
    workflow_repo, _ = _get_repos()
    page = workflow_repo.list_workflows(
        status_filter=status,
        limit=limit,
        offset=offset,
    )
    workflows_out = [
        {
            "workflow_id": w.workflow_id,
            "status": w.status,
            "created_at": w.created_at,
            "updated_at": w.updated_at,
            "step_count": w.step_count,
            "issue_count": w.issue_count,
            "requires_review": w.requires_review,
        }
        for w in page.items
    ]
    return {
        "workflows": workflows_out,
        "total": page.total,
        "limit": limit,
        "offset": offset,
    }


@mcp.tool()
def get_workflow_detail(workflow_id: str) -> dict[str, Any]:
    """Get the full state of a specific workflow.

    Args:
        workflow_id: The workflow ID (e.g. 'wf_abc123').

    Returns:
        Full workflow state including steps, validation report, and review status.
    """
    workflow_repo, _ = _get_repos()
    state = workflow_repo.get_workflow(workflow_id)
    if state is None:
        return {"found": False, "workflow_id": workflow_id}

    steps_out = [
        {
            "step_id": step.step_id,
            "name": step.name,
            "status": step.status,
            "started_at": step.started_at,
            "completed_at": step.completed_at,
            "summary": step.summary,
            "issue_count": step.issue_count,
        }
        for step in (state.steps or [])
    ]

    review_out = None
    if state.review:
        review_out = {
            "review_id": state.review.review_id,
            "status": state.review.status.value,
            "trigger": state.review.trigger,
            "question": state.review.question,
            "proposed_action": state.review.proposed_action,
            "decision": state.review.decision.value if state.review.decision else None,
            "decided_by": state.review.decided_by,
            "decided_at": state.review.decided_at,
        }

    validation_out = None
    if state.validation_report:
        validation_out = {
            "valid": state.validation_report.valid,
            "schema_id": state.validation_report.schema_id,
            "requires_review": state.validation_report.requires_review,
            "severity_summary": state.validation_report.severity_summary,
            "issue_count": len(state.validation_report.issues),
        }

    return {
        "found": True,
        "workflow_id": state.workflow_id,
        "status": state.status.value,
        "created_at": state.created_at,
        "updated_at": state.updated_at,
        "steps": steps_out,
        "review": review_out,
        "validation_report": validation_out,
        "failure": state.failure.model_dump() if state.failure else None,
    }


@mcp.tool()
def get_workflow_events(workflow_id: str, limit: int = 20) -> dict[str, Any]:
    """Get the audit event timeline for a specific workflow.

    Each event records an action that occurred during workflow execution.
    Events are append-only and form the authoritative audit trail.

    Args:
        workflow_id: The workflow ID.
        limit: Maximum number of events to return (default 20, max 100).

    Returns:
        events: Chronological list of audit events.
        count: Number of events returned.
    """
    limit = min(limit, 100)
    _, event_repo = _get_repos()
    events = event_repo.list_events(workflow_id, limit=limit)

    events_out = [
        {
            "event_id": ev.event_id,
            "timestamp": ev.timestamp,
            "event_type": ev.event_type,
            "actor_type": ev.actor_type,
            "actor_id": ev.actor_id,
            "severity": ev.severity,
            "summary": ev.summary,
        }
        for ev in events
    ]
    return {"events": events_out, "count": len(events_out), "workflow_id": workflow_id}


@mcp.tool()
def get_pending_reviews() -> dict[str, Any]:
    """List all workflows currently waiting for human review.

    Returns:
        pending: List of workflows in NEEDS_HUMAN_REVIEW status.
        count: Number of pending reviews.
    """
    workflow_repo, _ = _get_repos()
    page = workflow_repo.list_workflows(status_filter="needs_human_review", limit=50, offset=0)

    pending_out = [
        {
            "workflow_id": w.workflow_id,
            "created_at": w.created_at,
            "updated_at": w.updated_at,
        }
        for w in page.items
    ]
    return {"pending": pending_out, "count": len(pending_out)}


@mcp.tool()
def generate_audit_summary(workflow_id: str) -> dict[str, Any]:
    """Generate a human-readable audit summary for a completed workflow.

    Reconstructs the full story: what was submitted, what happened at each step,
    whether review was required, and what decision was made.

    Args:
        workflow_id: The workflow ID to summarise.

    Returns:
        summary: Structured audit narrative suitable for review reports.
    """
    workflow_repo, event_repo = _get_repos()
    state = workflow_repo.get_workflow(workflow_id)
    if state is None:
        return {"found": False, "workflow_id": workflow_id}

    events = event_repo.list_events(workflow_id, limit=100)
    step_names = [step.name for step in (state.steps or [])]
    event_types = [ev.event_type for ev in events]

    review_summary = None
    if state.review:
        review_summary = {
            "triggered_by": state.review.trigger,
            "question": state.review.question,
            "decision": state.review.decision.value if state.review.decision else "pending",
            "decided_by": state.review.decided_by,
        }

    return {
        "found": True,
        "workflow_id": workflow_id,
        "final_status": state.status.value,
        "steps_executed": step_names,
        "event_count": len(events),
        "event_types_seen": list(dict.fromkeys(event_types)),
        "review_required": state.review is not None,
        "review_summary": review_summary,
        "validation_passed": (
            state.validation_report.valid if state.validation_report else None
        ),
        "created_at": state.created_at,
        "updated_at": state.updated_at,
    }


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


@mcp.resource("ojtflow://audit/workflow-statuses")
def workflow_statuses_resource() -> str:
    """All valid workflow status values."""
    statuses = [
        "created", "running", "needs_human_review",
        "approved", "rejected", "completed", "failed", "cancelled",
    ]
    return json.dumps({"statuses": statuses})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "7004"))
    if transport == "http":
        mcp.run(transport="streamable-http", host=host, port=port)
    else:
        mcp.run()
