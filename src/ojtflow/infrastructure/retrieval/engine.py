"""Deterministic retrieval utilities shared by retrieval adapters."""

from __future__ import annotations

import json
import math
import os
import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from typing import Any

from ojtflow.core.contracts.enums import EvidenceSourceType, TrustLevel
from ojtflow.core.contracts.evidence import Evidence
from ojtflow.core.contracts.retrieval import (
    RetrievalCoverage,
    RetrievalCoverageItem,
    RetrievalDiversitySelection,
    RetrievalDiversitySummary,
    RetrievalEvidenceSupportMatrix,
    RetrievalEvidenceSupportRow,
    RetrievalEvidenceBucket,
    RetrievalFacetBucket,
    RetrievalFacets,
    RetrievalHit,
    RetrievalInterpretation,
    RetrievalPackage,
    RetrievalQualitySignal,
    RetrievalQualitySummary,
    RetrievalQuery,
    RetrievalQueryAnalysis,
    RetrievalQueryAspect,
    RetrievalRecommendedAction,
    RetrievalRecommendedActionSummary,
    RetrievalScoreComponent,
    RetrievalStandardSearchPlan,
    RetrievalStandardSearchStep,
    RetrievalSource,
    RetrievalSnippet,
    RetrievalStrategyRecommendation,
    RetrievalTrace,
)
from ojtflow.core.policy.risk_rules import contains_prompt_injection, looks_sensitive_field
from ojtflow.infrastructure.retrieval.query_analysis import analyze_query

TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9_./%-]*", re.IGNORECASE)
SNIPPET_SEGMENT_PATTERN = re.compile(r"(?<=[.!?])\s+|\n{2,}|\r\n{2,}")
DEFAULT_EMBEDDING_DIMENSIONS = 64
RRF_K = 60
SNIPPET_MAX_CHARS = 280
DEFAULT_RANKING_BOOST_RULE_REGISTRY = (
    Path(__file__).resolve().parents[4] / "knowledge" / "retrieval" / "ranking_boost_rules.json"
)
DEFAULT_QUALITY_GATE_POLICY_REGISTRY = (
    Path(__file__).resolve().parents[4] / "knowledge" / "retrieval" / "quality_gate_policy.json"
)
DEFAULT_EVIDENCE_BUCKET_RULE_REGISTRY = (
    Path(__file__).resolve().parents[4] / "knowledge" / "retrieval" / "evidence_bucket_rules.json"
)
DEFAULT_CORRECTIVE_ACTION_RULE_REGISTRY = (
    Path(__file__).resolve().parents[4]
    / "knowledge"
    / "retrieval"
    / "corrective_action_rules.json"
)
DEFAULT_STRATEGY_RECOMMENDATION_RULE_REGISTRY = (
    Path(__file__).resolve().parents[4]
    / "knowledge"
    / "retrieval"
    / "strategy_recommendation_rules.json"
)
DEFAULT_STANDARD_SEARCH_PLAYBOOK_RULE_REGISTRY = (
    Path(__file__).resolve().parents[4]
    / "knowledge"
    / "retrieval"
    / "standard_search_playbook_rules.json"
)


@dataclass(frozen=True)
class KnowledgeChunk:
    """One retrievable knowledge segment."""

    chunk_id: str
    source_id: str
    source_type: EvidenceSourceType
    title: str
    content: str
    source_version: str = "1.0.0"
    trust_level: TrustLevel = TrustLevel.APPROVED
    clinical_domain: str | None = None
    standard_system: str | None = None
    locator: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RankingBoostCondition:
    """One allowlisted ranking-rule condition."""

    query_schema_id_in_source_id: bool = False
    any_query_fields_in_matched_terms: bool = False
    query_detected_format_present: bool = False
    filter_clinical_domain_matches_chunk: bool = False
    chunk_trust_levels: tuple[str, ...] = ()
    chunk_source_types: tuple[str, ...] = ()
    chunk_clinical_domains: tuple[str, ...] = ()
    chunk_standard_systems: tuple[str, ...] = ()
    any_matched_terms: tuple[str, ...] = ()
    any_concepts: tuple[str, ...] = ()
    any_rule_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class RankingBoostRule:
    """One auditable deterministic ranking boost rule."""

    rule_id: str
    weight: float
    reason: str
    match: RankingBoostCondition
    any_of: tuple[RankingBoostCondition, ...] = ()


@dataclass(frozen=True)
class AppliedRankingBoost:
    """One ranking boost applied to a specific hit."""

    rule_id: str
    weight: float
    reason: str

    def as_locator_payload(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "weight": self.weight,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class EvidenceBucketMatchRule:
    """Data-driven matcher for one evidence bucket."""

    source_types: tuple[str, ...] = ()
    source_id_contains: tuple[str, ...] = ()
    standard_systems: tuple[str, ...] = ()
    locator_any_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvidenceBucketRule:
    """One data-driven evidence pack bucket definition."""

    bucket_id: str
    label: str
    description: str
    required: bool
    suggested_filter: dict[str, str]
    match: EvidenceBucketMatchRule


@dataclass(frozen=True)
class CorrectiveActionRule:
    """One data-driven corrective retrieval action rule."""

    rule_id: str
    signal_code: str
    source: str
    priority: int
    action_type: str
    title: str | None = None
    description: str | None = None
    title_template: str | None = None
    title_prefix: str | None = None
    fallback_title: str | None = None
    title_from_signal: str | None = None
    description_from_signal: str | None = None
    fallback_action_type: str | None = None
    fallback_description: str | None = None
    metadata_list_path: str | None = None
    suggested_filter_path: str | None = None
    suggested_filter_from_metadata: dict[str, str] = field(default_factory=dict)
    metadata_keys: tuple[str, ...] = ()
    match_severities: tuple[str, ...] = ()


@dataclass(frozen=True)
class StrategyRecommendationMatch:
    """Data-driven matcher for route/quality-aware retrieval strategy notes."""

    any_profile_ids: tuple[str, ...] = ()
    any_retrieval_modes: tuple[str, ...] = ()
    any_quality_signal_codes: tuple[str, ...] = ()
    any_safety_flags: tuple[str, ...] = ()
    missing_required_bucket: bool | None = None
    reranker_enabled: bool | None = None


@dataclass(frozen=True)
class StrategyRecommendationRule:
    """One operator-facing retrieval strategy recommendation rule."""

    rule_id: str
    title: str
    technique: str
    status: str
    rationale: str
    priority: int
    suggested_filters: dict[str, str]
    match: StrategyRecommendationMatch


@dataclass(frozen=True)
class StandardSearchPlaybookMatch:
    """Matcher for one healthcare-standard search playbook step."""

    any_profile_ids: tuple[str, ...] = ()
    any_concepts: tuple[str, ...] = ()
    any_standards: tuple[str, ...] = ()
    any_query_aspects: tuple[str, ...] = ()
    any_fields: tuple[str, ...] = ()
    any_tokens: tuple[str, ...] = ()
    any_resource_types: tuple[str, ...] = ()
    any_quality_signal_codes: tuple[str, ...] = ()
    any_safety_flags: tuple[str, ...] = ()
    any_filters: dict[str, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class StandardSearchPlaybookRule:
    """One data-driven healthcare-standard search playbook rule."""

    rule_id: str
    label: str
    standard_system: str
    route_type: str
    query_template: str
    rationale: str
    priority: int
    suggested_filters: dict[str, str]
    governance_notes: tuple[str, ...]
    metadata: dict[str, Any]
    match: StandardSearchPlaybookMatch


@dataclass(frozen=True)
class RetrievalQualityPolicy:
    """Data-driven policy for package-level retrieval readiness scoring."""

    version: str
    severity_penalties: dict[str, int]
    blocking_severities: tuple[str, ...]
    review_severities: tuple[str, ...]
    review_score_below: int
    default_top_action: str
    ranking_thresholds: dict[str, int | float] = field(default_factory=dict)
    provenance_requirements: dict[str, Any] = field(default_factory=dict)
    concept_grounding_requirements: dict[str, Any] = field(default_factory=dict)
    evidence_bucket_requirements: dict[str, Any] = field(default_factory=dict)

    def penalty_for(self, severity: str) -> int:
        return self.severity_penalties.get(severity, 0)

    def metadata(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "severity_penalties": dict(self.severity_penalties),
            "blocking_severities": list(self.blocking_severities),
            "review_severities": list(self.review_severities),
            "review_score_below": self.review_score_below,
            "ranking_thresholds": dict(self.ranking_thresholds),
            "provenance_requirements": dict(self.provenance_requirements),
            "concept_grounding_requirements": dict(self.concept_grounding_requirements),
            "evidence_bucket_requirements": dict(self.evidence_bucket_requirements),
        }


class DeterministicEmbeddingProvider:
    """Stable local embedding provider for tests, demos, and lexical fallback.

    This is not a semantic model. It gives the retrieval pipeline a deterministic
    vector signal so fusion, tracing, and provider boundaries can be tested
    without external credentials.
    """

    def __init__(self, dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS) -> None:
        self.dimensions = dimensions
        self.provider_name = "deterministic"
        self.model = "deterministic-hash-v0"

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in tokenize(text):
            digest = sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:2], "big") % self.dimensions
            weight = 1.0 + (digest[2] / 255.0)
            vector[index] += weight
        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            return vector
        return [value / magnitude for value in vector]

    def embed_query(self, text: str) -> list[float]:
        return self.embed(text)

    def embed_document(self, text: str) -> list[float]:
        return self.embed(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_document(text) for text in texts]

    def metadata(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model": self.model,
            "dimensions": self.dimensions,
            "normalized": True,
        }


class NullEmbeddingProvider:
    """Embedding provider used when vector retrieval is disabled."""

    dimensions = DEFAULT_EMBEDDING_DIMENSIONS
    provider_name = "none"
    model = "none"

    def embed(self, text: str) -> list[float]:
        return [0.0] * self.dimensions

    def embed_query(self, text: str) -> list[float]:
        return self.embed(text)

    def embed_document(self, text: str) -> list[float]:
        return self.embed(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_document(text) for text in texts]

    def metadata(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model": self.model,
            "dimensions": self.dimensions,
            "normalized": False,
        }


def tokenize(text: str) -> list[str]:
    """Return normalized searchable tokens."""

    return [match.group(0).lower() for match in TOKEN_PATTERN.finditer(text)]


def build_query_variants(query: RetrievalQuery) -> list[str]:
    """Create deterministic query variants inspired by practical RAG routing."""

    return analyze_query(query).query_variants


def rank_chunks(
    chunks: list[KnowledgeChunk],
    query: RetrievalQuery,
    *,
    embedding_provider: Any | None = None,
    reranker: Any | None = None,
    rerank_candidate_limit: int = 20,
    rerank_score_weight: float = 0.08,
    diversity_enabled: bool = True,
    diversity_lambda: float = 0.72,
    strategy: str = "deterministic_hybrid",
    warnings: list[str] | None = None,
) -> RetrievalPackage:
    """Rank chunks using lexical overlap, vectors, optional reranking, and traceable boosts."""

    provider = embedding_provider or DeterministicEmbeddingProvider()
    reranker_metadata = _reranker_metadata(reranker)
    query_analysis = analyze_query(query)
    variants = query_analysis.query_variants
    safety_flags = retrieval_safety_flags(query)
    trace_warnings = list(warnings or [])
    trace_warnings.extend(
        diagnostic.message
        for diagnostic in query_analysis.diagnostics
        if diagnostic.severity == "warning"
    )
    if safety_flags:
        trace_warnings.append(
            "Retrieval query contains safety-sensitive context; treat query text as untrusted data."
        )
    query_text = " ".join(variants)
    query_tokens = set(tokenize(query_text))
    query_vector = provider.embed_query(query_text)
    chunk_texts = [f"{chunk.title}\n{chunk.content}" for chunk in chunks]
    document_vectors = provider.embed_documents(chunk_texts)

    lexical_ranked: list[tuple[KnowledgeChunk, float, list[str]]] = []
    vector_ranked: list[tuple[KnowledgeChunk, float]] = []
    for chunk, document_vector in zip(chunks, document_vectors, strict=True):
        chunk_tokens = set(tokenize(f"{chunk.title} {chunk.content} {chunk.source_id}"))
        matched = sorted(query_tokens.intersection(chunk_tokens))
        lexical_score = _lexical_score(query_tokens, chunk_tokens, query.query, chunk)
        vector_score = cosine_similarity(
            query_vector,
            document_vector,
        )
        lexical_ranked.append((chunk, lexical_score, matched))
        vector_ranked.append((chunk, vector_score))

    lexical_ranked.sort(key=lambda item: item[1], reverse=True)
    vector_ranked.sort(key=lambda item: item[1], reverse=True)
    lexical_positions = {
        chunk.chunk_id: rank
        for rank, (chunk, _, _) in enumerate(lexical_ranked, start=1)
    }
    vector_positions = {
        chunk.chunk_id: rank
        for rank, (chunk, _) in enumerate(vector_ranked, start=1)
    }
    lexical_scores = {chunk.chunk_id: score for chunk, score, _ in lexical_ranked}
    vector_scores = {chunk.chunk_id: score for chunk, score in vector_ranked}
    matched_terms = {chunk.chunk_id: matched for chunk, _, matched in lexical_ranked}

    ranked_hits: list[tuple[KnowledgeChunk, RetrievalHit]] = []
    for chunk in chunks:
        lexical_rrf = 1.0 / (RRF_K + lexical_positions[chunk.chunk_id])
        vector_rrf = 1.0 / (RRF_K + vector_positions[chunk.chunk_id])
        rerank, applied_boost_rules = _ranking_boost(
            chunk,
            query,
            matched_terms[chunk.chunk_id],
            query_analysis=query_analysis,
        )
        score = lexical_rrf + vector_rrf + rerank
        evidence = evidence_from_chunk(chunk, confidence=min(0.99, 0.55 + score * 8))
        score_components = _score_components(
            lexical_rrf=lexical_rrf,
            vector_rrf=vector_rrf,
            policy_boost=rerank,
            lexical_rank=lexical_positions[chunk.chunk_id],
            vector_rank=vector_positions[chunk.chunk_id],
            lexical_score=lexical_scores[chunk.chunk_id],
            vector_score=vector_scores[chunk.chunk_id],
            applied_boost_rules=applied_boost_rules,
        )
        ranked_hits.append(
            (
                chunk,
                RetrievalHit(
                    evidence=evidence,
                    score=round(score, 6),
                    lexical_score=round(lexical_scores[chunk.chunk_id], 6),
                    vector_score=round(vector_scores[chunk.chunk_id], 6),
                    rerank_score=round(rerank, 6),
                    score_components=score_components,
                    matched_terms=matched_terms[chunk.chunk_id][:12],
                    source_locator=hit_source_locator_from_chunk(
                        chunk,
                        applied_boost_rules=applied_boost_rules,
                        matched_terms=matched_terms[chunk.chunk_id],
                        query_analysis=query_analysis,
                    ),
                    snippet=snippet_from_chunk(
                        chunk,
                        query_tokens=query_tokens,
                        matched_terms=matched_terms[chunk.chunk_id],
                    ),
                ),
            )
        )

    ranked_hits.sort(key=lambda item: item[1].score, reverse=True)
    if _reranker_enabled(reranker) and ranked_hits:
        candidates = ranked_hits[: max(1, rerank_candidate_limit)]
        external_scores = reranker.score(query_text, [chunk for chunk, _ in candidates])
        if external_scores:
            for chunk, hit in candidates:
                external_score = external_scores.get(chunk.chunk_id, 0.0)
                contribution = external_score * rerank_score_weight
                hit.score = round(hit.score + contribution, 6)
                hit.rerank_score = round(hit.rerank_score + contribution, 6)
                hit.score_components = [
                    *hit.score_components,
                    _external_rerank_score_component(
                        external_score=external_score,
                        contribution=contribution,
                        score_weight=rerank_score_weight,
                    ),
                ]
                hit.evidence.confidence = round(min(0.99, 0.55 + hit.score * 8), 4)
            ranked_hits.sort(key=lambda item: item[1].score, reverse=True)

    selected_ranked_hits, diversity_metadata = _select_diverse_hits(
        ranked_hits,
        top_k=query.top_k,
        enabled=diversity_enabled,
        lambda_mult=diversity_lambda,
    )
    diversity_summary = diversity_summary_from_metadata(diversity_metadata)
    top_hits = [hit for _, hit in selected_ranked_hits]
    selected_chunks = [chunk for chunk, _ in selected_ranked_hits]
    fusion_diagnostics = fusion_diagnostics_from_rankings(
        lexical_positions=lexical_positions,
        vector_positions=vector_positions,
        top_hits=top_hits,
        top_k=query.top_k,
    )
    facets = facets_from_chunks(selected_chunks)
    coverage = coverage_from_chunks(selected_chunks, query_analysis)
    trace_warnings.extend(coverage.warnings)
    if diversity_metadata["duplicate_selected_source_count"]:
        trace_warnings.append(
            "Retrieval results include repeated source IDs after diversity selection."
        )
    trace = RetrievalTrace(
        strategy=strategy,
        query_variants=variants,
        query_variant_details=query_analysis.query_variant_details,
        fusion_diagnostics=fusion_diagnostics,
        filters_applied=query.filters,
        candidates_seen=len(chunks),
        final_hit_ids=[hit.evidence.evidence_id for hit in top_hits],
        safety_flags=safety_flags,
        warnings=trace_warnings,
    )
    quality_policy = active_quality_policy()
    evidence_buckets = evidence_buckets_from_hits(top_hits)
    attach_hit_match_explanations(top_hits, evidence_buckets)
    quality_signals = quality_signals_from_results(
        hits=top_hits,
        evidence_buckets=evidence_buckets,
        coverage=coverage,
        safety_flags=safety_flags,
        candidates_seen=len(chunks),
        diversity_metadata=diversity_metadata,
        policy=quality_policy,
        query_analysis=query_analysis,
    )
    quality_summary = quality_summary_from_signals(quality_signals, policy=quality_policy)
    recommended_actions = recommended_actions_from_context(
        quality_signals=quality_signals,
        query_analysis=query_analysis,
    )
    recommended_action_summary = recommended_action_summary_from_actions(recommended_actions)
    remediation_summary = remediation_summary_from_package_parts(
        hit_count=len(top_hits),
        quality_summary=quality_summary,
        recommended_action_summary=recommended_action_summary,
        trace_warning_count=len(trace_warnings),
    )
    interpretation = interpretation_from_package_parts(
        hits=top_hits,
        evidence_buckets=evidence_buckets,
        quality_summary=quality_summary,
        recommended_actions=recommended_actions,
        trace_warning_count=len(trace_warnings),
        remediation_summary=remediation_summary,
    )
    support_matrix = evidence_support_matrix_from_hits(top_hits, query)
    strategy_recommendations = strategy_recommendations_from_context(
        query_analysis=query_analysis,
        quality_signals=quality_signals,
        evidence_buckets=evidence_buckets,
        safety_flags=safety_flags,
        reranker_enabled=_reranker_enabled(reranker),
    )
    standard_search_plan = standard_search_plan_from_context(
        query=query,
        query_analysis=query_analysis,
        quality_signals=quality_signals,
        safety_flags=safety_flags,
        strategy_recommendations=strategy_recommendations,
    )
    return RetrievalPackage(
        hits=top_hits,
        evidence=[hit.evidence for hit in top_hits],
        evidence_buckets=evidence_buckets,
        coverage=coverage,
        facets=facets,
        quality_signals=quality_signals,
        quality_summary=quality_summary,
        recommended_actions=recommended_actions,
        recommended_action_summary=recommended_action_summary,
        remediation_summary=remediation_summary,
        interpretation=interpretation,
        support_matrix=support_matrix,
        strategy_recommendations=strategy_recommendations,
        standard_search_plan=standard_search_plan,
        diversity=diversity_summary,
        trace=trace,
        handoff_context={
            "retrieval_contract": "retrieval_package.v0",
            "query_fields": query.fields,
            "schema_id": query.schema_id,
            "strategy": strategy,
            "safety_flags": safety_flags,
            "embedding": provider.metadata(),
            "reranker": reranker_metadata,
            "fusion_diagnostics": fusion_diagnostics,
            "diversity": diversity_metadata,
            "quality_policy": quality_policy.metadata(),
            "quality_summary": quality_summary.model_dump(),
            "recommended_actions": [
                action.model_dump(mode="json") for action in recommended_actions
            ],
            "recommended_action_summary": recommended_action_summary.model_dump(mode="json"),
            "remediation_summary": remediation_summary,
            "interpretation": interpretation.model_dump(mode="json"),
            "support_matrix": support_matrix.model_dump(mode="json"),
            "strategy_recommendations": [
                recommendation.model_dump(mode="json")
                for recommendation in strategy_recommendations
            ],
            "standard_search_plan": (
                standard_search_plan.model_dump(mode="json")
                if standard_search_plan
                else None
            ),
            "query_analysis": query_analysis.model_dump(),
        },
    )


