"""Retrieval routes for evidence search and source inventory."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request

from ojtflow.application.governance_service import GovernanceService
from ojtflow.application.retrieval_judgment_service import RetrievalJudgmentService
from ojtflow.application.workflow_service import WorkflowService
from ojtflow.config import Settings
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.core.contracts.base import ContractModel, NonBlankStr
from ojtflow.core.contracts.graph import (
    GraphContextRecord,
    GraphExport,
    GraphExportFormat,
    GraphNeighborhood,
    GraphNeighborhoodQuery,
)
from ojtflow.core.contracts.retrieval import (
    CorpusAdapterCatalog,
    CorpusChunkingProfileCatalog,
    CorpusIngestionManifest,
    RetrievalJudgmentEvaluationResult,
    RetrievalIntegrityReport,
    RetrievalPackage,
    RetrievalPlan,
    RetrievalQuery,
    RetrievalRelevanceJudgment,
    RetrievalRelevanceJudgmentSummary,
    RetrievalSearchOptions,
    RetrievalSearchPreset,
    RetrievalSource,
    RetrievalSourceTrustPolicyCatalog,
    RetrievalStrategyCatalog,
)
from ojtflow.infrastructure.retrieval.catalogs import (
    load_corpus_adapter_catalog,
    load_corpus_chunking_profile_catalog,
    load_retrieval_strategy_catalog,
    load_source_trust_policy_catalog,
)
from ojtflow.infrastructure.retrieval.corpus import build_corpus_ingestion_manifest
from ojtflow.infrastructure.retrieval.presets import (
    load_retrieval_search_options,
    load_retrieval_search_presets,
)
from ojtflow.interfaces.api.deps import (
    get_api_settings,
    get_governance_service,
    get_retrieval_judgment_service,
    get_workflow_service,
    require_authentication,
)
from ojtflow.interfaces.api.limits import enforce_inline_json_limit
from ojtflow.interfaces.api.responses import ok
from ojtflow.interfaces.api.schemas import (
    RetrievalJudgmentEvaluationRequest,
    RetrievalJudgmentRequest,
    RetrievalReindexRequest,
    RetrievalSearchRequest,
)

router = APIRouter(tags=["retrieval"])


class RetrievalPlanEnvelope(ContractModel):
    data: RetrievalPlan
    error: None = None


class RetrievalPackageEnvelope(ContractModel):
    data: RetrievalPackage
    error: None = None


class RetrievalPresetsEnvelope(ContractModel):
    data: list[RetrievalSearchPreset]
    error: None = None


class RetrievalSearchOptionsEnvelope(ContractModel):
    data: RetrievalSearchOptions
    error: None = None


class RetrievalSourcePoliciesEnvelope(ContractModel):
    data: RetrievalSourceTrustPolicyCatalog
    error: None = None


class RetrievalCorpusAdaptersEnvelope(ContractModel):
    data: CorpusAdapterCatalog
    error: None = None


class RetrievalCorpusManifestEnvelope(ContractModel):
    data: CorpusIngestionManifest
    error: None = None


class RetrievalCorpusChunkingProfilesEnvelope(ContractModel):
    data: CorpusChunkingProfileCatalog
    error: None = None


class RetrievalStrategiesEnvelope(ContractModel):
    data: RetrievalStrategyCatalog
    error: None = None


class RetrievalSourcesEnvelope(ContractModel):
    data: list[RetrievalSource]
    error: None = None


class RetrievalReindexResult(ContractModel):
    repository: NonBlankStr
    include_seeded: bool
    include_corpus: bool
    chunks_indexed: int
    embedding: dict[str, Any] | None = None
    embedding_generation_id: str | None = None
    framework: dict[str, Any] | None = None
    corpus: dict[str, Any] | None = None


class RetrievalReindexEnvelope(ContractModel):
    data: RetrievalReindexResult
    error: None = None


class RetrievalIntegrityEnvelope(ContractModel):
    data: RetrievalIntegrityReport
    error: None = None


class RetrievalGraphContextsEnvelope(ContractModel):
    data: list[GraphContextRecord]
    error: None = None


class RetrievalGraphExportEnvelope(ContractModel):
    data: GraphExport
    error: None = None


class RetrievalGraphNeighborhoodEnvelope(ContractModel):
    data: GraphNeighborhood
    error: None = None


class RetrievalJudgmentsEnvelope(ContractModel):
    data: list[RetrievalRelevanceJudgment]
    error: None = None


class RetrievalJudgmentSummaryEnvelope(ContractModel):
    data: RetrievalRelevanceJudgmentSummary
    error: None = None


class RetrievalJudgmentEvaluationEnvelope(ContractModel):
    data: RetrievalJudgmentEvaluationResult
    error: None = None


class RetrievalJudgmentEnvelope(ContractModel):
    data: RetrievalRelevanceJudgment
    error: None = None


class RetrievalJudgmentDeleteResult(ContractModel):
    deleted: bool
    judgment_id: NonBlankStr


class RetrievalJudgmentDeleteEnvelope(ContractModel):
    data: RetrievalJudgmentDeleteResult
    error: None = None


@router.post("/retrieval/plan", response_model=RetrievalPlanEnvelope)
async def plan_retrieval(
    request: RetrievalSearchRequest,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    service: WorkflowService = Depends(get_workflow_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    governance.require_permission(user=authenticated.user, permission_scope="retrieval:read")
    enforce_inline_json_limit(request, settings, field_name="retrieval_plan_request")
    plan = service.plan_retrieval(
        _retrieval_query_from_request(request),
        owner_user_id=authenticated.user.user_id,
    )
    return ok(plan)


@router.post("/retrieval/search", response_model=RetrievalPackageEnvelope)
async def search_retrieval(
    request: RetrievalSearchRequest,
    http_request: Request,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    service: WorkflowService = Depends(get_workflow_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    governance.require_permission(user=authenticated.user, permission_scope="retrieval:read")
    enforce_inline_json_limit(request, settings, field_name="retrieval_request")
    package = service.search_retrieval(
        _retrieval_query_from_request(request),
        owner_user_id=authenticated.user.user_id,
        request_id=getattr(http_request.state, "request_id", None),
    )
    return ok(package)


@router.get("/retrieval/graph/contexts", response_model=RetrievalGraphContextsEnvelope)
async def list_retrieval_graph_contexts(
    workflow_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    governance.require_permission(user=authenticated.user, permission_scope="retrieval:read")
    return ok(
        service.list_graph_contexts(
            owner_user_id=authenticated.user.user_id,
            workflow_id=_optional_query_value(workflow_id),
            limit=limit,
        )
    )


@router.get("/retrieval/graph/export", response_model=RetrievalGraphExportEnvelope)
async def export_retrieval_graph_contexts(
    workflow_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    export_format: GraphExportFormat = Query(default="jsonl", alias="format"),
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    governance.require_permission(user=authenticated.user, permission_scope="retrieval:read")
    return ok(
        service.export_graph_contexts(
            owner_user_id=authenticated.user.user_id,
            workflow_id=_optional_query_value(workflow_id),
            limit=limit,
            export_format=export_format,
        )
    )


@router.get("/retrieval/graph/neighborhood", response_model=RetrievalGraphNeighborhoodEnvelope)
async def get_retrieval_graph_neighborhood(
    workflow_id: str | None = None,
    q: str | None = None,
    node_id: str | None = None,
    evidence_id: str | None = None,
    source_id: str | None = None,
    normalized_code: str | None = None,
    resource_type: str | None = None,
    field: str | None = None,
    relation: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    max_depth: int = Query(default=1, ge=0, le=2),
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    governance.require_permission(user=authenticated.user, permission_scope="retrieval:read")
    return ok(
        service.graph_neighborhood(
            owner_user_id=authenticated.user.user_id,
            query=GraphNeighborhoodQuery(
                workflow_id=_optional_query_value(workflow_id),
                q=_optional_query_value(q),
                node_id=_optional_query_value(node_id),
                evidence_id=_optional_query_value(evidence_id),
                source_id=_optional_query_value(source_id),
                normalized_code=_optional_query_value(normalized_code),
                resource_type=_optional_query_value(resource_type),
                field=_optional_query_value(field),
                relation=_optional_query_value(relation),
                limit=limit,
                max_depth=max_depth,
            ),
        )
    )


def _retrieval_query_from_request(request: RetrievalSearchRequest) -> RetrievalQuery:
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
    return RetrievalQuery(
        query=request.query,
        workflow_id=request.workflow_id,
        fields=request.fields,
        schema_id=request.schema_id,
        detected_format=request.detected_format,
        resource_type=request.resource_type,
        top_k=request.top_k,
        filters=filters,
    )


@router.get("/retrieval/presets", response_model=RetrievalPresetsEnvelope)
async def list_retrieval_presets(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    governance.require_permission(user=authenticated.user, permission_scope="retrieval:read")
    return ok(load_retrieval_search_presets(settings.resolved_knowledge_dir))


@router.get("/retrieval/search-options", response_model=RetrievalSearchOptionsEnvelope)
async def get_retrieval_search_options(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    governance.require_permission(user=authenticated.user, permission_scope="retrieval:read")
    return ok(load_retrieval_search_options(settings.resolved_knowledge_dir))


@router.get("/retrieval/source-policies", response_model=RetrievalSourcePoliciesEnvelope)
async def get_retrieval_source_policies(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    governance.require_permission(user=authenticated.user, permission_scope="retrieval:read")
    return ok(load_source_trust_policy_catalog(settings.resolved_knowledge_dir))


@router.get("/retrieval/corpus/adapters", response_model=RetrievalCorpusAdaptersEnvelope)
async def get_retrieval_corpus_adapters(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    governance.require_permission(user=authenticated.user, permission_scope="retrieval:read")
    return ok(load_corpus_adapter_catalog(settings.resolved_knowledge_dir))


@router.get("/retrieval/corpus/manifest", response_model=RetrievalCorpusManifestEnvelope)
async def get_retrieval_corpus_manifest(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    governance.require_permission(user=authenticated.user, permission_scope="retrieval:read")
    knowledge_root = settings.resolved_knowledge_dir
    return ok(
        build_corpus_ingestion_manifest(
            (knowledge_root / "corpus",),
            knowledge_root=knowledge_root,
        )
    )


@router.get(
    "/retrieval/corpus/chunking-profiles",
    response_model=RetrievalCorpusChunkingProfilesEnvelope,
)
async def get_retrieval_corpus_chunking_profiles(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    governance.require_permission(user=authenticated.user, permission_scope="retrieval:read")
    return ok(load_corpus_chunking_profile_catalog(settings.resolved_knowledge_dir))


@router.get("/retrieval/strategies", response_model=RetrievalStrategiesEnvelope)
async def get_retrieval_strategies(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    governance.require_permission(user=authenticated.user, permission_scope="retrieval:read")
    return ok(load_retrieval_strategy_catalog(settings.resolved_knowledge_dir))


@router.get("/retrieval/judgments", response_model=RetrievalJudgmentsEnvelope)
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


@router.get("/retrieval/judgments/summary", response_model=RetrievalJudgmentSummaryEnvelope)
async def summarize_retrieval_judgments(
    query_text: str | None = Query(default=None, alias="query"),
    limit: int = Query(default=1000, ge=1, le=1000),
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: RetrievalJudgmentService = Depends(get_retrieval_judgment_service),
) -> dict:
    return ok(
        service.summary(
            owner_user_id=authenticated.user.user_id,
            query=_optional_query_value(query_text),
            limit=limit,
        )
    )


@router.post("/retrieval/judgments/evaluate", response_model=RetrievalJudgmentEvaluationEnvelope)
async def evaluate_retrieval_judgments(
    request: RetrievalJudgmentEvaluationRequest,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: RetrievalJudgmentService = Depends(get_retrieval_judgment_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    enforce_inline_json_limit(request, settings, field_name="retrieval_judgment_evaluation")
    return ok(
        service.evaluate_ranked_results(
            owner_user_id=authenticated.user.user_id,
            query=request.query,
            ranked_evidence_ids=request.ranked_evidence_ids,
            cutoff=request.cutoff,
        )
    )


@router.put("/retrieval/judgments", response_model=RetrievalJudgmentEnvelope)
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


@router.delete(
    "/retrieval/judgments/{judgment_id}",
    response_model=RetrievalJudgmentDeleteEnvelope,
)
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


@router.get("/retrieval/sources", response_model=RetrievalSourcesEnvelope)
async def list_retrieval_sources(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    governance.require_permission(user=authenticated.user, permission_scope="retrieval:read")
    return ok(service.list_retrieval_sources())


@router.post("/retrieval/reindex", response_model=RetrievalReindexEnvelope)
async def reindex_retrieval(
    request: RetrievalReindexRequest,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    governance.require_permission(user=authenticated.user, permission_scope="admin:write")
    return ok(
        service.reindex_retrieval(
            include_seeded=request.include_seeded,
            include_corpus=request.include_corpus,
        )
    )


@router.get("/retrieval/integrity", response_model=RetrievalIntegrityEnvelope)
async def retrieval_integrity(
    include_seeded: bool = Query(default=True),
    include_corpus: bool = Query(default=False),
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    governance.require_permission(user=authenticated.user, permission_scope="admin:read")
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
