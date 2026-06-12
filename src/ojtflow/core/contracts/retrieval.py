"""Retrieval contracts for evidence-grounded workflow context."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel, NonBlankStr
from ojtflow.core.contracts.enums import EvidenceSourceType, TrustLevel
from ojtflow.core.contracts.evidence import Evidence
from ojtflow.core.ids import new_id
from ojtflow.core.time import utc_now


class RetrievalQuery(ContractModel):
    """Normalized retrieval request used by workflow and direct API paths."""

    query: NonBlankStr
    workflow_id: str | None = None
    fields: list[str] = Field(default_factory=list)
    schema_id: str | None = None
    detected_format: str | None = None
    resource_type: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    filters: dict[str, Any] = Field(default_factory=dict)


RetrievalJudgmentValue = Literal["relevant", "partial", "not_relevant"]


class RetrievalRelevanceJudgmentWrite(ContractModel):
    """Validated operator relevance judgment before persistence metadata."""

    query: NonBlankStr
    evidence_id: NonBlankStr
    value: RetrievalJudgmentValue
    rating: int = Field(ge=0, le=3)
    source_id: NonBlankStr | None = None
    source_type: EvidenceSourceType | None = None
    source_version: NonBlankStr | None = None
    run_id: NonBlankStr | None = None
    search_signature: NonBlankStr | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalRelevanceJudgment(RetrievalRelevanceJudgmentWrite):
    """Durable relevance judgment for search evaluation and tuning."""

    judgment_id: NonBlankStr
    owner_user_id: NonBlankStr
    query_hash: NonBlankStr
    created_at: NonBlankStr
    updated_at: NonBlankStr


class RetrievalRelevanceJudgmentSummary(ContractModel):
    """Aggregate inventory summary for durable retrieval judgments."""

    total_count: int = Field(ge=0)
    query_count: int = Field(ge=0)
    evidence_count: int = Field(ge=0)
    source_count: int = Field(ge=0)
    relevant_count: int = Field(ge=0)
    partial_count: int = Field(ge=0)
    not_relevant_count: int = Field(ge=0)
    average_rating: float | None = None
    latest_updated_at: NonBlankStr | None = None
    sample_limit: int = Field(ge=1)
    value_counts: dict[RetrievalJudgmentValue, int] = Field(default_factory=dict)


class RetrievalEvaluationRecommendation(ContractModel):
    """Actionable retrieval tuning recommendation derived from judged results."""

    rule_id: NonBlankStr
    severity: NonBlankStr
    metric: NonBlankStr
    message: NonBlankStr
    suggested_action: NonBlankStr
    evidence_ids: list[NonBlankStr] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalEvaluationReadiness(ContractModel):
    """Interpretation of whether judgment metrics are sufficiently labeled."""

    status: NonBlankStr
    label: NonBlankStr
    message: NonBlankStr
    min_judged_count: int = Field(ge=0)
    min_coverage_at_k: float = Field(ge=0.0, le=1.0)


class RetrievalJudgmentEvaluationResult(ContractModel):
    """Judgment-aware evaluation for one ranked retrieval result set."""

    query: NonBlankStr
    ranked_evidence_ids: list[NonBlankStr] = Field(default_factory=list)
    cutoff: int = Field(ge=1)
    judged_count: int = Field(ge=0)
    unjudged_count: int = Field(ge=0)
    relevant_count: int = Field(ge=0)
    partial_count: int = Field(ge=0)
    not_relevant_count: int = Field(ge=0)
    coverage_at_k: float = Field(ge=0.0, le=1.0)
    hit_rate_at_k: float = Field(ge=0.0, le=1.0)
    precision_at_k: float = Field(ge=0.0, le=1.0)
    judged_precision: float | None = Field(default=None, ge=0.0, le=1.0)
    average_precision_at_k: float = Field(ge=0.0, le=1.0)
    mrr_at_k: float = Field(ge=0.0, le=1.0)
    ndcg_at_k: float | None = Field(default=None, ge=0.0, le=1.0)
    average_rating: float | None = None
    unjudged_evidence_ids: list[NonBlankStr] = Field(default_factory=list)
    judgment_ids: list[NonBlankStr] = Field(default_factory=list)
    evaluation_readiness: RetrievalEvaluationReadiness
    recommendations: list[RetrievalEvaluationRecommendation] = Field(default_factory=list)


class RetrievalSnippet(ContractModel):
    """Query-focused extractive snippet from a retrieved evidence chunk."""

    text: NonBlankStr
    start_char: int = Field(ge=0)
    end_char: int = Field(ge=0)
    matched_terms: list[str] = Field(default_factory=list)
    extraction_strategy: str = "deterministic_sentence_window_v0"


class RetrievalQueryVariant(ContractModel):
    """One query variant with provenance for query-rewrite transparency."""

    variant: NonBlankStr
    source: NonBlankStr
    reason: NonBlankStr
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalScoreComponent(ContractModel):
    """One auditable contribution to a retrieval hit's final score."""

    component: NonBlankStr
    label: NonBlankStr
    value: float
    rank: int | None = Field(default=None, ge=1)
    description: NonBlankStr
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalFacetBucket(ContractModel):
    """One result facet bucket and selected-hit count."""

    value: NonBlankStr
    count: int = Field(ge=1)


