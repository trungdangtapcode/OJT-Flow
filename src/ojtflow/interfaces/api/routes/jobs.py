"""Background job routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from ojtflow.application.background_job_service import BackgroundJobService
from ojtflow.application.workflow_service import WorkflowService
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.core.contracts.base import ContractModel, NonBlankStr
from ojtflow.core.contracts.jobs import BackgroundJob, JobStatus, JobType
from ojtflow.interfaces.api.deps import (
    get_background_job_service,
    get_workflow_service,
    require_authentication,
)
from ojtflow.interfaces.api.responses import ok
from ojtflow.interfaces.api.schemas import RetrievalReindexJobRequest

router = APIRouter(tags=["jobs"])


class JobEnvelope(ContractModel):
    data: BackgroundJob
    error: None = None


class JobsEnvelope(ContractModel):
    data: list[BackgroundJob]
    error: None = None


@router.get("/jobs", response_model=JobsEnvelope)
async def list_jobs(
    status: JobStatus | None = Query(default=None),
    job_type: JobType | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    authenticated: AuthenticatedSession = Depends(require_authentication),
    jobs: BackgroundJobService = Depends(get_background_job_service),
) -> dict:
    """List user-owned background jobs."""

    return ok(
        jobs.list_jobs(
            owner_user_id=authenticated.user.user_id,
            status=status,
            job_type=job_type,
            limit=limit,
        )
    )


@router.get("/jobs/{job_id}", response_model=JobEnvelope)
async def get_job(
    job_id: NonBlankStr,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    jobs: BackgroundJobService = Depends(get_background_job_service),
) -> dict:
    """Return one user-owned background job."""

    return ok(jobs.get_job(owner_user_id=authenticated.user.user_id, job_id=job_id))


@router.post("/jobs/retrieval-reindex", response_model=JobEnvelope)
async def create_retrieval_reindex_job(
    request: RetrievalReindexJobRequest,
    http_request: Request,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    jobs: BackgroundJobService = Depends(get_background_job_service),
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    """Create a retrieval reindex job and run it synchronously by default."""

    job = jobs.create_job(
        owner_user_id=authenticated.user.user_id,
        job_type="retrieval_reindex",
        input={
            "include_seeded": request.include_seeded,
            "include_corpus": request.include_corpus,
            "request_id": getattr(http_request.state, "request_id", None),
        },
    )
    if request.execute_now:
        job = jobs.run_sync(
            owner_user_id=authenticated.user.user_id,
            job_id=job.job_id,
            handler=lambda _: workflow_service.reindex_retrieval(
                include_seeded=request.include_seeded,
                include_corpus=request.include_corpus,
            ),
        )
    return ok(job)
