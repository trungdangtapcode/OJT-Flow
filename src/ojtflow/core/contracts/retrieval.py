"""Retrieval contracts for evidence-grounded workflow context."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel, NonBlankStr
from ojtflow.core.contracts.enums import EvidenceSourceType, TrustLevel
from ojtflow.core.contracts.evidence import Evidence


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