class RetrievalFacets(ContractModel):
    """Facet buckets summarizing final selected retrieval hits."""

    source_type: list[RetrievalFacetBucket] = Field(default_factory=list)
    clinical_domain: list[RetrievalFacetBucket] = Field(default_factory=list)
    standard_system: list[RetrievalFacetBucket] = Field(default_factory=list)
    trust_level: list[RetrievalFacetBucket] = Field(default_factory=list)


class RetrievalCoverageItem(ContractModel):
    """Coverage diagnostic for an expected retrieval metadata value."""

    field: NonBlankStr
    value: NonBlankStr
    selected_count: int = Field(ge=0)
    status: NonBlankStr
    severity: NonBlankStr
    reason: NonBlankStr
    suggested_action: NonBlankStr
    suggested_filter: dict[str, str] = Field(default_factory=dict)


class RetrievalCoverage(ContractModel):
    """Coverage diagnostics for final selected retrieval hits."""

    standard_system: list[RetrievalCoverageItem] = Field(default_factory=list)
    query_aspects: list[RetrievalCoverageItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class RetrievalDiversitySelection(ContractModel):
    """One selected hit's source-aware diversity selection explanation."""

    evidence_id: NonBlankStr
    source_id: NonBlankStr
    selected_rank: int = Field(ge=1)
    original_rank: int = Field(ge=1)
    relevance_score: float
    redundancy_score: float = Field(ge=0.0, le=1.0)
    selection_score: float
    reason: NonBlankStr


class RetrievalDiversitySummary(ContractModel):
    """Package-level source-diversity summary for final evidence selection."""

    enabled: bool = False
    selection_mode: NonBlankStr = "score_order"
    lambda_value: float | None = Field(default=None, ge=0.0, le=1.0)
    candidate_source_count: int = Field(ge=0)
    selected_source_count: int = Field(ge=0)
    duplicate_selected_source_count: int = Field(ge=0)
    selected_hits: list[RetrievalDiversitySelection] = Field(default_factory=list)


class RetrievalHit(ContractModel):
    """One ranked retrieval candidate with transparent scoring components."""

    evidence: Evidence
    score: float
    lexical_score: float = 0.0
    vector_score: float = 0.0
    rerank_score: float = 0.0
    score_components: list[RetrievalScoreComponent] = Field(default_factory=list)
    matched_terms: list[str] = Field(default_factory=list)
    source_locator: dict[str, Any] = Field(default_factory=dict)
    match_explanation: dict[str, Any] = Field(default_factory=dict)
    snippet: RetrievalSnippet | None = None


RetrievalEvidenceBucketKind = Literal[
    "schema",
    "policy",
    "terminology",
    "fhir_mapping",
    "source_locator",
    "prior_decision",
    "other",
]


class RetrievalEvidenceBucket(ContractModel):
    """Operator-facing evidence bucket for clinical workflow audit panels."""

    bucket_id: RetrievalEvidenceBucketKind
    label: NonBlankStr
    description: NonBlankStr
    evidence_ids: list[NonBlankStr] = Field(default_factory=list)
    source_ids: list[NonBlankStr] = Field(default_factory=list)
    hit_count: int = Field(ge=0)
    required: bool = False
    status: NonBlankStr
    warnings: list[NonBlankStr] = Field(default_factory=list)
    suggested_filter: dict[str, NonBlankStr] = Field(default_factory=dict)


class RetrievalTrace(ContractModel):
    """Debuggable trace for retrieval strategy and candidate selection."""

    strategy: str
    request_id: str | None = None
    query_variants: list[str] = Field(default_factory=list)
    query_variant_details: list[RetrievalQueryVariant] = Field(default_factory=list)
    fusion_diagnostics: dict[str, Any] = Field(default_factory=dict)
    filters_applied: dict[str, Any] = Field(default_factory=dict)
    candidates_seen: int = 0
    final_hit_ids: list[str] = Field(default_factory=list)
    safety_flags: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class RetrievalQualitySignal(ContractModel):
    """Operator-facing quality gate signal for one retrieval package."""

    code: NonBlankStr
    severity: NonBlankStr
    message: NonBlankStr
    suggested_action: NonBlankStr
    evidence_ids: list[NonBlankStr] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalQualitySummary(ContractModel):
    """Aggregate readiness summary for a retrieval package."""

    status: NonBlankStr
    score: int = Field(ge=0, le=100)
    success_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)
    destructive_count: int = Field(ge=0)
    info_count: int = Field(ge=0)
    top_action: NonBlankStr
    blocker_codes: list[NonBlankStr] = Field(default_factory=list)
    warning_codes: list[NonBlankStr] = Field(default_factory=list)


RetrievalRecommendedActionType = Literal[
    "apply_filter",
    "broaden_query",
    "rewrite_query",
    "reindex_source",
    "add_source",
    "require_review",
    "diversify_sources",
]


class RetrievalRecommendedAction(ContractModel):
    """Concrete corrective retrieval action derived from package quality signals."""

    action_id: NonBlankStr
    priority: int = Field(ge=1)
    severity: NonBlankStr
    action_type: RetrievalRecommendedActionType
    title: NonBlankStr
    description: NonBlankStr
    suggested_filter: dict[str, NonBlankStr] = Field(default_factory=dict)
    source_signal_codes: list[NonBlankStr] = Field(default_factory=list)
    evidence_ids: list[NonBlankStr] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalRecommendedActionSummary(ContractModel):
    """Aggregate corrective-action urgency summary for retrieval triage."""

    count: int = Field(ge=0)
    highest_priority: int | None = Field(default=None, ge=1)
    highest_severity: NonBlankStr | None = None
    top_action_title: NonBlankStr | None = None
    apply_filter_count: int = Field(ge=0)
    broaden_query_count: int = Field(ge=0)
    action_type_counts: dict[NonBlankStr, int] = Field(default_factory=dict)


