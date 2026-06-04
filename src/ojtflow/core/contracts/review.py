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
            ReviewDecision.CANCEL,
        ]
    )
    decision: ReviewDecision | None = None
    decision_payload: dict[str, Any] | None = None
    decided_by: str | None = None
    decided_at: str | None = None
    clarification_requests: list[dict[str, Any]] = Field(default_factory=list)

    def request_clarification(
        self,
        requested_by: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Record a non-terminal clarification request while keeping review pending."""

        self.clarification_requests.append(
            {
                "requested_by": requested_by,
                "requested_at": utc_now().isoformat(),
                "payload": payload or {},
            }
        )

    def apply_decision(
        self,
        decision: ReviewDecision,
        decided_by: str,
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
            self.request_clarification(decided_by, payload)
            self.decision = None
            self.decision_payload = None
            self.decided_by = None
            self.decided_at = None
            self.status = ReviewStatus.PENDING
        elif decision == ReviewDecision.CANCEL:
            self.status = ReviewStatus.CANCELLED
