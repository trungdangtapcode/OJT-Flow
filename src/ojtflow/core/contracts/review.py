"""Human review contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.contracts.enums import ReviewDecision, ReviewStatus
from ojtflow.core.ids import new_id
from ojtflow.core.time import utc_now


class HumanReview(ContractModel):
    """A review request that can pause and resume a workflow."""

    review_id: str = Field(default_factory=lambda: new_id("rev"))
    workflow_id: str
    status: ReviewStatus = ReviewStatus.PENDING
    trigger: str
    question: str
    proposed_action: dict[str, Any] = Field(default_factory=dict)
    allowed_decisions: list[ReviewDecision] = Field(
        default_factory=lambda: [
            ReviewDecision.APPROVE,
            ReviewDecision.APPROVE_WITH_EDITS,
            ReviewDecision.REJECT,
            ReviewDecision.CLARIFY,
        ]
    )
    decision: ReviewDecision | None = None
    decision_payload: dict[str, Any] | None = None
    decided_by: str | None = None
    decided_at: str | None = None

    def apply_decision(
        self,
        decision: ReviewDecision,
        decided_by: str = "user",
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Record a review decision."""

        self.decision = decision
        self.decision_payload = payload
        self.decided_by = decided_by
        self.decided_at = utc_now().isoformat()
        if decision == ReviewDecision.APPROVE:
            self.status = ReviewStatus.APPROVED
        elif decision == ReviewDecision.APPROVE_WITH_EDITS:
            self.status = ReviewStatus.APPROVED_WITH_EDITS
        elif decision == ReviewDecision.REJECT:
            self.status = ReviewStatus.REJECTED
        elif decision == ReviewDecision.CLARIFY:
            self.status = ReviewStatus.CLARIFICATION_REQUESTED
        elif decision == ReviewDecision.CANCEL:
            self.status = ReviewStatus.CANCELLED

