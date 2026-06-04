"""Retrieval contracts for evidence-grounded workflow context."""

from __future__ import annotations

from typing import Any

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


class RetrievalSnippet(ContractModel):
    """Query-focused extractive snippet from a retrieved evidence chunk."""

    text: NonBlankStr
    start_char: int = Field(ge=0)
    end_char: int = Field(ge=0)
    matched_terms: list[str] = Field(default_factory=list)
    extraction_strategy: str = "deterministic_sentence_window_v0"


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


class RetrievalCoverage(ContractModel):
    """Coverage diagnostics for final selected retrieval hits."""

    standard_system: list[RetrievalCoverageItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class RetrievalHit(ContractModel):
    """One ranked retrieval candidate with transparent scoring components."""

    evidence: Evidence
    score: float
    lexical_score: float = 0.0
    vector_score: float = 0.0
    rerank_score: float = 0.0
    matched_terms: list[str] = Field(default_factory=list)
    source_locator: dict[str, Any] = Field(default_factory=dict)
    snippet: RetrievalSnippet | None = None


class RetrievalTrace(ContractModel):
    """Debuggable trace for retrieval strategy and candidate selection."""

    strategy: str
    query_variants: list[str] = Field(default_factory=list)
    filters_applied: dict[str, Any] = Field(default_factory=dict)
    candidates_seen: int = 0
    final_hit_ids: list[str] = Field(default_factory=list)
    safety_flags: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


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


class RetrievalSearchHint(ContractModel):
    """External medical search syntax hint derived from deterministic analysis."""

    target: NonBlankStr
    query: NonBlankStr
    url: str | None = None
    rationale: NonBlankStr
    warnings: list[str] = Field(default_factory=list)


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
    filter_suggestions: list[RetrievalFilterSuggestion] = Field(default_factory=list)
    diagnostics: list[RetrievalQueryDiagnostic] = Field(default_factory=list)
    search_hints: list[RetrievalSearchHint] = Field(default_factory=list)


class RetrievalPackage(ContractModel):
    """Evidence package returned to workflow state and API callers."""

    hits: list[RetrievalHit] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    coverage: RetrievalCoverage | None = None
    facets: RetrievalFacets | None = None
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
