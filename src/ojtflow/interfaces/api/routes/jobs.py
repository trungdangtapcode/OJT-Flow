"""Background job routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from ojtflow.application.governance_service import GovernanceService
from ojtflow.application.background_job_service import BackgroundJobService
from ojtflow.application.retrieval_reindex_safety import (
    approval_token_matches_report,
    build_embedding_reindex_safety_report,
    compare_embedding_reindex_manifests,
    retrieval_manifest_hash,
)
from ojtflow.application.workflow_service import WorkflowService
from ojtflow.config import Settings
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.core.contracts.base import ContractModel, NonBlankStr
from ojtflow.core.contracts.jobs import BackgroundJob, JobStatus, JobType
from ojtflow.core.errors import PolicyBlockedError
from ojtflow.infrastructure.retrieval.reindex_markers import (
    write_embedding_reindex_rollback_marker,
)
from ojtflow.interfaces.api.deps import (
    get_api_settings,
    get_background_job_service,
    get_governance_service,
    get_workflow_service,
    require_authentication,
)
from ojtflow.interfaces.api.responses import ok
from ojtflow.interfaces.api.schemas import (
    EmbeddingReindexJobRequest,
    RetrievalReindexJobRequest,
)

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


@router.post("/jobs/{job_id}/cancel", response_model=JobEnvelope)
async def cancel_job(
    job_id: NonBlankStr,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    jobs: BackgroundJobService = Depends(get_background_job_service),
) -> dict:
    """Cancel a queued or running user-owned background job."""

    return ok(jobs.cancel_job(owner_user_id=authenticated.user.user_id, job_id=job_id))


@router.post("/jobs/retrieval-reindex", response_model=JobEnvelope)
async def create_retrieval_reindex_job(
    request: RetrievalReindexJobRequest,
    http_request: Request,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    jobs: BackgroundJobService = Depends(get_background_job_service),
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    """Create a retrieval reindex job and run it synchronously by default."""

    governance.require_permission(user=authenticated.user, permission_scope="admin:write")
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


@router.post("/jobs/embedding-reindex", response_model=JobEnvelope)
async def create_embedding_reindex_job(
    request: EmbeddingReindexJobRequest,
    http_request: Request,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    jobs: BackgroundJobService = Depends(get_background_job_service),
    workflow_service: WorkflowService = Depends(get_workflow_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Create an approval-gated embedding reindex job."""

    governance.require_permission(user=authenticated.user, permission_scope="admin:write")
    before_manifest = workflow_service.retrieval_index_manifest(
        owner_user_id=authenticated.user.user_id,
    )
    safety_report = build_embedding_reindex_safety_report(
        current_manifest=before_manifest,
        include_seeded=request.include_seeded,
        include_corpus=request.include_corpus,
    )
    if not approval_token_matches_report(
        report=safety_report,
        approval_token=request.approval_token,
    ):
        raise PolicyBlockedError(
            "Embedding reindex approval token does not match the current dry-run report.",
            details={
                "approval_payload_hash": safety_report.approval_payload_hash,
                "required_action": safety_report.required_operator_action,
            },
        )

    request_id = getattr(http_request.state, "request_id", None)
    job = jobs.create_job(
        owner_user_id=authenticated.user.user_id,
        job_type="embedding_reindex",
        input={
            "include_seeded": request.include_seeded,
            "include_corpus": request.include_corpus,
            "request_id": request_id,
            "approval_token_hash": safety_report.approval_token_hash,
            "approval_payload_hash": safety_report.approval_payload_hash,
            "before_manifest_hash": retrieval_manifest_hash(before_manifest),
        },
    )
    if request.execute_now:
        job = jobs.run_sync(
            owner_user_id=authenticated.user.user_id,
            job_id=job.job_id,
            handler=lambda running_job: _run_embedding_reindex_job(
                running_job,
                owner_user_id=authenticated.user.user_id,
                before_manifest=before_manifest,
                safety_report=safety_report,
                workflow_service=workflow_service,
                data_dir=settings.resolved_data_dir,
                request_id=request_id,
            ),
        )
    return ok(job)


def _run_embedding_reindex_job(
    job: BackgroundJob,
    *,
    owner_user_id: str,
    before_manifest,
    safety_report,
    workflow_service: WorkflowService,
    data_dir,
    request_id: str | None,
) -> dict:
    rollback_marker = write_embedding_reindex_rollback_marker(
        data_dir=data_dir,
        before_manifest=before_manifest,
        safety_report=safety_report,
        job_id=job.job_id,
        request_id=request_id,
    )
    reindex_output = workflow_service.reindex_retrieval(
        include_seeded=bool(job.input.get("include_seeded", True)),
        include_corpus=bool(job.input.get("include_corpus", True)),
    )
    after_manifest = workflow_service.retrieval_index_manifest(
        owner_user_id=owner_user_id,
    )
    comparison = compare_embedding_reindex_manifests(
        before=before_manifest,
        after=after_manifest,
    )
    return {
        "safety_report": safety_report.model_dump(
            mode="json",
            exclude={"approval_token"},
        ),
        "rollback_marker": rollback_marker.model_dump(mode="json"),
        "reindex_output": reindex_output,
        "after_manifest": after_manifest.model_dump(mode="json"),
        "quality_comparison": comparison.model_dump(mode="json"),
    }
