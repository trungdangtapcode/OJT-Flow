"""Direct deterministic conversion routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ojtflow.application.workflow_service import WorkflowService
from ojtflow.config import Settings
from ojtflow.interfaces.api.deps import get_api_settings, get_workflow_service
from ojtflow.interfaces.api.limits import enforce_inline_text_limit
from ojtflow.interfaces.api.responses import ok
from ojtflow.interfaces.api.schemas import ConvertRequest

router = APIRouter(tags=["convert"])


@router.post("/convert")
async def convert(
    request: ConvertRequest,
    service: WorkflowService = Depends(get_workflow_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    enforce_inline_text_limit(request.data, settings)
    return ok(
        service.convert_data(
            data=request.data,
            declared_format=request.input_format,
            target_format=request.target_format,
        )
    )
