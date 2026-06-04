"""Summary contracts for enterprise workflow list surfaces."""

from __future__ import annotations

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.contracts.enums import WorkflowStatus


class WorkflowSummaryItem(ContractModel):
    """Small workflow projection for paginated operations tables."""

    workflow_id: str
    owner_user_id: str | None = None
    status: WorkflowStatus
    instruction: str
    schema_id: str | None = None
    target_format: str | None = None
    issue_count: int = 0
    review_id: str | None = None
    review_status: str | None = None
    evidence_count: int = 0
    created_at: str
    updated_at: str


class WorkflowSummaryPage(ContractModel):
    """Paginated summary response."""

    items: list[WorkflowSummaryItem] = Field(default_factory=list)
    page: int
    page_size: int
    total: int


class WorkflowStats(ContractModel):
    """Operations dashboard aggregate counts."""

    total: int = 0
    by_status: dict[str, int] = Field(default_factory=dict)
    pending_reviews: int = 0
    failed: int = 0
    completed: int = 0
    review_gated: int = 0
    average_issue_count: float = 0.0
