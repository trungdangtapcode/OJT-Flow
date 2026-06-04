"""Retrieval routes for evidence search and source inventory."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from ojtflow.application.retrieval_judgment_service import RetrievalJudgmentService
from ojtflow.application.workflow_service import WorkflowService
from ojtflow.config import Settings
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.core.contracts.base import NonBlankStr
from ojtflow.core.contracts.retrieval import RetrievalQuery
from ojtflow.infrastructure.retrieval.presets import (
    load_retrieval_search_options,
    load_retrieval_search_presets,
)
from ojtflow.interfaces.api.deps import (
    get_api_settings,
    get_retrieval_judgment_service,
    get_workflow_service,
    require_authentication,
)
from ojtflow.interfaces.api.limits import enforce_inline_json_limit
from ojtflow.interfaces.api.responses import ok
from ojtflow.interfaces.api.schemas import (
    RetrievalJudgmentRequest,
    RetrievalReindexRequest,
    RetrievalSearchRequest,
)

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
        **request.filters.model_dump(exclude_none=True, mode="json"),
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
    filters = {key: _filter_value(value) for key, value in filters.items()}
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


@router.get("/retrieval/presets")
async def list_retrieval_presets(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    del authenticated
    return ok(load_retrieval_search_presets(settings.resolved_knowledge_dir))


@router.get("/retrieval/search-options")
async def get_retrieval_search_options(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    del authenticated
    return ok(load_retrieval_search_options(settings.resolved_knowledge_dir))


@router.get("/retrieval/judgments")
async def list_retrieval_judgments(
    query_text: str | None = Query(default=None, alias="query"),
    run_id: str | None = None,
    evidence_id: str | None = None,
    limit: int = Query(default=500, ge=1, le=1000),
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: RetrievalJudgmentService = Depends(get_retrieval_judgment_service),
) -> dict:
    return ok(
        service.list(
            owner_user_id=authenticated.user.user_id,
            query=_optional_query_value(query_text),
            run_id=_optional_query_value(run_id),
            evidence_id=_optional_query_value(evidence_id),
            limit=limit,
        )
    )


@router.put("/retrieval/judgments")
async def upsert_retrieval_judgment(
    request: RetrievalJudgmentRequest,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: RetrievalJudgmentService = Depends(get_retrieval_judgment_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    enforce_inline_json_limit(request, settings, field_name="retrieval_judgment")
    return ok(
        service.upsert(
            owner_user_id=authenticated.user.user_id,
            query=request.query,
            evidence_id=request.evidence_id,
            value=request.value,
            rating=request.rating,
            source_id=request.source_id,
            source_type=request.source_type,
            source_version=request.source_version,
            run_id=request.run_id,
            search_signature=request.search_signature,
            metadata=request.metadata,
        )
    )


@router.delete("/retrieval/judgments/{judgment_id}")
async def delete_retrieval_judgment(
    judgment_id: NonBlankStr,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: RetrievalJudgmentService = Depends(get_retrieval_judgment_service),
) -> dict:
    service.delete(
        owner_user_id=authenticated.user.user_id,
        judgment_id=judgment_id,
    )
    return ok({"deleted": True, "judgment_id": judgment_id})


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


def _filter_value(value: Any) -> Any:
    if hasattr(value, "value"):
        return value.value
    return value


def _optional_query_value(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