class RetrievalStrategyRecommendation(ContractModel):
    """Backend-owned explanation of the selected retrieval strategy."""

    recommendation_id: NonBlankStr
    title: NonBlankStr
    technique: NonBlankStr
    status: NonBlankStr
    rationale: NonBlankStr
    source_signal_codes: list[NonBlankStr] = Field(default_factory=list)
    suggested_filters: dict[str, NonBlankStr] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalStandardSearchStep(ContractModel):
    """One healthcare-standard search step recommended for follow-up retrieval."""

    step_id: NonBlankStr
    label: NonBlankStr
    standard_system: NonBlankStr
    route_type: NonBlankStr
    query: NonBlankStr
    rationale: NonBlankStr
    priority: int = Field(ge=1)
    suggested_filters: dict[str, NonBlankStr] = Field(default_factory=dict)
    governance_notes: list[NonBlankStr] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalStandardSearchPlan(ContractModel):
    """Standards-aware playbook for the next governed healthcare search."""

    plan_id: NonBlankStr
    summary: NonBlankStr
    primary_route: NonBlankStr
    steps: list[RetrievalStandardSearchStep] = Field(default_factory=list)
    missing_routes: list[NonBlankStr] = Field(default_factory=list)
    governance_notes: list[NonBlankStr] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalFilterSuggestion(ContractModel):
    """Metadata filter suggested by deterministic self-query analysis."""

    field: NonBlankStr
    value: NonBlankStr
    reason: NonBlankStr
    rule_id: NonBlankStr
    confidence: float = Field(ge=0.0, le=1.0)
    applied: bool = False


class RetrievalQueryDiagnostic(ContractModel):
    """Operator-facing query quality diagnostic before retrieval execution."""

    code: NonBlankStr
    severity: NonBlankStr
    message: NonBlankStr
    suggested_action: NonBlankStr
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalSearchHint(ContractModel):
    """External medical search syntax hint derived from deterministic analysis."""

    target: NonBlankStr
    query: NonBlankStr
    url: str | None = None
    rationale: NonBlankStr
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalQueryProfile(ContractModel):
    """Data-driven query route hint for adaptive retrieval and operator review."""

    profile_id: NonBlankStr
    label: NonBlankStr
    route: NonBlankStr
    complexity: NonBlankStr
    retrieval_mode: NonBlankStr
    description: NonBlankStr
    suggested_filters: dict[str, str] = Field(default_factory=dict)
    rule_ids: list[NonBlankStr] = Field(default_factory=list)


class RetrievalQueryRoute(ContractModel):
    """Selected retrieval strategy route for the normalized query context."""

    route_id: NonBlankStr
    strategy_id: NonBlankStr
    label: NonBlankStr
    retrieval_mode: NonBlankStr
    rationale: NonBlankStr
    rule_id: NonBlankStr
    priority: int = Field(ge=1)
    confidence: float = Field(ge=0.0, le=1.0)
    matched_criteria: list[NonBlankStr] = Field(default_factory=list)
    suggested_filters: dict[str, str] = Field(default_factory=dict)
    risk_controls: list[NonBlankStr] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalQueryAspect(ContractModel):
    """Data-driven search aspect for decomposed healthcare retrieval planning."""

    aspect_id: NonBlankStr
    label: NonBlankStr
    question: NonBlankStr
    rationale: NonBlankStr
    priority: int = Field(ge=1)
    rule_id: NonBlankStr
    suggested_terms: list[NonBlankStr] = Field(default_factory=list)
    suggested_filters: dict[str, str] = Field(default_factory=dict)


RetrievalTaskTarget = Literal["local_corpus", "external_medical_index"]
RetrievalTaskActionType = Literal["run_local_search", "open_external_url", "copy_query"]


CorpusLifecycleState = Literal[
    "candidate",
    "approved",
    "deprecated",
    "blocked",
    "failed",
    "needs_review",
]


class CorpusLicenseMetadata(ContractModel):
    """License and use constraints for one corpus source adapter."""

    license_id: NonBlankStr
    name: NonBlankStr
    url: str | None = None
    constraints: list[NonBlankStr] = Field(default_factory=list)


class CorpusSourceAdapter(ContractModel):
    """Data-driven source adapter spec for governed corpus ingestion."""

    adapter_id: NonBlankStr
    source_id: NonBlankStr
    title: NonBlankStr
    authority: NonBlankStr
    source_type: EvidenceSourceType
    clinical_domain: NonBlankStr
    standard_system: NonBlankStr
    access_mode: NonBlankStr
    ingestion_mode: NonBlankStr
    release_version: NonBlankStr
    refresh_cadence: NonBlankStr
    reviewer_state: CorpusLifecycleState
    lifecycle_state: CorpusLifecycleState
    enabled: bool = True
    source_urls: dict[NonBlankStr, NonBlankStr] = Field(default_factory=dict)
    local_paths: list[NonBlankStr] = Field(default_factory=list)
    parser: NonBlankStr = "plain_text"
    chunk_profile: NonBlankStr = "paragraph_window_v0"
    fetch_time_policy: NonBlankStr = "record_fetch_or_filesystem_observed_time"
    license: CorpusLicenseMetadata
    governance_notes: list[NonBlankStr] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CorpusAdapterCatalog(ContractModel):
    """Versioned corpus adapter registry loaded from trusted knowledge data."""

    version: NonBlankStr
    adapters: list[CorpusSourceAdapter] = Field(default_factory=list)


