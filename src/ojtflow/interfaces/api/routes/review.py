"""Human review routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ojtflow.application.governance_service import GovernanceService
from ojtflow.application.workflow_service import WorkflowService
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.core.contracts.base import NonBlankStr
from ojtflow.interfaces.api.deps import (
    get_governance_service,
    get_workflow_service,
    require_authentication,
)
from ojtflow.interfaces.api.responses import ok, raise_for_failed_workflow
from ojtflow.interfaces.api.schemas import SubmitReviewRequest

router = APIRouter(tags=["review"])


@router.post("/review/{review_id}")
async def submit_review(
    review_id: NonBlankStr,
    request: SubmitReviewRequest,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    governance.require_permission(user=authenticated.user, permission_scope="review:write")
    workflow = service.submit_review(
        review_id=review_id,
        decision=request.decision,
        decided_by=authenticated.user.user_id,
        payload=request.payload,
        owner_user_id=authenticated.user.user_id,
    )
    raise_for_failed_workflow(workflow)
    return ok(workflow)
