"""Retrieval routes for evidence search and source inventory."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ojtflow.application.workflow_service import WorkflowService
from ojtflow.config import Settings
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.core.contracts.retrieval import RetrievalQuery
from ojtflow.interfaces.api.deps import get_api_settings, get_workflow_service, require_authentication
from ojtflow.interfaces.api.limits import enforce_inline_json_limit
from ojtflow.interfaces.api.responses import ok
from ojtflow.interfaces.api.schemas import RetrievalReindexRequest, RetrievalSearchRequest

router = APIRouter(tags=["retrieval"])


@router.post("/retrieval/search")
async def search_retrieval(
    request: RetrievalSearchRequest,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: WorkflowService = Depends(get_workflow_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    enforce_inline_json_limit(request, settings, field_name="retrieval_request")
    filters = {
        **request.filters,
        **{
            key: value
            for key, value in {
                "clinical_domain": request.clinical_domain,
                "standard_system": request.standard_system,
                "trust_level": request.trust_level,
                "source_type": request.source_type,
            }.items()
            if value
        },
    }
    package = service.search_retrieval(
        RetrievalQuery(
            query=request.query,
            workflow_id=request.workflow_id,
            fields=request.fields,
            schema_id=request.schema_id,
            detected_format=request.detected_format,
            resource_type=request.resource_type,
            top_k=request.top_k,
            filters=filters,
        ),
        owner_user_id=authenticated.user.user_id,
    )
    return ok(package)


@router.get("/retrieval/sources")
async def list_retrieval_sources(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    del authenticated
    return ok(service.list_retrieval_sources())


@router.post("/retrieval/reindex")
async def reindex_retrieval(
    request: RetrievalReindexRequest,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    del authenticated
    return ok(
        service.reindex_retrieval(
            include_seeded=request.include_seeded,
            include_corpus=request.include_corpus,
        )
    )


@router.get("/retrieval/integrity")
async def retrieval_integrity(
    include_seeded: bool = Query(default=True),
    include_corpus: bool = Query(default=False),
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    del authenticated
    return ok(
        service.retrieval_integrity_report(
            include_seeded=include_seeded,
            include_corpus=include_corpus,
        )
    )
