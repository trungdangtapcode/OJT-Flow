"""Workflow routes."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query, Request

from ojtflow.application.workflow_service import WorkflowService
from ojtflow.config import Settings
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.core.contracts.base import NonBlankStr
from ojtflow.core.contracts.events import WorkflowEvent
from ojtflow.core.contracts.enums import WorkflowStatus
from ojtflow.core.contracts.workflow import WorkflowState
from ojtflow.interfaces.api.deps import (
    get_api_settings,
    get_workflow_service,
    require_authentication,
)
from ojtflow.interfaces.api.limits import enforce_inline_text_limit
from ojtflow.interfaces.api.responses import ok, raise_for_failed_workflow
from ojtflow.interfaces.api.schemas import StartWorkflowRequest

router = APIRouter(tags=["workflows"])

SummarySort = Literal[
    "updated_at",
    "created_at",
    "status",
    "workflow_id",
    "issue_count",
    "evidence_count",
]
SortDirection = Literal["asc", "desc"]
ReviewSummaryStatus = Literal[
    "pending",
    "approved",
    "approved_with_edits",
    "rejected",
    "clarification_requested",
    "cancelled",
    "all",
]


@router.post("/workflows")
async def start_workflow(
    request: StartWorkflowRequest,
    http_request: Request,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: WorkflowService = Depends(get_workflow_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    enforce_inline_text_limit(request.data, settings)
    workflow = service.start_workflow(
        instruction=request.instruction,
        data=request.data,
        declared_format=request.input_format,
        target_format=request.target_format,
        schema_id=request.schema_id,
        require_human_review=request.require_human_review,
        owner_user_id=authenticated.user.user_id,
        request_id=getattr(http_request.state, "request_id", None),
    )
    raise_for_failed_workflow(workflow)
    return ok(workflow)


@router.get("/workflows")
async def list_workflows(
    status: WorkflowStatus | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    return ok(
        service.list_workflows(
            status=status,
            limit=limit,
            owner_user_id=authenticated.user.user_id,
        )
    )


@router.get("/workflows/summary")
async def list_workflow_summaries(
    status: WorkflowStatus | None = None,
    q: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    sort: SummarySort = "updated_at",
    direction: SortDirection = "desc",
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    return ok(
        service.list_workflow_summaries(
            status=status,
            q=q,
            page=page,
            page_size=page_size,
            sort=sort,
            direction=direction,
            owner_user_id=authenticated.user.user_id,
        )
    )


@router.get("/workflows/stats")
async def workflow_stats(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    return ok(service.workflow_stats(owner_user_id=authenticated.user.user_id))


@router.get("/workflows/{workflow_id}")
async def get_workflow(
    workflow_id: NonBlankStr,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    return ok(service.get_workflow(workflow_id, owner_user_id=authenticated.user.user_id))


@router.get("/workflows/{workflow_id}/events")
async def get_workflow_events(
    workflow_id: NonBlankStr,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    return ok(service.list_events(workflow_id, owner_user_id=authenticated.user.user_id))


@router.get("/workflows/{workflow_id}/output")
async def get_workflow_output(
    workflow_id: NonBlankStr,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    return ok(
        service.get_workflow_output(
            workflow_id,
            owner_user_id=authenticated.user.user_id,
        )
    )


@router.get("/reviews")
async def list_reviews(
    status: str | None = "pending",
    limit: int = Query(default=50, ge=1, le=100),
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    return ok(
        service.list_reviews(
            status=status,
            limit=limit,
            owner_user_id=authenticated.user.user_id,
        )
    )


@router.get("/reviews/summary")
async def list_review_summaries(
    status: ReviewSummaryStatus = "pending",
    q: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    sort: SummarySort = "updated_at",
    direction: SortDirection = "desc",
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    review_status = None if status == "all" else status
    return ok(
        service.list_review_summaries(
            status=review_status,
            q=q,
            page=page,
            page_size=page_size,
            sort=sort,
            direction=direction,
            owner_user_id=authenticated.user.user_id,
        )
    )


@router.get("/schemas")
async def list_schemas(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    del authenticated
    return ok(service.list_schemas())