class CorpusChunkingProfile(ContractModel):
    """Data-driven chunking behavior for one family of corpus artifacts."""

    profile_id: NonBlankStr
    label: NonBlankStr
    description: NonBlankStr
    boundary_strategy: NonBlankStr
    max_chars: int = Field(ge=200, le=8000)
    overlap_chars: int = Field(ge=0, le=2000)
    preferred_extensions: list[NonBlankStr] = Field(default_factory=list)
    metadata_fields: list[NonBlankStr] = Field(default_factory=list)
    intended_sources: list[NonBlankStr] = Field(default_factory=list)
    lifecycle_state: CorpusLifecycleState = "approved"
    governance_notes: list[NonBlankStr] = Field(default_factory=list)


class CorpusChunkingProfileCatalog(ContractModel):
    """Versioned chunking profile registry loaded from trusted knowledge data."""

    version: NonBlankStr
    profiles: list[CorpusChunkingProfile] = Field(default_factory=list)


class CorpusIngestionItem(ContractModel):
    """One observed ingestion artifact with governance and consistency metadata."""

    item_id: NonBlankStr
    source_id: NonBlankStr
    adapter_id: NonBlankStr | None = None
    title: NonBlankStr
    source_type: EvidenceSourceType
    clinical_domain: NonBlankStr
    standard_system: NonBlankStr
    release_version: NonBlankStr
    fetched_at: NonBlankStr
    fetch_time_source: NonBlankStr
    content_hash: NonBlankStr
    size_bytes: int = Field(ge=0)
    path: NonBlankStr | None = None
    source_url: str | None = None
    license: CorpusLicenseMetadata
    reviewer_state: CorpusLifecycleState
    lifecycle_state: CorpusLifecycleState
    enabled: bool = True
    warnings: list[NonBlankStr] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CorpusIngestionManifest(ContractModel):
    """Versioned manifest describing the files available for corpus indexing."""

    version: NonBlankStr
    generated_at: NonBlankStr
    adapter_catalog_version: NonBlankStr
    knowledge_root: NonBlankStr
    item_count: int = Field(ge=0)
    enabled_adapter_count: int = Field(ge=0)
    approved_item_count: int = Field(ge=0)
    needs_review_item_count: int = Field(ge=0)
    items: list[CorpusIngestionItem] = Field(default_factory=list)


CorpusIndexDecision = Literal["indexed", "indexed_needs_review", "skipped"]


class CorpusIngestionLedgerRecord(ContractModel):
    """Chunk-level lineage record for one indexed corpus chunk."""

    ledger_record_id: NonBlankStr
    ingestion_run_id: NonBlankStr
    item_id: NonBlankStr
    chunk_id: NonBlankStr
    source_id: NonBlankStr
    adapter_id: NonBlankStr | None = None
    adapter_version: NonBlankStr
    title: NonBlankStr
    source_type: EvidenceSourceType
    clinical_domain: NonBlankStr
    standard_system: NonBlankStr
    source_version: NonBlankStr
    path: NonBlankStr | None = None
    source_url: str | None = None
    raw_artifact_hash: NonBlankStr
    chunk_content_hash: NonBlankStr
    chunk_index: int = Field(ge=0)
    chunk_start_char: int = Field(ge=0)
    chunk_end_char: int = Field(ge=0)
    chunk_profile: NonBlankStr | None = None
    parser: NonBlankStr | None = None
    reviewer_state: CorpusLifecycleState
    lifecycle_state: CorpusLifecycleState
    reviewer_decision: CorpusLifecycleState
    index_decision: CorpusIndexDecision
    approved_for_indexing: bool = False
    warnings: list[NonBlankStr] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CorpusIngestionLedgerSummary(ContractModel):
    """Aggregate chunk-level lineage state for a corpus ingestion run."""

    source_count: int = Field(ge=0)
    chunk_count: int = Field(ge=0)
    approved_chunk_count: int = Field(ge=0)
    needs_review_chunk_count: int = Field(ge=0)
    deprecated_chunk_count: int = Field(ge=0)
    unapproved_chunk_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)


class CorpusIngestionLedger(ContractModel):
    """Versioned chunk-level ledger for auditable corpus indexing."""

    version: NonBlankStr
    generated_at: NonBlankStr
    ingestion_run_id: NonBlankStr
    adapter_catalog_version: NonBlankStr
    knowledge_root: NonBlankStr
    chunking: dict[str, int] = Field(default_factory=dict)
    summary: CorpusIngestionLedgerSummary
    records: list[CorpusIngestionLedgerRecord] = Field(default_factory=list)


RetrievalIndexComponentId = Literal["lexical", "vector", "graph"]
RetrievalIndexComponentStatus = Literal[
    "ready",
    "stale",
    "empty",
    "not_available",
]


