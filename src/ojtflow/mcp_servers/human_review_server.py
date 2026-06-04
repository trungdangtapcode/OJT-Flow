"""MCP server: human review and approval tools.

Allows an AI agent to inspect pending review requests and fetch the
context needed to brief a human reviewer. Actual decision submission
goes through the OJTFlow REST API (POST /api/v1/review/{id}) to ensure
proper authentication and audit logging.

Run locally:
    python -m ojtflow.mcp_servers.human_review_server
"""

from __future__ import annotations

import json
from typing import Any

from fastmcp import FastMCP

from ojtflow.config import get_settings
from ojtflow.infrastructure.storage.sqlite import (
    SQLiteBackboneStore,
    SQLiteWorkflowRepository,
)

mcp = FastMCP(
    "ojtflow-human-review",
    instructions=(
        "Tools for inspecting pending human review requests in OJTFlow. "
        "Use these to understand what action is being proposed and what the reviewer needs to decide. "
        "IMPORTANT: Do not submit decisions autonomously. "
        "Always present the review to a human and let them confirm before calling the API. "
        "Decisions must be submitted via POST /api/v1/review/{review_id} with authentication."
    ),
)


def _workflow_repo() -> SQLiteWorkflowRepository:
    settings = get_settings()
    backbone = SQLiteBackboneStore(
        settings.resolved_database_path,
        settings.resolved_data_dir,
    )
    return SQLiteWorkflowRepository(backbone)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def list_pending_reviews() -> dict[str, Any]:
    """List all workflows currently paused and waiting for human review.

    Returns:
        pending: List of pending review items with workflow ID, trigger,
                 question, and proposed action.
        count: Total number of pending reviews.
    """
    repo = _workflow_repo()
    page = repo.list_workflows(status_filter="needs_human_review", limit=50, offset=0)

    pending_out = []
    for w in page.items:
        state = repo.get_workflow(w.workflow_id)
        if state is None or state.review is None:
            continue
        pending_out.append(
            {
                "review_id": state.review.review_id,
                "workflow_id": state.workflow_id,
                "trigger": state.review.trigger,
                "question": state.review.question,
                "proposed_action": state.review.proposed_action,
                "allowed_decisions": [d.value for d in state.review.allowed_decisions],
                "created_at": state.created_at,
                "updated_at": state.updated_at,
            }
        )

    return {"pending": pending_out, "count": len(pending_out)}


@mcp.tool()
def get_review_context(workflow_id: str) -> dict[str, Any]:
    """Get full review context for a workflow paused for human approval.

    Returns everything a reviewer needs to make a decision:
    the question, proposed action, validation issues, and steps completed so far.

    Args:
        workflow_id: The workflow ID that is paused for review.

    Returns:
        review: The review request details.
        validation_issues: Issues that triggered the review.
        steps_completed: Steps that ran before the review gate.
        decision_guide: Explanation of each allowed decision.
    """
    repo = _workflow_repo()
    state = repo.get_workflow(workflow_id)
    if state is None:
        return {"found": False, "workflow_id": workflow_id}
    if state.review is None:
        return {
            "found": True,
            "workflow_id": workflow_id,
            "has_review": False,
            "status": state.status.value,
        }

    issues_out: list[dict[str, Any]] = []
    if state.validation_report:
        issues_out = [
            {
                "kind": issue.kind,
                "severity": issue.severity.value,
                "message": issue.message,
                "field": issue.location.field if issue.location else None,
                "row": issue.location.row if issue.location else None,
                "suggested_action": issue.suggested_action,
            }
            for issue in state.validation_report.issues
        ]

    steps_out = [
        {"name": step.name, "status": step.status, "summary": step.summary}
        for step in (state.steps or [])
    ]

    decision_guide = {
        "approve": "Accept the proposed action exactly as described and continue the workflow.",
        "approve_with_edits": "Accept with modifications — include edited_plan in your decision payload.",
        "reject": "Decline the proposed action; the workflow will be marked rejected.",
        "clarify": "Request more information — the review stays pending and a clarification is recorded.",
        "cancel": "Cancel the entire workflow without transforming the data.",
    }

    return {
        "found": True,
        "workflow_id": workflow_id,
        "has_review": True,
        "review": {
            "review_id": state.review.review_id,
            "trigger": state.review.trigger,
            "question": state.review.question,
            "proposed_action": state.review.proposed_action,
            "allowed_decisions": [d.value for d in state.review.allowed_decisions],
            "clarification_requests": state.review.clarification_requests,
        },
        "validation_issues": issues_out,
        "steps_completed": steps_out,
        "decision_guide": decision_guide,
        "submit_decision_endpoint": f"POST /api/v1/review/{state.review.review_id}",
    }


@mcp.tool()
def format_review_briefing(workflow_id: str) -> dict[str, Any]:
    """Format a concise briefing for a human reviewer.

    Summarises the key facts a reviewer needs without overwhelming detail.
    Use this to generate the content you present to a clinician or data steward.

    Args:
        workflow_id: The workflow ID paused for review.

    Returns:
        briefing: A structured summary ready to show to a human reviewer.
    """
    repo = _workflow_repo()
    state = repo.get_workflow(workflow_id)

    if state is None or state.review is None:
        return {"found": False, "workflow_id": workflow_id}

    critical_issues = []
    warnings = []
    if state.validation_report:
        for issue in state.validation_report.issues:
            if issue.severity.value in ("critical", "error"):
                critical_issues.append(issue.message)
            elif issue.requires_review:
                warnings.append(issue.message)

    return {
        "found": True,
        "briefing": {
            "review_id": state.review.review_id,
            "question_for_reviewer": state.review.question,
            "proposed_action": state.review.proposed_action,
            "critical_issues": critical_issues,
            "warnings_requiring_review": warnings,
            "allowed_decisions": [d.value for d in state.review.allowed_decisions],
            "action_required": (
                f"Submit decision to: POST /api/v1/review/{state.review.review_id}"
            ),
            "example_approve_payload": {
                "decision": "approve",
                "decided_by": "<reviewer_id>",
            },
            "example_reject_payload": {
                "decision": "reject",
                "decided_by": "<reviewer_id>",
                "payload": {"reason": "data quality too low"},
            },
        },
    }


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


@mcp.resource("ojtflow://review/decision-options")
def decision_options_resource() -> str:
    """Explanation of all review decision options."""
    options = {
        "approve": {
            "description": "Accept the proposed action and continue the workflow.",
            "requires_payload": False,
        },
        "approve_with_edits": {
            "description": "Accept with modifications to the proposed plan.",
            "requires_payload": True,
            "payload_example": {"edited_plan": {"fill_missing": False}},
        },
        "reject": {
            "description": "Decline the action; workflow ends in rejected state.",
            "requires_payload": False,
        },
        "clarify": {
            "description": "Request more information; review stays pending.",
            "requires_payload": True,
            "payload_example": {"clarification": "Which date format should be used?"},
        },
        "cancel": {
            "description": "Cancel the workflow entirely.",
            "requires_payload": False,
        },
    }
    return json.dumps(options, indent=2)


@mcp.resource("ojtflow://review/safety-rules")
def safety_rules_resource() -> str:
    """Safety rules for human review in OJTFlow."""
    rules = [
        "Never submit approve on behalf of a human without explicit confirmation.",
        "Always show the proposed_action to the reviewer before submitting a decision.",
        "If critical issues exist, recommend reject or clarify, not approve.",
        "PHI detected in data must be flagged to the reviewer before any decision.",
        "Decisions are irreversible — rejected and cancelled workflows cannot be resumed.",
    ]
    return json.dumps({"safety_rules": rules}, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