def evidence_buckets_from_hits(hits: list[RetrievalHit]) -> list[RetrievalEvidenceBucket]:
    """Group selected evidence into clinical workflow audit buckets."""

    bucket_rules = active_evidence_bucket_rules()
    bucket_hits: dict[str, list[RetrievalHit]] = {
        rule.bucket_id: [] for rule in bucket_rules
    }
    for hit in hits:
        for bucket_id in _bucket_ids_for_hit(hit, bucket_rules):
            bucket_hits[bucket_id].append(hit)

    buckets: list[RetrievalEvidenceBucket] = []
    for rule in bucket_rules:
        selected_hits = _unique_hits(bucket_hits.get(rule.bucket_id, []))
        warnings = []
        if rule.required and not selected_hits:
            warnings.append(f"missing_{rule.bucket_id}_evidence")
        buckets.append(
            RetrievalEvidenceBucket(
                bucket_id=rule.bucket_id,
                label=rule.label,
                description=rule.description,
                evidence_ids=[hit.evidence.evidence_id for hit in selected_hits],
                source_ids=_unique_strings(hit.evidence.source_id for hit in selected_hits),
                hit_count=len(selected_hits),
                required=rule.required,
                status="available" if selected_hits else "missing",
                warnings=warnings,
                suggested_filter=rule.suggested_filter,
            )
        )
    return buckets


def attach_hit_match_explanations(
    hits: list[RetrievalHit],
    evidence_buckets: list[RetrievalEvidenceBucket],
) -> None:
    """Attach stable per-hit match explanations for UI and audit exports."""

    buckets_by_evidence_id: dict[str, list[RetrievalEvidenceBucket]] = {}
    for bucket in evidence_buckets:
        for evidence_id in bucket.evidence_ids:
            buckets_by_evidence_id.setdefault(evidence_id, []).append(bucket)
    for hit in hits:
        matched_buckets = buckets_by_evidence_id.get(hit.evidence.evidence_id, [])
        hit.match_explanation = hit_match_explanation(hit, matched_buckets)


def evidence_support_matrix_from_hits(
    hits: list[RetrievalHit],
    query: RetrievalQuery,
) -> RetrievalEvidenceSupportMatrix:
    """Build claim-to-evidence support rows for assistant and MCP synthesis."""

    rows = [
        _evidence_support_row_from_hit(hit, index=index)
        for index, hit in enumerate(hits, start=1)
    ]
    status_counts = Counter(row.support_status for row in rows)
    warnings: list[str] = []
    if not rows:
        warnings.append("no_ranked_evidence")
    if any(row.support_status in {"weak", "unsupported"} for row in rows):
        warnings.append("weak_evidence_support_present")
    return RetrievalEvidenceSupportMatrix(
        query_claim=query.query,
        row_count=len(rows),
        strong_count=status_counts.get("strong", 0),
        partial_count=status_counts.get("partial", 0),
        weak_count=status_counts.get("weak", 0),
        unsupported_count=status_counts.get("unsupported", 0),
        rows=rows,
        warnings=warnings,
    )


def _evidence_support_row_from_hit(
    hit: RetrievalHit,
    *,
    index: int,
) -> RetrievalEvidenceSupportRow:
    explanation = hit.match_explanation if isinstance(hit.match_explanation, dict) else {}
    support_status = _support_status_from_hit(hit) or "weak"
    warnings = _support_row_warnings(hit, explanation)
    return RetrievalEvidenceSupportRow(
        claim_id=f"claim:{index}",
        claim=hit.evidence.claim,
        support_status=_support_status_value(support_status),
        evidence_id=hit.evidence.evidence_id,
        source_id=hit.evidence.source_id,
        source_type=hit.evidence.source_type,
        source_version=hit.evidence.source_version,
        source_locator=_support_source_locator(hit),
        matched_terms=_unique_strings(hit.matched_terms)[:12],
        score=hit.score,
        confidence=hit.evidence.confidence,
        reasoning=_support_row_reasoning(hit, explanation, warnings),
        warnings=warnings,
        metadata={
            "rank": index,
            "bucket_ids": _nonblank_strings(explanation.get("bucket_ids"), limit=8),
            "bucket_labels": _nonblank_strings(explanation.get("bucket_labels"), limit=8),
            "concept_labels": _nonblank_strings(explanation.get("concept_labels"), limit=8),
            "aspect_labels": _nonblank_strings(explanation.get("aspect_labels"), limit=8),
            "top_score_driver": _top_score_driver(explanation),
        },
    )


def _support_source_locator(hit: RetrievalHit) -> dict[str, Any]:
    locator = dict(hit.evidence.locator)
    locator.update(hit.source_locator)
    return locator


def _support_status_value(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"strong", "partial", "weak", "unsupported"}:
        return normalized
    return "weak"