class RetrievalIndexComponent(ContractModel):
    """One index component in the active retrieval runtime."""

    component_id: RetrievalIndexComponentId
    status: RetrievalIndexComponentStatus
    generation_id: NonBlankStr | None = None
    expected_generation_id: NonBlankStr | None = None
    provider: NonBlankStr | None = None
    model: NonBlankStr | None = None
    dimensions: int | None = Field(default=None, ge=0)
    chunk_count: int = Field(default=0, ge=0)
    source_count: int = Field(default=0, ge=0)
    stale_chunk_count: int = Field(default=0, ge=0)
    graph_count: int = Field(default=0, ge=0)
    node_count: int = Field(default=0, ge=0)
    edge_count: int = Field(default=0, ge=0)
    triple_count: int = Field(default=0, ge=0)
    warnings: list[NonBlankStr] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalIndexManifestSummary(ContractModel):
    """Aggregate index manifest counters."""

    component_count: int = Field(ge=0)
    ready_component_count: int = Field(ge=0)
    stale_component_count: int = Field(ge=0)
    unavailable_component_count: int = Field(ge=0)
    chunk_count: int = Field(ge=0)
    source_count: int = Field(ge=0)
    stale_chunk_count: int = Field(ge=0)
    graph_count: int = Field(ge=0)
    node_count: int = Field(ge=0)
    edge_count: int = Field(ge=0)
    triple_count: int = Field(ge=0)


class RetrievalIndexManifest(ContractModel):
    """Operational manifest for active lexical, vector, and graph indexes."""

    version: NonBlankStr
    generated_at: NonBlankStr
    repository: NonBlankStr
    retrieval_framework: NonBlankStr
    knowledge_root: NonBlankStr
    corpus_ingestion_run_ids: list[NonBlankStr] = Field(default_factory=list)
    embedding_generation_id: NonBlankStr | None = None
    lexical_generation_id: NonBlankStr | None = None
    graph_generation_id: NonBlankStr | None = None
    summary: RetrievalIndexManifestSummary
    components: list[RetrievalIndexComponent] = Field(default_factory=list)
    warnings: list[NonBlankStr] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EmbeddingReindexImpactSummary(ContractModel):
    """Dry-run impact summary for an embedding reindex request."""

    include_seeded: bool = True
    include_corpus: bool = True
    chunk_count: int = Field(ge=0)
    source_count: int = Field(ge=0)
    stale_chunk_count: int = Field(ge=0)
    current_embedding_generation_id: NonBlankStr | None = None
    target_embedding_generation_id: NonBlankStr | None = None
    embedding_generation_changed: bool = False
    approval_required: bool = True
    expected_job_type: NonBlankStr = "embedding_reindex"


class EmbeddingReindexSafetyReport(ContractModel):
    """Approval-gated dry-run report for embedding reindex operations."""

    version: NonBlankStr
    generated_at: NonBlankStr
    approval_token: NonBlankStr
    approval_token_hash: NonBlankStr
    approval_payload_hash: NonBlankStr
    impact: EmbeddingReindexImpactSummary
    current_manifest: RetrievalIndexManifest
    warnings: list[NonBlankStr] = Field(default_factory=list)
    required_operator_action: NonBlankStr
    metadata: dict[str, Any] = Field(default_factory=dict)


class EmbeddingReindexRollbackMarker(ContractModel):
    """Sanitized marker that captures pre-reindex state for manual rollback."""

    marker_id: str = Field(default_factory=lambda: new_id("embmark"))
    marked_at: str = Field(default_factory=lambda: utc_now().isoformat())
    job_id: NonBlankStr | None = None
    request_id: NonBlankStr | None = None
    approval_token_hash: NonBlankStr
    before_manifest_hash: NonBlankStr
    before_lexical_generation_id: NonBlankStr | None = None
    before_embedding_generation_id: NonBlankStr | None = None
    before_graph_generation_id: NonBlankStr | None = None
    corpus_ingestion_run_ids: list[NonBlankStr] = Field(default_factory=list)
    destructive: bool = False
    rollback_note: NonBlankStr
    marker_ref_hash: NonBlankStr | None = None


class EmbeddingReindexQualityComparison(ContractModel):
    """Post-run comparison between preflight and completed index manifests."""

    status: NonBlankStr
    before_manifest_hash: NonBlankStr
    after_manifest_hash: NonBlankStr
    chunk_count_before: int = Field(ge=0)
    chunk_count_after: int = Field(ge=0)
    chunk_count_delta: int
    source_count_before: int = Field(ge=0)
    source_count_after: int = Field(ge=0)
    source_count_delta: int
    stale_chunk_count_before: int = Field(ge=0)
    stale_chunk_count_after: int = Field(ge=0)
    stale_chunk_count_delta: int
    embedding_generation_changed: bool = False
    corpus_ingestion_run_ids_added: list[NonBlankStr] = Field(default_factory=list)
    corpus_ingestion_run_ids_removed: list[NonBlankStr] = Field(default_factory=list)
    warnings: list[NonBlankStr] = Field(default_factory=list)


