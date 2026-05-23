"""Workflow routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ojtflow.application.workflow_service import WorkflowService
from ojtflow.core.contracts.events import WorkflowEvent
from ojtflow.core.contracts.workflow import WorkflowState
from ojtflow.interfaces.api.deps import get_workflow_service
from ojtflow.interfaces.api.responses import ok
from ojtflow.interfaces.api.schemas import StartWorkflowRequest

router = APIRouter(tags=["workflows"])


@router.post("/workflows")
def start_workflow(
    request: StartWorkflowRequest,
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    workflow = service.start_workflow(
        instruction=request.instruction,
        data=request.data,
        declared_format=request.input_format,
        target_format=request.target_format,
        schema_id=request.schema_id,
        require_human_review=request.require_human_review,
    )
    return ok(workflow)


@router.get("/workflows/{workflow_id}")
def get_workflow(
    workflow_id: str,
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    return ok(service.get_workflow(workflow_id))


@router.get("/workflows/{workflow_id}/events")
def get_workflow_events(
    workflow_id: str,
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    return ok(service.list_events(workflow_id))
