"""MCP server: workflow audit and history tools.

Exposes read-only access to workflow history, events, and audit records
so an AI agent can reconstruct what happened during a workflow.

Run locally:
    python -m ojtflow.mcp_servers.workflow_audit_server
"""

from __future__ import annotations

import json
from typing import Any

from fastmcp import FastMCP

from ojtflow.config import get_settings
from ojtflow.core.contracts.enums import WorkflowStatus
from ojtflow.core.errors import NotFoundError
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
) -> dict[str, Any]:
    """List recent workflows with their current status.

    Args:
        status: Optional filter — one of 'created', 'running', 'needs_human_review',
                'completed', 'failed', 'cancelled'.
        limit: Maximum number of results (default 10, max 50).

    Returns:
        workflows: List of workflow summaries.
        count: Total count returned.
    """
    limit = min(limit, 50)
    workflow_repo, _ = _get_repos()

    ws = WorkflowStatus(status) if status else None
    states = workflow_repo.list(status=ws, limit=limit)

    workflows_out = [
        {
            "workflow_id": s.workflow_id,
            "status": s.status.value,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
            "step_count": len(s.steps or []),
            "has_review": s.review is not None,
            "review_status": s.review.status.value if s.review else None,
        }
        for s in states
    ]
    return {"workflows": workflows_out, "count": len(workflows_out)}


@mcp.tool()
def get_workflow_detail(workflow_id: str) -> dict[str, Any]:
    """Get the full state of a specific workflow.

    Args:
        workflow_id: The workflow ID (e.g. 'wf_abc123').

    Returns:
        Full workflow state including steps, validation report, and review status.
    """
    workflow_repo, _ = _get_repos()
    try:
        state = workflow_repo.get(workflow_id)
    except NotFoundError:
        return {"found": False, "workflow_id": workflow_id}

    steps_out = [
        {
            "name": step.name,
            "status": step.status,
            "summary": step.summary,
            "issue_count": step.issue_count,
            "completed_at": step.completed_at,
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
        }

    validation_out = None
    if state.validation_report:
        validation_out = {
            "valid": state.validation_report.valid,
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
    }


@mcp.tool()
def get_workflow_events(workflow_id: str, limit: int = 20) -> dict[str, Any]:
    """Get the audit event timeline for a specific workflow.

    Args:
        workflow_id: The workflow ID.
        limit: Maximum number of events (default 20, max 100).

    Returns:
        events: Chronological list of audit events.
        count: Number of events returned.
    """
    limit = min(limit, 100)
    _, event_repo = _get_repos()
    events = event_repo.list_for_workflow(workflow_id)[:limit]

    events_out = [
        {
            "event_id": ev.event_id,
            "timestamp": ev.timestamp,
            "event_type": ev.event_type.value,
            "actor_id": ev.actor_id,
            "severity": ev.severity.value,
            "summary": ev.summary,
        }
        for ev in events
    ]
    return {"events": events_out, "count": len(events_out), "workflow_id": workflow_id}


@mcp.tool()
def get_pending_reviews() -> dict[str, Any]:
    """List all workflows currently waiting for human review.

    Returns:
        pending: List of workflows needing review with their review question.
        count: Number pending.
    """
    workflow_repo, _ = _get_repos()
    states = workflow_repo.list(status=WorkflowStatus.NEEDS_HUMAN_REVIEW, limit=50)

    pending_out = [
        {
            "workflow_id": s.workflow_id,
            "updated_at": s.updated_at,
            "question": s.review.question if s.review else None,
            "trigger": s.review.trigger if s.review else None,
        }
        for s in states
    ]
    return {"pending": pending_out, "count": len(pending_out)}


@mcp.tool()
def generate_audit_summary(workflow_id: str) -> dict[str, Any]:
    """Generate a human-readable audit summary for a workflow.

    Args:
        workflow_id: The workflow ID to summarise.

    Returns:
        summary: Structured audit narrative.
    """
    workflow_repo, event_repo = _get_repos()
    try:
        state = workflow_repo.get(workflow_id)
    except NotFoundError:
        return {"found": False, "workflow_id": workflow_id}

    events = event_repo.list_for_workflow(workflow_id)
    step_names = [step.name for step in (state.steps or [])]
    event_types = list(dict.fromkeys(ev.event_type.value for ev in events))

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
        "event_types_seen": event_types,
        "review_required": state.review is not None,
        "review_summary": review_summary,
        "validation_passed": state.validation_report.valid if state.validation_report else None,
        "created_at": state.created_at,
        "updated_at": state.updated_at,
    }


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


@mcp.resource("ojtflow://audit/workflow-statuses")
def workflow_statuses_resource() -> str:
    """All valid workflow status values."""
    statuses = [s.value for s in WorkflowStatus]
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
        mcp.run(transport="stdio", show_banner=False)