class RetrievalSearchTask(ContractModel):
    """Executable retrieval task derived from query analysis before ranking."""

    task_id: NonBlankStr
    label: NonBlankStr
    target: RetrievalTaskTarget
    action_type: RetrievalTaskActionType
    query: NonBlankStr
    rationale: NonBlankStr
    priority: int = Field(ge=1)
    required: bool = False
    aspect_id: NonBlankStr | None = None
    search_hint_target: NonBlankStr | None = None
    query_variants: list[NonBlankStr] = Field(default_factory=list)
    standards: list[NonBlankStr] = Field(default_factory=list)
    suggested_filters: dict[str, str] = Field(default_factory=dict)
    warnings: list[NonBlankStr] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalSearchPreset(ContractModel):
    """Operator-facing retrieval query preset loaded from trusted knowledge data."""

    preset_id: NonBlankStr
    label: NonBlankStr
    description: NonBlankStr
    category: NonBlankStr | None = None
    query: NonBlankStr
    top_k: int = Field(default=5, ge=1, le=20)
    fields: list[NonBlankStr] = Field(default_factory=list)
    schema_id: NonBlankStr | None = None
    detected_format: NonBlankStr | None = None
    resource_type: NonBlankStr | None = None
    clinical_domain: NonBlankStr | None = None
    standard_system: NonBlankStr | None = None
    trust_level: TrustLevel | None = TrustLevel.APPROVED
    source_type: EvidenceSourceType | None = None
    target_sources: list[NonBlankStr] = Field(default_factory=list)
    launch_hint_targets: list[NonBlankStr] = Field(default_factory=list)


class RetrievalSearchOption(ContractModel):
    """One data-driven option for operator retrieval controls."""

    value: NonBlankStr
    label: NonBlankStr
    description: NonBlankStr | None = None


class RetrievalSearchOptions(ContractModel):
    """Data-driven retrieval query-builder options loaded from trusted knowledge data."""

    version: NonBlankStr = "retrieval_search_options.v1"
    detected_formats: list[RetrievalSearchOption] = Field(default_factory=list)
    top_k_values: list[int] = Field(default_factory=list)


class RetrievalSourceTrustPolicy(ContractModel):
    """Governance policy for one retrievable healthcare source."""

    source_id: NonBlankStr
    source_name: NonBlankStr
    authority: NonBlankStr
    domain: NonBlankStr
    standard_system: NonBlankStr
    clinical_scope: list[NonBlankStr] = Field(default_factory=list)
    intended_use: list[NonBlankStr] = Field(default_factory=list)
    prohibited_use: list[NonBlankStr] = Field(default_factory=list)
    refresh_cadence: NonBlankStr
    license_constraints: list[NonBlankStr] = Field(default_factory=list)
    access_mode: NonBlankStr
    ingestion_mode: NonBlankStr
    evidence_tier: NonBlankStr
    requires_reviewer_approval: bool = True
    source_urls: dict[NonBlankStr, NonBlankStr] = Field(default_factory=dict)
    policy_notes: list[NonBlankStr] = Field(default_factory=list)


class RetrievalSourceTrustPolicyCatalog(ContractModel):
    """Versioned source governance catalog loaded from trusted data."""

    version: NonBlankStr
    policies: list[RetrievalSourceTrustPolicy] = Field(default_factory=list)


class RetrievalStrategyProfile(ContractModel):
    """Operator-facing retrieval/RAG strategy preset and runtime contract."""

    strategy_id: NonBlankStr
    label: NonBlankStr
    status: NonBlankStr
    technique_family: NonBlankStr
    description: NonBlankStr
    intended_use: list[NonBlankStr] = Field(default_factory=list)
    avoid_when: list[NonBlankStr] = Field(default_factory=list)
    query_transformations: list[NonBlankStr] = Field(default_factory=list)
    retrieval_modes: list[NonBlankStr] = Field(default_factory=list)
    required_runtime: list[NonBlankStr] = Field(default_factory=list)
    compatible_filters: list[NonBlankStr] = Field(default_factory=list)
    risk_controls: list[NonBlankStr] = Field(default_factory=list)
    roadmap_refs: list[NonBlankStr] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalStrategyCatalog(ContractModel):
    """Versioned retrieval strategy registry loaded from trusted data."""

    version: NonBlankStr
    strategies: list[RetrievalStrategyProfile] = Field(default_factory=list)


class RetrievalConceptCandidate(ContractModel):
    """Controlled-vocabulary concept candidate detected in a retrieval query."""

    concept_id: NonBlankStr
    display_name: NonBlankStr
    standard_system: NonBlankStr
    code: str | None = None
    clinical_domain: str | None = None
    matched_aliases: list[NonBlankStr] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    source: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalQueryAnalysis(ContractModel):
    """Auditable query understanding used before first-stage retrieval."""

    strategy: str = "deterministic_clinical_expansion_v0"
    detected_concepts: list[str] = Field(default_factory=list)
    concept_candidates: list[RetrievalConceptCandidate] = Field(default_factory=list)
    expanded_terms: list[str] = Field(default_factory=list)
    standards: list[str] = Field(default_factory=list)
    rule_ids: list[str] = Field(default_factory=list)
    query_variants: list[str] = Field(default_factory=list)
    query_variant_details: list[RetrievalQueryVariant] = Field(default_factory=list)
    filter_suggestions: list[RetrievalFilterSuggestion] = Field(default_factory=list)
    diagnostics: list[RetrievalQueryDiagnostic] = Field(default_factory=list)
    search_hints: list[RetrievalSearchHint] = Field(default_factory=list)
    query_profile: RetrievalQueryProfile | None = None
    query_route: RetrievalQueryRoute | None = None
    query_aspects: list[RetrievalQueryAspect] = Field(default_factory=list)
    retrieval_tasks: list[RetrievalSearchTask] = Field(default_factory=list)


class RetrievalPlanCoverageSummary(ContractModel):
    """Backend-owned pre-search coverage summary for a retrieval plan."""

    ready: bool
    local_task_count: int = Field(ge=0)
    required_local_task_count: int = Field(ge=0)
    external_task_count: int = Field(ge=0)
    standard_count: int = Field(ge=0)
    filter_count: int = Field(ge=0)
    standards: list[NonBlankStr] = Field(default_factory=list)
    warnings: list[NonBlankStr] = Field(default_factory=list)
    next_action: NonBlankStr
    summary: NonBlankStr