def _support_row_warnings(
    hit: RetrievalHit,
    explanation: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []
    if not hit.matched_terms:
        warnings.append("no_exact_matched_terms")
    if int(explanation.get("provenance_count") or 0) == 0:
        warnings.append("thin_source_provenance")
    if hit.evidence.confidence is not None and hit.evidence.confidence < 0.7:
        warnings.append("low_confidence_evidence")
    if _support_status_from_hit(hit) in {"weak", "unsupported"}:
        warnings.append("manual_evidence_review_recommended")
    return _unique_strings(warnings)


def _support_row_reasoning(
    hit: RetrievalHit,
    explanation: dict[str, Any],
    warnings: list[str],
) -> str:
    pieces: list[str] = []
    top_score_driver = _top_score_driver(explanation)
    if top_score_driver:
        pieces.append(f"Ranked by {top_score_driver}.")
    if hit.matched_terms:
        pieces.append(
            "Matched query terms: " + ", ".join(_unique_strings(hit.matched_terms)[:6]) + "."
        )
    bucket_labels = _nonblank_strings(explanation.get("bucket_labels"), limit=4)
    if bucket_labels:
        pieces.append("Evidence bucket coverage: " + ", ".join(bucket_labels) + ".")
    if warnings:
        pieces.append("Review warning(s): " + ", ".join(warnings) + ".")
    return " ".join(pieces) or "Selected as ranked evidence; inspect source locator before use."


def hit_match_explanation(
    hit: RetrievalHit,
    evidence_buckets: list[RetrievalEvidenceBucket],
) -> dict[str, Any]:
    """Build a deterministic explanation for why one hit was selected."""

    concept_matches = _locator_concept_matches(hit.source_locator)
    aspect_matches = _locator_query_aspect_matches(hit.source_locator)
    ranking_rule_ids = _ranking_signal_rule_ids(hit.source_locator)
    top_component = _top_score_component(hit.score_components)
    provenance_fields = _provenance_field_labels(hit.evidence)
    return {
        "version": 1,
        "support_status": _hit_support_status(
            matched_terms=hit.matched_terms,
            provenance_fields=provenance_fields,
            concept_matches=concept_matches,
            aspect_matches=aspect_matches,
        ),
        "top_score_driver": (
            f"{top_component.label} {_signed_score(top_component.value)}"
            if top_component
            else None
        ),
        "top_score_component": (
            {
                "component": top_component.component,
                "label": top_component.label,
                "rank": top_component.rank,
                "value": top_component.value,
            }
            if top_component
            else None
        ),
        "matched_terms": _unique_strings(hit.matched_terms)[:6],
        "bucket_ids": _unique_strings([bucket.bucket_id for bucket in evidence_buckets])[:8],
        "bucket_labels": _unique_strings([bucket.label for bucket in evidence_buckets])[:4],
        "concept_ids": _unique_strings(
            [
                str(match.get("concept_id"))
                for match in concept_matches
                if match.get("concept_id")
            ]
        )[:8],
        "concept_labels": _unique_strings(
            [_concept_match_label(match) for match in concept_matches]
        )[:4],
        "aspect_ids": _unique_strings(
            [
                str(match.get("aspect_id"))
                for match in aspect_matches
                if match.get("aspect_id")
            ]
        )[:8],
        "aspect_labels": _unique_strings(
            [str(match.get("label")) for match in aspect_matches if match.get("label")]
        )[:4],
        "provenance_count": len(provenance_fields),
        "provenance_fields": provenance_fields[:12],
        "ranking_signal_count": len(ranking_rule_ids),
        "ranking_signal_rule_ids": ranking_rule_ids[:12],
    }


def _locator_query_aspect_matches(locator: dict[str, Any]) -> list[dict[str, Any]]:
    matches = locator.get("query_aspect_matches")
    return [match for match in matches if isinstance(match, dict)] if isinstance(matches, list) else []


def _ranking_signal_rule_ids(locator: dict[str, Any]) -> list[str]:
    detailed = locator.get("ranking_boosts")
    if isinstance(detailed, list):
        detailed_ids = [
            str(item.get("rule_id"))
            for item in detailed
            if isinstance(item, dict) and item.get("rule_id")
        ]
        if detailed_ids:
            return _unique_strings(detailed_ids)
    raw_ids = locator.get("ranking_boost_rules")
    return _unique_strings([str(item) for item in raw_ids]) if isinstance(raw_ids, list) else []


def _top_score_component(
    components: list[RetrievalScoreComponent],
) -> RetrievalScoreComponent | None:
    if not components:
        return None
    return sorted(components, key=lambda component: abs(component.value), reverse=True)[0]


def _provenance_field_labels(evidence: Evidence) -> list[str]:
    labels: list[str] = []
    if evidence.source_version:
        labels.append("Version")
    locator_fields: tuple[tuple[str, str], ...] = (
        ("Standard", "standard"),
        ("System", "standard_system"),
        ("URL", "url"),
        ("Path", "path"),
        ("API", "api"),
        ("PMID", "pmid"),
        ("DOI", "doi"),
        ("Resource", "resource"),
        ("Table", "table"),
        ("Document", "document_id"),
        ("Chunk", "chunk_id"),
    )
    for label, key in locator_fields:
        value = evidence.locator.get(key)
        if value not in (None, "", [], {}):
            labels.append(label)
    return _unique_strings(labels)


def _hit_support_status(
    *,
    matched_terms: list[str],
    provenance_fields: list[str],
    concept_matches: list[dict[str, Any]],
    aspect_matches: list[dict[str, Any]],
) -> str:
    if matched_terms and provenance_fields and (concept_matches or aspect_matches):
        return "strong"
    if matched_terms or provenance_fields:
        return "partial"
    return "weak"


def _concept_match_label(match: dict[str, Any]) -> str:
    standard_system = match.get("standard_system")
    code = match.get("code")
    display_name = match.get("display_name")
    if standard_system and code:
        return f"{standard_system} {code}"
    if display_name:
        return str(display_name)
    return str(match.get("concept_id") or "concept")


def _signed_score(value: float) -> str:
    if value > 0:
        return f"+{value:.3f}"
    return f"{value:.3f}"


def _unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _bucket_ids_for_hit(
    hit: RetrievalHit,
    bucket_rules: list[EvidenceBucketRule],
) -> list[str]:
    matched = [
        rule.bucket_id
        for rule in bucket_rules
        if rule.bucket_id != "other" and _evidence_bucket_rule_matches(hit, rule)
    ]
    return matched or ["other"]


def _evidence_bucket_rule_matches(hit: RetrievalHit, rule: EvidenceBucketRule) -> bool:
    evidence = hit.evidence
    locator = evidence.locator
    source_type = (
        evidence.source_type.value
        if hasattr(evidence.source_type, "value")
        else str(evidence.source_type)
    )
    source_id = evidence.source_id.lower()
    standard_system = str(locator.get("standard_system") or "").lower()
    match = rule.match

    if source_type in match.source_types:
        return True
    if any(fragment in source_id for fragment in match.source_id_contains):
        return True
    if standard_system in {value.lower() for value in match.standard_systems}:
        return True
    return any(key in locator for key in match.locator_any_keys)


def _unique_hits(hits: list[RetrievalHit]) -> list[RetrievalHit]:
    seen: set[str] = set()
    unique: list[RetrievalHit] = []
    for hit in hits:
        if hit.evidence.evidence_id in seen:
            continue
        seen.add(hit.evidence.evidence_id)
        unique.append(hit)
    return unique


def _unique_strings(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique


def coverage_from_chunks(
    chunks: list[KnowledgeChunk],
    query_analysis: RetrievalQueryAnalysis,
) -> RetrievalCoverage:
    """Report whether final hits cover standards inferred from the query."""

    standard_counts = Counter(chunk.standard_system for chunk in chunks if chunk.standard_system)
    standard_items = [
        _standard_coverage_item(standard, standard_counts)
        for standard in _expected_standard_values(query_analysis.standards)
    ]
    aspect_items = [
        item
        for aspect in query_analysis.query_aspects
        for item in [_query_aspect_coverage_item(aspect, chunks)]
        if item is not None
    ]
    warnings = [
        item.reason
        for item in [*standard_items, *aspect_items]
        if item.status == "missing" and item.severity == "warning"
    ]
    return RetrievalCoverage(
        standard_system=standard_items,
        query_aspects=aspect_items,
        warnings=warnings,
    )


def quality_signals_from_results(
    *,
    hits: list[RetrievalHit],
    evidence_buckets: list[RetrievalEvidenceBucket] | None = None,
    coverage: RetrievalCoverage | None,
    safety_flags: list[str],
    candidates_seen: int,
    diversity_metadata: dict[str, Any] | None = None,
    policy: RetrievalQualityPolicy | None = None,
    query_analysis: RetrievalQueryAnalysis | None = None,
) -> list[RetrievalQualitySignal]:
    """Build deterministic package-level retrieval quality signals."""

    active_policy = policy or active_quality_policy()
    evidence_ids = [hit.evidence.evidence_id for hit in hits]
    signals: list[RetrievalQualitySignal] = []
    bucket_gaps = _required_evidence_bucket_gaps(
        evidence_buckets or evidence_buckets_from_hits(hits),
        active_policy,
    )
    if hits:
        top_hit = hits[0]
        min_top_matched_terms = active_policy.ranking_thresholds.get(
            "min_top_matched_terms",
        )
        matched_term_count = len(top_hit.matched_terms)
        signals.append(
            RetrievalQualitySignal(
                code="hits_available",
                severity="success",
                message=(
                    f"Retrieved {len(hits)} evidence item(s) from "
                    f"{candidates_seen} candidate(s)."
                ),
                suggested_action=(
                    "Review the ranked evidence and score explanations before using it "
                    "downstream."
                ),
                evidence_ids=evidence_ids,
                metadata={"hit_count": len(hits), "candidate_count": candidates_seen},
            )
            )
        if bucket_gaps:
            signals.append(
                RetrievalQualitySignal(
                    code="missing_required_evidence_buckets",
                    severity="warning",
                    message=(
                        "Selected evidence is missing required clinical audit "
                        "bucket(s): "
                        f"{', '.join(str(gap['bucket_id']) for gap in bucket_gaps)}."
                    ),
                    suggested_action=(
                        "Retrieve or add the missing required evidence classes before "
                        "using the package for validation, explanations, or agent handoff."
                    ),
                    evidence_ids=evidence_ids,
                    metadata={
                        "missing_buckets": bucket_gaps,
                        "requirements": active_policy.evidence_bucket_requirements,
                    },
                )
            )
        if (
            isinstance(min_top_matched_terms, int)
            and min_top_matched_terms > 0
            and matched_term_count < min_top_matched_terms
        ):
            signals.append(
                RetrievalQualitySignal(
                    code="weak_top_hit_match",
                    severity="warning",
                    message=(
                        "Top-ranked evidence matched fewer exact query terms than the "
                        "active quality policy requires."
                    ),
                    suggested_action=(
                        "Rewrite or broaden the query, inspect score components, and "
                        "confirm the top evidence before downstream use."
                    ),
                    evidence_ids=[top_hit.evidence.evidence_id],
                    metadata={
                        "top_evidence_id": top_hit.evidence.evidence_id,
                        "matched_term_count": matched_term_count,
                        "min_top_matched_terms": min_top_matched_terms,
                        "score": top_hit.score,
                        "lexical_score": top_hit.lexical_score,
                        "vector_score": top_hit.vector_score,
                    },
                )
            )
        provenance_issues = _provenance_quality_issues(hits, active_policy)
        if provenance_issues:
            signals.append(
                RetrievalQualitySignal(
                    code="weak_evidence_provenance",
                    severity="warning",
                    message=(
                        "Selected evidence is missing provenance metadata required by "
                        "the active quality policy."
                    ),
                    suggested_action=(
                        "Reindex the source with version and locator metadata, or replace "
                        "the evidence with an auditable source before downstream use."
                    ),
                    evidence_ids=[
                        str(issue["evidence_id"])
                        for issue in provenance_issues
                        if issue.get("evidence_id")
                    ],
                    metadata={
                        "issue_count": len(provenance_issues),
                        "requirements": active_policy.provenance_requirements,
                        "issues": provenance_issues,
                    },
                )
            )
        concept_issues = _concept_grounding_issues(
            hits,
            active_policy,
            query_analysis=query_analysis,
        )
        if concept_issues:
            signals.append(
                RetrievalQualitySignal(
                    code="missing_concept_grounding",
                    severity="warning",
                    message=(
                        "Selected evidence does not ground every controlled medical "
                        "concept detected in the query."
                    ),
                    suggested_action=(
                        "Apply terminology or clinical-domain filters, broaden the query, "
                        "or add terminology-backed sources before downstream use."
                    ),
                    evidence_ids=evidence_ids,
                    metadata={
                        "issue_count": len(concept_issues),
                        "requirements": active_policy.concept_grounding_requirements,
                        "missing_concepts": concept_issues,
                    },
                )
            )
    else:
        signals.append(
            RetrievalQualitySignal(
                code="no_hits",
                severity="destructive",
                message="No retrieval evidence matched the current query and filters.",
                suggested_action=(
                    "Broaden the query, remove restrictive filters, or reindex trusted "
                    "knowledge."
                ),
                metadata={"candidate_count": candidates_seen},
            )
        )

    if coverage and coverage.standard_system:
        missing = [
            item
            for item in coverage.standard_system
            if item.status == "missing" and item.severity == "warning"
        ]
        if missing:
            signals.append(
                RetrievalQualitySignal(
                    code="missing_standard_coverage",
                    severity="warning",
                    message=(
                        "Selected evidence is missing expected standard grounding for "
                        f"{', '.join(item.value for item in missing)}."
                    ),
                    suggested_action="Apply the suggested standard filters or broaden the query.",
                    metadata={
                        "missing_standards": [item.value for item in missing],
                        "suggested_filters": [
                            item.suggested_filter
                            for item in missing
                            if item.suggested_filter
                        ],
                    },
                )
            )
        else:
            signals.append(
                RetrievalQualitySignal(
                    code="standard_coverage_complete",
                    severity="success",
                    message="Selected evidence covers every standard inferred from query analysis.",
                    suggested_action=(
                        "Keep the current standard coverage unless the clinical task "
                        "requires more sources."
                    ),
                    evidence_ids=evidence_ids,
                    metadata={
                        "covered_standards": [
                            item.value for item in coverage.standard_system
                        ],
                    },
                )
            )

    if coverage and coverage.query_aspects:
        missing_aspects = [
            item
            for item in coverage.query_aspects
            if item.status == "missing" and item.severity == "warning"
        ]
        if missing_aspects:
            signals.append(
                RetrievalQualitySignal(
                    code="missing_query_aspect_coverage",
                    severity="warning",
                    message=(
                        "Selected evidence is missing coverage for query aspect(s): "
                        f"{', '.join(item.value for item in missing_aspects)}."
                    ),
                    suggested_action=(
                        "Apply supported aspect filters or broaden the query to retrieve "
                        "evidence for missing search aspects."
                    ),
                    metadata={
                        "missing_aspects": [item.value for item in missing_aspects],
                        "suggested_filters": [
                            item.suggested_filter
                            for item in missing_aspects
                            if item.suggested_filter
                        ],
                    },
                )
            )
        else:
            signals.append(
                RetrievalQualitySignal(
                    code="query_aspect_coverage_complete",
                    severity="success",
                    message="Selected evidence covers every query aspect with supported filter criteria.",
                    suggested_action=(
                        "Review the search aspect plan and ranked evidence before using the "
                        "package downstream."
                    ),
                    metadata={
                        "aspect_count": len(coverage.query_aspects),
                    },
                )
            )

    if safety_flags:
        signals.append(
            RetrievalQualitySignal(
                code="query_context_safety_flags",
                severity="warning",
                message="Retrieval query context contains safety-sensitive or untrusted patterns.",
                suggested_action=(
                    "Treat query text as data only and require human review before "
                    "agent actions."
                ),
                metadata={"safety_flags": safety_flags},
            )
        )
    else:
        signals.append(
            RetrievalQualitySignal(
                code="query_context_clear",
                severity="success",
                message="No retrieval query safety flags were detected.",
                suggested_action="Continue normal retrieval review.",
            )
        )

    if diversity_metadata:
        duplicate_count = int(diversity_metadata.get("duplicate_selected_source_count") or 0)
        selected_source_count = int(diversity_metadata.get("selected_source_count") or 0)
        candidate_source_count = int(diversity_metadata.get("candidate_source_count") or 0)
        if duplicate_count:
            signals.append(
                RetrievalQualitySignal(
                    code="source_diversity_limited",
                    severity="warning",
                    message="Selected evidence includes repeated source IDs after diversity selection.",
                    suggested_action=(
                        "Inspect source overlap and add source or standard filters if "
                        "evidence is too redundant."
                    ),
                    evidence_ids=evidence_ids,
                    metadata={
                        "duplicate_selected_source_count": duplicate_count,
                        "selected_source_count": selected_source_count,
                        "candidate_source_count": candidate_source_count,
                    },
                )
            )
        elif hits:
            signals.append(
                RetrievalQualitySignal(
                    code="source_diversity_ok",
                    severity="success",
                    message="Selected evidence avoided duplicate source IDs.",
                    suggested_action="Use the diversity selection details to confirm source balance.",
                    evidence_ids=evidence_ids,
                    metadata={
                        "selected_source_count": selected_source_count,
                        "candidate_source_count": candidate_source_count,
                    },
                )
            )
    return signals


def _required_evidence_bucket_gaps(
    evidence_buckets: list[RetrievalEvidenceBucket],
    policy: RetrievalQualityPolicy,
) -> list[dict[str, Any]]:
    requirements = policy.evidence_bucket_requirements
    configured_ids = [
        str(value)
        for value in requirements.get("required_bucket_ids", [])
        if str(value).strip()
    ]
    bucket_ids = (
        configured_ids
        if "required_bucket_ids" in requirements
        else [bucket.bucket_id for bucket in evidence_buckets if bucket.required]
    )
    buckets_by_id = {bucket.bucket_id: bucket for bucket in evidence_buckets}
    gaps: list[dict[str, Any]] = []
    for bucket_id in bucket_ids:
        bucket = buckets_by_id.get(bucket_id)
        if bucket and bucket.hit_count > 0:
            continue
        gaps.append(
            {
                "bucket_id": bucket_id,
                "label": bucket.label if bucket else bucket_id,
                "required": True,
                "status": bucket.status if bucket else "missing",
                "warnings": list(bucket.warnings) if bucket else [],
                "suggested_filter": dict(bucket.suggested_filter) if bucket else {},
            }
        )
    return gaps


def quality_summary_from_signals(
    signals: list[RetrievalQualitySignal],
    *,
    policy: RetrievalQualityPolicy | None = None,
) -> RetrievalQualitySummary:
    """Summarize package quality signals into an operator-readiness score."""

    active_policy = policy or active_quality_policy()
    success_count = sum(
        1
        for signal in signals
        if active_policy.penalty_for(signal.severity) == 0 and signal.severity == "success"
    )
    warning_signals = [
        signal for signal in signals if signal.severity in active_policy.review_severities
    ]
    destructive_signals = [
        signal
        for signal in signals
        if signal.severity in active_policy.blocking_severities
    ]
    info_count = sum(1 for signal in signals if signal.severity == "info")
    score = max(
        0,
        min(
            100,
            100 - sum(active_policy.penalty_for(signal.severity) for signal in signals),
        ),
    )
    status = "ready"
    if destructive_signals:
        status = "blocked"
    elif warning_signals or score < active_policy.review_score_below:
        status = "review"
    top_signal = (
        destructive_signals[0]
        if destructive_signals
        else warning_signals[0]
        if warning_signals
        else signals[0]
        if signals
        else None
    )
    return RetrievalQualitySummary(
        status=status,
        score=score,
        success_count=success_count,
        warning_count=len(warning_signals),
        destructive_count=len(destructive_signals),
        info_count=info_count,
        top_action=(
            top_signal.suggested_action
            if top_signal
            else active_policy.default_top_action
        ),
        blocker_codes=[signal.code for signal in destructive_signals],
        warning_codes=[signal.code for signal in warning_signals],
    )


def recommended_actions_from_signals(
    signals: list[RetrievalQualitySignal],
) -> list[RetrievalRecommendedAction]:
    """Derive concrete corrective retrieval actions from quality signals."""

    return _recommended_actions_from_signals(
        signals,
        source="quality_signal",
    )


def recommended_actions_from_context(
    *,
    quality_signals: list[RetrievalQualitySignal],
    query_analysis: RetrievalQueryAnalysis,
) -> list[RetrievalRecommendedAction]:
    """Derive corrective actions from retrieval quality and query diagnostics."""

    actions = recommended_actions_from_signals(quality_signals)
    diagnostic_signals = [
        RetrievalQualitySignal(
            code=diagnostic.code,
            severity=diagnostic.severity,
            message=diagnostic.message,
            suggested_action=diagnostic.suggested_action,
            metadata={
                **diagnostic.metadata,
                "source": "query_diagnostic",
            },
        )
        for diagnostic in query_analysis.diagnostics
        if diagnostic.severity != "info"
    ]
    actions.extend(
        _recommended_actions_from_signals(
            diagnostic_signals,
            source="query_diagnostic",
        )
    )
    return _unique_recommended_actions(actions)


def _recommended_actions_from_signals(
    signals: list[RetrievalQualitySignal],
    *,
    source: str,
) -> list[RetrievalRecommendedAction]:
    rules = active_corrective_action_rules()
    actions: list[RetrievalRecommendedAction] = []
    for signal in signals:
        if signal.severity == "success":
            continue
        for rule in rules:
            if rule.source != source:
                continue
            if not _corrective_action_rule_matches(signal, rule):
                continue
            actions.extend(_actions_from_corrective_rule(signal, rule))
    return _unique_recommended_actions(actions)


def recommended_action_summary_from_actions(
    actions: list[RetrievalRecommendedAction],
) -> RetrievalRecommendedActionSummary:
    """Summarize corrective retrieval actions for API and UI triage."""

    top_action = actions[0] if actions else None
    action_type_counts = Counter(action.action_type for action in actions)
    return RetrievalRecommendedActionSummary(
        count=len(actions),
        highest_priority=top_action.priority if top_action else None,
        highest_severity=top_action.severity if top_action else None,
        top_action_title=top_action.title if top_action else None,
        apply_filter_count=action_type_counts.get("apply_filter", 0),
        broaden_query_count=action_type_counts.get("broaden_query", 0),
        action_type_counts=dict(sorted(action_type_counts.items())),
    )


def remediation_summary_from_package_parts(
    *,
    hit_count: int,
    quality_summary: RetrievalQualitySummary | None,
    recommended_action_summary: RetrievalRecommendedActionSummary | None,
    trace_warning_count: int,
) -> str | None:
    """Build the operator-facing next step for package triage and audit exports."""

    if recommended_action_summary and recommended_action_summary.count > 0:
        action_types = ", ".join(
            f"{_humanize(action_type)} {count}"
            for action_type, count in sorted(
                recommended_action_summary.action_type_counts.items(),
                key=lambda item: (-item[1], item[0]),
            )[:3]
            if count > 0
        )
        priority = (
            f"P{recommended_action_summary.highest_priority}"
            if recommended_action_summary.highest_priority
            else "priority unreported"
        )
        top_action = (
            recommended_action_summary.top_action_title
            or "Inspect backend corrective actions"
        )
        return (
            f"{top_action} ({priority}; {action_types})"
            if action_types
            else f"{top_action} ({priority})"
        )
    if quality_summary and quality_summary.top_action:
        return quality_summary.top_action
    warning_count = (quality_summary.warning_count if quality_summary else 0) + trace_warning_count
    if warning_count > 0:
        return f"Inspect {_format_count(warning_count, 'warning')} before using this evidence"
    if hit_count == 0:
        return "Broaden search scope or inspect source inventory"
    return None


def interpretation_from_package_parts(
    *,
    hits: list[RetrievalHit],
    evidence_buckets: list[RetrievalEvidenceBucket],
    quality_summary: RetrievalQualitySummary | None,
    recommended_actions: list[RetrievalRecommendedAction],
    trace_warning_count: int,
    remediation_summary: str | None,
) -> RetrievalInterpretation:
    """Build a reusable package-level interpretation for UI, assistant, and MCP clients."""

    top_hit = hits[0] if hits else None
    required_buckets = [bucket for bucket in evidence_buckets if bucket.required]
    missing_required_buckets = [bucket for bucket in required_buckets if bucket.hit_count <= 0]
    primary_action = min(recommended_actions, key=lambda action: action.priority, default=None)
    quality_warning_count = quality_summary.warning_count if quality_summary else 0
    warning_count = quality_warning_count + trace_warning_count
    next_action_title = primary_action.title if primary_action else None
    next_action_detail = primary_action.description if primary_action else remediation_summary

    if top_hit is None:
        status = "no_ranked_evidence"
        summary = (
            "No ranked evidence was returned. Review filters, source inventory, and "
            "backend warnings before treating this as evidence absence."
        )
    elif missing_required_buckets:
        status = "support_gaps"
        summary = (
            f"The top result is {top_hit.evidence.source_id}, but required evidence "
            f"support is missing for {_join_labels(bucket.label for bucket in missing_required_buckets)}."
        )
    elif warning_count > 0:
        status = "review_warnings"
        summary = (
            f"The package returned {_format_count(len(hits), 'ranked hit')}; "
            "warnings indicate the search should be reviewed before trusting result order."
        )
    else:
        status = "ready_to_review"
        summary = (
            f"The top result is {top_hit.evidence.source_id}. It has "
            f"{_support_status_from_hit(top_hit)} operational support from retrieval trace signals."
        )

    match_explanation = _match_explanation(top_hit)
    return RetrievalInterpretation(
        status=status,
        summary=summary,
        top_evidence_id=top_hit.evidence.evidence_id if top_hit else None,
        top_source_id=top_hit.evidence.source_id if top_hit else None,
        top_score_driver=_top_score_driver(match_explanation),
        support_status=_support_status_from_hit(top_hit) if top_hit else None,
        matched_terms=_nonblank_strings(match_explanation.get("matched_terms"), limit=6)
        if match_explanation
        else [],
        concept_labels=_nonblank_strings(match_explanation.get("concept_labels"), limit=4)
        if match_explanation
        else [],
        aspect_labels=_nonblank_strings(match_explanation.get("aspect_labels"), limit=4)
        if match_explanation
        else [],
        required_bucket_count=len(required_buckets),
        covered_required_bucket_count=len(required_buckets) - len(missing_required_buckets),
        missing_required_buckets=[bucket.label for bucket in missing_required_buckets],
        warning_count=warning_count,
        next_action_title=next_action_title,
        next_action_detail=next_action_detail,
        metadata={
            "quality_status": quality_summary.status if quality_summary else None,
            "quality_score": quality_summary.score if quality_summary else None,
            "recommended_action_count": len(recommended_actions),
            "trace_warning_count": trace_warning_count,
        },
    )


def _match_explanation(hit: RetrievalHit | None) -> dict[str, Any]:
    if hit is None or not isinstance(hit.match_explanation, dict):
        return {}
    return hit.match_explanation


def _top_score_driver(match_explanation: dict[str, Any]) -> str | None:
    value = match_explanation.get("top_score_driver")
    return value.strip() if isinstance(value, str) and value.strip() else None


def _support_status_from_hit(hit: RetrievalHit | None) -> str | None:
    explanation = _match_explanation(hit)
    value = explanation.get("support_status")
    if isinstance(value, str) and value.strip():
        return value.strip()
    if hit is None:
        return None
    if hit.matched_terms and hit.evidence.confidence >= 0.75:
        return "strong"
    if hit.matched_terms:
        return "partial"
    return "weak"


def _nonblank_strings(value: Any, *, limit: int) -> list[str]:
    if not isinstance(value, list):
        return []
    strings = [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return strings[:limit]


def _join_labels(labels: Iterable[str]) -> str:
    values = [label for label in labels if label]
    return ", ".join(values) if values else "required buckets"


def _humanize(value: str) -> str:
    return value.replace("_", " ")


def _format_count(count: int, noun: str) -> str:
    return f"{count} {noun if count == 1 else noun + 's'}"


def strategy_recommendations_from_context(
    *,
    query_analysis: RetrievalQueryAnalysis,
    quality_signals: list[RetrievalQualitySignal],
    evidence_buckets: list[RetrievalEvidenceBucket],
    safety_flags: list[str],
    reranker_enabled: bool,
) -> list[RetrievalStrategyRecommendation]:
    """Explain the retrieval strategy through data-driven recommendation rules."""

    rules = active_strategy_recommendation_rules()
    signal_codes = {signal.code for signal in quality_signals}
    signal_codes_by_rule = {
        rule.rule_id: [
            signal.code
            for signal in quality_signals
            if _strategy_rule_signal_matches(signal.code, rule.match)
        ]
        for rule in rules
    }
    missing_required_bucket = any(
        bucket.required and bucket.hit_count == 0 for bucket in evidence_buckets
    )
    matches = [
        rule
        for rule in rules
        if _strategy_recommendation_rule_matches(
            rule,
            query_analysis=query_analysis,
            signal_codes=signal_codes,
            safety_flags=set(safety_flags),
            missing_required_bucket=missing_required_bucket,
            reranker_enabled=reranker_enabled,
        )
    ]
    matches.sort(key=lambda rule: rule.priority)
    return [
        RetrievalStrategyRecommendation(
            recommendation_id=f"strategy:{rule.rule_id}",
            title=rule.title,
            technique=rule.technique,
            status=rule.status,
            rationale=rule.rationale,
            source_signal_codes=signal_codes_by_rule.get(rule.rule_id, []),
            suggested_filters=rule.suggested_filters,
            metadata={
                "rule_id": rule.rule_id,
                "priority": rule.priority,
                "query_profile_id": (
                    query_analysis.query_profile.profile_id
                    if query_analysis.query_profile
                    else None
                ),
                "retrieval_mode": (
                    query_analysis.query_profile.retrieval_mode
                    if query_analysis.query_profile
                    else None
                ),
            },
        )
        for rule in matches
    ]


def standard_search_plan_from_context(
    *,
    query: RetrievalQuery,
    query_analysis: RetrievalQueryAnalysis,
    quality_signals: list[RetrievalQualitySignal],
    safety_flags: list[str],
    strategy_recommendations: list[RetrievalStrategyRecommendation],
) -> RetrievalStandardSearchPlan | None:
    """Build a healthcare-standard follow-up search plan from trusted rules."""

    rules = active_standard_search_playbook_rules()
    if not rules:
        return None
    signal_codes = {signal.code for signal in quality_signals}
    matched_rules = [
        rule
        for rule in rules
        if _standard_search_playbook_rule_matches(
            rule,
            query=query,
            query_analysis=query_analysis,
            signal_codes=signal_codes,
            safety_flags=set(safety_flags),
        )
    ]
    matched_rules.sort(key=lambda rule: rule.priority)
    if not matched_rules:
        return None

    template_context = _standard_search_template_context(
        query=query,
        query_analysis=query_analysis,
        signal_codes=signal_codes,
        strategy_recommendations=strategy_recommendations,
    )
    steps = [
        RetrievalStandardSearchStep(
            step_id=f"standard_search:{rule.rule_id}",
            label=rule.label,
            standard_system=rule.standard_system,
            route_type=rule.route_type,
            query=_render_standard_search_template(rule.query_template, template_context),
            rationale=rule.rationale,
            priority=rule.priority,
            suggested_filters=rule.suggested_filters,
            governance_notes=list(rule.governance_notes),
            metadata={
                **rule.metadata,
                "rule_id": rule.rule_id,
                "matched_standards": _matched_values(
                    query_analysis.standards,
                    rule.match.any_standards,
                ),
                "matched_concepts": _matched_values(
                    query_analysis.detected_concepts,
                    rule.match.any_concepts,
                ),
                "matched_query_aspects": _matched_values(
                    (aspect.aspect_id for aspect in query_analysis.query_aspects),
                    rule.match.any_query_aspects,
                ),
                "matched_fields": _matched_values(
                    query.fields,
                    rule.match.any_fields,
                    case_sensitive=False,
                ),
                "source_quality_signal_codes": sorted(
                    signal_codes.intersection(rule.match.any_quality_signal_codes)
                ),
            },
        )
        for rule in matched_rules
    ]
    primary_route = steps[0].route_type
    governance_notes = _unique_strings(
        note for step in steps for note in step.governance_notes
    )
    missing_routes = _standard_search_missing_routes(steps, query_analysis)
    return RetrievalStandardSearchPlan(
        plan_id="standard_search_playbook.v1",
        summary=(
            f"Run {len(steps)} governed healthcare-standard search step(s) before "
            "treating this evidence package as complete."
        ),
        primary_route=primary_route,
        steps=steps[:6],
        missing_routes=missing_routes,
        governance_notes=governance_notes[:6],
        metadata={
            "query_profile_id": (
                query_analysis.query_profile.profile_id
                if query_analysis.query_profile
                else None
            ),
            "detected_standards": list(query_analysis.standards),
            "detected_concepts": list(query_analysis.detected_concepts),
            "source_rule_count": len(matched_rules),
        },
    )


def _standard_search_playbook_rule_matches(
    rule: StandardSearchPlaybookRule,
    *,
    query: RetrievalQuery,
    query_analysis: RetrievalQueryAnalysis,
    signal_codes: set[str],
    safety_flags: set[str],
) -> bool:
    match = rule.match
    profile_id = query_analysis.query_profile.profile_id if query_analysis.query_profile else None
    resource_type = (query.resource_type or "").lower()
    query_aspect_ids = {aspect.aspect_id for aspect in query_analysis.query_aspects}
    query_fields = {field.lower() for field in query.fields}
    query_tokens = set(tokenize(query.query))
    for field_name, expected_values in match.any_filters.items():
        value = query.filters.get(field_name)
        if value is None:
            return False
        if str(value).lower() not in {item.lower() for item in expected_values}:
            return False
    trigger_matches: list[bool] = []
    if match.any_profile_ids:
        trigger_matches.append(profile_id in match.any_profile_ids)
    if match.any_concepts:
        trigger_matches.append(
            bool(set(query_analysis.detected_concepts).intersection(match.any_concepts))
        )
    if match.any_standards:
        trigger_matches.append(
            bool(set(query_analysis.standards).intersection(match.any_standards))
        )
    if match.any_query_aspects:
        trigger_matches.append(bool(query_aspect_ids.intersection(match.any_query_aspects)))
    if match.any_fields:
        trigger_matches.append(
            bool(query_fields.intersection({field.lower() for field in match.any_fields}))
        )
    if match.any_tokens:
        trigger_matches.append(
            bool(query_tokens.intersection({token.lower() for token in match.any_tokens}))
        )
    if match.any_resource_types:
        trigger_matches.append(
            resource_type in {value.lower() for value in match.any_resource_types}
        )
    if match.any_quality_signal_codes:
        trigger_matches.append(bool(signal_codes.intersection(match.any_quality_signal_codes)))
    if match.any_safety_flags:
        trigger_matches.append(bool(safety_flags.intersection(match.any_safety_flags)))
    return any(trigger_matches) if trigger_matches else True


def _standard_search_template_context(
    *,
    query: RetrievalQuery,
    query_analysis: RetrievalQueryAnalysis,
    signal_codes: set[str],
    strategy_recommendations: list[RetrievalStrategyRecommendation],
) -> dict[str, str]:
    return {
        "query": query.query,
        "fields": ", ".join(query.fields) if query.fields else "unspecified fields",
        "schema_id": query.schema_id or "unspecified schema",
        "detected_format": query.detected_format or "unspecified format",
        "resource_type": query.resource_type or "Observation",
        "standards": ", ".join(query_analysis.standards) if query_analysis.standards else "no detected standards",
        "concepts": ", ".join(query_analysis.detected_concepts) if query_analysis.detected_concepts else "no detected concepts",
        "query_aspects": ", ".join(aspect.label for aspect in query_analysis.query_aspects)
        if query_analysis.query_aspects
        else "no decomposed query aspects",
        "quality_signals": ", ".join(sorted(signal_codes)) if signal_codes else "no quality signals",
        "strategy_titles": ", ".join(
            recommendation.title for recommendation in strategy_recommendations[:3]
        )
        or "no strategy recommendations",
    }


def _render_standard_search_template(template: str, context: dict[str, str]) -> str:
    try:
        rendered = template.format(**context)
    except KeyError as exc:
        missing_key = str(exc).strip("'")
        raise ValueError(
            f"Invalid standard search playbook template: unknown key {missing_key}"
        ) from exc
    return " ".join(rendered.split())


def _matched_values(
    values: Iterable[str],
    candidates: Iterable[str],
    *,
    case_sensitive: bool = True,
) -> list[str]:
    if case_sensitive:
        candidate_set = set(candidates)
        return [value for value in values if value in candidate_set]
    candidate_set = {candidate.lower() for candidate in candidates}
    return [value for value in values if value.lower() in candidate_set]


def _standard_search_missing_routes(
    steps: list[RetrievalStandardSearchStep],
    query_analysis: RetrievalQueryAnalysis,
) -> list[str]:
    route_types = {step.route_type for step in steps}
    missing: list[str] = []
    if "FHIR" in query_analysis.standards and "fhir_search" not in route_types:
        missing.append("fhir_search")
    if "LOINC" in query_analysis.standards and "terminology_lookup" not in route_types:
        missing.append("loinc_lookup")
    if "UCUM" in query_analysis.standards and "unit_validation" not in route_types:
        missing.append("ucum_unit_validation")
    return missing


def _corrective_action_rule_matches(
    signal: RetrievalQualitySignal,
    rule: CorrectiveActionRule,
) -> bool:
    if rule.signal_code != "*" and rule.signal_code != signal.code:
        return False
    if rule.match_severities and signal.severity not in rule.match_severities:
        return False
    return True


def _strategy_recommendation_rule_matches(
    rule: StrategyRecommendationRule,
    *,
    query_analysis: RetrievalQueryAnalysis,
    signal_codes: set[str],
    safety_flags: set[str],
    missing_required_bucket: bool,
    reranker_enabled: bool,
) -> bool:
    match = rule.match
    profile = query_analysis.query_profile
    if match.any_profile_ids and (
        not profile or profile.profile_id not in match.any_profile_ids
    ):
        return False
    if match.any_retrieval_modes and (
        not profile or profile.retrieval_mode not in match.any_retrieval_modes
    ):
        return False
    if match.any_quality_signal_codes and not signal_codes.intersection(
        match.any_quality_signal_codes
    ):
        return False
    if match.any_safety_flags and not safety_flags.intersection(match.any_safety_flags):
        return False
    if (
        match.missing_required_bucket is not None
        and match.missing_required_bucket != missing_required_bucket
    ):
        return False
    if match.reranker_enabled is not None and match.reranker_enabled != reranker_enabled:
        return False
    return True


def _strategy_rule_signal_matches(
    signal_code: str,
    match: StrategyRecommendationMatch,
) -> bool:
    return bool(
        match.any_quality_signal_codes
        and signal_code in match.any_quality_signal_codes
    )


def _actions_from_corrective_rule(
    signal: RetrievalQualitySignal,
    rule: CorrectiveActionRule,
) -> list[RetrievalRecommendedAction]:
    if rule.metadata_list_path:
        items = _metadata_list(signal.metadata.get(rule.metadata_list_path))
        return _actions_from_metadata_items(signal, rule, items)
    return [
        _recommended_action(
            signal=signal,
            rule=rule,
            action_type=rule.action_type,
            priority=rule.priority,
            title=_rule_title(signal, rule, {}),
            description=_rule_description(signal, rule, {}),
            metadata=signal.metadata if rule.source == "query_diagnostic" else None,
        )
    ]


def _actions_from_metadata_items(
    signal: RetrievalQualitySignal,
    rule: CorrectiveActionRule,
    items: list[dict[str, Any]],
) -> list[RetrievalRecommendedAction]:
    actions: list[RetrievalRecommendedAction] = []
    for item in items:
        suggested_filter = _rule_suggested_filter(rule, item)
        if rule.suggested_filter_path and not suggested_filter:
            continue
        metadata = {
            key: _metadata_text(item.get(key), "")
            for key in rule.metadata_keys
            if _metadata_text(item.get(key), "")
        }
        actions.append(
            _recommended_action(
                signal=signal,
                rule=rule,
                action_type=rule.action_type
                if suggested_filter or not rule.fallback_action_type
                else rule.fallback_action_type,
                priority=rule.priority,
                title=_rule_title(signal, rule, item, suggested_filter=suggested_filter),
                description=_rule_description(signal, rule, item),
                suggested_filter=suggested_filter,
                metadata=metadata,
            )
        )
    if actions or not rule.fallback_action_type:
        return actions
    return [
        _recommended_action(
            signal=signal,
            rule=rule,
            action_type=rule.fallback_action_type,
            priority=rule.priority,
            title=rule.fallback_title or _rule_title(signal, rule, {}),
            description=rule.fallback_description or _rule_description(signal, rule, {}),
        )
    ]


def _rule_title(
    signal: RetrievalQualitySignal,
    rule: CorrectiveActionRule,
    metadata: dict[str, Any],
    *,
    suggested_filter: dict[str, str] | None = None,
) -> str:
    if rule.title_from_signal:
        return _signal_text(signal, rule.title_from_signal)
    if rule.title_template:
        return _format_template(rule.title_template, metadata)
    if rule.title_prefix and suggested_filter:
        return f"{rule.title_prefix}: {_filter_label(suggested_filter)}"
    if rule.title_prefix:
        return rule.title_prefix
    return rule.title or signal.suggested_action


def _rule_description(
    signal: RetrievalQualitySignal,
    rule: CorrectiveActionRule,
    metadata: dict[str, Any],
) -> str:
    del metadata
    if rule.description_from_signal:
        return _signal_text(signal, rule.description_from_signal)
    return rule.description or signal.message


def _rule_suggested_filter(
    rule: CorrectiveActionRule,
    metadata: dict[str, Any],
) -> dict[str, str]:
    if rule.suggested_filter_path:
        return _metadata_string_map(metadata.get(rule.suggested_filter_path))
    if not rule.suggested_filter_from_metadata:
        return _metadata_string_map(metadata)
    return {
        target_key: _metadata_text(metadata.get(source_key), "")
        for target_key, source_key in rule.suggested_filter_from_metadata.items()
        if _metadata_text(metadata.get(source_key), "")
    }


def _template_values(metadata: dict[str, Any]) -> dict[str, str]:
    return {
        key: _metadata_text(value, key)
        for key, value in metadata.items()
    }


def _format_template(template: str, metadata: dict[str, Any]) -> str:
    values = _template_values(metadata)
    return re.sub(
        r"\{([a-zA-Z0-9_]+)\}",
        lambda match: values.get(match.group(1), match.group(1)),
        template,
    )


def _signal_text(signal: RetrievalQualitySignal, field_name: str) -> str:
    if field_name == "message":
        return signal.message
    if field_name == "suggested_action":
        return signal.suggested_action
    return signal.suggested_action


def _recommended_action(
    *,
    signal: RetrievalQualitySignal,
    rule: CorrectiveActionRule,
    action_type: str,
    priority: int,
    title: str,
    description: str,
    suggested_filter: dict[str, str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> RetrievalRecommendedAction:
    action_metadata = dict(metadata or {})
    action_metadata["corrective_rule_id"] = rule.rule_id
    action_metadata["corrective_rule_source"] = rule.source
    action_metadata["source_signal_severity"] = signal.severity
    action_id = _stable_action_id(
        signal.code,
        action_type,
        title,
        suggested_filter or {},
        action_metadata,
    )
    return RetrievalRecommendedAction(
        action_id=action_id,
        priority=priority,
        severity=signal.severity,
        action_type=action_type,
        title=title,
        description=description,
        suggested_filter=suggested_filter or {},
        source_signal_codes=[signal.code],
        evidence_ids=signal.evidence_ids,
        metadata=action_metadata,
    )


def _unique_recommended_actions(
    actions: list[RetrievalRecommendedAction],
) -> list[RetrievalRecommendedAction]:
    severity_rank = {"destructive": 0, "warning": 1, "info": 2, "success": 3}
    unique: dict[str, RetrievalRecommendedAction] = {}
    for action in actions:
        existing = unique.get(action.action_id)
        if not existing:
            unique[action.action_id] = action
            continue
        source_codes = sorted(
            set(existing.source_signal_codes).union(action.source_signal_codes)
        )
        evidence_ids = sorted(set(existing.evidence_ids).union(action.evidence_ids))
        unique[action.action_id] = existing.model_copy(
            update={
                "priority": min(existing.priority, action.priority),
                "source_signal_codes": source_codes,
                "evidence_ids": evidence_ids,
            }
        )
    return sorted(
        unique.values(),
        key=lambda action: (
            action.priority,
            severity_rank.get(action.severity, 9),
        ),
    )


def _stable_action_id(
    signal_code: str,
    action_type: str,
    title: str,
    suggested_filter: dict[str, str],
    metadata: dict[str, Any],
) -> str:
    payload = json.dumps(
        {
            "signal_code": signal_code,
            "action_type": action_type,
            "title": title,
            "suggested_filter": suggested_filter,
            "corrective_rule_id": metadata.get("corrective_rule_id"),
            "corrective_rule_source": metadata.get("corrective_rule_source"),
            "bucket_id": metadata.get("bucket_id"),
            "concept_id": metadata.get("concept_id"),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"retrieval_action:{sha256(payload.encode('utf-8')).hexdigest()[:12]}"


def _metadata_list(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _metadata_string_map(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key): str(item)
        for key, item in value.items()
        if str(key).strip() and str(item).strip()
    }


def _metadata_text(value: Any, fallback: str) -> str:
    text = str(value).strip() if value is not None else ""
    return text or fallback


def _filter_label(suggested_filter: dict[str, str]) -> str:
    return ", ".join(f"{key}={value}" for key, value in suggested_filter.items())


def _allowed_recommended_action_types() -> set[str]:
    return {
        "apply_filter",
        "broaden_query",
        "rewrite_query",
        "reindex_source",
        "add_source",
        "require_review",
        "diversify_sources",
    }


def _provenance_quality_issues(
    hits: list[RetrievalHit],
    policy: RetrievalQualityPolicy,
) -> list[dict[str, Any]]:
    requirements = policy.provenance_requirements
    if not requirements:
        return []
    source_types = {
        str(value)
        for value in requirements.get("source_types", [])
        if str(value).strip()
    }
    locator_any_keys = [
        str(value)
        for value in requirements.get("locator_any_keys", [])
        if str(value).strip()
    ]
    require_source_version = bool(requirements.get("require_source_version"))
    issues: list[dict[str, Any]] = []
    for hit in hits:
        source_type = hit.evidence.source_type.value
        if source_types and source_type not in source_types:
            continue
        missing: list[str] = []
        if require_source_version and not hit.evidence.source_version:
            missing.append("source_version")
        locator = hit.evidence.locator if isinstance(hit.evidence.locator, dict) else {}
        if locator_any_keys and not any(_has_locator_value(locator, key) for key in locator_any_keys):
            missing.append("locator_any_keys")
        if missing:
            issues.append(
                {
                    "evidence_id": hit.evidence.evidence_id,
                    "source_id": hit.evidence.source_id,
                    "source_type": source_type,
                    "missing": missing,
                    "locator_any_keys": locator_any_keys,
                }
            )
    return issues


def _concept_grounding_issues(
    hits: list[RetrievalHit],
    policy: RetrievalQualityPolicy,
    *,
    query_analysis: RetrievalQueryAnalysis | None,
) -> list[dict[str, Any]]:
    requirements = policy.concept_grounding_requirements
    if (
        not requirements
        or not requirements.get("require_detected_concepts")
        or query_analysis is None
    ):
        return []
    min_confidence = requirements.get("min_confidence", 0)
    if not isinstance(min_confidence, int | float):
        min_confidence = 0
    candidates = [
        candidate
        for candidate in query_analysis.concept_candidates
        if candidate.confidence >= float(min_confidence)
    ]
    if not candidates:
        return []
    matched_concept_ids = {
        str(match.get("concept_id"))
        for hit in hits
        for match in _locator_concept_matches(hit.source_locator)
        if match.get("concept_id")
    }
    issues: list[dict[str, Any]] = []
    for candidate in candidates:
        if candidate.concept_id in matched_concept_ids:
            continue
        issues.append(
            {
                "concept_id": candidate.concept_id,
                "display_name": candidate.display_name,
                "standard_system": candidate.standard_system,
                "code": candidate.code,
                "confidence": candidate.confidence,
            }
        )
    return issues


def _locator_concept_matches(locator: dict[str, Any]) -> list[dict[str, Any]]:
    matches = locator.get("concept_matches")
    return matches if isinstance(matches, list) else []


def _has_locator_value(locator: dict[str, Any], key: str) -> bool:
    value = locator.get(key)
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list | tuple | set | dict):
        return bool(value)
    return True


def active_quality_policy() -> RetrievalQualityPolicy:
    """Load the active retrieval quality policy from trusted data."""

    path = os.environ.get("OJT_RETRIEVAL_QUALITY_POLICY_PATH")
    return _load_quality_policy(path or str(DEFAULT_QUALITY_GATE_POLICY_REGISTRY))


def active_evidence_bucket_rules() -> list[EvidenceBucketRule]:
    """Load active evidence bucket rules from trusted data."""

    path = os.environ.get("OJT_EVIDENCE_BUCKET_RULES_PATH")
    return _load_evidence_bucket_rules(path or str(DEFAULT_EVIDENCE_BUCKET_RULE_REGISTRY))


def active_corrective_action_rules() -> list[CorrectiveActionRule]:
    """Load active corrective retrieval action rules from trusted data."""

    path = os.environ.get("OJT_CORRECTIVE_ACTION_RULES_PATH")
    return _load_corrective_action_rules(path or str(DEFAULT_CORRECTIVE_ACTION_RULE_REGISTRY))


def active_strategy_recommendation_rules() -> list[StrategyRecommendationRule]:
    """Load active retrieval strategy recommendation rules from trusted data."""

    path = os.environ.get("OJT_STRATEGY_RECOMMENDATION_RULES_PATH")
    return _load_strategy_recommendation_rules(
        path or str(DEFAULT_STRATEGY_RECOMMENDATION_RULE_REGISTRY)
    )


def active_standard_search_playbook_rules() -> list[StandardSearchPlaybookRule]:
    """Load active healthcare-standard search playbook rules from trusted data."""

    path = os.environ.get("OJT_STANDARD_SEARCH_PLAYBOOK_RULES_PATH")
    return _load_standard_search_playbook_rules(
        path or str(DEFAULT_STANDARD_SEARCH_PLAYBOOK_RULE_REGISTRY)
    )


@lru_cache(maxsize=4)
def _load_strategy_recommendation_rules(path_text: str) -> list[StrategyRecommendationRule]:
    path = Path(path_text)
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(
            f"Invalid strategy recommendation registry at {path}: expected object"
        )
    records = raw.get("rules")
    if not isinstance(records, list):
        raise ValueError(
            f"Invalid strategy recommendation registry at {path}: rules must be a list"
        )
    rules = [_strategy_recommendation_rule(record, path=path) for record in records]
    rule_ids = [rule.rule_id for rule in rules]
    if len(set(rule_ids)) != len(rule_ids):
        raise ValueError(
            f"Invalid strategy recommendation registry at {path}: duplicate rule_id"
        )
    return sorted(rules, key=lambda rule: rule.priority)


@lru_cache(maxsize=4)
def _load_standard_search_playbook_rules(path_text: str) -> list[StandardSearchPlaybookRule]:
    path = Path(path_text)
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid standard search playbook registry at {path}: expected object")
    records = raw.get("rules")
    if not isinstance(records, list):
        raise ValueError(
            f"Invalid standard search playbook registry at {path}: rules must be a list"
        )
    rules = [_standard_search_playbook_rule(record, path=path) for record in records]
    rule_ids = [rule.rule_id for rule in rules]
    if len(set(rule_ids)) != len(rule_ids):
        raise ValueError(
            f"Invalid standard search playbook registry at {path}: duplicate rule_id"
        )
    return sorted(rules, key=lambda rule: rule.priority)


def _standard_search_playbook_rule(
    value: Any,
    *,
    path: Path,
) -> StandardSearchPlaybookRule:
    if not isinstance(value, dict):
        raise ValueError(
            f"Invalid standard search playbook registry at {path}: rule must be an object"
        )
    priority = value.get("priority", 100)
    if not isinstance(priority, int) or isinstance(priority, bool) or priority < 1:
        raise ValueError(
            f"Invalid standard search playbook registry at {path}: "
            "priority must be a positive integer"
        )
    suggested_filters = value.get("suggested_filters", {})
    if not isinstance(suggested_filters, dict):
        raise ValueError(
            f"Invalid standard search playbook registry at {path}: "
            "suggested_filters must be an object"
        )
    metadata = value.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError(
            f"Invalid standard search playbook registry at {path}: metadata must be an object"
        )
    match = value.get("match", {})
    if not isinstance(match, dict):
        raise ValueError(
            f"Invalid standard search playbook registry at {path}: match must be an object"
        )
    any_filters = match.get("any_filters", {})
    if not isinstance(any_filters, dict):
        raise ValueError(
            f"Invalid standard search playbook registry at {path}: any_filters must be an object"
        )
    return StandardSearchPlaybookRule(
        rule_id=_required_quality_policy_text(value.get("rule_id"), path=path),
        label=_required_quality_policy_text(value.get("label"), path=path),
        standard_system=_required_quality_policy_text(value.get("standard_system"), path=path),
        route_type=_required_quality_policy_text(value.get("route_type"), path=path),
        query_template=_required_quality_policy_text(value.get("query_template"), path=path),
        rationale=_required_quality_policy_text(value.get("rationale"), path=path),
        priority=priority,
        suggested_filters={
            _required_quality_policy_text(key, path=path): _required_quality_policy_text(
                item,
                path=path,
            )
            for key, item in suggested_filters.items()
        },
        governance_notes=tuple(
            _required_quality_policy_text(item, path=path)
            for item in _quality_policy_text_list(
                value.get("governance_notes", []),
                field="governance_notes",
                path=path,
            )
        ),
        metadata=dict(metadata),
        match=StandardSearchPlaybookMatch(
            any_profile_ids=tuple(
                _required_quality_policy_text(item, path=path)
                for item in _quality_policy_text_list(
                    match.get("any_profile_ids", []),
                    field="any_profile_ids",
                    path=path,
                )
            ),
            any_concepts=tuple(
                _required_quality_policy_text(item, path=path)
                for item in _quality_policy_text_list(
                    match.get("any_concepts", []),
                    field="any_concepts",
                    path=path,
                )
            ),
            any_standards=tuple(
                _required_quality_policy_text(item, path=path)
                for item in _quality_policy_text_list(
                    match.get("any_standards", []),
                    field="any_standards",
                    path=path,
                )
            ),
            any_query_aspects=tuple(
                _required_quality_policy_text(item, path=path)
                for item in _quality_policy_text_list(
                    match.get("any_query_aspects", []),
                    field="any_query_aspects",
                    path=path,
                )
            ),
            any_fields=tuple(
                _required_quality_policy_text(item, path=path)
                for item in _quality_policy_text_list(
                    match.get("any_fields", []),
                    field="any_fields",
                    path=path,
                )
            ),
            any_tokens=tuple(
                _required_quality_policy_text(item, path=path)
                for item in _quality_policy_text_list(
                    match.get("any_tokens", []),
                    field="any_tokens",
                    path=path,
                )
            ),
            any_resource_types=tuple(
                _required_quality_policy_text(item, path=path)
                for item in _quality_policy_text_list(
                    match.get("any_resource_types", []),
                    field="any_resource_types",
                    path=path,
                )
            ),
            any_quality_signal_codes=tuple(
                _required_quality_policy_text(item, path=path)
                for item in _quality_policy_text_list(
                    match.get("any_quality_signal_codes", []),
                    field="any_quality_signal_codes",
                    path=path,
                )
            ),
            any_safety_flags=tuple(
                _required_quality_policy_text(item, path=path)
                for item in _quality_policy_text_list(
                    match.get("any_safety_flags", []),
                    field="any_safety_flags",
                    path=path,
                )
            ),
            any_filters={
                _required_quality_policy_text(key, path=path): tuple(
                    _required_quality_policy_text(item, path=path)
                    for item in _quality_policy_text_list(
                        values,
                        field=f"any_filters.{key}",
                        path=path,
                    )
                )
                for key, values in any_filters.items()
            },
        ),
    )


def _strategy_recommendation_rule(
    value: Any,
    *,
    path: Path,
) -> StrategyRecommendationRule:
    if not isinstance(value, dict):
        raise ValueError(
            f"Invalid strategy recommendation registry at {path}: rule must be an object"
        )
    priority = value.get("priority", 100)
    if not isinstance(priority, int) or isinstance(priority, bool) or priority < 1:
        raise ValueError(
            f"Invalid strategy recommendation registry at {path}: "
            "priority must be a positive integer"
        )
    match = value.get("match", {})
    if not isinstance(match, dict):
        raise ValueError(
            f"Invalid strategy recommendation registry at {path}: match must be an object"
        )
    suggested_filters = value.get("suggested_filters", {})
    if not isinstance(suggested_filters, dict):
        raise ValueError(
            f"Invalid strategy recommendation registry at {path}: "
            "suggested_filters must be an object"
        )
    return StrategyRecommendationRule(
        rule_id=_required_quality_policy_text(value.get("rule_id"), path=path),
        title=_required_quality_policy_text(value.get("title"), path=path),
        technique=_required_quality_policy_text(value.get("technique"), path=path),
        status=_required_quality_policy_text(value.get("status"), path=path),
        rationale=_required_quality_policy_text(value.get("rationale"), path=path),
        priority=priority,
        suggested_filters={
            _required_quality_policy_text(key, path=path): _required_quality_policy_text(
                item,
                path=path,
            )
            for key, item in suggested_filters.items()
        },
        match=StrategyRecommendationMatch(
            any_profile_ids=tuple(
                _required_quality_policy_text(item, path=path)
                for item in _quality_policy_text_list(
                    match.get("any_profile_ids", []),
                    field="any_profile_ids",
                    path=path,
                )
            ),
            any_retrieval_modes=tuple(
                _required_quality_policy_text(item, path=path)
                for item in _quality_policy_text_list(
                    match.get("any_retrieval_modes", []),
                    field="any_retrieval_modes",
                    path=path,
                )
            ),
            any_quality_signal_codes=tuple(
                _required_quality_policy_text(item, path=path)
                for item in _quality_policy_text_list(
                    match.get("any_quality_signal_codes", []),
                    field="any_quality_signal_codes",
                    path=path,
                )
            ),
            any_safety_flags=tuple(
                _required_quality_policy_text(item, path=path)
                for item in _quality_policy_text_list(
                    match.get("any_safety_flags", []),
                    field="any_safety_flags",
                    path=path,
                )
            ),
            missing_required_bucket=_optional_bool_match(
                match.get("missing_required_bucket"),
                field="missing_required_bucket",
                path=path,
            ),
            reranker_enabled=_optional_bool_match(
                match.get("reranker_enabled"),
                field="reranker_enabled",
                path=path,
            ),
        ),
    )


def _optional_bool_match(value: Any, *, field: str, path: Path) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    raise ValueError(
        f"Invalid strategy recommendation registry at {path}: {field} must be a boolean"
    )


@lru_cache(maxsize=4)
def _load_corrective_action_rules(path_text: str) -> list[CorrectiveActionRule]:
    path = Path(path_text)
    if not path.exists():
        return _default_corrective_action_rules()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid corrective action registry at {path}: expected object")
    rules = raw.get("rules")
    if not isinstance(rules, list):
        raise ValueError(f"Invalid corrective action registry at {path}: rules must be a list")
    parsed = [_corrective_action_rule(item, path=path) for item in rules]
    rule_ids = [rule.rule_id for rule in parsed]
    if len(set(rule_ids)) != len(rule_ids):
        raise ValueError(f"Invalid corrective action registry at {path}: duplicate rule_id")
    return parsed


def _corrective_action_rule(value: Any, *, path: Path) -> CorrectiveActionRule:
    if not isinstance(value, dict):
        raise ValueError(f"Invalid corrective action registry at {path}: rule must be an object")
    action_type = _required_quality_policy_text(value.get("action_type"), path=path)
    fallback_action_type = _optional_quality_policy_text(value.get("fallback_action_type"))
    for field_name, candidate in {
        "action_type": action_type,
        "fallback_action_type": fallback_action_type,
    }.items():
        if candidate and candidate not in _allowed_recommended_action_types():
            raise ValueError(
                f"Invalid corrective action registry at {path}: "
                f"{field_name} {candidate!r} is unsupported"
            )
    priority = value.get("priority")
    if not isinstance(priority, int) or isinstance(priority, bool) or priority < 1:
        raise ValueError(
            f"Invalid corrective action registry at {path}: priority must be a positive integer"
        )
    suggested_filter_from_metadata = value.get("suggested_filter_from_metadata", {})
    if not isinstance(suggested_filter_from_metadata, dict):
        raise ValueError(
            f"Invalid corrective action registry at {path}: "
            "suggested_filter_from_metadata must be an object"
        )
    return CorrectiveActionRule(
        rule_id=_required_quality_policy_text(value.get("rule_id"), path=path),
        signal_code=_required_quality_policy_text(value.get("signal_code"), path=path),
        source=_corrective_action_rule_source(value.get("source"), path=path),
        priority=priority,
        action_type=action_type,
        title=_optional_quality_policy_text(value.get("title")),
        description=_optional_quality_policy_text(value.get("description")),
        title_template=_optional_quality_policy_text(value.get("title_template")),
        title_prefix=_optional_quality_policy_text(value.get("title_prefix")),
        fallback_title=_optional_quality_policy_text(value.get("fallback_title")),
        title_from_signal=_optional_quality_policy_text(value.get("title_from_signal")),
        description_from_signal=_optional_quality_policy_text(
            value.get("description_from_signal")
        ),
        fallback_action_type=fallback_action_type,
        fallback_description=_optional_quality_policy_text(value.get("fallback_description")),
        metadata_list_path=_optional_quality_policy_text(value.get("metadata_list_path")),
        suggested_filter_path=_optional_quality_policy_text(value.get("suggested_filter_path")),
        suggested_filter_from_metadata={
            _required_quality_policy_text(key, path=path): _required_quality_policy_text(
                item,
                path=path,
            )
            for key, item in suggested_filter_from_metadata.items()
        },
        metadata_keys=tuple(
            _required_quality_policy_text(item, path=path)
            for item in _quality_policy_text_list(
                value.get("metadata_keys", []),
                field="metadata_keys",
                path=path,
            )
        ),
        match_severities=tuple(
            _required_quality_policy_text(item, path=path)
            for item in _quality_policy_text_list(
                value.get("match_severities", []),
                field="match_severities",
                path=path,
            )
        ),
    )


def _corrective_action_rule_source(value: Any, *, path: Path) -> str:
    source = _optional_quality_policy_text(value) or "quality_signal"
    if source not in {"quality_signal", "query_diagnostic"}:
        raise ValueError(
            f"Invalid corrective action registry at {path}: "
            "source must be quality_signal or query_diagnostic"
        )
    return source


def _default_corrective_action_rules() -> list[CorrectiveActionRule]:
    path = Path("default_corrective_action_rules")
    raw_rules: list[dict[str, Any]] = [
        {
            "rule_id": "overconstrained_metadata_broaden_query",
            "source": "query_diagnostic",
            "signal_code": "overconstrained_metadata_filters",
            "priority": 8,
            "action_type": "broaden_query",
            "title": "Broaden over-filtered search",
            "description": (
                "Clear narrow metadata filters or add schema, fields, resource type, "
                "format, or clinical terms before treating low evidence coverage as real."
            ),
        },
        {
            "rule_id": "no_hits_broaden_query",
            "signal_code": "no_hits",
            "priority": 10,
            "action_type": "broaden_query",
            "title": "Broaden the search",
            "description": (
                "Remove restrictive filters, use fewer exact terms, or reindex trusted "
                "knowledge before relying on this package."
            ),
        },
        {
            "rule_id": "query_context_safety_review",
            "signal_code": "query_context_safety_flags",
            "priority": 15,
            "action_type": "require_review",
            "title": "Require human review",
            "description": (
                "Treat the query text as untrusted data and require review before running "
                "write-capable or agent handoff steps."
            ),
        },
        {
            "rule_id": "missing_required_bucket_recovery",
            "signal_code": "missing_required_evidence_buckets",
            "priority": 20,
            "action_type": "apply_filter",
            "fallback_action_type": "add_source",
            "title_template": "Recover {label} evidence",
            "description": (
                "Run a targeted remediation search or add an approved source for this "
                "required evidence class."
            ),
            "metadata_list_path": "missing_buckets",
            "suggested_filter_path": "suggested_filter",
            "metadata_keys": ["bucket_id"],
        },
        {
            "rule_id": "missing_standard_filter_recovery",
            "signal_code": "missing_standard_coverage",
            "priority": 30,
            "action_type": "apply_filter",
            "fallback_action_type": "broaden_query",
            "title_prefix": "Recover standard coverage",
            "fallback_title": "Broaden standard search",
            "description_from_signal": "suggested_action",
            "metadata_list_path": "suggested_filters",
        },
        {
            "rule_id": "missing_concept_grounding_recovery",
            "signal_code": "missing_concept_grounding",
            "priority": 35,
            "action_type": "apply_filter",
            "fallback_action_type": "add_source",
            "title_template": "Recover concept grounding: {display_name}",
            "fallback_title": "Add terminology-backed evidence",
            "description": (
                "Run a terminology-focused search so selected evidence grounds this "
                "detected medical concept before downstream use."
            ),
            "fallback_description": (
                "Add or reindex approved terminology sources that ground the detected "
                "medical concepts."
            ),
            "metadata_list_path": "missing_concepts",
            "suggested_filter_from_metadata": {"standard_system": "standard_system"},
            "metadata_keys": ["concept_id", "standard_system"],
        },
        {
            "rule_id": "missing_query_aspect_filter_recovery",
            "signal_code": "missing_query_aspect_coverage",
            "priority": 38,
            "action_type": "apply_filter",
            "fallback_action_type": "broaden_query",
            "title_prefix": "Recover aspect coverage",
            "fallback_title": "Broaden aspect search",
            "description_from_signal": "suggested_action",
            "metadata_list_path": "suggested_filters",
        },
        {
            "rule_id": "weak_top_hit_rewrite_query",
            "signal_code": "weak_top_hit_match",
            "priority": 40,
            "action_type": "rewrite_query",
            "title": "Rewrite the query",
            "description": (
                "Use more specific clinical terms, identifiers, standards, or schema "
                "fields so the top result has stronger exact-term support."
            ),
        },
        {
            "rule_id": "source_diversity_recovery",
            "signal_code": "source_diversity_limited",
            "priority": 45,
            "action_type": "diversify_sources",
            "title": "Diversify selected sources",
            "description": (
                "Apply source, standard, or clinical-domain filters to reduce "
                "duplicate-source evidence before downstream use."
            ),
        },
        {
            "rule_id": "weak_provenance_reindex",
            "signal_code": "weak_evidence_provenance",
            "priority": 50,
            "action_type": "reindex_source",
            "title": "Repair source provenance",
            "description": (
                "Reindex the source with version and locator metadata, or replace the "
                "evidence with an auditable source."
            ),
        },
        {
            "rule_id": "default_warning_review",
            "signal_code": "*",
            "match_severities": ["warning", "destructive"],
            "priority": 90,
            "action_type": "require_review",
            "title_from_signal": "suggested_action",
            "description_from_signal": "message",
        },
    ]
    return [_corrective_action_rule(item, path=path) for item in raw_rules]


@lru_cache(maxsize=4)
def _load_evidence_bucket_rules(path_text: str) -> list[EvidenceBucketRule]:
    path = Path(path_text)
    if not path.exists():
        return _default_evidence_bucket_rules()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid evidence bucket registry at {path}: expected object")
    buckets = raw.get("buckets")
    if not isinstance(buckets, list):
        raise ValueError(f"Invalid evidence bucket registry at {path}: buckets must be a list")
    rules = [_evidence_bucket_rule(item, path=path) for item in buckets]
    bucket_ids = [rule.bucket_id for rule in rules]
    if len(set(bucket_ids)) != len(bucket_ids):
        raise ValueError(f"Invalid evidence bucket registry at {path}: duplicate bucket_id")
    if "other" not in set(bucket_ids):
        rules.append(_default_other_bucket_rule())
    return rules


def _evidence_bucket_rule(value: Any, *, path: Path) -> EvidenceBucketRule:
    if not isinstance(value, dict):
        raise ValueError(f"Invalid evidence bucket registry at {path}: bucket must be an object")
    bucket_id = _required_quality_policy_text(value.get("bucket_id"), path=path)
    allowed_bucket_ids = {
        "schema",
        "policy",
        "terminology",
        "fhir_mapping",
        "source_locator",
        "prior_decision",
        "other",
    }
    if bucket_id not in allowed_bucket_ids:
        raise ValueError(
            f"Invalid evidence bucket registry at {path}: unsupported bucket_id {bucket_id!r}"
        )
    suggested_filter = value.get("suggested_filter", {})
    match = value.get("match", {})
    if not isinstance(suggested_filter, dict):
        raise ValueError(
            f"Invalid evidence bucket registry at {path}: suggested_filter must be an object"
        )
    if not isinstance(match, dict):
        raise ValueError(f"Invalid evidence bucket registry at {path}: match must be an object")
    return EvidenceBucketRule(
        bucket_id=bucket_id,
        label=_required_quality_policy_text(value.get("label"), path=path),
        description=_required_quality_policy_text(value.get("description"), path=path),
        required=bool(value.get("required", False)),
        suggested_filter={
            _required_quality_policy_text(key, path=path): _required_quality_policy_text(
                item,
                path=path,
            )
            for key, item in suggested_filter.items()
        },
        match=EvidenceBucketMatchRule(
            source_types=tuple(
                _required_quality_policy_text(item, path=path)
                for item in _quality_policy_text_list(
                    match.get("source_types", []),
                    field="source_types",
                    path=path,
                )
            ),
            source_id_contains=tuple(
                _required_quality_policy_text(item, path=path).lower()
                for item in _quality_policy_text_list(
                    match.get("source_id_contains", []),
                    field="source_id_contains",
                    path=path,
                )
            ),
            standard_systems=tuple(
                _required_quality_policy_text(item, path=path)
                for item in _quality_policy_text_list(
                    match.get("standard_systems", []),
                    field="standard_systems",
                    path=path,
                )
            ),
            locator_any_keys=tuple(
                _required_quality_policy_text(item, path=path)
                for item in _quality_policy_text_list(
                    match.get("locator_any_keys", []),
                    field="locator_any_keys",
                    path=path,
                )
            ),
        ),
    )


def _default_evidence_bucket_rules() -> list[EvidenceBucketRule]:
    return [
        EvidenceBucketRule(
            bucket_id="schema",
            label="Schema",
            description="Schemas, field dictionaries, and data contracts supporting parsing or validation.",
            required=True,
            suggested_filter={"source_type": EvidenceSourceType.SCHEMA.value},
            match=EvidenceBucketMatchRule(
                source_types=(
                    EvidenceSourceType.SCHEMA.value,
                    EvidenceSourceType.DATA_DICTIONARY.value,
                    EvidenceSourceType.VALIDATION_REPORT.value,
                )
            ),
        ),
        EvidenceBucketRule(
            bucket_id="policy",
            label="Policy",
            description="Governance, PHI, review, and safety rules retrieved for the workflow.",
            required=True,
            suggested_filter={"standard_system": "ojtflow_policy"},
            match=EvidenceBucketMatchRule(
                source_types=(
                    EvidenceSourceType.AUDIT_EVENT.value,
                    EvidenceSourceType.TOOL_OUTPUT.value,
                ),
                source_id_contains=("policy", "review", "governance"),
            ),
        ),
        EvidenceBucketRule(
            bucket_id="terminology",
            label="Terminology",
            description="Controlled terminology and unit evidence such as LOINC, UCUM, RxNorm, or SNOMED CT.",
            required=False,
            suggested_filter={"source_type": EvidenceSourceType.TERMINOLOGY_SYSTEM.value},
            match=EvidenceBucketMatchRule(
                source_types=(EvidenceSourceType.TERMINOLOGY_SYSTEM.value,),
                standard_systems=("LOINC", "UCUM", "RxNorm", "SNOMED_CT", "SNOMED", "MeSH"),
            ),
        ),
        EvidenceBucketRule(
            bucket_id="fhir_mapping",
            label="FHIR mapping",
            description="FHIR resource, search parameter, and mapping evidence for clinical package output.",
            required=False,
            suggested_filter={"standard_system": "FHIR"},
            match=EvidenceBucketMatchRule(
                standard_systems=("FHIR",),
                source_id_contains=("fhir",),
            ),
        ),
        EvidenceBucketRule(
            bucket_id="source_locator",
            label="Source locators",
            description="Input rows, OCR boxes, document chunks, or other source-local evidence locators.",
            required=False,
            suggested_filter={},
            match=EvidenceBucketMatchRule(
                source_types=(
                    EvidenceSourceType.INPUT_DATA.value,
                    EvidenceSourceType.OCR_BOX.value,
                    EvidenceSourceType.DICOM_METADATA.value,
                    EvidenceSourceType.IMAGE_MASK.value,
                    EvidenceSourceType.VIDEO_TRACK.value,
                ),
                locator_any_keys=("row", "column", "page", "bbox", "chunk_id"),
            ),
        ),
        EvidenceBucketRule(
            bucket_id="prior_decision",
            label="Prior decisions",
            description="Human decisions, audit events, or accepted transformations that can guide repeat work.",
            required=False,
            suggested_filter={"source_type": EvidenceSourceType.HUMAN_DECISION.value},
            match=EvidenceBucketMatchRule(
                source_types=(
                    EvidenceSourceType.HUMAN_DECISION.value,
                    EvidenceSourceType.AUDIT_EVENT.value,
                ),
                source_id_contains=("prior",),
            ),
        ),
        _default_other_bucket_rule(),
    ]


def _default_other_bucket_rule() -> EvidenceBucketRule:
    return EvidenceBucketRule(
        bucket_id="other",
        label="Other evidence",
        description="Retrieved evidence that does not fit a higher-priority clinical workflow bucket.",
        required=False,
        suggested_filter={},
        match=EvidenceBucketMatchRule(),
    )


@lru_cache(maxsize=4)
def _load_quality_policy(path_text: str) -> RetrievalQualityPolicy:
    path = Path(path_text)
    if not path.exists():
        return _default_quality_policy()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid retrieval quality policy at {path}: expected object")
    severity_penalties = raw.get("severity_penalties")
    blocking_severities = raw.get("blocking_severities")
    review_severities = raw.get("review_severities")
    status_thresholds = raw.get("status_thresholds")
    ranking_thresholds = raw.get("ranking_thresholds", {})
    provenance_requirements = raw.get("provenance_requirements", {})
    concept_grounding_requirements = raw.get("concept_grounding_requirements", {})
    evidence_bucket_requirements = raw.get("evidence_bucket_requirements", {})
    if not isinstance(severity_penalties, dict):
        raise ValueError(
            f"Invalid retrieval quality policy at {path}: severity_penalties must be an object"
        )
    if not isinstance(blocking_severities, list):
        raise ValueError(
            f"Invalid retrieval quality policy at {path}: blocking_severities must be a list"
        )
    if not isinstance(review_severities, list):
        raise ValueError(
            f"Invalid retrieval quality policy at {path}: review_severities must be a list"
        )
    if not isinstance(status_thresholds, dict):
        raise ValueError(
            f"Invalid retrieval quality policy at {path}: status_thresholds must be an object"
        )
    if not isinstance(ranking_thresholds, dict):
        raise ValueError(
            f"Invalid retrieval quality policy at {path}: ranking_thresholds must be an object"
        )
    if not isinstance(provenance_requirements, dict):
        raise ValueError(
            f"Invalid retrieval quality policy at {path}: provenance_requirements must be an object"
        )
    if not isinstance(concept_grounding_requirements, dict):
        raise ValueError(
            f"Invalid retrieval quality policy at {path}: "
            "concept_grounding_requirements must be an object"
        )
    if not isinstance(evidence_bucket_requirements, dict):
        raise ValueError(
            f"Invalid retrieval quality policy at {path}: "
            "evidence_bucket_requirements must be an object"
        )
    return RetrievalQualityPolicy(
        version=_optional_quality_policy_text(raw.get("version")) or "retrieval_quality_policy.v1",
        severity_penalties={
            _required_quality_policy_text(key, path=path): _quality_policy_penalty(
                value,
                path=path,
            )
            for key, value in severity_penalties.items()
        },
        blocking_severities=tuple(
            _required_quality_policy_text(value, path=path) for value in blocking_severities
        ),
        review_severities=tuple(
            _required_quality_policy_text(value, path=path) for value in review_severities
        ),
        review_score_below=_quality_policy_score_threshold(
            status_thresholds.get("review_score_below"),
            path=path,
        ),
        default_top_action=_optional_quality_policy_text(raw.get("default_top_action"))
        or _default_quality_policy().default_top_action,
        ranking_thresholds={
            _required_quality_policy_text(key, path=path): _quality_policy_ranking_threshold(
                value,
                path=path,
            )
            for key, value in ranking_thresholds.items()
        },
        provenance_requirements=_quality_policy_provenance_requirements(
            provenance_requirements,
            path=path,
        ),
        concept_grounding_requirements=_quality_policy_concept_grounding_requirements(
            concept_grounding_requirements,
            path=path,
        ),
        evidence_bucket_requirements=_quality_policy_evidence_bucket_requirements(
            evidence_bucket_requirements,
            path=path,
        ),
    )


def _default_quality_policy() -> RetrievalQualityPolicy:
    return RetrievalQualityPolicy(
        version="retrieval_quality_policy.v1",
        severity_penalties={
            "success": 0,
            "info": 5,
            "warning": 15,
            "destructive": 40,
            "error": 40,
        },
        blocking_severities=("destructive", "error"),
        review_severities=("warning",),
        review_score_below=85,
        default_top_action="Run retrieval before assessing package readiness.",
        ranking_thresholds={"min_top_matched_terms": 1},
        provenance_requirements={
            "source_types": [
                EvidenceSourceType.HEALTHCARE_STANDARD.value,
                EvidenceSourceType.TERMINOLOGY_SYSTEM.value,
                EvidenceSourceType.DATA_DICTIONARY.value,
            ],
            "require_source_version": True,
            "locator_any_keys": [
                "path",
                "url",
                "standard",
                "pmid",
                "doi",
                "api",
                "resource",
                "table",
                "document_id",
            ],
        },
        concept_grounding_requirements={
            "require_detected_concepts": True,
            "min_confidence": 0.7,
        },
        evidence_bucket_requirements={
            "required_bucket_ids": ["schema", "policy"],
        },
    )


def _required_quality_policy_text(value: Any, *, path: Path) -> str:
    text = _optional_quality_policy_text(value)
    if not text:
        raise ValueError(f"Invalid retrieval quality policy at {path}: value cannot be blank")
    return text


def _optional_quality_policy_text(value: Any) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split())
    return text or None


def _quality_policy_penalty(value: Any, *, path: Path) -> int:
    if not isinstance(value, int):
        raise ValueError(
            f"Invalid retrieval quality policy at {path}: severity penalty must be an integer"
        )
    if value < 0 or value > 100:
        raise ValueError(
            f"Invalid retrieval quality policy at {path}: severity penalty must be 0-100"
        )
    return value


def _quality_policy_score_threshold(value: Any, *, path: Path) -> int:
    if not isinstance(value, int):
        raise ValueError(
            f"Invalid retrieval quality policy at {path}: review_score_below must be an integer"
        )
    if value < 0 or value > 100:
        raise ValueError(
            f"Invalid retrieval quality policy at {path}: review_score_below must be 0-100"
        )
    return value


def _quality_policy_ranking_threshold(value: Any, *, path: Path) -> int | float:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ValueError(
            f"Invalid retrieval quality policy at {path}: ranking threshold must be numeric"
        )
    if value < 0:
        raise ValueError(
            f"Invalid retrieval quality policy at {path}: ranking threshold must be non-negative"
        )
    return value


def _quality_policy_provenance_requirements(
    value: dict[str, Any],
    *,
    path: Path,
) -> dict[str, Any]:
    requirements: dict[str, Any] = {}
    if "source_types" in value:
        requirements["source_types"] = [
            _required_quality_policy_text(item, path=path)
            for item in _quality_policy_text_list(
                value["source_types"],
                field="source_types",
                path=path,
            )
        ]
    if "locator_any_keys" in value:
        requirements["locator_any_keys"] = [
            _required_quality_policy_text(item, path=path)
            for item in _quality_policy_text_list(
                value["locator_any_keys"],
                field="locator_any_keys",
                path=path,
            )
        ]
    if "require_source_version" in value:
        if not isinstance(value["require_source_version"], bool):
            raise ValueError(
                f"Invalid retrieval quality policy at {path}: "
                "require_source_version must be a boolean"
            )
        requirements["require_source_version"] = value["require_source_version"]
    return requirements


def _quality_policy_concept_grounding_requirements(
    value: dict[str, Any],
    *,
    path: Path,
) -> dict[str, Any]:
    requirements: dict[str, Any] = {}
    if "require_detected_concepts" in value:
        if not isinstance(value["require_detected_concepts"], bool):
            raise ValueError(
                f"Invalid retrieval quality policy at {path}: "
                "require_detected_concepts must be a boolean"
            )
        requirements["require_detected_concepts"] = value["require_detected_concepts"]
    if "min_confidence" in value:
        min_confidence = _quality_policy_ranking_threshold(value["min_confidence"], path=path)
        if min_confidence > 1:
            raise ValueError(
                f"Invalid retrieval quality policy at {path}: min_confidence must be 0-1"
            )
        requirements["min_confidence"] = min_confidence
    return requirements


def _quality_policy_evidence_bucket_requirements(
    value: dict[str, Any],
    *,
    path: Path,
) -> dict[str, Any]:
    requirements: dict[str, Any] = {}
    if "required_bucket_ids" in value:
        requirements["required_bucket_ids"] = [
            _required_quality_policy_text(item, path=path)
            for item in _quality_policy_text_list(
                value["required_bucket_ids"],
                field="required_bucket_ids",
                path=path,
            )
        ]
    return requirements


def _quality_policy_text_list(value: Any, *, field: str, path: Path) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(
            f"Invalid retrieval quality policy at {path}: {field} must be a list"
        )
    return value


def facets_from_chunks(chunks: list[KnowledgeChunk]) -> RetrievalFacets:
    """Build final-hit facets for operator scan/filter UX."""

    return RetrievalFacets(
        source_type=_facet_buckets(chunk.source_type.value for chunk in chunks),
        clinical_domain=_facet_buckets(chunk.clinical_domain for chunk in chunks),
        standard_system=_facet_buckets(chunk.standard_system for chunk in chunks),
        trust_level=_facet_buckets(chunk.trust_level.value for chunk in chunks),
    )


def retrieval_safety_flags(query: RetrievalQuery) -> list[str]:
    """Return deterministic safety flags for user-controlled retrieval context."""

    inspected_text = " ".join(
        value
        for value in [
            query.query,
            *query.fields,
            query.schema_id or "",
            query.detected_format or "",
            query.resource_type or "",
        ]
        if value
    )
    flags: list[str] = []
    if contains_prompt_injection(inspected_text):
        flags.append("prompt_injection_pattern_in_query")
    if any(looks_sensitive_field(field) for field in query.fields):
        flags.append("sensitive_field_context")
    return flags


def evidence_from_chunk(chunk: KnowledgeChunk, *, confidence: float) -> Evidence:
    """Convert an internal chunk to the public evidence contract."""

    locator = {
        **chunk.locator,
        "chunk_id": chunk.chunk_id,
        "title": chunk.title,
        "clinical_domain": chunk.clinical_domain,
        "standard_system": chunk.standard_system,
        "metadata": chunk.metadata,
    }
    return Evidence(
        source_type=chunk.source_type,
        source_id=chunk.source_id,
        source_version=chunk.source_version,
        claim=chunk.content,
        locator=locator,
        confidence=round(confidence, 4),
        trust_level=chunk.trust_level,
    )


def snippet_from_chunk(
    chunk: KnowledgeChunk,
    *,
    query_tokens: set[str],
    matched_terms: list[str],
) -> RetrievalSnippet:
    """Extract the most query-relevant sentence/window from a chunk."""

    content = _snippet_source_text(chunk.content)
    if not content:
        content = chunk.title
    segments = _snippet_segments(content)
    ranked_segments = [
        (
            _snippet_score(segment_text, query_tokens=query_tokens, matched_terms=matched_terms),
            start,
            end,
            segment_text,
        )
        for start, end, segment_text in segments
    ]
    ranked_segments.sort(
        key=lambda item: (
            item[0],
            -abs(len(item[3]) - SNIPPET_MAX_CHARS),
        ),
        reverse=True,
    )
    _, start, _end, text = (
        ranked_segments[0] if ranked_segments[0][0] > 0 else (0.0, *segments[0])
    )
    cropped_start, cropped_text = _crop_snippet(
        text,
        start_char=start,
        matched_terms=matched_terms,
    )
    snippet_terms = [
        term
        for term in matched_terms
        if term in set(tokenize(cropped_text))
    ][:8]
    return RetrievalSnippet(
        text=cropped_text,
        start_char=cropped_start,
        end_char=cropped_start + len(cropped_text),
        matched_terms=snippet_terms,
    )


def sources_from_chunks(chunks: list[KnowledgeChunk]) -> list[RetrievalSource]:
    """Build source inventory entries from chunks."""

    grouped: dict[str, list[KnowledgeChunk]] = {}
    for chunk in chunks:
        grouped.setdefault(chunk.source_id, []).append(chunk)
    sources: list[RetrievalSource] = []
    for source_id, source_chunks in sorted(grouped.items()):
        first = source_chunks[0]
        source_metadata = _source_inventory_metadata(first.metadata)
        sources.append(
            RetrievalSource(
                source_id=source_id,
                source_type=first.source_type,
                title=first.title,
                source_version=first.source_version,
                trust_level=first.trust_level,
                clinical_domain=first.clinical_domain,
                standard_system=first.standard_system,
                chunk_count=len(source_chunks),
                authority=source_metadata.get("authority"),
                access_mode=source_metadata.get("access_mode"),
                ingestion_mode=source_metadata.get("ingestion_mode"),
                license_id=source_metadata.get("license_id"),
                license_name=source_metadata.get("license_name"),
                reviewer_state=source_metadata.get("reviewer_state"),
                lifecycle_state=source_metadata.get("lifecycle_state"),
                content_hash=source_metadata.get("content_hash"),
                canonical_source_id=source_metadata.get("canonical_source_id"),
                chunk_profile=source_metadata.get("chunk_profile"),
                resource_type=source_metadata.get("resource_type"),
            )
        )
    return sources


def _source_inventory_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        key: metadata.get(key)
        for key in (
            "authority",
            "access_mode",
            "ingestion_mode",
            "license_id",
            "license_name",
            "reviewer_state",
            "lifecycle_state",
            "content_hash",
            "canonical_source_id",
            "chunk_profile",
            "resource_type",
        )
        if metadata.get(key) is not None
    }


def default_healthcare_chunks(knowledge_root: Path) -> list[KnowledgeChunk]:
    """Load project knowledge files and built-in healthcare standard scaffolds."""

    chunks = [
        KnowledgeChunk(
            chunk_id="chunk_schema_lab_result_required_fields_v1",
            source_id="schema:lab_result_v1",
            source_type=EvidenceSourceType.SCHEMA,
            title="Synthetic Lab Result Schema",
            content=(
                "Lab result records require date, patient_id, lab_name, value, and unit "
                "fields. Date should use ISO YYYY-MM-DD. Patient identifiers are "
                "sensitive in healthcare workflows."
            ),
            clinical_domain="laboratory",
            standard_system="ojtflow_schema",
            locator={"path": "knowledge/schemas/lab_result_v1.schema.json"},
        ),
        KnowledgeChunk(
            chunk_id="chunk_standard_fhir_observation_v0",
            source_id="standard:fhir_observation_r4",
            source_type=EvidenceSourceType.HEALTHCARE_STANDARD,
            title="FHIR Observation R4",
            source_version="R4",
            content=(
                "FHIR Observation represents measurements and assertions such as "
                "laboratory results. A FHIR-like Observation profile should preserve "
                "resourceType, status, code, subject, effective date, value, unit, and "
                "source evidence."
            ),
            clinical_domain="laboratory",
            standard_system="FHIR",
            locator={"standard": "HL7 FHIR R4 Observation"},
        ),
        KnowledgeChunk(
            chunk_id="chunk_standard_fhir_condition_v0",
            source_id="standard:fhir_condition_r4",
            source_type=EvidenceSourceType.HEALTHCARE_STANDARD,
            title="FHIR Condition R4",
            source_version="R4",
            content=(
                "FHIR Condition represents detailed information about conditions, "
                "problems, and diagnoses. A FHIR-like Condition profile should "
                "preserve resourceType, code, subject, clinicalStatus, "
                "verificationStatus, onset or recorded date, source evidence, and "
                "review limitations."
            ),
            clinical_domain="problem_list",
            standard_system="FHIR",
            locator={"standard": "HL7 FHIR R4 Condition"},
        ),
        KnowledgeChunk(
            chunk_id="chunk_standard_fhir_allergyintolerance_v0",
            source_id="standard:fhir_allergyintolerance_r4",
            source_type=EvidenceSourceType.HEALTHCARE_STANDARD,
            title="FHIR AllergyIntolerance R4",
            source_version="R4",
            content=(
                "FHIR AllergyIntolerance represents allergy, intolerance, and risk "
                "of adverse reaction to a substance. A FHIR-like AllergyIntolerance "
                "profile should preserve resourceType, code, patient, clinicalStatus, "
                "verificationStatus, reaction manifestation, reaction substance, "
                "recorder/source, and uncertainty before safety use."
            ),
            clinical_domain="allergy",
            standard_system="FHIR",
            locator={"standard": "HL7 FHIR R4 AllergyIntolerance"},
        ),
        KnowledgeChunk(
            chunk_id="chunk_terminology_loinc_lab_codes_v0",
            source_id="terminology:loinc",
            source_type=EvidenceSourceType.TERMINOLOGY_SYSTEM,
            title="LOINC Laboratory Terminology",
            content=(
                "LOINC is the preferred terminology direction for laboratory test "
                "identifiers. OJTFlow should retain original lab_name text and add "
                "normalized coding evidence only when confidence is explicit."
            ),
            clinical_domain="laboratory",
            standard_system="LOINC",
            locator={"standard": "LOINC"},
        ),
        KnowledgeChunk(
            chunk_id="chunk_terminology_ucum_units_v0",
            source_id="terminology:ucum",
            source_type=EvidenceSourceType.TERMINOLOGY_SYSTEM,
            title="UCUM Units",
            content=(
                "UCUM is the target unit vocabulary for computable laboratory units. "
                "Missing or ambiguous units require human review before downstream "
                "clinical or analytics use."
            ),
            clinical_domain="laboratory",
            standard_system="UCUM",
            locator={"standard": "UCUM"},
        ),
        KnowledgeChunk(
            chunk_id="chunk_terminology_rxnorm_medications_v0",
            source_id="terminology:rxnorm",
            source_type=EvidenceSourceType.TERMINOLOGY_SYSTEM,
            title="RxNorm Medication Terminology",
            content=(
                "RxNorm is the terminology direction for normalized medication concepts. "
                "It is a future adapter boundary and should not be inferred from "
                "unrelated lab data."
            ),
            clinical_domain="medication",
            standard_system="RxNorm",
            locator={"standard": "RxNorm"},
        ),
        KnowledgeChunk(
            chunk_id="chunk_terminology_rxnorm_allergy_substances_v0",
            source_id="terminology:rxnorm_allergy_substances",
            source_type=EvidenceSourceType.TERMINOLOGY_SYSTEM,
            title="RxNorm Allergy Substance Grounding",
            content=(
                "RxNorm can ground medication ingredient or product identity in "
                "allergy and intolerance records. OJTFlow should preserve the "
                "original substance text, mapping confidence, and verification "
                "status before using ingredient-level evidence in safety workflows."
            ),
            clinical_domain="allergy",
            standard_system="RxNorm",
            locator={"standard": "RxNorm"},
        ),
        KnowledgeChunk(
            chunk_id="chunk_terminology_snomed_ct_conditions_v0",
            source_id="terminology:snomed_ct",
            source_type=EvidenceSourceType.TERMINOLOGY_SYSTEM,
            title="SNOMED CT Clinical Findings",
            content=(
                "SNOMED CT is a clinical terminology direction for problem-list "
                "and diagnosis concepts. OJTFlow should use SNOMED CT lookup as "
                "grounding evidence only and preserve uncertainty before any "
                "FHIR Condition or analytics mapping."
            ),
            clinical_domain="problem_list",
            standard_system="SNOMED CT",
            locator={"standard": "SNOMED CT"},
        ),
        KnowledgeChunk(
            chunk_id="chunk_terminology_snomed_ct_allergy_findings_v0",
            source_id="terminology:snomed_ct_allergy",
            source_type=EvidenceSourceType.TERMINOLOGY_SYSTEM,
            title="SNOMED CT Allergy Findings",
            content=(
                "SNOMED CT can ground allergy, sensitivity, intolerance, and reaction "
                "manifestation concepts. Retrieval should treat SNOMED CT allergy "
                "matches as review evidence and keep clinicalStatus, verificationStatus, "
                "severity, and source provenance explicit."
            ),
            clinical_domain="allergy",
            standard_system="SNOMED CT",
            locator={"standard": "SNOMED CT"},
        ),
        KnowledgeChunk(
            chunk_id="chunk_terminology_icd10cm_diagnoses_v0",
            source_id="terminology:icd10cm",
            source_type=EvidenceSourceType.TERMINOLOGY_SYSTEM,
            title="ICD-10-CM Diagnosis Coding",
            content=(
                "ICD-10-CM is the U.S. clinical modification used to code and "
                "classify medical diagnoses. OJTFlow retrieval can surface "
                "ICD-10-CM evidence for review, but final diagnosis-code "
                "assignment must remain coder or clinician reviewed."
            ),
            clinical_domain="problem_list",
            standard_system="ICD-10-CM",
            locator={"standard": "CDC/NCHS ICD-10-CM"},
        ),
        KnowledgeChunk(
            chunk_id="chunk_standard_omop_analytics_v0",
            source_id="standard:omop_cdm",
            source_type=EvidenceSourceType.HEALTHCARE_STANDARD,
            title="OMOP Common Data Model",
            content=(
                "OMOP CDM is an analytics export direction for observational health data. "
                "It should be implemented as a downstream mapping after source evidence, "
                "validation issues, and coding confidence are preserved."
            ),
            clinical_domain="analytics",
            standard_system="OMOP",
            locator={"standard": "OMOP CDM"},
        ),
        KnowledgeChunk(
            chunk_id="chunk_standard_mesh_pubmed_search_v0",
            source_id="standard:mesh_pubmed_search",
            source_type=EvidenceSourceType.HEALTHCARE_STANDARD,
            title="MeSH and PubMed Search",
            content=(
                "MeSH is the controlled vocabulary direction for biomedical literature "
                "subject searching. PubMed search should combine MeSH review with "
                "title/abstract text words, field tags, publication type filters, and "
                "Search Details review before being treated as a final evidence strategy."
            ),
            clinical_domain="literature",
            standard_system="MeSH",
            locator={"standard": "NLM MeSH and PubMed"},
        ),
        KnowledgeChunk(
            chunk_id="chunk_standard_clinicaltrials_gov_api_v0",
            source_id="standard:clinicaltrials_gov_api",
            source_type=EvidenceSourceType.HEALTHCARE_STANDARD,
            title="ClinicalTrials.gov API v2",
            content=(
                "ClinicalTrials.gov API v2 provides study search for clinical trial "
                "context. OJTFlow search hints should prefer condition, intervention, "
                "recruitment status, eligibility, NCT identifier, and dataTimestamp "
                "verification before trial records are used as workflow evidence."
            ),
            clinical_domain="literature",
            standard_system="ClinicalTrials.gov",
            locator={"standard": "ClinicalTrials.gov API v2"},
        ),
        KnowledgeChunk(
            chunk_id="chunk_standard_openfda_drug_apis_v0",
            source_id="standard:openfda_drug_apis",
            source_type=EvidenceSourceType.HEALTHCARE_STANDARD,
            title="openFDA Drug APIs",
            content=(
                "openFDA drug APIs provide public drug label, adverse event, NDC, "
                "recall, and Drugs@FDA retrieval context. OJTFlow should treat FAERS "
                "adverse event records as signal context only and preserve endpoint, "
                "query, date, product identity, and limitations in evidence."
            ),
            clinical_domain="medication",
            standard_system="openFDA",
            locator={"standard": "openFDA drug APIs"},
        ),
    ]

    file_specs = [
        (
            "chunk_dictionary_lab_fields_v1",
            "dictionary:lab_fields_v1",
            EvidenceSourceType.DATA_DICTIONARY,
            "Lab Fields Data Dictionary",
            knowledge_root / "data_dictionaries/lab_fields.md",
            "laboratory",
            "ojtflow_dictionary",
        ),
        (
            "chunk_governance_human_review_v1",
            "governance:human_review_triggers_v1",
            EvidenceSourceType.DATA_DICTIONARY,
            "Human Review Triggers",
            knowledge_root / "governance/human_review_triggers.md",
            "governance",
            "ojtflow_policy",
        ),
        (
            "chunk_example_csv_lab_to_json_v1",
            "example:csv_lab_to_json_records_v1",
            EvidenceSourceType.TRANSFORMATION_EXAMPLE,
            "CSV Lab To JSON Records",
            knowledge_root / "transformation_examples/csv_lab_to_json_records.md",
            "laboratory",
            "ojtflow_example",
        ),
        (
            "chunk_terminology_medical_concepts_v1",
            "terminology:medical_concepts_v1",
            EvidenceSourceType.TERMINOLOGY_SYSTEM,
            "Medical Concept Seed Registry",
            knowledge_root / "terminologies/medical_concepts.json",
            "multi_domain",
            "ojtflow_terminology",
        ),
        (
            "chunk_dictionary_query_expansion_rules_v1",
            "dictionary:query_expansion_rules_v1",
            EvidenceSourceType.DATA_DICTIONARY,
            "Query Expansion Rule Registry",
            knowledge_root / "retrieval/query_expansion_rules.json",
            "retrieval",
            "ojtflow_retrieval",
        ),
        (
            "chunk_dictionary_filter_suggestion_rules_v1",
            "dictionary:filter_suggestion_rules_v1",
            EvidenceSourceType.DATA_DICTIONARY,
            "Filter Suggestion Rule Registry",
            knowledge_root / "retrieval/filter_suggestion_rules.json",
            "retrieval",
            "ojtflow_retrieval",
        ),
        (
            "chunk_dictionary_query_profile_rules_v1",
            "dictionary:query_profile_rules_v1",
            EvidenceSourceType.DATA_DICTIONARY,
            "Query Profile Rule Registry",
            knowledge_root / "retrieval/query_profile_rules.json",
            "retrieval",
            "ojtflow_retrieval",
        ),
        (
            "chunk_dictionary_query_aspect_rules_v1",
            "dictionary:query_aspect_rules_v1",
            EvidenceSourceType.DATA_DICTIONARY,
            "Query Aspect Rule Registry",
            knowledge_root / "retrieval/query_aspect_rules.json",
            "retrieval",
            "ojtflow_retrieval",
        ),
        (
            "chunk_dictionary_ranking_boost_rules_v1",
            "dictionary:ranking_boost_rules_v1",
            EvidenceSourceType.DATA_DICTIONARY,
            "Ranking Boost Rule Registry",
            knowledge_root / "retrieval/ranking_boost_rules.json",
            "retrieval",
            "ojtflow_retrieval",
        ),
        (
            "chunk_dictionary_evaluation_policy_v1",
            "dictionary:retrieval_evaluation_policy_v1",
            EvidenceSourceType.DATA_DICTIONARY,
            "Retrieval Evaluation Policy Registry",
            knowledge_root / "retrieval/evaluation_policy.json",
            "retrieval",
            "ojtflow_retrieval",
        ),
        (
            "chunk_dictionary_quality_gate_policy_v1",
            "dictionary:retrieval_quality_gate_policy_v1",
            EvidenceSourceType.DATA_DICTIONARY,
            "Retrieval Quality Gate Policy Registry",
            knowledge_root / "retrieval/quality_gate_policy.json",
            "retrieval",
            "ojtflow_retrieval",
        ),
        (
            "chunk_dictionary_search_hint_targets_v1",
            "dictionary:search_hint_targets_v1",
            EvidenceSourceType.DATA_DICTIONARY,
            "Search Hint Target Registry",
            knowledge_root / "retrieval/search_hint_targets.json",
            "retrieval",
            "ojtflow_retrieval",
        ),
        (
            "chunk_source_catalog_official_healthcare_sources_v1",
            "catalog:official_healthcare_sources_v1",
            EvidenceSourceType.DATA_DICTIONARY,
            "Official Healthcare Source Catalog",
            knowledge_root / "source_catalog/official_healthcare_sources.json",
            "multi_domain",
            "ojtflow_source_catalog",
        ),
        (
            "chunk_standard_fhir_search_parameters_r4_v1",
            "standard:fhir_search_parameters_r4_v1",
            EvidenceSourceType.HEALTHCARE_STANDARD,
            "FHIR R4 Search Parameter Seed",
            knowledge_root / "terminologies/fhir_search_parameters.json",
            "interoperability",
            "FHIR",
        ),
        (
            "chunk_standard_clinical_data_standards_map_v1",
            "standard:clinical_data_standards_map_v1",
            EvidenceSourceType.HEALTHCARE_STANDARD,
            "Clinical Data Standards Map",
            knowledge_root / "corpus/clinical_data_standards_map.md",
            "multi_domain",
            "ojtflow_standard_map",
        ),
        (
            "chunk_dictionary_medical_search_playbook_v1",
            "dictionary:medical_search_playbook_v1",
            EvidenceSourceType.DATA_DICTIONARY,
            "Medical Search Playbook",
            knowledge_root / "corpus/medical_search_playbook.md",
            "retrieval",
            "ojtflow_retrieval",
        ),
        (
            "chunk_catalog_public_dataset_ingestion_plan_v1",
            "catalog:public_dataset_ingestion_plan_v1",
            EvidenceSourceType.DATA_DICTIONARY,
            "Public Dataset Ingestion Plan",
            knowledge_root / "corpus/public_dataset_ingestion_plan.md",
            "multi_domain",
            "ojtflow_source_catalog",
        ),
        (
            "chunk_corpus_laboratory_semantic_retrieval_v1",
            "corpus:laboratory_semantic_retrieval_v1",
            EvidenceSourceType.DATA_DICTIONARY,
            "Laboratory Semantic Retrieval Corpus",
            knowledge_root / "corpus/laboratory_semantic_retrieval.md",
            "laboratory",
            "ojtflow_retrieval",
        ),
        (
            "chunk_dictionary_corrective_action_rules_v1",
            "dictionary:corrective_action_rules_v1",
            EvidenceSourceType.DATA_DICTIONARY,
            "Corrective Action Rule Registry",
            knowledge_root / "retrieval/corrective_action_rules.json",
            "retrieval",
            "ojtflow_retrieval",
        ),
        (
            "chunk_dictionary_evidence_bucket_rules_v1",
            "dictionary:evidence_bucket_rules_v1",
            EvidenceSourceType.DATA_DICTIONARY,
            "Evidence Bucket Rule Registry",
            knowledge_root / "retrieval/evidence_bucket_rules.json",
            "retrieval",
            "ojtflow_retrieval",
        ),
        (
            "chunk_dictionary_query_diagnostic_rules_v1",
            "dictionary:query_diagnostic_rules_v1",
            EvidenceSourceType.DATA_DICTIONARY,
            "Query Diagnostic Rule Registry",
            knowledge_root / "retrieval/query_diagnostic_rules.json",
            "retrieval",
            "ojtflow_retrieval",
        ),
        (
            "chunk_dictionary_strategy_recommendation_rules_v1",
            "dictionary:strategy_recommendation_rules_v1",
            EvidenceSourceType.DATA_DICTIONARY,
            "Strategy Recommendation Rule Registry",
            knowledge_root / "retrieval/strategy_recommendation_rules.json",
            "retrieval",
            "ojtflow_retrieval",
        ),
    ]
    for (
        chunk_id,
        source_id,
        source_type,
        title,
        path,
        clinical_domain,
        standard_system,
    ) in file_specs:
        if not path.exists():
            continue
        chunks.append(
            KnowledgeChunk(
                chunk_id=chunk_id,
                source_id=source_id,
                source_type=source_type,
                title=title,
                content=path.read_text(encoding="utf-8").strip(),
                clinical_domain=clinical_domain,
                standard_system=standard_system,
                locator={"path": str(path.relative_to(knowledge_root.parent))},
            )
        )
    return chunks


def chunk_metadata_json(chunk: KnowledgeChunk) -> str:
    """Serialize chunk metadata for SQL storage."""

    return json.dumps(
        {
            "locator": chunk.locator,
            "metadata": chunk.metadata,
            "clinical_domain": chunk.clinical_domain,
            "standard_system": chunk.standard_system,
        },
        sort_keys=True,
    )


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=True))


def _lexical_score(
    query_tokens: set[str],
    chunk_tokens: set[str],
    query_text: str,
    chunk: KnowledgeChunk,
) -> float:
    if not query_tokens:
        return 0.0
    overlap = len(query_tokens.intersection(chunk_tokens)) / len(query_tokens)
    phrase_boost = 0.15 if query_text.lower() in chunk.content.lower() else 0.0
    title_boost = 0.08 if any(token in tokenize(chunk.title) for token in query_tokens) else 0.0
    return overlap + phrase_boost + title_boost


def _facet_buckets(values: Iterable[object | None]) -> list[RetrievalFacetBucket]:
    counts = Counter(str(value) for value in values if value)
    return [
        RetrievalFacetBucket(value=value, count=count)
        for value, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]


def _expected_standard_values(standards: list[str]) -> list[str]:
    mapped: list[str] = []
    for standard in standards:
        if standard in {
            "FHIR",
            "LOINC",
            "UCUM",
            "RxNorm",
            "OMOP",
            "MeSH",
            "ClinicalTrials.gov",
            "openFDA",
        }:
            mapped.append(standard)
        elif standard == "OJTFlow policy":
            mapped.append("ojtflow_policy")
        elif standard == "OJTFlow schema":
            mapped.append("ojtflow_schema")
    return _dedupe_strings(mapped)


def _standard_coverage_item(
    standard: str,
    counts: Counter,
) -> RetrievalCoverageItem:
    selected_count = int(counts.get(standard, 0))
    if selected_count:
        return RetrievalCoverageItem(
            field="standard_system",
            value=standard,
            selected_count=selected_count,
            status="covered",
            severity="info",
            reason=f"Selected evidence includes {standard} grounding.",
            suggested_action=(
                "Keep the current retrieval scope; selected evidence already includes "
                f"{standard} grounding."
            ),
        )
    return RetrievalCoverageItem(
        field="standard_system",
        value=standard,
        selected_count=0,
        status="missing",
        severity="warning",
        reason=f"Query analysis expected {standard} grounding, but no selected evidence used that standard.",
        suggested_action=(
            f"Apply standard_system={standard} or broaden the query to retrieve "
            f"{standard}-grounded evidence."
        ),
        suggested_filter={"standard_system": standard},
    )


def _query_aspect_coverage_item(
    aspect: RetrievalQueryAspect,
    chunks: list[KnowledgeChunk],
) -> RetrievalCoverageItem | None:
    supported_filters = {
        field: value
        for field, value in aspect.suggested_filters.items()
        if field in {"clinical_domain", "standard_system", "source_type", "trust_level", "source_id"}
    }
    if not supported_filters:
        return None
    selected_count = sum(
        1 for chunk in chunks if _chunk_matches_filters(chunk, supported_filters)
    )
    if selected_count:
        return RetrievalCoverageItem(
            field="query_aspect",
            value=aspect.aspect_id,
            selected_count=selected_count,
            status="covered",
            severity="info",
            reason=(
                f"Selected evidence covers search aspect {aspect.label} "
                f"using supported filter criteria."
            ),
            suggested_action=(
                "Keep the current retrieval scope; selected evidence covers this "
                "search aspect."
            ),
            suggested_filter=dict(supported_filters),
        )
    return RetrievalCoverageItem(
        field="query_aspect",
        value=aspect.aspect_id,
        selected_count=0,
        status="missing",
        severity="warning",
        reason=(
            f"Search aspect {aspect.label} expected evidence matching "
            f"{_format_filter_map(supported_filters)}, but no selected evidence matched."
        ),
        suggested_action=(
            "Apply the aspect filter or broaden the query to retrieve evidence for "
            f"{aspect.label}."
        ),
        suggested_filter=dict(supported_filters),
    )


def _chunk_matches_filters(chunk: KnowledgeChunk, filters: dict[str, str]) -> bool:
    return all(
        _normalized_chunk_filter_value(chunk, field) == value.lower()
        for field, value in filters.items()
    )


def _normalized_chunk_filter_value(chunk: KnowledgeChunk, field: str) -> str | None:
    if field == "clinical_domain":
        return chunk.clinical_domain.lower() if chunk.clinical_domain else None
    if field == "standard_system":
        return chunk.standard_system.lower() if chunk.standard_system else None
    if field == "source_type":
        return chunk.source_type.value.lower()
    if field == "trust_level":
        return chunk.trust_level.value.lower()
    if field == "source_id":
        return chunk.source_id.lower()
    return None


def _format_filter_map(filters: dict[str, str]) -> str:
    return ", ".join(f"{field}={value}" for field, value in sorted(filters.items()))


def _dedupe_strings(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped


def _has_intersection(left: Iterable[str], right: Iterable[str]) -> bool:
    right_set = {value.lower() for value in right}
    return bool(right_set and {value.lower() for value in left}.intersection(right_set))


def _snippet_source_text(content: str) -> str:
    text = re.sub(r"^#{1,6}\s+", "", content, flags=re.MULTILINE)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _snippet_segments(content: str) -> list[tuple[int, int, str]]:
    segments: list[tuple[int, int, str]] = []
    cursor = 0
    for match in SNIPPET_SEGMENT_PATTERN.finditer(content):
        end = match.start()
        segment = content[cursor:end].strip()
        if segment:
            start = content.find(segment, cursor, end + len(segment))
            segments.append((start, start + len(segment), segment))
        cursor = match.end()
    tail = content[cursor:].strip()
    if tail:
        start = content.find(tail, cursor)
        segments.append((start, start + len(tail), tail))
    if not segments and content:
        segments.append((0, len(content), content))
    return segments


def _snippet_score(
    text: str,
    *,
    query_tokens: set[str],
    matched_terms: list[str],
) -> float:
    text_tokens = set(tokenize(text))
    matched = set(matched_terms)
    if not text_tokens:
        return 0.0
    exact_overlap = len(text_tokens.intersection(matched))
    query_overlap = len(text_tokens.intersection(query_tokens))
    density = exact_overlap / max(1, len(text_tokens))
    return exact_overlap * 2.0 + query_overlap * 0.25 + density


def _crop_snippet(
    text: str,
    *,
    start_char: int,
    matched_terms: list[str],
) -> tuple[int, str]:
    if len(text) <= SNIPPET_MAX_CHARS:
        return start_char, text
    lower_text = text.lower()
    first_match = min(
        (
            index
            for term in matched_terms
            if term
            for index in [lower_text.find(term.lower())]
            if index >= 0
        ),
        default=0,
    )
    local_start = max(0, first_match - SNIPPET_MAX_CHARS // 3)
    local_end = min(len(text), local_start + SNIPPET_MAX_CHARS)
    local_start = max(0, local_end - SNIPPET_MAX_CHARS)
    raw = text[local_start:local_end]
    leading_trim = len(raw) - len(raw.lstrip())
    return start_char + local_start + leading_trim, raw.strip()


def _ranking_boost(
    chunk: KnowledgeChunk,
    query: RetrievalQuery,
    matched_terms: list[str],
    *,
    query_analysis: RetrievalQueryAnalysis,
) -> tuple[float, list[AppliedRankingBoost]]:
    boost = 0.0
    applied_rules: list[AppliedRankingBoost] = []
    for rule in _ranking_boost_rules():
        if _ranking_boost_rule_matches(
            rule,
            chunk=chunk,
            query=query,
            matched_terms=matched_terms,
            query_analysis=query_analysis,
        ):
            boost += rule.weight
            applied_rules.append(
                AppliedRankingBoost(
                    rule_id=rule.rule_id,
                    weight=rule.weight,
                    reason=rule.reason,
                )
            )
    return boost, applied_rules


def _score_components(
    *,
    lexical_rrf: float,
    vector_rrf: float,
    policy_boost: float,
    lexical_rank: int,
    vector_rank: int,
    lexical_score: float,
    vector_score: float,
    applied_boost_rules: list[AppliedRankingBoost],
) -> list[RetrievalScoreComponent]:
    components = [
        RetrievalScoreComponent(
            component="lexical_rrf",
            label="Lexical RRF",
            value=round(lexical_rrf, 6),
            rank=lexical_rank,
            description="Reciprocal-rank contribution from lexical retrieval.",
            metadata={
                "raw_score": round(lexical_score, 6),
                "rrf_k": RRF_K,
            },
        ),
        RetrievalScoreComponent(
            component="vector_rrf",
            label="Vector RRF",
            value=round(vector_rrf, 6),
            rank=vector_rank,
            description="Reciprocal-rank contribution from vector retrieval.",
            metadata={
                "raw_score": round(vector_score, 6),
                "rrf_k": RRF_K,
            },
        ),
    ]
    if policy_boost:
        components.append(
            RetrievalScoreComponent(
                component="policy_boost",
                label="Policy boost",
                value=round(policy_boost, 6),
                description="Sum of applied deterministic ranking boost policy weights.",
                metadata={
                    "rule_ids": [rule.rule_id for rule in applied_boost_rules],
                },
            )
        )
    return components


def fusion_diagnostics_from_rankings(
    *,
    lexical_positions: dict[str, int],
    vector_positions: dict[str, int],
    top_hits: list[RetrievalHit],
    top_k: int,
) -> dict[str, Any]:
    """Summarize lexical/vector fusion agreement for operator diagnostics."""

    cutoff = max(1, min(top_k, len(lexical_positions), len(vector_positions)))
    lexical_top = {
        chunk_id
        for chunk_id, _rank in sorted(
            lexical_positions.items(),
            key=lambda item: item[1],
        )[:cutoff]
    }
    vector_top = {
        chunk_id
        for chunk_id, _rank in sorted(
            vector_positions.items(),
            key=lambda item: item[1],
        )[:cutoff]
    }
    overlap_count = len(lexical_top.intersection(vector_top))
    selected_rank_deltas: list[int] = []
    lexical_dominant = 0
    vector_dominant = 0
    balanced = 0
    selected_items: list[dict[str, Any]] = []
    for hit in top_hits:
        chunk_id = str(hit.evidence.locator.get("chunk_id", hit.evidence.evidence_id))
        lexical_rank = lexical_positions.get(chunk_id)
        vector_rank = vector_positions.get(chunk_id)
        lexical_component = next(
            (component for component in hit.score_components if component.component == "lexical_rrf"),
            None,
        )
        vector_component = next(
            (component for component in hit.score_components if component.component == "vector_rrf"),
            None,
        )
        lexical_value = lexical_component.value if lexical_component else 0.0
        vector_value = vector_component.value if vector_component else 0.0
        if lexical_rank is not None and vector_rank is not None:
            selected_rank_deltas.append(abs(lexical_rank - vector_rank))
        if abs(lexical_value - vector_value) < 0.000001:
            balanced += 1
            dominant_signal = "balanced"
        elif lexical_value > vector_value:
            lexical_dominant += 1
            dominant_signal = "lexical"
        else:
            vector_dominant += 1
            dominant_signal = "vector"
        selected_items.append(
            {
                "evidence_id": hit.evidence.evidence_id,
                "chunk_id": chunk_id,
                "lexical_rank": lexical_rank,
                "vector_rank": vector_rank,
                "rank_delta": None
                if lexical_rank is None or vector_rank is None
                else abs(lexical_rank - vector_rank),
                "dominant_signal": dominant_signal,
            }
        )

    mean_selected_rank_delta = (
        sum(selected_rank_deltas) / len(selected_rank_deltas)
        if selected_rank_deltas
        else 0.0
    )
    agreement_ratio = overlap_count / cutoff if cutoff else 0.0
    if agreement_ratio >= 0.75 and mean_selected_rank_delta <= 2:
        interpretation = "lexical_vector_agree"
    elif agreement_ratio <= 0.25:
        interpretation = "lexical_vector_diverge"
    else:
        interpretation = "mixed_fusion_signals"
    return {
        "method": "reciprocal_rank_fusion",
        "rrf_k": RRF_K,
        "cutoff": cutoff,
        "top_overlap_count": overlap_count,
        "top_overlap_ratio": round(agreement_ratio, 4),
        "mean_selected_rank_delta": round(mean_selected_rank_delta, 4),
        "selected_signal_balance": {
            "lexical_dominant": lexical_dominant,
            "vector_dominant": vector_dominant,
            "balanced": balanced,
        },
        "interpretation": interpretation,
        "selected_hits": selected_items,
    }


def _external_rerank_score_component(
    *,
    external_score: float,
    contribution: float,
    score_weight: float,
) -> RetrievalScoreComponent:
    return RetrievalScoreComponent(
        component="external_rerank",
        label="External rerank",
        value=round(contribution, 6),
        description="Weighted second-stage reranker contribution.",
        metadata={
            "raw_score": round(external_score, 6),
            "score_weight": score_weight,
        },
    )


def _ranking_boost_rule_matches(
    rule: RankingBoostRule,
    *,
    chunk: KnowledgeChunk,
    query: RetrievalQuery,
    matched_terms: list[str],
    query_analysis: RetrievalQueryAnalysis,
) -> bool:
    if not _ranking_boost_condition_matches(
        rule.match,
        chunk=chunk,
        query=query,
        matched_terms=matched_terms,
        query_analysis=query_analysis,
    ):
        return False
    if not rule.any_of:
        return True
    return any(
        _ranking_boost_condition_matches(
            condition,
            chunk=chunk,
            query=query,
            matched_terms=matched_terms,
            query_analysis=query_analysis,
        )
        for condition in rule.any_of
    )


def _ranking_boost_condition_matches(
    condition: RankingBoostCondition,
    *,
    chunk: KnowledgeChunk,
    query: RetrievalQuery,
    matched_terms: list[str],
    query_analysis: RetrievalQueryAnalysis,
) -> bool:
    if condition.query_schema_id_in_source_id and not (
        query.schema_id and query.schema_id in chunk.source_id
    ):
        return False
    if condition.any_query_fields_in_matched_terms and not (
        query.fields and {field.lower() for field in query.fields}.intersection(matched_terms)
    ):
        return False
    if condition.query_detected_format_present and not query.detected_format:
        return False
    if condition.filter_clinical_domain_matches_chunk and not (
        query.filters.get("clinical_domain") and query.filters.get("clinical_domain") == chunk.clinical_domain
    ):
        return False
    if condition.chunk_trust_levels and chunk.trust_level.value not in condition.chunk_trust_levels:
        return False
    if condition.chunk_source_types and chunk.source_type.value not in condition.chunk_source_types:
        return False
    if condition.chunk_clinical_domains and chunk.clinical_domain not in condition.chunk_clinical_domains:
        return False
    if condition.chunk_standard_systems and chunk.standard_system not in condition.chunk_standard_systems:
        return False
    if condition.any_matched_terms and not _has_intersection(matched_terms, condition.any_matched_terms):
        return False
    if condition.any_concepts and not _has_intersection(
        query_analysis.detected_concepts,
        condition.any_concepts,
    ):
        return False
    if condition.any_rule_ids and not _has_intersection(query_analysis.rule_ids, condition.any_rule_ids):
        return False
    return True


def _ranking_boost_rules() -> tuple[RankingBoostRule, ...]:
    path = os.environ.get("OJT_RANKING_BOOST_RULES_PATH")
    return _load_ranking_boost_rules(path or str(DEFAULT_RANKING_BOOST_RULE_REGISTRY))


def _load_ranking_boost_rules(path_text: str) -> tuple[RankingBoostRule, ...]:
    path = Path(path_text)
    if not path.exists():
        return ()
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = raw.get("rules") if isinstance(raw, dict) else None
    if not isinstance(records, list):
        raise ValueError(f"Invalid ranking boost registry at {path}: expected rules list")
    rules = tuple(_ranking_boost_rule(record, path=path) for record in records)
    _ensure_unique_ranking_boost_rule_ids(rules, path=path)
    return rules


def _ranking_boost_rule(record: Any, *, path: Path) -> RankingBoostRule:
    if not isinstance(record, dict):
        raise ValueError(f"Invalid ranking boost registry at {path}: rule must be an object")
    required = ("rule_id", "weight", "reason", "match")
    missing = [field_name for field_name in required if field_name not in record]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"Invalid ranking boost registry at {path}: missing {missing_text}")
    any_of = record.get("any_of", [])
    if not isinstance(any_of, list):
        raise ValueError(f"Invalid ranking boost registry at {path}: any_of must be a list")
    return RankingBoostRule(
        rule_id=_required_ranking_boost_text(record["rule_id"], field="rule_id", path=path),
        weight=_ranking_boost_weight(record["weight"], path=path),
        reason=_required_ranking_boost_text(record["reason"], field="reason", path=path),
        match=_ranking_boost_condition(record["match"], path=path),
        any_of=tuple(_ranking_boost_condition(condition, path=path) for condition in any_of),
    )


def _ranking_boost_condition(record: Any, *, path: Path) -> RankingBoostCondition:
    if not isinstance(record, dict):
        raise ValueError(f"Invalid ranking boost registry at {path}: condition must be an object")
    condition = RankingBoostCondition(
        query_schema_id_in_source_id=_optional_bool(
            record.get("query_schema_id_in_source_id"),
            field="query_schema_id_in_source_id",
            path=path,
        ),
        any_query_fields_in_matched_terms=_optional_bool(
            record.get("any_query_fields_in_matched_terms"),
            field="any_query_fields_in_matched_terms",
            path=path,
        ),
        query_detected_format_present=_optional_bool(
            record.get("query_detected_format_present"),
            field="query_detected_format_present",
            path=path,
        ),
        filter_clinical_domain_matches_chunk=_optional_bool(
            record.get("filter_clinical_domain_matches_chunk"),
            field="filter_clinical_domain_matches_chunk",
            path=path,
        ),
        chunk_trust_levels=_enum_values(
            record.get("chunk_trust_levels"),
            field="chunk_trust_levels",
            path=path,
            enum_type=TrustLevel,
        ),
        chunk_source_types=_enum_values(
            record.get("chunk_source_types"),
            field="chunk_source_types",
            path=path,
            enum_type=EvidenceSourceType,
        ),
        chunk_clinical_domains=_optional_text_tuple(
            record.get("chunk_clinical_domains"),
            field="chunk_clinical_domains",
            path=path,
        ),
        chunk_standard_systems=_optional_text_tuple(
            record.get("chunk_standard_systems"),
            field="chunk_standard_systems",
            path=path,
        ),
        any_matched_terms=_optional_text_tuple(
            record.get("any_matched_terms"),
            field="any_matched_terms",
            path=path,
        ),
        any_concepts=_optional_text_tuple(record.get("any_concepts"), field="any_concepts", path=path),
        any_rule_ids=_optional_text_tuple(record.get("any_rule_ids"), field="any_rule_ids", path=path),
    )
    if not _ranking_condition_has_criterion(condition):
        raise ValueError(
            f"Invalid ranking boost registry at {path}: condition must include at least one criterion"
        )
    return condition


def _ranking_condition_has_criterion(condition: RankingBoostCondition) -> bool:
    return any(
        (
            condition.query_schema_id_in_source_id,
            condition.any_query_fields_in_matched_terms,
            condition.query_detected_format_present,
            condition.filter_clinical_domain_matches_chunk,
            condition.chunk_trust_levels,
            condition.chunk_source_types,
            condition.chunk_standard_systems,
            condition.any_matched_terms,
            condition.any_concepts,
            condition.any_rule_ids,
        )
    )


def _ranking_boost_weight(value: Any, *, path: Path) -> float:
    try:
        weight = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid ranking boost registry at {path}: weight must be a number") from exc
    if weight < 0.0 or weight > 1.0:
        raise ValueError(f"Invalid ranking boost registry at {path}: weight must be between 0 and 1")
    return weight


def _optional_bool(value: Any, *, field: str, path: Path) -> bool:
    if value is None:
        return False
    if not isinstance(value, bool):
        raise ValueError(f"Invalid ranking boost registry at {path}: {field} must be a boolean")
    return value


def _enum_values(value: Any, *, field: str, path: Path, enum_type: Any) -> tuple[str, ...]:
    values = _optional_text_tuple(value, field=field, path=path)
    normalized: list[str] = []
    for item in values:
        try:
            normalized.append(enum_type(item).value)
        except ValueError as exc:
            raise ValueError(
                f"Invalid ranking boost registry at {path}: unsupported {field} value {item}"
            ) from exc
    return tuple(normalized)


def _optional_text_tuple(value: Any, *, field: str, path: Path) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"Invalid ranking boost registry at {path}: {field} must be a list")
    return tuple(
        normalized
        for item in value
        for normalized in [" ".join(str(item).split())]
        if normalized
    )


def _required_ranking_boost_text(value: Any, *, field: str, path: Path) -> str:
    text = " ".join(str(value).split())
    if not text:
        raise ValueError(f"Invalid ranking boost registry at {path}: {field} cannot be blank")
    return text


def _ensure_unique_ranking_boost_rule_ids(
    rules: tuple[RankingBoostRule, ...],
    *,
    path: Path,
) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for rule in rules:
        if rule.rule_id in seen:
            duplicates.add(rule.rule_id)
        seen.add(rule.rule_id)
    if duplicates:
        duplicate_text = ", ".join(sorted(duplicates))
        raise ValueError(
            f"Invalid ranking boost registry at {path}: duplicate rule_id {duplicate_text}"
        )


def hit_source_locator_from_chunk(
    chunk: KnowledgeChunk,
    *,
    applied_boost_rules: list[AppliedRankingBoost],
    matched_terms: list[str],
    query_analysis: RetrievalQueryAnalysis,
) -> dict[str, Any]:
    locator = dict(chunk.locator)
    if applied_boost_rules:
        locator["ranking_boost_rules"] = [rule.rule_id for rule in applied_boost_rules]
        locator["ranking_boosts"] = [
            rule.as_locator_payload()
            for rule in applied_boost_rules
        ]
    aspect_matches = _query_aspect_matches_for_chunk(
        chunk,
        matched_terms=matched_terms,
        query_analysis=query_analysis,
    )
    if aspect_matches:
        locator["query_aspect_matches"] = aspect_matches
    concept_matches = _concept_matches_for_chunk(
        chunk,
        matched_terms=matched_terms,
        query_analysis=query_analysis,
    )
    if concept_matches:
        locator["concept_matches"] = concept_matches
    return locator


def _concept_matches_for_chunk(
    chunk: KnowledgeChunk,
    *,
    matched_terms: list[str],
    query_analysis: RetrievalQueryAnalysis,
) -> list[dict[str, Any]]:
    if not query_analysis.concept_candidates:
        return []
    haystack = _concept_match_haystack(chunk)
    token_set = set(tokenize(haystack))
    matched_term_set = set(matched_terms)
    matches: list[dict[str, Any]] = []
    for candidate in query_analysis.concept_candidates:
        matched_fields: list[str] = []
        matched_aliases = [
            alias
            for alias in candidate.matched_aliases
            if _concept_term_matches(alias, haystack=haystack, tokens=token_set)
        ]
        candidate_terms = [
            candidate.display_name,
            candidate.code or "",
            candidate.concept_id,
            *candidate.matched_aliases,
        ]
        matched_terms_for_candidate = sorted(
            {
                term
                for term in matched_term_set
                if any(
                    _concept_term_matches(
                        concept_term,
                        haystack=term,
                        tokens={term},
                    )
                    for concept_term in candidate_terms
                    if concept_term
                )
            }
        )
        if chunk.standard_system and chunk.standard_system == candidate.standard_system:
            matched_fields.append("standard_system")
        if candidate.code and _concept_term_matches(
            candidate.code,
            haystack=haystack,
            tokens=token_set,
        ):
            matched_fields.append("code")
        if _concept_term_matches(
            candidate.display_name,
            haystack=haystack,
            tokens=token_set,
        ):
            matched_fields.append("display_name")
        if matched_aliases:
            matched_fields.append("alias")
        if matched_terms_for_candidate:
            matched_fields.append("matched_term")
        if not matched_fields:
            continue
        matches.append(
            {
                "concept_id": candidate.concept_id,
                "display_name": candidate.display_name,
                "standard_system": candidate.standard_system,
                "code": candidate.code,
                "clinical_domain": candidate.clinical_domain,
                "confidence": candidate.confidence,
                "matched_aliases": matched_aliases[:6],
                "matched_fields": sorted(set(matched_fields)),
                "matched_terms": matched_terms_for_candidate[:8],
                "reason": (
                    f"Evidence supports detected {candidate.standard_system} concept "
                    f"{candidate.display_name}."
                ),
            }
        )
    return matches


def _concept_match_haystack(chunk: KnowledgeChunk) -> str:
    return " ".join(
        [
            chunk.chunk_id,
            chunk.source_id,
            chunk.title,
            chunk.content,
            chunk.clinical_domain or "",
            chunk.standard_system or "",
            json.dumps(chunk.locator, default=str, sort_keys=True),
            json.dumps(chunk.metadata, default=str, sort_keys=True),
        ]
    ).lower()


def _concept_term_matches(term: str, *, haystack: str, tokens: set[str]) -> bool:
    normalized = " ".join(str(term).lower().split())
    if not normalized:
        return False
    if " " in normalized:
        return normalized in haystack
    return normalized in tokens or normalized in haystack


def _query_aspect_matches_for_chunk(
    chunk: KnowledgeChunk,
    *,
    matched_terms: list[str],
    query_analysis: RetrievalQueryAnalysis,
) -> list[dict[str, Any]]:
    matches = [
        match
        for aspect in query_analysis.query_aspects
        for match in [_query_aspect_match_for_chunk(chunk, aspect, matched_terms)]
        if match is not None
    ]
    matches.sort(key=lambda item: (item["priority"], item["aspect_id"]))
    return matches


def _query_aspect_match_for_chunk(
    chunk: KnowledgeChunk,
    aspect: RetrievalQueryAspect,
    matched_terms: list[str],
) -> dict[str, Any] | None:
    supported_filters = {
        field: value
        for field, value in aspect.suggested_filters.items()
        if field in {"clinical_domain", "standard_system", "source_type", "trust_level", "source_id"}
    }
    matched_filters = (
        dict(supported_filters)
        if supported_filters and _chunk_matches_filters(chunk, supported_filters)
        else {}
    )
    matched_suggested_terms = _matched_aspect_terms(chunk, aspect, matched_terms)
    if not matched_filters and not matched_suggested_terms:
        return None
    reasons: list[str] = []
    if matched_filters:
        reasons.append(f"metadata matched {_format_filter_map(matched_filters)}")
    if matched_suggested_terms:
        reasons.append(f"term matched {', '.join(matched_suggested_terms[:4])}")
    return {
        "aspect_id": aspect.aspect_id,
        "label": aspect.label,
        "priority": aspect.priority,
        "rule_id": aspect.rule_id,
        "matched_filters": matched_filters,
        "matched_terms": matched_suggested_terms,
        "reason": "; ".join(reasons),
    }


def _matched_aspect_terms(
    chunk: KnowledgeChunk,
    aspect: RetrievalQueryAspect,
    matched_terms: list[str],
) -> list[str]:
    if not aspect.suggested_terms:
        return []
    chunk_text = f"{chunk.title} {chunk.content} {chunk.source_id}".lower()
    matched_token_set = {term.lower() for term in matched_terms}
    matched: list[str] = []
    for term in aspect.suggested_terms:
        term_text = term.lower()
        term_tokens = set(tokenize(term_text))
        if term_text in chunk_text or (term_tokens and term_tokens.intersection(matched_token_set)):
            matched.append(term)
    return _dedupe_strings(matched)


def _reranker_enabled(reranker: Any | None) -> bool:
    return bool(reranker and getattr(reranker, "enabled", False))


def _reranker_metadata(reranker: Any | None) -> dict[str, Any]:
    if reranker is None:
        return {"provider": "none", "model": "none", "enabled": False}
    metadata = getattr(reranker, "metadata", None)
    if callable(metadata):
        return metadata()
    return {
        "provider": getattr(reranker, "provider_name", "unknown"),
        "model": getattr(reranker, "model", "unknown"),
        "enabled": _reranker_enabled(reranker),
    }


def _select_diverse_hits(
    ranked_hits: list[tuple[KnowledgeChunk, RetrievalHit]],
    *,
    top_k: int,
    enabled: bool,
    lambda_mult: float,
) -> tuple[list[tuple[KnowledgeChunk, RetrievalHit]], dict[str, Any]]:
    original_ranks = {
        hit.evidence.evidence_id: rank
        for rank, (_, hit) in enumerate(ranked_hits, start=1)
    }
    relevance = _normalized_hit_relevance(ranked_hits) if ranked_hits else {}
    if not enabled or top_k <= 1 or len(ranked_hits) <= 1:
        selected = ranked_hits[:top_k]
        selection_details = _score_order_selection_details(
            selected,
            relevance=relevance,
            original_ranks=original_ranks,
        )
        return selected, _diversity_metadata(
            ranked_hits,
            selected,
            enabled=enabled,
            lambda_mult=lambda_mult,
            selection_details=selection_details,
        )

    clamped_lambda = max(0.0, min(1.0, lambda_mult))
    candidates = list(ranked_hits)
    selected: list[tuple[KnowledgeChunk, RetrievalHit]] = [candidates.pop(0)]
    selection_details = [
        _diversity_selection_detail(
            selected[0],
            selected_rank=1,
            original_rank=original_ranks[selected[0][1].evidence.evidence_id],
            relevance_score=relevance[selected[0][1].evidence.evidence_id],
            redundancy_score=0.0,
            selection_score=relevance[selected[0][1].evidence.evidence_id],
            reason="Top-ranked hit selected as the initial MMR seed.",
        )
    ]

    while candidates and len(selected) < top_k:
        best_index = 0
        best_score = float("-inf")
        best_redundancy = 0.0
        for index, candidate in enumerate(candidates):
            chunk, hit = candidate
            redundancy = max(
                _chunk_redundancy(chunk, selected_chunk)
                for selected_chunk, _ in selected
            )
            mmr_score = (
                clamped_lambda * relevance[hit.evidence.evidence_id]
                - (1.0 - clamped_lambda) * redundancy
            )
            if mmr_score > best_score:
                best_score = mmr_score
                best_index = index
                best_redundancy = redundancy
        selected_candidate = candidates.pop(best_index)
        selected.append(selected_candidate)
        _, selected_hit = selected_candidate
        selection_details.append(
            _diversity_selection_detail(
                selected_candidate,
                selected_rank=len(selected),
                original_rank=original_ranks[selected_hit.evidence.evidence_id],
                relevance_score=relevance[selected_hit.evidence.evidence_id],
                redundancy_score=best_redundancy,
                selection_score=best_score,
                reason=_mmr_selection_reason(best_redundancy),
            )
        )

    return selected, _diversity_metadata(
        ranked_hits,
        selected,
        enabled=enabled,
        lambda_mult=clamped_lambda,
        selection_details=selection_details,
    )


def _score_order_selection_details(
    selected: list[tuple[KnowledgeChunk, RetrievalHit]],
    *,
    relevance: dict[str, float],
    original_ranks: dict[str, int],
) -> list[RetrievalDiversitySelection]:
    return [
        _diversity_selection_detail(
            candidate,
            selected_rank=index,
            original_rank=original_ranks[hit.evidence.evidence_id],
            relevance_score=relevance.get(hit.evidence.evidence_id, 1.0),
            redundancy_score=0.0,
            selection_score=relevance.get(hit.evidence.evidence_id, 1.0),
            reason="Selected by score order because diversity selection was not applied.",
        )
        for index, candidate in enumerate(selected, start=1)
        for _, hit in [candidate]
    ]


def _diversity_selection_detail(
    candidate: tuple[KnowledgeChunk, RetrievalHit],
    *,
    selected_rank: int,
    original_rank: int,
    relevance_score: float,
    redundancy_score: float,
    selection_score: float,
    reason: str,
) -> RetrievalDiversitySelection:
    chunk, hit = candidate
    return RetrievalDiversitySelection(
        evidence_id=hit.evidence.evidence_id,
        source_id=chunk.source_id,
        selected_rank=selected_rank,
        original_rank=original_rank,
        relevance_score=round(relevance_score, 6),
        redundancy_score=round(redundancy_score, 6),
        selection_score=round(selection_score, 6),
        reason=reason,
    )


def _mmr_selection_reason(redundancy_score: float) -> str:
    if redundancy_score >= 0.999:
        return "Selected despite same-source redundancy because relevance remained strongest."
    if redundancy_score > 0:
        return "Selected after balancing relevance against overlap with already selected evidence."
    return "Selected from a new source with no measured redundancy penalty."


def _normalized_hit_relevance(
    ranked_hits: list[tuple[KnowledgeChunk, RetrievalHit]],
) -> dict[str, float]:
    scores = [hit.score for _, hit in ranked_hits]
    minimum = min(scores)
    maximum = max(scores)
    if maximum == minimum:
        return {hit.evidence.evidence_id: 1.0 for _, hit in ranked_hits}
    span = maximum - minimum
    return {
        hit.evidence.evidence_id: (hit.score - minimum) / span
        for _, hit in ranked_hits
    }


def _chunk_redundancy(left: KnowledgeChunk, right: KnowledgeChunk) -> float:
    source_similarity = 1.0 if left.source_id == right.source_id else 0.0
    left_tokens = set(tokenize(f"{left.title} {left.content}"))
    right_tokens = set(tokenize(f"{right.title} {right.content}"))
    token_similarity = _jaccard_similarity(left_tokens, right_tokens)
    return max(source_similarity, token_similarity)


def _jaccard_similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left.intersection(right)) / len(left.union(right))


def _diversity_metadata(
    ranked_hits: list[tuple[KnowledgeChunk, RetrievalHit]],
    selected: list[tuple[KnowledgeChunk, RetrievalHit]],
    *,
    enabled: bool,
    lambda_mult: float,
    selection_details: list[RetrievalDiversitySelection],
) -> dict[str, Any]:
    candidate_sources = {chunk.source_id for chunk, _ in ranked_hits}
    selected_sources = [chunk.source_id for chunk, _ in selected]
    return {
        "enabled": enabled,
        "selection_mode": "mmr_source_diversity" if enabled else "score_order",
        "lambda": round(lambda_mult, 4),
        "candidate_source_count": len(candidate_sources),
        "selected_source_count": len(set(selected_sources)),
        "duplicate_selected_source_count": len(selected_sources) - len(set(selected_sources)),
        "selected_hits": [
            detail.model_dump(mode="json")
            for detail in selection_details
        ],
    }


def diversity_summary_from_metadata(metadata: dict[str, Any]) -> RetrievalDiversitySummary:
    """Build the first-class diversity contract from legacy handoff metadata."""

    selected_hits = [
        item
        if isinstance(item, RetrievalDiversitySelection)
        else RetrievalDiversitySelection.model_validate(item)
        for item in metadata.get("selected_hits", [])
    ]
    lambda_value = metadata.get("lambda")
    return RetrievalDiversitySummary(
        enabled=bool(metadata.get("enabled")),
        selection_mode=str(metadata.get("selection_mode") or "score_order"),
        lambda_value=(
            float(lambda_value)
            if isinstance(lambda_value, (int, float)) and not isinstance(lambda_value, bool)
            else None
        ),
        candidate_source_count=int(metadata.get("candidate_source_count") or 0),
        selected_source_count=int(metadata.get("selected_source_count") or 0),
        duplicate_selected_source_count=int(
            metadata.get("duplicate_selected_source_count") or 0
        ),
        selected_hits=selected_hits,
    )
