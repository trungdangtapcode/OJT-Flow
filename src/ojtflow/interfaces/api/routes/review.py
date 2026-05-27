"""Human review routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ojtflow.application.workflow_service import WorkflowService
from ojtflow.core.contracts.workflow import WorkflowState
from ojtflow.interfaces.api.deps import get_workflow_service
from ojtflow.interfaces.api.responses import ok
from ojtflow.interfaces.api.schemas import SubmitReviewRequest

router = APIRouter(tags=["review"])


@router.post("/review/{review_id}")
async def submit_review(
    review_id: str,
    request: SubmitReviewRequest,
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    workflow = service.submit_review(
        review_id=review_id,
        decision=request.decision,
        decided_by=request.decided_by,
        payload=request.payload,
    )
    return ok(workflow)