class RetrievalPlanTaskSummary(ContractModel):
    """Backend-owned operator summary for pre-search task execution."""

    total_task_count: int = Field(ge=0)
    runnable_local_count: int = Field(ge=0)
    required_runnable_local_count: int = Field(ge=0)
    external_open_count: int = Field(ge=0)
    external_copy_count: int = Field(ge=0)
    manual_followup_count: int = Field(ge=0)
    blocked_task_count: int = Field(ge=0)
    primary_action: NonBlankStr
    summary: NonBlankStr


class RetrievalPlanRiskSignal(ContractModel):
    """Prioritized risk signal for pre-search retrieval planning."""

    code: NonBlankStr
    severity: NonBlankStr
    message: NonBlankStr
    suggested_action: NonBlankStr
    source: NonBlankStr
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalPlan(ContractModel):
    """Plan-only retrieval response before ranked evidence is generated."""

    query: RetrievalQuery
    query_analysis: RetrievalQueryAnalysis
    coverage_summary: RetrievalPlanCoverageSummary
    task_summary: RetrievalPlanTaskSummary
    risk_signals: list[RetrievalPlanRiskSignal] = Field(default_factory=list)
    search_signature: NonBlankStr
    summary: NonBlankStr


class RetrievalInterpretation(ContractModel):
    """Package-level, operator-facing explanation of retrieval support quality."""

    status: NonBlankStr
    summary: NonBlankStr
    top_evidence_id: NonBlankStr | None = None
    top_source_id: NonBlankStr | None = None
    top_score_driver: NonBlankStr | None = None
    support_status: NonBlankStr | None = None
    matched_terms: list[NonBlankStr] = Field(default_factory=list)
    concept_labels: list[NonBlankStr] = Field(default_factory=list)
    aspect_labels: list[NonBlankStr] = Field(default_factory=list)
    required_bucket_count: int = Field(default=0, ge=0)
    covered_required_bucket_count: int = Field(default=0, ge=0)
    missing_required_buckets: list[NonBlankStr] = Field(default_factory=list)
    warning_count: int = Field(default=0, ge=0)
    next_action_title: NonBlankStr | None = None
    next_action_detail: NonBlankStr | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


RetrievalSupportStatus = Literal["strong", "partial", "weak", "unsupported"]


class RetrievalEvidenceSupportRow(ContractModel):
    """One auditable support row connecting a claim to ranked evidence."""

    claim_id: NonBlankStr
    claim: NonBlankStr
    support_status: RetrievalSupportStatus
    evidence_id: NonBlankStr
    source_id: NonBlankStr
    source_type: EvidenceSourceType
    source_version: NonBlankStr | None = None
    source_locator: dict[str, Any] = Field(default_factory=dict)
    matched_terms: list[NonBlankStr] = Field(default_factory=list)
    score: float
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    reasoning: NonBlankStr
    warnings: list[NonBlankStr] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalEvidenceSupportMatrix(ContractModel):
    """Evidence support matrix for retrieval answers and downstream synthesis."""

    version: NonBlankStr = "retrieval_evidence_support_matrix.v1"
    query_claim: NonBlankStr
    row_count: int = Field(ge=0)
    strong_count: int = Field(ge=0)
    partial_count: int = Field(ge=0)
    weak_count: int = Field(ge=0)
    unsupported_count: int = Field(ge=0)
    rows: list[RetrievalEvidenceSupportRow] = Field(default_factory=list)
    warnings: list[NonBlankStr] = Field(default_factory=list)


RetrievalAnswerStatus = Literal["supported", "partial", "refused", "review_required"]


class RetrievalAnswerCitation(ContractModel):
    """One citation used by a guarded retrieval answer."""

    citation_id: NonBlankStr
    evidence_id: NonBlankStr
    source_id: NonBlankStr
    source_type: EvidenceSourceType
    source_version: NonBlankStr | None = None
    source_locator: dict[str, Any] = Field(default_factory=dict)
    supported_claim_ids: list[NonBlankStr] = Field(default_factory=list)


class RetrievalAnswerClaim(ContractModel):
    """One answer claim after evidence-support and graph checks."""

    claim_id: NonBlankStr
    text: NonBlankStr
    support_status: RetrievalSupportStatus
    evidence_ids: list[NonBlankStr] = Field(default_factory=list)
    citation_ids: list[NonBlankStr] = Field(default_factory=list)
    graph_path_refs: list[NonBlankStr] = Field(default_factory=list)
    graph_guard: dict[str, Any] = Field(default_factory=dict)
    warnings: list[NonBlankStr] = Field(default_factory=list)


