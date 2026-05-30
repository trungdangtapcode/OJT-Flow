"""Retrieval routes for evidence search and source inventory."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ojtflow.application.workflow_service import WorkflowService
from ojtflow.core.contracts.retrieval import RetrievalQuery
from ojtflow.interfaces.api.deps import get_workflow_service
from ojtflow.interfaces.api.responses import ok
from ojtflow.interfaces.api.schemas import RetrievalSearchRequest

router = APIRouter(tags=["retrieval"])


@router.post("/retrieval/search")
async def search_retrieval(
    request: RetrievalSearchRequest,
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
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
        )
    )
    return ok(package)


@router.get("/retrieval/sources")
async def list_retrieval_sources(
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    return ok(service.list_retrieval_sources())
