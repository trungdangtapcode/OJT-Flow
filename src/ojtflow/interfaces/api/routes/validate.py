"""Direct validation routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ojtflow.application.workflow_service import WorkflowService
from ojtflow.config import Settings
from ojtflow.interfaces.api.deps import get_api_settings, get_workflow_service
from ojtflow.interfaces.api.limits import enforce_inline_text_limit
from ojtflow.interfaces.api.responses import ok
from ojtflow.interfaces.api.schemas import ValidateRequest

router = APIRouter(tags=["validate"])


@router.post("/validate")
async def validate(
    request: ValidateRequest,
    service: WorkflowService = Depends(get_workflow_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    enforce_inline_text_limit(request.data, settings)
    return ok(
        service.validate_data(
            data=request.data,
            declared_format=request.input_format,
            schema_id=request.schema_id,
        )
    )
