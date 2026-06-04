"""Helpers for workflow summary projections."""

from __future__ import annotations

from collections import Counter

from ojtflow.core.contracts.enums import WorkflowStatus
from ojtflow.core.contracts.summary import WorkflowStats, WorkflowSummaryItem, WorkflowSummaryPage
from ojtflow.core.contracts.workflow import WorkflowState

ALLOWED_SUMMARY_SORTS = {
    "updated_at",
    "created_at",
    "status",
    "workflow_id",
    "issue_count",
    "evidence_count",
}


def clamp_page(page: int) -> int:
    return max(1, page)


def clamp_page_size(page_size: int) -> int:
    return max(1, min(page_size, 100))


def normalize_sort(sort: str) -> str:
    return sort if sort in ALLOWED_SUMMARY_SORTS else "updated_at"


def normalize_direction(direction: str) -> str:
    return "asc" if direction.lower() == "asc" else "desc"


def _as_iso(value: object) -> str:
    isoformat = getattr(value, "isoformat", None)
    if callable(isoformat):
        return str(isoformat())
    return str(value)


def workflow_to_summary(workflow: WorkflowState) -> WorkflowSummaryItem:
    issue_count = len(workflow.validation_report.issues) if workflow.validation_report else 0
    review_id = workflow.review.review_id if workflow.review else None
    review_status = workflow.review.status.value if workflow.review else None
    schema_id = workflow.intent.options.get("schema_id")
    return WorkflowSummaryItem(
        workflow_id=workflow.workflow_id,
        owner_user_id=workflow.owner_user_id,
        status=workflow.status,
        instruction=workflow.user_instruction,
        schema_id=str(schema_id) if schema_id else None,
        target_format=workflow.intent.target_format.value if workflow.intent.target_format else None,
        issue_count=issue_count,
        review_id=review_id,
        review_status=review_status,
        evidence_count=len(workflow.retrieved_context),
        created_at=_as_iso(workflow.created_at),
        updated_at=_as_iso(workflow.updated_at),
    )


def filter_sort_page_summaries(
    workflows: list[WorkflowState],
    *,
    status: WorkflowStatus | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 25,
    sort: str = "updated_at",
    direction: str = "desc",
    reviews_only: bool = False,
    review_status: str | None = None,
    owner_user_id: str | None = None,
) -> WorkflowSummaryPage:
    summaries = [workflow_to_summary(workflow) for workflow in workflows]
    if owner_user_id is not None:
        summaries = [item for item in summaries if item.owner_user_id == owner_user_id]
    if status:
        summaries = [item for item in summaries if item.status == status]
    if reviews_only:
        summaries = [item for item in summaries if item.review_id]
    if review_status:
        summaries = [item for item in summaries if item.review_status == review_status]
    if q and q.strip():
        needle = q.strip().lower()
        summaries = [
            item
            for item in summaries
            if needle in item.workflow_id.lower()
            or needle in item.instruction.lower()
            or (item.schema_id and needle in item.schema_id.lower())
            or (item.review_id and needle in item.review_id.lower())
        ]

    sort = normalize_sort(sort)
    reverse = normalize_direction(direction) == "desc"
    # Match the Postgres adapter: primary sort is caller-controlled, with a
    # deterministic workflow_id ascending tie-breaker for stable pagination.
    summaries.sort(key=lambda item: item.workflow_id)
    summaries.sort(key=lambda item: getattr(item, sort), reverse=reverse)

    page = clamp_page(page)
    page_size = clamp_page_size(page_size)
    total = len(summaries)
    start = (page - 1) * page_size
    return WorkflowSummaryPage(
        items=summaries[start : start + page_size],
        page=page,
        page_size=page_size,
        total=total,
    )


def workflow_stats(
    workflows: list[WorkflowState],
    *,
    owner_user_id: str | None = None,
) -> WorkflowStats:
    summaries = [workflow_to_summary(workflow) for workflow in workflows]
    if owner_user_id is not None:
        summaries = [item for item in summaries if item.owner_user_id == owner_user_id]
    by_status = Counter(item.status.value for item in summaries)
    issue_total = sum(item.issue_count for item in summaries)
    total = len(summaries)
    return WorkflowStats(
        total=total,
        by_status=dict(by_status),
        pending_reviews=sum(1 for item in summaries if item.review_status == "pending"),
        failed=by_status.get(WorkflowStatus.FAILED.value, 0),
        completed=by_status.get(WorkflowStatus.COMPLETED.value, 0),
        review_gated=sum(1 for item in summaries if item.review_id),
        average_issue_count=round(issue_total / total, 2) if total else 0.0,
    )