class RetrievalAnswerFreshnessWarning(ContractModel):
    """Freshness, lifecycle, or version warning for cited evidence."""

    warning_id: NonBlankStr
    severity: NonBlankStr
    evidence_id: NonBlankStr | None = None
    source_id: NonBlankStr | None = None
    source_version: NonBlankStr | None = None
    message: NonBlankStr
    suggested_action: NonBlankStr
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalAnswer(ContractModel):
    """Self-checked answer synthesized only from retrieved evidence."""

    version: NonBlankStr = "retrieval_answer.v1"
    status: RetrievalAnswerStatus
    answer_text: NonBlankStr
    refusal_reason: NonBlankStr | None = None
    requires_human_review: bool = True
    confidence: float = Field(ge=0.0, le=1.0)
    claims: list[RetrievalAnswerClaim] = Field(default_factory=list)
    citations: list[RetrievalAnswerCitation] = Field(default_factory=list)
    unsupported_claims: list[RetrievalAnswerClaim] = Field(default_factory=list)
    missing_evidence_gaps: list[NonBlankStr] = Field(default_factory=list)
    freshness_warnings: list[RetrievalAnswerFreshnessWarning] = Field(default_factory=list)
    graph_path_summary: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalPackage(ContractModel):
    """Evidence package returned to workflow state and API callers."""

    hits: list[RetrievalHit] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    evidence_buckets: list[RetrievalEvidenceBucket] = Field(default_factory=list)
    coverage: RetrievalCoverage | None = None
    facets: RetrievalFacets | None = None
    quality_signals: list[RetrievalQualitySignal] = Field(default_factory=list)
    quality_summary: RetrievalQualitySummary | None = None
    recommended_actions: list[RetrievalRecommendedAction] = Field(default_factory=list)
    recommended_action_summary: RetrievalRecommendedActionSummary | None = None
    remediation_summary: NonBlankStr | None = None
    interpretation: RetrievalInterpretation | None = None
    support_matrix: RetrievalEvidenceSupportMatrix | None = None
    answer: RetrievalAnswer | None = None
    strategy_recommendations: list[RetrievalStrategyRecommendation] = Field(default_factory=list)
    standard_search_plan: RetrievalStandardSearchPlan | None = None
    diversity: RetrievalDiversitySummary | None = None
    trace: RetrievalTrace
    handoff_context: dict[str, Any] = Field(default_factory=dict)


class RetrievalSource(ContractModel):
    """Inventory entry for available trusted retrieval sources."""

    source_id: str
    source_type: EvidenceSourceType
    title: str
    source_version: str | None = None
    trust_level: TrustLevel = TrustLevel.APPROVED
    clinical_domain: str | None = None
    standard_system: str | None = None
    chunk_count: int = 0
    authority: str | None = None
    access_mode: str | None = None
    ingestion_mode: str | None = None
    license_id: str | None = None
    license_name: str | None = None
    reviewer_state: CorpusLifecycleState | None = None
    lifecycle_state: CorpusLifecycleState | None = None
    content_hash: str | None = None
    canonical_source_id: str | None = None
    chunk_profile: str | None = None
    resource_type: str | None = None


class RetrievalIntegrityItem(ContractModel):
    """One consistency check for a retrieval source family."""

    source_id: str
    status: NonBlankStr
    expected_chunk_count: int = Field(ge=0)
    indexed_chunk_count: int = Field(ge=0)
    expected_hash: str | None = None
    indexed_hash: str | None = None
    message: NonBlankStr


class RetrievalIntegrityReport(ContractModel):
    """Consistency report comparing trusted knowledge sources with the index."""

    repository: NonBlankStr
    status: NonBlankStr
    checked_scope: NonBlankStr
    expected_source_count: int = Field(ge=0)
    indexed_source_count: int = Field(ge=0)
    ok_count: int = Field(ge=0)
    stale_count: int = Field(ge=0)
    missing_count: int = Field(ge=0)
    extra_count: int = Field(ge=0)
    checks: list[RetrievalIntegrityItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


RetrievalFreshnessStatus = Literal["ready", "watch", "needs_review", "blocked"]


class RetrievalFreshnessSource(ContractModel):
    """Operational freshness/readiness status for one retrievable source."""

    source_id: NonBlankStr
    title: NonBlankStr
    source_type: EvidenceSourceType
    authority: NonBlankStr | None = None
    standard_system: NonBlankStr | None = None
    clinical_domain: NonBlankStr | None = None
    release_version: NonBlankStr | None = None
    refresh_cadence: NonBlankStr | None = None
    lifecycle_state: CorpusLifecycleState | None = None
    reviewer_state: CorpusLifecycleState | None = None
    indexed_chunk_count: int = Field(ge=0)
    manifest_item_count: int = Field(ge=0)
    last_observed_at: NonBlankStr | None = None
    age_days: int | None = Field(default=None, ge=0)
    freshness_window_days: int | None = Field(default=None, ge=1)
    status: RetrievalFreshnessStatus
    severity: NonBlankStr
    issues: list[NonBlankStr] = Field(default_factory=list)
    recommended_actions: list[NonBlankStr] = Field(default_factory=list)
    source_urls: dict[NonBlankStr, NonBlankStr] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalFreshnessReport(ContractModel):
    """Readiness gate for retrieval source freshness and corpus governance."""

    version: NonBlankStr
    generated_at: NonBlankStr
    status: RetrievalFreshnessStatus
    score: int = Field(ge=0, le=100)
    source_count: int = Field(ge=0)
    ready_count: int = Field(ge=0)
    watch_count: int = Field(ge=0)
    needs_review_count: int = Field(ge=0)
    blocked_count: int = Field(ge=0)
    stale_count: int = Field(ge=0)
    unindexed_count: int = Field(ge=0)
    missing_policy_count: int = Field(ge=0)
    adapter_catalog_version: NonBlankStr
    manifest_version: NonBlankStr
    policy_catalog_version: NonBlankStr
    sources: list[RetrievalFreshnessSource] = Field(default_factory=list)
    warnings: list[NonBlankStr] = Field(default_factory=list)
