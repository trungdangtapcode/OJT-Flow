"""MedSigLIP image classification routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ojtflow.application.background_job_service import BackgroundJobService
from ojtflow.application.governance_service import GovernanceService
from ojtflow.application.medsiglip_service import MedSiglipService
from ojtflow.config import Settings
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.contracts.jobs import BackgroundJob
from ojtflow.core.contracts.medsiglip import (
    MedSiglipClassificationRequest,
    MedSiglipClassificationResult,
    MedSiglipServiceStatus,
)
from ojtflow.interfaces.api.deps import (
    get_api_settings,
    get_background_job_service,
    get_governance_service,
    get_medsiglip_service,
    require_authentication,
)
from ojtflow.interfaces.api.limits import enforce_inline_json_limit
from ojtflow.interfaces.api.responses import ok
from ojtflow.interfaces.api.schemas import MedSiglipClassificationJobRequest

router = APIRouter(tags=["medsiglip"])


class MedSiglipStatusEnvelope(ContractModel):
    data: MedSiglipServiceStatus
    error: None = None


class MedSiglipClassificationEnvelope(ContractModel):
    data: MedSiglipClassificationResult
    error: None = None


class MedSiglipJobEnvelope(ContractModel):
    data: BackgroundJob
    error: None = None


@router.get("/medsiglip/status", response_model=MedSiglipStatusEnvelope)
async def medsiglip_status(
    service: MedSiglipService = Depends(get_medsiglip_service),
) -> dict:
    """Return sanitized MedSigLIP service status."""

    return ok(service.status())


@router.post("/medsiglip/classify", response_model=MedSiglipClassificationEnvelope)
async def classify_with_medsiglip(
    request: MedSiglipClassificationRequest,
    service: MedSiglipService = Depends(get_medsiglip_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Run synchronous MedSigLIP zero-shot classification."""

    enforce_inline_json_limit(request, settings, field_name="medsiglip_request")
    return ok(service.classify(request))


@router.post("/medsiglip/classification-jobs", response_model=MedSiglipJobEnvelope)
async def create_medsiglip_classification_job(
    request: MedSiglipClassificationJobRequest,
    http_request: Request,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    jobs: BackgroundJobService = Depends(get_background_job_service),
    service: MedSiglipService = Depends(get_medsiglip_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Create a durable MedSigLIP classification job."""

    governance.require_permission(user=authenticated.user, permission_scope="workflow:write")
    enforce_inline_json_limit(request, settings, field_name="medsiglip_request")
    job_request = MedSiglipClassificationRequest.model_validate(
        request.model_dump(mode="json", exclude={"execute_now"})
    )
    job = jobs.create_job(
        owner_user_id=authenticated.user.user_id,
        job_type="medsiglip_classification",
        input={
            **job_request.model_dump(mode="json"),
            "request_id": getattr(http_request.state, "request_id", None),
        },
    )
    if request.execute_now and jobs.queue_backed:
        job = jobs.enqueue(owner_user_id=authenticated.user.user_id, job_id=job.job_id)
    elif request.execute_now:
        job = jobs.run_sync(
            owner_user_id=authenticated.user.user_id,
            job_id=job.job_id,
            handler=service.classify_from_job,
        )
    return ok(job)
