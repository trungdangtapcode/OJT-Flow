"""Deterministic clinical query analysis for retrieval."""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from ojtflow.core.contracts.retrieval import (
    RetrievalConceptCandidate,
    RetrievalFilterSuggestion,
    RetrievalPlan,
    RetrievalPlanCoverageSummary,
    RetrievalPlanRiskSignal,
    RetrievalPlanTaskSummary,
    RetrievalQuery,
    RetrievalQueryAnalysis,
    RetrievalQueryAspect,
    RetrievalQueryDiagnostic,
    RetrievalQueryProfile,
    RetrievalQueryRoute,
    RetrievalRouteBudget,
    RetrievalQueryVariant,
    RetrievalSearchHint,
    RetrievalSearchTask,
)

QUERY_TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9_./%-]*", re.IGNORECASE)
DEFAULT_MEDICAL_CONCEPT_REGISTRY = (
    Path(__file__).resolve().parents[4] / "knowledge" / "terminologies" / "medical_concepts.json"
)
DEFAULT_QUERY_EXPANSION_RULE_REGISTRY = (
    Path(__file__).resolve().parents[4] / "knowledge" / "retrieval" / "query_expansion_rules.json"
)
DEFAULT_FILTER_SUGGESTION_RULE_REGISTRY = (
    Path(__file__).resolve().parents[4] / "knowledge" / "retrieval" / "filter_suggestion_rules.json"
)
DEFAULT_QUERY_DIAGNOSTIC_RULE_REGISTRY = (
    Path(__file__).resolve().parents[4] / "knowledge" / "retrieval" / "query_diagnostic_rules.json"
)
DEFAULT_QUERY_PROFILE_RULE_REGISTRY = (
    Path(__file__).resolve().parents[4] / "knowledge" / "retrieval" / "query_profile_rules.json"
)
DEFAULT_QUERY_ASPECT_RULE_REGISTRY = (
    Path(__file__).resolve().parents[4] / "knowledge" / "retrieval" / "query_aspect_rules.json"
)
DEFAULT_QUERY_TRANSFORMATION_RULE_REGISTRY = (
    Path(__file__).resolve().parents[4]
    / "knowledge"
    / "retrieval"
    / "query_transformation_rules.json"
)
DEFAULT_QUERY_ROUTE_RULE_REGISTRY = (
    Path(__file__).resolve().parents[4]
    / "knowledge"
    / "retrieval"
    / "query_route_rules.json"
)
DEFAULT_SEARCH_HINT_TARGET_REGISTRY = (
    Path(__file__).resolve().parents[4] / "knowledge" / "retrieval" / "search_hint_targets.json"
)
DEFAULT_FHIR_SEARCH_PARAMETER_REGISTRY = (
    Path(__file__).resolve().parents[4]
    / "knowledge"
    / "terminologies"
    / "fhir_search_parameters.json"
)

SUPPORTED_FILTER_SUGGESTION_FIELDS = {
    "clinical_domain",
    "source_id",
    "source_type",
    "standard_system",
    "trust_level",
}


@dataclass(frozen=True)
class QueryExpansionRule:
    """One auditable query expansion rule."""

    rule_id: str
    concept: str
    triggers: tuple[str, ...]
    expanded_terms: tuple[str, ...]
    standards: tuple[str, ...]
    variant: str


@dataclass(frozen=True)
class FilterSuggestionMatch:
    """Matcher for a metadata filter suggestion rule."""

    any_concepts: tuple[str, ...] = ()
    any_standards: tuple[str, ...] = ()
    any_rule_ids: tuple[str, ...] = ()
    any_candidate_domains: tuple[str, ...] = ()
    any_candidate_standards: tuple[str, ...] = ()


@dataclass(frozen=True)
class FilterSuggestionRule:
    """One auditable metadata filter suggestion rule."""

    rule_id: str
    field: str
    value: str
    reason: str
    confidence: float
    match: FilterSuggestionMatch


@dataclass(frozen=True)
class QueryDiagnosticRule:
    """One data-driven query-quality diagnostic rule."""

    rule_id: str
    condition: str
    code: str
    severity: str
    message: str
    suggested_action: str


@dataclass(frozen=True)
class QueryProfileMatch:
    """Matcher for a data-driven query profile rule."""

    any_concepts: tuple[str, ...] = ()
    any_standards: tuple[str, ...] = ()
    any_rule_ids: tuple[str, ...] = ()
    any_tokens: tuple[str, ...] = ()
    any_candidate_domains: tuple[str, ...] = ()
    any_candidate_standards: tuple[str, ...] = ()


@dataclass(frozen=True)
class QueryProfileRule:
    """One data-driven query profile and route hint."""

    rule_id: str
    profile_id: str
    label: str
    route: str
    complexity: str
    retrieval_mode: str
    description: str
    priority: int
    suggested_filters: dict[str, str]
    match: QueryProfileMatch


@dataclass(frozen=True)
class QueryAspectMatch:
    """Matcher for a data-driven query aspect rule."""

    any_concepts: tuple[str, ...] = ()
    any_standards: tuple[str, ...] = ()
    any_rule_ids: tuple[str, ...] = ()
    any_tokens: tuple[str, ...] = ()
    any_candidate_domains: tuple[str, ...] = ()
    any_candidate_standards: tuple[str, ...] = ()


@dataclass(frozen=True)
class QueryAspectRule:
    """One data-driven decomposed search aspect."""

    rule_id: str
    aspect_id: str
    label: str
    question: str
    rationale: str
    priority: int
    suggested_terms: tuple[str, ...]
    suggested_filters: dict[str, str]
    match: QueryAspectMatch


@dataclass(frozen=True)
class QueryTransformationMatch:
    """Matcher for a data-driven query transformation rule."""

    any_concepts: tuple[str, ...] = ()
    any_standards: tuple[str, ...] = ()
    any_rule_ids: tuple[str, ...] = ()
    any_tokens: tuple[str, ...] = ()
    any_profile_ids: tuple[str, ...] = ()
    any_profile_routes: tuple[str, ...] = ()
    any_candidate_domains: tuple[str, ...] = ()
    any_candidate_standards: tuple[str, ...] = ()


@dataclass(frozen=True)
class QueryTransformationRule:
    """One rewrite, step-back, multi-query, or optional HyDE transformation."""

    rule_id: str
    strategy: str
    reason: str
    variant_template: str
    priority: int
    enabled: bool
    requires_hyde_enabled: bool
    match: QueryTransformationMatch


@dataclass(frozen=True)
class QueryRouteMatch:
    """Matcher for a data-driven retrieval strategy route."""

    any_profile_ids: tuple[str, ...] = ()
    any_profile_routes: tuple[str, ...] = ()
    any_retrieval_modes: tuple[str, ...] = ()
    any_detected_formats: tuple[str, ...] = ()
    any_resource_types: tuple[str, ...] = ()
    any_filter_keys: tuple[str, ...] = ()
    any_filter_values: tuple[str, ...] = ()
    any_diagnostic_codes: tuple[str, ...] = ()
    any_concepts: tuple[str, ...] = ()
    any_standards: tuple[str, ...] = ()
    any_tokens: tuple[str, ...] = ()
    require_fields: bool = False


@dataclass(frozen=True)
class QueryRouteRule:
    """One data-driven strategy selection rule."""

    rule_id: str
    route_id: str
    strategy_id: str
    label: str
    retrieval_mode: str
    rationale: str
    priority: int
    confidence: float
    suggested_filters: dict[str, str]
    risk_controls: tuple[str, ...]
    budget: RetrievalRouteBudget | None
    match: QueryRouteMatch


@dataclass(frozen=True)
class SearchHintTarget:
    """Operator-facing metadata for one external search target."""

    target: str
    label: str
    rationale: str
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class FhirSearchParameter:
    """Curated FHIR search parameter hint loaded from trusted registry data."""

    name: str
    parameter_type: str
    target_field: str
    example: str
    standard_systems: tuple[str, ...]


@dataclass(frozen=True)
class FhirSearchResource:
    """FHIR resource-level search parameter seed."""

    resource_type: str
    clinical_domain: str | None
    parameters: tuple[FhirSearchParameter, ...]


def analyze_query(query: RetrievalQuery) -> RetrievalQueryAnalysis:
    """Return deterministic query analysis and healthcare-aware variants."""

    base_variants = _base_query_variant_details(query)
    haystack = _query_haystack(query)
    tokens = set(_tokens(haystack))
    concept_candidates = _concept_candidates(haystack=haystack, tokens=tokens)
    matched_rules = [
        rule
        for rule in _query_expansion_rules()
        if _rule_matches(rule, haystack=haystack, tokens=tokens)
    ]
    concepts = _dedupe(
        [
            *(rule.concept for rule in matched_rules),
            *(candidate.concept_id for candidate in concept_candidates),
        ]
    )
    expanded_terms = _dedupe(
        [
            *(term for rule in matched_rules for term in rule.expanded_terms),
            *(candidate.display_name for candidate in concept_candidates),
            *(alias for candidate in concept_candidates for alias in candidate.matched_aliases),
        ]
    )
    standards = _dedupe(
        [
            *(standard for rule in matched_rules for standard in rule.standards),
            *(candidate.standard_system for candidate in concept_candidates),
        ]
    )
    rule_ids = _dedupe(rule.rule_id for rule in matched_rules)
    candidate_domains = _candidate_domains(concept_candidates)
    candidate_standards = _candidate_standards(concept_candidates)
    query_profile = _query_profile(
        concepts=concepts,
        standards=standards,
        rule_ids=rule_ids,
        tokens=tokens,
        candidate_domains=candidate_domains,
        candidate_standards=candidate_standards,
    )
    query_aspects = _query_aspects(
        concepts=concepts,
        standards=standards,
        rule_ids=rule_ids,
        tokens=tokens,
        candidate_domains=candidate_domains,
        candidate_standards=candidate_standards,
    )
    transformation_variants = _query_transformation_variant_details(
        query,
        concepts=concepts,
        standards=standards,
        rule_ids=rule_ids,
        tokens=tokens,
        candidate_domains=candidate_domains,
        candidate_standards=candidate_standards,
        query_profile=query_profile,
        query_aspects=query_aspects,
    )
    variant_details = _dedupe_query_variant_details(
        [
            *base_variants,
            *transformation_variants,
            *(
                RetrievalQueryVariant(
                    variant=rule.variant,
                    source="query_expansion_rule",
                    reason=f"Matched query expansion rule {rule.rule_id}.",
                    metadata={
                        "rule_id": rule.rule_id,
                        "concept": rule.concept,
                        "standards": list(rule.standards),
                    },
                )
                for rule in matched_rules
            ),
            *_concept_candidate_variant_details(concept_candidates),
            *_standards_variant_details(standards),
            *_expanded_terms_variant_details(expanded_terms),
            *_query_aspect_variant_details(query_aspects),
        ]
    )
    variants = [detail.variant for detail in variant_details]
    filter_suggestions = _filter_suggestions(
        query,
        concepts,
        standards,
        rule_ids,
        concept_candidates,
    )
    diagnostics = _query_diagnostics(
        query,
        concepts=concepts,
        standards=standards,
        tokens=tokens,
    )
    search_hints = _search_hints(
        query,
        concepts=concepts,
        standards=standards,
        concept_candidates=concept_candidates,
    )
    query_route = _query_route(
        query,
        concepts=concepts,
        standards=standards,
        tokens=tokens,
        query_profile=query_profile,
        diagnostics=diagnostics,
    )
    return RetrievalQueryAnalysis(
        detected_concepts=concepts,
        concept_candidates=concept_candidates,
        expanded_terms=expanded_terms,
        standards=standards,
        rule_ids=rule_ids,
        query_variants=variants,
        query_variant_details=variant_details,
        filter_suggestions=filter_suggestions,
        diagnostics=diagnostics,
        search_hints=search_hints,
        query_profile=query_profile,
        query_route=query_route,
        query_aspects=query_aspects,
        retrieval_tasks=_retrieval_tasks(
            query,
            aspects=query_aspects,
            hints=search_hints,
            variants=variant_details,
            filter_suggestions=filter_suggestions,
            standards=standards,
        ),
    )


def build_retrieval_plan(query: RetrievalQuery) -> RetrievalPlan:
    """Build a plan-only retrieval response from deterministic query analysis."""

    analysis = analyze_query(query)
    profile_label = analysis.query_profile.label if analysis.query_profile else "standard retrieval"
    coverage_summary = _plan_coverage_summary(analysis)
    return RetrievalPlan(
        query=query,
        query_analysis=analysis,
        coverage_summary=coverage_summary,
        task_summary=_plan_task_summary(analysis),
        risk_signals=_plan_risk_signals(analysis, coverage_summary),
        search_signature="pending",
        summary=(
            f"Plan uses {profile_label} with {len(analysis.query_aspects)} "
            f"search aspect(s) and {len(analysis.search_hints)} medical search hint(s)."
        ),
    )


def _plan_risk_signals(
    analysis: RetrievalQueryAnalysis,
    coverage_summary: RetrievalPlanCoverageSummary,
) -> list[RetrievalPlanRiskSignal]:
    signals: list[RetrievalPlanRiskSignal] = []
    if coverage_summary.required_local_task_count == 0:
        signals.append(
            RetrievalPlanRiskSignal(
                code="no_required_local_task",
                severity="warning",
                message="The retrieval plan has no required local corpus task.",
                suggested_action=(
                    "Add a healthcare standard, schema, resource type, field list, or clinical domain "
                    "so the trusted corpus search has a concrete coverage target."
                ),
                source="coverage_summary",
                metadata={
                    "local_task_count": coverage_summary.local_task_count,
                    "external_task_count": coverage_summary.external_task_count,
                },
            )
        )
    if coverage_summary.standard_count == 0:
        signals.append(
            RetrievalPlanRiskSignal(
                code="no_standard_inferred",
                severity="warning",
                message="No healthcare standard was inferred for this plan.",
                suggested_action=(
                    "Specify FHIR, LOINC, UCUM, RxNorm, OMOP, MeSH, openFDA, or a known schema "
                    "when those standards are relevant."
                ),
                source="coverage_summary",
                metadata={"detected_concepts": list(analysis.detected_concepts)},
            )
        )
    if coverage_summary.filter_count == 0 and coverage_summary.ready:
        signals.append(
            RetrievalPlanRiskSignal(
                code="unscoped_ready_plan",
                severity="info",
                message="The plan is ready but has no suggested metadata filters.",
                suggested_action=(
                    "Run the broad search first, then apply evidence facets only if coverage is too noisy."
                ),
                source="coverage_summary",
            )
        )
    for diagnostic in analysis.diagnostics:
        if diagnostic.severity == "info":
            continue
        signals.append(
            RetrievalPlanRiskSignal(
                code=f"diagnostic_{diagnostic.code}",
                severity=diagnostic.severity,
                message=diagnostic.message,
                suggested_action=diagnostic.suggested_action,
                source="query_diagnostic",
                metadata=dict(diagnostic.metadata),
            )
        )
    signals.sort(key=lambda signal: (_risk_severity_rank(signal.severity), signal.code))
    return signals[:6]


def _risk_severity_rank(severity: str) -> int:
    if severity in {"destructive", "error"}:
        return 0
    if severity == "warning":
        return 1
    if severity == "info":
        return 2
    return 3


def _plan_coverage_summary(analysis: RetrievalQueryAnalysis) -> RetrievalPlanCoverageSummary:
    local_tasks = [task for task in analysis.retrieval_tasks if task.target == "local_corpus"]
    external_tasks = [
        task for task in analysis.retrieval_tasks if task.target == "external_medical_index"
    ]
    standards = _dedupe(
        [
            *analysis.standards,
            *(standard for task in analysis.retrieval_tasks for standard in task.standards),
        ]
    )
    filters = {
        (suggestion.field, suggestion.value)
        for suggestion in analysis.filter_suggestions
        if not suggestion.applied
    }
    filters.update(
        (field, value)
        for task in analysis.retrieval_tasks
        for field, value in task.suggested_filters.items()
    )
    warnings = _dedupe(
        [
            *(
                diagnostic.code
                for diagnostic in analysis.diagnostics
                if diagnostic.severity != "info"
            ),
            *(warning for task in analysis.retrieval_tasks for warning in task.warnings),
        ]
    )
    required_local_task_count = sum(1 for task in local_tasks if task.required)
    ready = required_local_task_count > 0 and bool(standards)
    summary = (
        f"{required_local_task_count}/{len(local_tasks)} required local task(s), "
        f"{len(external_tasks)} external follow-up(s), {len(standards)} standard(s), "
        f"and {len(filters)} suggested filter(s)."
    )
    if not ready:
        summary = (
            "Plan needs more detail before review-grade search: "
            f"{summary}"
        )
    next_action = _plan_coverage_next_action(
        ready=ready,
        required_local_task_count=required_local_task_count,
        external_task_count=len(external_tasks),
        standard_count=len(standards),
        filter_count=len(filters),
    )
    return RetrievalPlanCoverageSummary(
        ready=ready,
        local_task_count=len(local_tasks),
        required_local_task_count=required_local_task_count,
        external_task_count=len(external_tasks),
        standard_count=len(standards),
        filter_count=len(filters),
        standards=standards,
        warnings=warnings,
        next_action=next_action,
        summary=summary,
    )


def _plan_task_summary(analysis: RetrievalQueryAnalysis) -> RetrievalPlanTaskSummary:
    runnable_local = [
        task
        for task in analysis.retrieval_tasks
        if task.target == "local_corpus" and task.action_type == "run_local_search"
    ]
    required_runnable_local = [task for task in runnable_local if task.required]
    external_open = [
        task
        for task in analysis.retrieval_tasks
        if task.target == "external_medical_index" and task.action_type == "open_external_url"
    ]
    external_copy = [
        task
        for task in analysis.retrieval_tasks
        if task.target == "external_medical_index" and task.action_type == "copy_query"
    ]
    blocked_tasks = [
        task
        for task in analysis.retrieval_tasks
        if task.action_type not in {"run_local_search", "open_external_url", "copy_query"}
    ]
    manual_followup_count = len(external_open) + len(external_copy)
    if required_runnable_local:
        primary_action = "Run required local search tasks first, then review external follow-ups."
    elif runnable_local:
        primary_action = "Run the local search task, then review external follow-ups."
    elif manual_followup_count:
        primary_action = "Review external medical search follow-ups before trusting the plan."
    else:
        primary_action = "Add a more specific healthcare query before executing retrieval."
    return RetrievalPlanTaskSummary(
        total_task_count=len(analysis.retrieval_tasks),
        runnable_local_count=len(runnable_local),
        required_runnable_local_count=len(required_runnable_local),
        external_open_count=len(external_open),
        external_copy_count=len(external_copy),
        manual_followup_count=manual_followup_count,
        blocked_task_count=len(blocked_tasks),
        primary_action=primary_action,
        summary=(
            f"{len(runnable_local)} local runnable task(s), "
            f"{manual_followup_count} external/manual follow-up(s), "
            f"and {len(blocked_tasks)} blocked task(s)."
        ),
    )


def _plan_coverage_next_action(
    *,
    ready: bool,
    required_local_task_count: int,
    external_task_count: int,
    standard_count: int,
    filter_count: int,
) -> str:
    if not ready and standard_count == 0:
        return "Add a healthcare standard, schema, resource type, field list, or clinical domain."
    if not ready and required_local_task_count == 0:
        return "Refine the query until the plan has at least one required local corpus task."
    if filter_count > 0:
        return "Review suggested filters, then run the local evidence search."
    if external_task_count > 0:
        return "Run local evidence search, then inspect external follow-up tasks if coverage is incomplete."
    return "Run local evidence search."


def _concept_candidates(
    *,
    haystack: str,
    tokens: set[str],
) -> list[RetrievalConceptCandidate]:
    candidates: list[RetrievalConceptCandidate] = []
    for concept in _medical_concept_registry():
        aliases = _matching_aliases(concept.get("aliases", []), haystack=haystack, tokens=tokens)
        if not aliases:
            continue
        confidence = min(0.96, 0.72 + 0.08 * len(aliases))
        candidates.append(
            RetrievalConceptCandidate(
                concept_id=str(concept["concept_id"]),
                display_name=str(concept["display_name"]),
                standard_system=str(concept["standard_system"]),
                code=_optional_string(concept.get("code")),
                clinical_domain=_optional_string(concept.get("clinical_domain")),
                matched_aliases=aliases,
                confidence=round(confidence, 3),
                source=_optional_string(concept.get("source")),
                metadata=(
                    concept["metadata"]
                    if isinstance(concept.get("metadata"), dict)
                    else {}
                ),
            )
        )
    candidates.sort(key=lambda candidate: (-candidate.confidence, candidate.display_name))
    return candidates


def _candidate_domains(candidates: list[RetrievalConceptCandidate]) -> list[str]:
    return _dedupe(
        candidate.clinical_domain
        for candidate in candidates
        if candidate.clinical_domain
    )


def _candidate_standards(candidates: list[RetrievalConceptCandidate]) -> list[str]:
    return _dedupe(candidate.standard_system for candidate in candidates)


def _concept_candidate_variant_details(
    candidates: list[RetrievalConceptCandidate],
) -> list[RetrievalQueryVariant]:
    return [
        RetrievalQueryVariant(
            variant=" ".join(
                value
                for value in [
                    candidate.display_name,
                    candidate.standard_system,
                    candidate.code or "",
                    " ".join(candidate.matched_aliases),
                    candidate.clinical_domain or "",
                ]
                if value
            ),
            source="concept_registry",
            reason=f"Matched controlled-vocabulary concept {candidate.concept_id}.",
            metadata={
                "concept_id": candidate.concept_id,
                "standard_system": candidate.standard_system,
                "code": candidate.code,
                "confidence": candidate.confidence,
            },
        )
        for candidate in candidates
    ]


def _query_expansion_rules() -> tuple[QueryExpansionRule, ...]:
    path = os.environ.get("OJT_QUERY_EXPANSION_RULES_PATH")
    return _load_query_expansion_rules(path or str(DEFAULT_QUERY_EXPANSION_RULE_REGISTRY))


def _load_query_expansion_rules(path_text: str) -> tuple[QueryExpansionRule, ...]:
    path = Path(path_text)
    if not path.exists():
        return ()
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = raw.get("rules") if isinstance(raw, dict) else None
    if not isinstance(records, list):
        raise ValueError(f"Invalid query expansion registry at {path}: expected rules list")

    rules = tuple(_query_expansion_rule(record, path=path) for record in records)
    _ensure_unique_rule_ids(rules, path=path)
    return rules


def _query_expansion_rule(record: Any, *, path: Path) -> QueryExpansionRule:
    if not isinstance(record, dict):
        raise ValueError(f"Invalid query expansion registry at {path}: rule must be an object")
    required = ("rule_id", "concept", "triggers", "expanded_terms", "standards", "variant")
    missing = [field for field in required if field not in record]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(
            f"Invalid query expansion registry at {path}: missing {missing_text}"
        )
    return QueryExpansionRule(
        rule_id=_required_text(record["rule_id"], field="rule_id", path=path),
        concept=_required_text(record["concept"], field="concept", path=path),
        triggers=_text_tuple(record["triggers"], field="triggers", path=path),
        expanded_terms=_text_tuple(
            record["expanded_terms"],
            field="expanded_terms",
            path=path,
        ),
        standards=_text_tuple(record["standards"], field="standards", path=path),
        variant=_required_text(record["variant"], field="variant", path=path),
    )


def _text_tuple(value: Any, *, field: str, path: Path) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"Invalid query expansion registry at {path}: {field} must be a list")
    items = tuple(
        normalized
        for item in value
        for normalized in [" ".join(str(item).split())]
        if normalized
    )
    if not items:
        raise ValueError(f"Invalid query expansion registry at {path}: {field} cannot be empty")
    return items


def _required_text(value: Any, *, field: str, path: Path) -> str:
    text = " ".join(str(value).split())
    if not text:
        raise ValueError(f"Invalid query expansion registry at {path}: {field} cannot be blank")
    return text


def _ensure_unique_rule_ids(rules: tuple[QueryExpansionRule, ...], *, path: Path) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for rule in rules:
        if rule.rule_id in seen:
            duplicates.add(rule.rule_id)
        seen.add(rule.rule_id)
    if duplicates:
        duplicate_text = ", ".join(sorted(duplicates))
        raise ValueError(
            f"Invalid query expansion registry at {path}: duplicate rule_id {duplicate_text}"
        )


def _filter_suggestion_rules() -> tuple[FilterSuggestionRule, ...]:
    path = os.environ.get("OJT_FILTER_SUGGESTION_RULES_PATH")
    return _load_filter_suggestion_rules(path or str(DEFAULT_FILTER_SUGGESTION_RULE_REGISTRY))


def _load_filter_suggestion_rules(path_text: str) -> tuple[FilterSuggestionRule, ...]:
    path = Path(path_text)
    if not path.exists():
        return ()
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = raw.get("rules") if isinstance(raw, dict) else None
    if not isinstance(records, list):
        raise ValueError(f"Invalid filter suggestion registry at {path}: expected rules list")

    rules = tuple(_filter_suggestion_rule(record, path=path) for record in records)
    _ensure_unique_filter_suggestion_rule_ids(rules, path=path)
    return rules


def _filter_suggestion_rule(record: Any, *, path: Path) -> FilterSuggestionRule:
    if not isinstance(record, dict):
        raise ValueError(f"Invalid filter suggestion registry at {path}: rule must be an object")
    required = ("rule_id", "field", "value", "reason", "confidence", "match")
    missing = [field for field in required if field not in record]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(
            f"Invalid filter suggestion registry at {path}: missing {missing_text}"
        )
    field = _required_filter_suggestion_text(record["field"], field="field", path=path)
    if field not in SUPPORTED_FILTER_SUGGESTION_FIELDS:
        allowed = ", ".join(sorted(SUPPORTED_FILTER_SUGGESTION_FIELDS))
        raise ValueError(
            f"Invalid filter suggestion registry at {path}: field must be one of {allowed}"
        )
    return FilterSuggestionRule(
        rule_id=_required_filter_suggestion_text(record["rule_id"], field="rule_id", path=path),
        field=field,
        value=_required_filter_suggestion_text(record["value"], field="value", path=path),
        reason=_required_filter_suggestion_text(record["reason"], field="reason", path=path),
        confidence=_confidence(record["confidence"], path=path),
        match=_filter_suggestion_match(record["match"], path=path),
    )


def _filter_suggestion_match(record: Any, *, path: Path) -> FilterSuggestionMatch:
    if not isinstance(record, dict):
        raise ValueError(f"Invalid filter suggestion registry at {path}: match must be an object")
    match = FilterSuggestionMatch(
        any_concepts=_optional_filter_suggestion_text_tuple(
            record.get("any_concepts"),
            field="any_concepts",
            path=path,
        ),
        any_standards=_optional_filter_suggestion_text_tuple(
            record.get("any_standards"),
            field="any_standards",
            path=path,
        ),
        any_rule_ids=_optional_filter_suggestion_text_tuple(
            record.get("any_rule_ids"),
            field="any_rule_ids",
            path=path,
        ),
        any_candidate_domains=_optional_filter_suggestion_text_tuple(
            record.get("any_candidate_domains"),
            field="any_candidate_domains",
            path=path,
        ),
        any_candidate_standards=_optional_filter_suggestion_text_tuple(
            record.get("any_candidate_standards"),
            field="any_candidate_standards",
            path=path,
        ),
    )
    if not any(
        (
            match.any_concepts,
            match.any_standards,
            match.any_rule_ids,
            match.any_candidate_domains,
            match.any_candidate_standards,
        )
    ):
        raise ValueError(
            f"Invalid filter suggestion registry at {path}: match must include at least one criterion"
        )
    return match


def _confidence(value: Any, *, path: Path) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid filter suggestion registry at {path}: confidence must be a number"
        ) from exc
    if confidence < 0.0 or confidence > 1.0:
        raise ValueError(
            f"Invalid filter suggestion registry at {path}: confidence must be between 0 and 1"
        )
    return confidence


def _optional_filter_suggestion_text_tuple(
    value: Any,
    *,
    field: str,
    path: Path,
) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"Invalid filter suggestion registry at {path}: {field} must be a list")
    return tuple(
        normalized
        for item in value
        for normalized in [" ".join(str(item).split())]
        if normalized
    )


def _required_filter_suggestion_text(value: Any, *, field: str, path: Path) -> str:
    text = " ".join(str(value).split())
    if not text:
        raise ValueError(f"Invalid filter suggestion registry at {path}: {field} cannot be blank")
    return text


def _ensure_unique_filter_suggestion_rule_ids(
    rules: tuple[FilterSuggestionRule, ...],
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
            f"Invalid filter suggestion registry at {path}: duplicate rule_id {duplicate_text}"
        )


def _query_diagnostic_rules() -> tuple[QueryDiagnosticRule, ...]:
    path = os.environ.get("OJT_QUERY_DIAGNOSTIC_RULES_PATH")
    return _load_query_diagnostic_rules(path or str(DEFAULT_QUERY_DIAGNOSTIC_RULE_REGISTRY))


def _load_query_diagnostic_rules(path_text: str) -> tuple[QueryDiagnosticRule, ...]:
    path = Path(path_text)
    if not path.exists():
        return _default_query_diagnostic_rules()
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = raw.get("rules") if isinstance(raw, dict) else None
    if not isinstance(records, list):
        raise ValueError(f"Invalid query diagnostic registry at {path}: expected rules list")

    rules = tuple(_query_diagnostic_rule(record, path=path) for record in records)
    _ensure_unique_query_diagnostic_rule_ids(rules, path=path)
    return rules


def _query_diagnostic_rule(record: Any, *, path: Path) -> QueryDiagnosticRule:
    if not isinstance(record, dict):
        raise ValueError(f"Invalid query diagnostic registry at {path}: rule must be an object")
    required = ("rule_id", "condition", "code", "severity", "message", "suggested_action")
    missing = [field for field in required if field not in record]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(
            f"Invalid query diagnostic registry at {path}: missing {missing_text}"
        )
    condition = _required_query_diagnostic_text(
        record["condition"],
        field="condition",
        path=path,
    )
    allowed_conditions = {
        "low_specificity_query",
        "no_healthcare_concept_detected",
        "overconstrained_metadata_filters",
        "standard_filter_conflicts_with_query",
    }
    if condition not in allowed_conditions:
        allowed = ", ".join(sorted(allowed_conditions))
        raise ValueError(
            f"Invalid query diagnostic registry at {path}: condition must be one of {allowed}"
        )
    return QueryDiagnosticRule(
        rule_id=_required_query_diagnostic_text(record["rule_id"], field="rule_id", path=path),
        condition=condition,
        code=_required_query_diagnostic_text(record["code"], field="code", path=path),
        severity=_required_query_diagnostic_text(record["severity"], field="severity", path=path),
        message=_required_query_diagnostic_text(record["message"], field="message", path=path),
        suggested_action=_required_query_diagnostic_text(
            record["suggested_action"],
            field="suggested_action",
            path=path,
        ),
    )


def _required_query_diagnostic_text(value: Any, *, field: str, path: Path) -> str:
    text = " ".join(str(value).split())
    if not text:
        raise ValueError(f"Invalid query diagnostic registry at {path}: {field} cannot be blank")
    return text


def _ensure_unique_query_diagnostic_rule_ids(
    rules: tuple[QueryDiagnosticRule, ...],
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
            f"Invalid query diagnostic registry at {path}: duplicate rule_id {duplicate_text}"
        )


def _default_query_diagnostic_rules() -> tuple[QueryDiagnosticRule, ...]:
    return (
        QueryDiagnosticRule(
            rule_id="low_specificity_query",
            condition="low_specificity_query",
            code="low_specificity_query",
            severity="warning",
            message="Retrieval query has limited context for healthcare evidence ranking.",
            suggested_action="Add a schema, resource type, clinical domain, standard, or field list.",
        ),
        QueryDiagnosticRule(
            rule_id="no_healthcare_concept_detected",
            condition="no_healthcare_concept_detected",
            code="no_healthcare_concept_detected",
            severity="info",
            message="No healthcare retrieval concept matched deterministic query rules.",
            suggested_action=(
                "Use explicit terms such as FHIR, LOINC, UCUM, RxNorm, OMOP, MeSH, "
                "lab, unit, medication, literature, or patient identifier when relevant."
            ),
        ),
        QueryDiagnosticRule(
            rule_id="standard_filter_conflicts_with_query",
            condition="standard_filter_conflicts_with_query",
            code="standard_filter_conflicts_with_query",
            severity="warning",
            message=(
                "Applied standard_system={applied_standard} does not match detected "
                "query standards: {suggested_standards}."
            ),
            suggested_action=(
                "Remove the standard filter or choose one of the detected standard filters."
            ),
        ),
        QueryDiagnosticRule(
            rule_id="overconstrained_metadata_filters",
            condition="overconstrained_metadata_filters",
            code="overconstrained_metadata_filters",
            severity="warning",
            message=(
                "Retrieval has {filter_count} active metadata filters "
                "({active_filters}) but limited query context."
            ),
            suggested_action=(
                "Add schema, fields, resource type, format, or clinical terms; otherwise "
                "remove narrow filters before judging evidence coverage."
            ),
        ),
    )


def _query_profile_rules() -> tuple[QueryProfileRule, ...]:
    path = os.environ.get("OJT_QUERY_PROFILE_RULES_PATH")
    return _load_query_profile_rules(path or str(DEFAULT_QUERY_PROFILE_RULE_REGISTRY))


def _load_query_profile_rules(path_text: str) -> tuple[QueryProfileRule, ...]:
    path = Path(path_text)
    if not path.exists():
        return ()
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = raw.get("rules") if isinstance(raw, dict) else None
    if not isinstance(records, list):
        raise ValueError(f"Invalid query profile registry at {path}: expected rules list")

    rules = tuple(_query_profile_rule(record, path=path) for record in records)
    _ensure_unique_query_profile_rule_ids(rules, path=path)
    return rules


def _query_profile_rule(record: Any, *, path: Path) -> QueryProfileRule:
    if not isinstance(record, dict):
        raise ValueError(f"Invalid query profile registry at {path}: rule must be an object")
    required = (
        "rule_id",
        "profile_id",
        "label",
        "route",
        "complexity",
        "retrieval_mode",
        "description",
        "match",
    )
    missing = [field for field in required if field not in record]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"Invalid query profile registry at {path}: missing {missing_text}")
    match = record["match"]
    if not isinstance(match, dict):
        raise ValueError(f"Invalid query profile registry at {path}: match must be an object")
    suggested_filters = record.get("suggested_filters", {})
    if not isinstance(suggested_filters, dict):
        raise ValueError(
            f"Invalid query profile registry at {path}: suggested_filters must be an object"
        )
    return QueryProfileRule(
        rule_id=_required_query_profile_text(record["rule_id"], field="rule_id", path=path),
        profile_id=_required_query_profile_text(
            record["profile_id"],
            field="profile_id",
            path=path,
        ),
        label=_required_query_profile_text(record["label"], field="label", path=path),
        route=_required_query_profile_text(record["route"], field="route", path=path),
        complexity=_required_query_profile_text(
            record["complexity"],
            field="complexity",
            path=path,
        ),
        retrieval_mode=_required_query_profile_text(
            record["retrieval_mode"],
            field="retrieval_mode",
            path=path,
        ),
        description=_required_query_profile_text(
            record["description"],
            field="description",
            path=path,
        ),
        priority=_optional_query_profile_int(record.get("priority"), default=100, path=path),
        suggested_filters={
            _required_query_profile_text(
                key,
                field="suggested_filters key",
                path=path,
            ): _required_query_profile_text(
                value,
                field="suggested_filters value",
                path=path,
            )
            for key, value in suggested_filters.items()
        },
        match=QueryProfileMatch(
            any_concepts=_query_profile_text_tuple(match.get("any_concepts"), path=path),
            any_standards=_query_profile_text_tuple(match.get("any_standards"), path=path),
            any_rule_ids=_query_profile_text_tuple(match.get("any_rule_ids"), path=path),
            any_tokens=_query_profile_text_tuple(match.get("any_tokens"), path=path),
            any_candidate_domains=_query_profile_text_tuple(
                match.get("any_candidate_domains"),
                path=path,
            ),
            any_candidate_standards=_query_profile_text_tuple(
                match.get("any_candidate_standards"),
                path=path,
            ),
        ),
    )


def _required_query_profile_text(value: Any, *, field: str, path: Path) -> str:
    text = " ".join(str(value).split())
    if not text:
        raise ValueError(f"Invalid query profile registry at {path}: {field} cannot be blank")
    return text


def _optional_query_profile_int(value: Any, *, default: int, path: Path) -> int:
    if value is None:
        return default
    if not isinstance(value, int):
        raise ValueError(f"Invalid query profile registry at {path}: priority must be an integer")
    return value


def _query_profile_text_tuple(value: Any, *, path: Path) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"Invalid query profile registry at {path}: match values must be lists")
    return tuple(
        _required_query_profile_text(item, field="match value", path=path) for item in value
    )


def _ensure_unique_query_profile_rule_ids(
    rules: tuple[QueryProfileRule, ...],
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
            f"Invalid query profile registry at {path}: duplicate rule_id {duplicate_text}"
        )


def _query_aspect_rules() -> tuple[QueryAspectRule, ...]:
    path = os.environ.get("OJT_QUERY_ASPECT_RULES_PATH")
    return _load_query_aspect_rules(path or str(DEFAULT_QUERY_ASPECT_RULE_REGISTRY))


def _load_query_aspect_rules(path_text: str) -> tuple[QueryAspectRule, ...]:
    path = Path(path_text)
    if not path.exists():
        return ()
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = raw.get("rules") if isinstance(raw, dict) else None
    if not isinstance(records, list):
        raise ValueError(f"Invalid query aspect registry at {path}: expected rules list")

    rules = tuple(_query_aspect_rule(record, path=path) for record in records)
    _ensure_unique_query_aspect_rule_ids(rules, path=path)
    return rules


def _query_aspect_rule(record: Any, *, path: Path) -> QueryAspectRule:
    if not isinstance(record, dict):
        raise ValueError(f"Invalid query aspect registry at {path}: rule must be an object")
    required = (
        "rule_id",
        "aspect_id",
        "label",
        "question",
        "rationale",
        "match",
    )
    missing = [field for field in required if field not in record]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"Invalid query aspect registry at {path}: missing {missing_text}")
    match = record["match"]
    if not isinstance(match, dict):
        raise ValueError(f"Invalid query aspect registry at {path}: match must be an object")
    aspect_match = QueryAspectMatch(
        any_concepts=_query_aspect_text_tuple(match.get("any_concepts"), path=path),
        any_standards=_query_aspect_text_tuple(match.get("any_standards"), path=path),
        any_rule_ids=_query_aspect_text_tuple(match.get("any_rule_ids"), path=path),
        any_tokens=_query_aspect_text_tuple(match.get("any_tokens"), path=path),
        any_candidate_domains=_query_aspect_text_tuple(
            match.get("any_candidate_domains"),
            path=path,
        ),
        any_candidate_standards=_query_aspect_text_tuple(
            match.get("any_candidate_standards"),
            path=path,
        ),
    )
    if not any(
        (
            aspect_match.any_concepts,
            aspect_match.any_standards,
            aspect_match.any_rule_ids,
            aspect_match.any_tokens,
            aspect_match.any_candidate_domains,
            aspect_match.any_candidate_standards,
        )
    ):
        raise ValueError(
            f"Invalid query aspect registry at {path}: match must include at least one criterion"
        )
    suggested_filters = record.get("suggested_filters", {})
    if not isinstance(suggested_filters, dict):
        raise ValueError(
            f"Invalid query aspect registry at {path}: suggested_filters must be an object"
        )
    return QueryAspectRule(
        rule_id=_required_query_aspect_text(record["rule_id"], field="rule_id", path=path),
        aspect_id=_required_query_aspect_text(
            record["aspect_id"],
            field="aspect_id",
            path=path,
        ),
        label=_required_query_aspect_text(record["label"], field="label", path=path),
        question=_required_query_aspect_text(
            record["question"],
            field="question",
            path=path,
        ),
        rationale=_required_query_aspect_text(
            record["rationale"],
            field="rationale",
            path=path,
        ),
        priority=_optional_query_aspect_int(record.get("priority"), default=100, path=path),
        suggested_terms=_query_aspect_text_tuple(record.get("suggested_terms"), path=path),
        suggested_filters={
            _required_query_aspect_text(
                key,
                field="suggested_filters key",
                path=path,
            ): _required_query_aspect_text(
                value,
                field="suggested_filters value",
                path=path,
            )
            for key, value in suggested_filters.items()
        },
        match=aspect_match,
    )


def _required_query_aspect_text(value: Any, *, field: str, path: Path) -> str:
    text = " ".join(str(value).split())
    if not text:
        raise ValueError(f"Invalid query aspect registry at {path}: {field} cannot be blank")
    return text


def _optional_query_aspect_int(value: Any, *, default: int, path: Path) -> int:
    if value is None:
        return default
    if not isinstance(value, int):
        raise ValueError(f"Invalid query aspect registry at {path}: priority must be an integer")
    if value < 1:
        raise ValueError(f"Invalid query aspect registry at {path}: priority must be positive")
    return value


def _query_aspect_text_tuple(value: Any, *, path: Path) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"Invalid query aspect registry at {path}: match values must be lists")
    return tuple(
        _required_query_aspect_text(item, field="match value", path=path) for item in value
    )


def _ensure_unique_query_aspect_rule_ids(
    rules: tuple[QueryAspectRule, ...],
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
            f"Invalid query aspect registry at {path}: duplicate rule_id {duplicate_text}"
        )


def _query_transformation_rules() -> tuple[QueryTransformationRule, ...]:
    path = os.environ.get("OJT_QUERY_TRANSFORMATION_RULES_PATH")
    return _load_query_transformation_rules(
        path or str(DEFAULT_QUERY_TRANSFORMATION_RULE_REGISTRY)
    )


def _load_query_transformation_rules(path_text: str) -> tuple[QueryTransformationRule, ...]:
    path = Path(path_text)
    if not path.exists():
        return ()
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = raw.get("rules") if isinstance(raw, dict) else None
    if not isinstance(records, list):
        raise ValueError(
            f"Invalid query transformation registry at {path}: expected rules list"
        )
    rules = tuple(_query_transformation_rule(record, path=path) for record in records)
    _ensure_unique_query_transformation_rule_ids(rules, path=path)
    return rules


def _query_transformation_rule(record: Any, *, path: Path) -> QueryTransformationRule:
    if not isinstance(record, dict):
        raise ValueError(
            f"Invalid query transformation registry at {path}: rule must be an object"
        )
    required = ("rule_id", "strategy", "reason", "variant_template", "match")
    missing = [field for field in required if field not in record]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(
            f"Invalid query transformation registry at {path}: missing {missing_text}"
        )
    match = record["match"]
    if not isinstance(match, dict):
        raise ValueError(
            f"Invalid query transformation registry at {path}: match must be an object"
        )
    transformation_match = QueryTransformationMatch(
        any_concepts=_query_transformation_text_tuple(match.get("any_concepts"), path=path),
        any_standards=_query_transformation_text_tuple(match.get("any_standards"), path=path),
        any_rule_ids=_query_transformation_text_tuple(match.get("any_rule_ids"), path=path),
        any_tokens=_query_transformation_text_tuple(match.get("any_tokens"), path=path),
        any_profile_ids=_query_transformation_text_tuple(
            match.get("any_profile_ids"),
            path=path,
        ),
        any_profile_routes=_query_transformation_text_tuple(
            match.get("any_profile_routes"),
            path=path,
        ),
        any_candidate_domains=_query_transformation_text_tuple(
            match.get("any_candidate_domains"),
            path=path,
        ),
        any_candidate_standards=_query_transformation_text_tuple(
            match.get("any_candidate_standards"),
            path=path,
        ),
    )
    if not any(transformation_match.__dict__.values()):
        raise ValueError(
            f"Invalid query transformation registry at {path}: match must include criteria"
        )
    return QueryTransformationRule(
        rule_id=_required_query_transformation_text(
            record["rule_id"],
            field="rule_id",
            path=path,
        ),
        strategy=_required_query_transformation_text(
            record["strategy"],
            field="strategy",
            path=path,
        ),
        reason=_required_query_transformation_text(
            record["reason"],
            field="reason",
            path=path,
        ),
        variant_template=_required_query_transformation_text(
            record["variant_template"],
            field="variant_template",
            path=path,
        ),
        priority=_optional_query_transformation_int(
            record.get("priority"),
            default=100,
            path=path,
        ),
        enabled=_optional_query_transformation_bool(
            record.get("enabled"),
            default=True,
            path=path,
            field="enabled",
        ),
        requires_hyde_enabled=_optional_query_transformation_bool(
            record.get("requires_hyde_enabled"),
            default=False,
            path=path,
            field="requires_hyde_enabled",
        ),
        match=transformation_match,
    )


def _required_query_transformation_text(value: Any, *, field: str, path: Path) -> str:
    text = " ".join(str(value).split())
    if not text:
        raise ValueError(
            f"Invalid query transformation registry at {path}: {field} cannot be blank"
        )
    return text


def _optional_query_transformation_int(value: Any, *, default: int, path: Path) -> int:
    if value is None:
        return default
    if not isinstance(value, int):
        raise ValueError(
            f"Invalid query transformation registry at {path}: priority must be an integer"
        )
    if value < 1:
        raise ValueError(
            f"Invalid query transformation registry at {path}: priority must be positive"
        )
    return value


def _optional_query_transformation_bool(
    value: Any,
    *,
    default: bool,
    path: Path,
    field: str,
) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ValueError(
            f"Invalid query transformation registry at {path}: {field} must be boolean"
        )
    return value


def _query_transformation_text_tuple(value: Any, *, path: Path) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(
            f"Invalid query transformation registry at {path}: match values must be lists"
        )
    return tuple(
        _required_query_transformation_text(item, field="match value", path=path)
        for item in value
    )


def _ensure_unique_query_transformation_rule_ids(
    rules: tuple[QueryTransformationRule, ...],
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
            f"Invalid query transformation registry at {path}: duplicate rule_id {duplicate_text}"
        )


def _query_route(
    query: RetrievalQuery,
    *,
    concepts: list[str],
    standards: list[str],
    tokens: set[str],
    query_profile: RetrievalQueryProfile | None,
    diagnostics: list[RetrievalQueryDiagnostic],
) -> RetrievalQueryRoute | None:
    matched = [
        (rule, criteria)
        for rule in _query_route_rules()
        if (criteria := _query_route_match_criteria(
            rule,
            query=query,
            concepts=concepts,
            standards=standards,
            tokens=tokens,
            query_profile=query_profile,
            diagnostics=diagnostics,
        ))
    ]
    if not matched:
        return None
    matched.sort(key=lambda item: (item[0].priority, item[0].route_id))
    selected, criteria = matched[0]
    metadata = {
        "profile_id": query_profile.profile_id if query_profile else None,
        "profile_route": query_profile.route if query_profile else None,
        "detected_format": query.detected_format,
        "resource_type": query.resource_type,
        "filter_keys": sorted(query.filters),
        "diagnostic_codes": [diagnostic.code for diagnostic in diagnostics],
    }
    return RetrievalQueryRoute(
        route_id=selected.route_id,
        strategy_id=selected.strategy_id,
        label=selected.label,
        retrieval_mode=selected.retrieval_mode,
        rationale=selected.rationale,
        rule_id=selected.rule_id,
        priority=selected.priority,
        confidence=selected.confidence,
        matched_criteria=criteria,
        suggested_filters=dict(selected.suggested_filters),
        risk_controls=list(selected.risk_controls),
        budget=selected.budget,
        metadata={key: value for key, value in metadata.items() if value},
    )


def _query_route_match_criteria(
    rule: QueryRouteRule,
    *,
    query: RetrievalQuery,
    concepts: list[str],
    standards: list[str],
    tokens: set[str],
    query_profile: RetrievalQueryProfile | None,
    diagnostics: list[RetrievalQueryDiagnostic],
) -> list[str]:
    match = rule.match
    criteria: list[str] = []
    profile_ids = [query_profile.profile_id] if query_profile else []
    profile_routes = [query_profile.route] if query_profile else []
    retrieval_modes = [query_profile.retrieval_mode] if query_profile else []
    detected_formats = [query.detected_format] if query.detected_format else []
    resource_types = [query.resource_type] if query.resource_type else []
    filter_keys = [str(key) for key in query.filters]
    filter_values = [str(value) for value in query.filters.values() if value is not None]
    diagnostic_codes = [diagnostic.code for diagnostic in diagnostics]
    checks = [
        ("profile_id", _intersection_values(profile_ids, match.any_profile_ids)),
        ("profile_route", _intersection_values(profile_routes, match.any_profile_routes)),
        (
            "retrieval_mode",
            _intersection_values(retrieval_modes, match.any_retrieval_modes),
        ),
        (
            "detected_format",
            _intersection_values(detected_formats, match.any_detected_formats),
        ),
        ("resource_type", _intersection_values(resource_types, match.any_resource_types)),
        ("filter_key", _intersection_values(filter_keys, match.any_filter_keys)),
        ("filter_value", _intersection_values(filter_values, match.any_filter_values)),
        (
            "diagnostic_code",
            _intersection_values(diagnostic_codes, match.any_diagnostic_codes),
        ),
        ("concept", _intersection_values(concepts, match.any_concepts)),
        ("standard", _intersection_values(standards, match.any_standards)),
        ("token", _intersection_values(tokens, match.any_tokens)),
    ]
    for label, values in checks:
        criteria.extend(f"{label}:{value}" for value in values)
    if match.require_fields and query.fields:
        criteria.append("fields:present")
    return criteria


def _query_route_rules() -> tuple[QueryRouteRule, ...]:
    path = os.environ.get("OJT_QUERY_ROUTE_RULES_PATH")
    return _load_query_route_rules(path or str(DEFAULT_QUERY_ROUTE_RULE_REGISTRY))


def _load_query_route_rules(path_text: str) -> tuple[QueryRouteRule, ...]:
    path = Path(path_text)
    if not path.exists():
        return ()
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = raw.get("rules") if isinstance(raw, dict) else None
    if not isinstance(records, list):
        raise ValueError(f"Invalid query route registry at {path}: expected rules list")
    rules = tuple(_query_route_rule(record, path=path) for record in records)
    _ensure_unique_query_route_rule_ids(rules, path=path)
    return rules


def _query_route_rule(record: Any, *, path: Path) -> QueryRouteRule:
    if not isinstance(record, dict):
        raise ValueError(f"Invalid query route registry at {path}: rule must be an object")
    required = (
        "rule_id",
        "route_id",
        "strategy_id",
        "label",
        "retrieval_mode",
        "rationale",
        "match",
    )
    missing = [field for field in required if field not in record]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"Invalid query route registry at {path}: missing {missing_text}")
    match = record["match"]
    if not isinstance(match, dict):
        raise ValueError(f"Invalid query route registry at {path}: match must be an object")
    route_match = QueryRouteMatch(
        any_profile_ids=_query_route_text_tuple(match.get("any_profile_ids"), path=path),
        any_profile_routes=_query_route_text_tuple(match.get("any_profile_routes"), path=path),
        any_retrieval_modes=_query_route_text_tuple(
            match.get("any_retrieval_modes"),
            path=path,
        ),
        any_detected_formats=_query_route_text_tuple(
            match.get("any_detected_formats"),
            path=path,
        ),
        any_resource_types=_query_route_text_tuple(match.get("any_resource_types"), path=path),
        any_filter_keys=_query_route_text_tuple(match.get("any_filter_keys"), path=path),
        any_filter_values=_query_route_text_tuple(match.get("any_filter_values"), path=path),
        any_diagnostic_codes=_query_route_text_tuple(
            match.get("any_diagnostic_codes"),
            path=path,
        ),
        any_concepts=_query_route_text_tuple(match.get("any_concepts"), path=path),
        any_standards=_query_route_text_tuple(match.get("any_standards"), path=path),
        any_tokens=_query_route_text_tuple(match.get("any_tokens"), path=path),
        require_fields=_optional_query_route_bool(
            match.get("require_fields"),
            default=False,
            path=path,
            field="match.require_fields",
        ),
    )
    if not any(
        (
            route_match.any_profile_ids,
            route_match.any_profile_routes,
            route_match.any_retrieval_modes,
            route_match.any_detected_formats,
            route_match.any_resource_types,
            route_match.any_filter_keys,
            route_match.any_filter_values,
            route_match.any_diagnostic_codes,
            route_match.any_concepts,
            route_match.any_standards,
            route_match.any_tokens,
            route_match.require_fields,
        )
    ):
        raise ValueError(f"Invalid query route registry at {path}: match must include criteria")
    suggested_filters = record.get("suggested_filters", {})
    if not isinstance(suggested_filters, dict):
        raise ValueError(
            f"Invalid query route registry at {path}: suggested_filters must be an object"
        )
    return QueryRouteRule(
        rule_id=_required_query_route_text(record["rule_id"], field="rule_id", path=path),
        route_id=_required_query_route_text(record["route_id"], field="route_id", path=path),
        strategy_id=_required_query_route_text(
            record["strategy_id"],
            field="strategy_id",
            path=path,
        ),
        label=_required_query_route_text(record["label"], field="label", path=path),
        retrieval_mode=_required_query_route_text(
            record["retrieval_mode"],
            field="retrieval_mode",
            path=path,
        ),
        rationale=_required_query_route_text(
            record["rationale"],
            field="rationale",
            path=path,
        ),
        priority=_optional_query_route_int(record.get("priority"), default=100, path=path),
        confidence=_optional_query_route_float(
            record.get("confidence"),
            default=0.8,
            path=path,
        ),
        suggested_filters=_query_route_text_map(
            suggested_filters,
            key_field="suggested_filters key",
            value_field="suggested_filters value",
            path=path,
        ),
        risk_controls=_query_route_text_tuple(record.get("risk_controls"), path=path),
        budget=_query_route_budget(record.get("budget"), path=path),
        match=route_match,
    )


def _query_route_budget(value: Any, *, path: Path) -> RetrievalRouteBudget | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError(f"Invalid query route registry at {path}: budget must be an object")
    try:
        return RetrievalRouteBudget.model_validate(value)
    except ValueError as exc:
        raise ValueError(f"Invalid query route registry at {path}: invalid budget") from exc


def _required_query_route_text(value: Any, *, field: str, path: Path) -> str:
    text = " ".join(str(value).split())
    if not text:
        raise ValueError(f"Invalid query route registry at {path}: {field} cannot be blank")
    return text


def _optional_query_route_int(value: Any, *, default: int, path: Path) -> int:
    if value is None:
        return default
    if not isinstance(value, int):
        raise ValueError(f"Invalid query route registry at {path}: priority must be an integer")
    if value < 1:
        raise ValueError(f"Invalid query route registry at {path}: priority must be positive")
    return value


def _optional_query_route_float(value: Any, *, default: float, path: Path) -> float:
    if value is None:
        return default
    if not isinstance(value, (int, float)):
        raise ValueError(f"Invalid query route registry at {path}: confidence must be a number")
    confidence = float(value)
    if confidence < 0.0 or confidence > 1.0:
        raise ValueError(
            f"Invalid query route registry at {path}: confidence must be between 0 and 1"
        )
    return confidence


def _optional_query_route_bool(
    value: Any,
    *,
    default: bool,
    path: Path,
    field: str,
) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ValueError(f"Invalid query route registry at {path}: {field} must be boolean")
    return value


def _query_route_text_tuple(value: Any, *, path: Path) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"Invalid query route registry at {path}: match values must be lists")
    return tuple(_required_query_route_text(item, field="match value", path=path) for item in value)


def _query_route_text_map(
    value: dict[Any, Any],
    *,
    key_field: str,
    value_field: str,
    path: Path,
) -> dict[str, str]:
    return {
        _required_query_route_text(key, field=key_field, path=path): _required_query_route_text(
            item,
            field=value_field,
            path=path,
        )
        for key, item in value.items()
    }


def _ensure_unique_query_route_rule_ids(
    rules: tuple[QueryRouteRule, ...],
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
            f"Invalid query route registry at {path}: duplicate rule_id {duplicate_text}"
        )


def _intersection_values(values: Iterable[str], candidates: tuple[str, ...]) -> list[str]:
    candidate_lookup = {candidate.casefold(): candidate for candidate in candidates}
    matched: list[str] = []
    for value in values:
        candidate = candidate_lookup.get(str(value).casefold())
        if candidate:
            matched.append(candidate)
    return _dedupe(matched)


def _search_hint_target(target: str) -> SearchHintTarget:
    targets = {item.target: item for item in _search_hint_targets()}
    return targets.get(
        target,
        SearchHintTarget(
            target=target,
            label=target,
            rationale="Review target-specific search syntax before use.",
            warnings=(),
        ),
    )


def _search_hint_targets() -> tuple[SearchHintTarget, ...]:
    path = os.environ.get("OJT_SEARCH_HINT_TARGETS_PATH")
    return _load_search_hint_targets(path or str(DEFAULT_SEARCH_HINT_TARGET_REGISTRY))


def _fhir_search_resource(resource_type: str) -> FhirSearchResource | None:
    resources = {
        item.resource_type.lower(): item for item in _fhir_search_resources()
    }
    return resources.get(resource_type.lower())


def _fhir_parameter_examples(
    resource_seed: FhirSearchResource | None,
    *,
    query_fields: list[str],
) -> list[dict[str, Any]]:
    if not resource_seed:
        return []
    field_tokens = {token for field in query_fields for token in _tokens(field)}
    preferred_names = _fhir_preferred_parameter_names(field_tokens)
    parameters = sorted(
        resource_seed.parameters,
        key=lambda parameter: (
            0 if parameter.name in preferred_names else 1,
            parameter.name,
        ),
    )
    return [
        {
            "name": parameter.name,
            "type": parameter.parameter_type,
            "target_field": parameter.target_field,
            "example": parameter.example,
            "standard_systems": list(parameter.standard_systems),
            "matched_dataset_field": parameter.name in preferred_names,
        }
        for parameter in parameters[:5]
    ]


def _fhir_preferred_parameter_names(field_tokens: set[str]) -> set[str]:
    preferred: set[str] = set()
    if {"lab", "test", "code", "loinc", "lab_name", "test_name"}.intersection(field_tokens):
        preferred.update({"code", "combo-code"})
    if {"patient", "patient_id", "subject", "mrn"}.intersection(field_tokens):
        preferred.update({"patient", "subject"})
    if {"date", "effective", "effective_date"}.intersection(field_tokens):
        preferred.add("date")
    if {"value", "unit", "units", "result_value"}.intersection(field_tokens):
        preferred.add("value-quantity")
    return preferred


def _fhir_search_registry_version() -> str | None:
    return _fhir_search_registry_raw().get("version")


def _fhir_search_resources() -> tuple[FhirSearchResource, ...]:
    raw = _fhir_search_registry_raw()
    records = raw.get("resources")
    path = Path(os.environ.get("OJT_FHIR_SEARCH_PARAMETERS_PATH") or str(DEFAULT_FHIR_SEARCH_PARAMETER_REGISTRY))
    if not isinstance(records, list):
        raise ValueError(f"Invalid FHIR search parameter registry at {path}: resources must be a list")
    return tuple(_fhir_search_resource_record(record, path=path) for record in records)


@lru_cache(maxsize=4)
def _fhir_search_registry_raw() -> dict[str, Any]:
    path = Path(
        os.environ.get("OJT_FHIR_SEARCH_PARAMETERS_PATH")
        or str(DEFAULT_FHIR_SEARCH_PARAMETER_REGISTRY)
    )
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid FHIR search parameter registry at {path}: expected object")
    return raw


def _fhir_search_resource_record(record: Any, *, path: Path) -> FhirSearchResource:
    if not isinstance(record, dict):
        raise ValueError(f"Invalid FHIR search parameter registry at {path}: resource must be an object")
    parameters = record.get("parameters")
    if not isinstance(parameters, list):
        raise ValueError(f"Invalid FHIR search parameter registry at {path}: parameters must be a list")
    return FhirSearchResource(
        resource_type=_required_search_hint_text(
            record.get("resource_type"),
            field="resource_type",
            path=path,
        ),
        clinical_domain=_optional_fhir_registry_text(record.get("clinical_domain")),
        parameters=tuple(
            _fhir_search_parameter_record(parameter, path=path)
            for parameter in parameters
        ),
    )


def _fhir_search_parameter_record(record: Any, *, path: Path) -> FhirSearchParameter:
    if not isinstance(record, dict):
        raise ValueError(f"Invalid FHIR search parameter registry at {path}: parameter must be an object")
    return FhirSearchParameter(
        name=_required_search_hint_text(record.get("name"), field="name", path=path),
        parameter_type=_required_search_hint_text(record.get("type"), field="type", path=path),
        target_field=_required_search_hint_text(
            record.get("target_field"),
            field="target_field",
            path=path,
        ),
        example=_required_search_hint_text(record.get("example"), field="example", path=path),
        standard_systems=_search_hint_text_tuple(
            record.get("standard_systems"),
            field="standard_systems",
            path=path,
        ),
    )


def _optional_fhir_registry_text(value: Any) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split())
    return text or None


def _load_search_hint_targets(path_text: str) -> tuple[SearchHintTarget, ...]:
    path = Path(path_text)
    if not path.exists():
        return ()
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = raw.get("targets") if isinstance(raw, dict) else None
    if not isinstance(records, list):
        raise ValueError(f"Invalid search hint target registry at {path}: expected targets list")

    targets = tuple(_search_hint_target_record(record, path=path) for record in records)
    _ensure_unique_search_hint_targets(targets, path=path)
    return targets


def _search_hint_target_record(record: Any, *, path: Path) -> SearchHintTarget:
    if not isinstance(record, dict):
        raise ValueError(f"Invalid search hint target registry at {path}: target must be an object")
    required = ("target", "label", "rationale", "warnings")
    missing = [field for field in required if field not in record]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(
            f"Invalid search hint target registry at {path}: missing {missing_text}"
        )
    return SearchHintTarget(
        target=_required_search_hint_text(record["target"], field="target", path=path),
        label=_required_search_hint_text(record["label"], field="label", path=path),
        rationale=_required_search_hint_text(record["rationale"], field="rationale", path=path),
        warnings=_search_hint_text_tuple(record["warnings"], field="warnings", path=path),
    )


def _search_hint_text_tuple(value: Any, *, field: str, path: Path) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"Invalid search hint target registry at {path}: {field} must be a list")
    items = tuple(
        normalized
        for item in value
        for normalized in [" ".join(str(item).split())]
        if normalized
    )
    if not items:
        raise ValueError(f"Invalid search hint target registry at {path}: {field} cannot be empty")
    return items


def _required_search_hint_text(value: Any, *, field: str, path: Path) -> str:
    text = " ".join(str(value).split())
    if not text:
        raise ValueError(f"Invalid search hint target registry at {path}: {field} cannot be blank")
    return text


def _ensure_unique_search_hint_targets(
    targets: tuple[SearchHintTarget, ...],
    *,
    path: Path,
) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for target in targets:
        if target.target in seen:
            duplicates.add(target.target)
        seen.add(target.target)
    if duplicates:
        duplicate_text = ", ".join(sorted(duplicates))
        raise ValueError(
            f"Invalid search hint target registry at {path}: duplicate target {duplicate_text}"
        )


def _matching_aliases(
    aliases: object,
    *,
    haystack: str,
    tokens: set[str],
) -> list[str]:
    if not isinstance(aliases, list):
        return []
    matched: list[str] = []
    for raw_alias in aliases:
        alias = " ".join(str(raw_alias).lower().split())
        if not alias:
            continue
        if " " in alias:
            if alias in haystack:
                matched.append(str(raw_alias))
            continue
        if alias in tokens:
            matched.append(str(raw_alias))
    return _dedupe(matched)


@lru_cache(maxsize=4)
def _load_medical_concept_registry(path_text: str) -> tuple[dict[str, Any], ...]:
    path = Path(path_text)
    if not path.exists():
        return ()
    raw = json.loads(path.read_text(encoding="utf-8"))
    concepts = raw.get("concepts") if isinstance(raw, dict) else None
    if not isinstance(concepts, list):
        return ()
    valid: list[dict[str, Any]] = []
    for concept in concepts:
        if not isinstance(concept, dict):
            continue
        required = {"concept_id", "display_name", "standard_system", "aliases"}
        if required.issubset(concept):
            valid.append(concept)
    return tuple(valid)


def _medical_concept_registry() -> tuple[dict[str, Any], ...]:
    path = os.environ.get("OJT_MEDICAL_CONCEPT_REGISTRY_PATH")
    return _load_medical_concept_registry(path or str(DEFAULT_MEDICAL_CONCEPT_REGISTRY))


def _base_query_variant_details(query: RetrievalQuery) -> list[RetrievalQueryVariant]:
    variants = [
        RetrievalQueryVariant(
            variant=query.query,
            source="user_query",
            reason="Original operator search text.",
        )
    ]
    if query.fields:
        fields_text = " ".join(query.fields)
        variants.append(
            RetrievalQueryVariant(
                variant=fields_text,
                source="requested_fields",
                reason="Requested input/output fields.",
                metadata={"fields": query.fields},
            )
        )
        variants.append(
            RetrievalQueryVariant(
                variant=f"healthcare fields {fields_text} validation units terminology",
                source="requested_fields",
                reason="Healthcare field validation and terminology context.",
                metadata={"fields": query.fields},
            )
        )
    if query.schema_id:
        variants.append(
            RetrievalQueryVariant(
                variant=f"{query.schema_id} schema required fields validation",
                source="schema_id",
                reason="Schema-specific required-field and validation context.",
                metadata={"schema_id": query.schema_id},
            )
        )
    if query.resource_type:
        variants.append(
            RetrievalQueryVariant(
                variant=f"FHIR {query.resource_type} resource profile required shape",
                source="resource_type",
                reason="FHIR-like resource profile context.",
                metadata={"resource_type": query.resource_type},
            )
        )
    if query.detected_format:
        variants.append(
            RetrievalQueryVariant(
                variant=f"{query.detected_format} parsing conversion data quality",
                source="detected_format",
                reason="Input format parsing and conversion context.",
                metadata={"detected_format": query.detected_format},
            )
        )
    return variants


def _query_haystack(query: RetrievalQuery) -> str:
    return " ".join(
        value
        for value in [
            query.query,
            *query.fields,
            query.schema_id or "",
            query.detected_format or "",
            query.resource_type or "",
            str(query.filters.get("clinical_domain") or ""),
            str(query.filters.get("standard_system") or ""),
            str(query.filters.get("source_type") or ""),
        ]
        if value
    ).lower()


def _rule_matches(
    rule: QueryExpansionRule,
    *,
    haystack: str,
    tokens: set[str],
) -> bool:
    for trigger in rule.triggers:
        normalized = trigger.lower()
        if " " in normalized:
            if normalized in haystack:
                return True
            continue
        if normalized in tokens:
            return True
    return False


def _tokens(text: str) -> list[str]:
    return [match.group(0).lower() for match in QUERY_TOKEN_PATTERN.finditer(text)]


def _standards_variant_details(standards: list[str]) -> list[RetrievalQueryVariant]:
    if not standards:
        return []
    return [
        RetrievalQueryVariant(
            variant=f"healthcare standards grounding {' '.join(standards)}",
            source="standard_inference",
            reason="Healthcare standards inferred from query analysis.",
            metadata={"standards": standards},
        )
    ]


def _expanded_terms_variant_details(
    expanded_terms: list[str],
) -> list[RetrievalQueryVariant]:
    if not expanded_terms:
        return []
    return [
        RetrievalQueryVariant(
            variant=" ".join(expanded_terms),
            source="expanded_terms",
            reason="Expanded terms from rules and controlled-vocabulary matches.",
            metadata={"term_count": len(expanded_terms)},
        )
    ]


def _query_aspect_variant_details(
    aspects: list[RetrievalQueryAspect],
) -> list[RetrievalQueryVariant]:
    return [
        RetrievalQueryVariant(
            variant=" ".join(
                value
                for value in [
                    aspect.question,
                    " ".join(aspect.suggested_terms),
                    " ".join(aspect.suggested_filters.values()),
                ]
                if value
            ),
            source="query_aspect_rule",
            reason=f"Matched query aspect rule {aspect.rule_id}.",
            metadata={
                "aspect_id": aspect.aspect_id,
                "priority": aspect.priority,
                "rule_id": aspect.rule_id,
                "suggested_filters": dict(aspect.suggested_filters),
                "suggested_terms": list(aspect.suggested_terms),
            },
        )
        for aspect in aspects
        if aspect.question or aspect.suggested_terms or aspect.suggested_filters
    ]


def _dedupe_query_variant_details(
    variants: Iterable[RetrievalQueryVariant],
) -> list[RetrievalQueryVariant]:
    seen: set[str] = set()
    deduped: list[RetrievalQueryVariant] = []
    for variant in variants:
        key = variant.variant.casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(variant)
    return deduped


def _filter_suggestions(
    query: RetrievalQuery,
    concepts: list[str],
    standards: list[str],
    rule_ids: list[str],
    concept_candidates: list[RetrievalConceptCandidate],
) -> list[RetrievalFilterSuggestion]:
    return _dedupe_suggestions(
        [
            _suggestion(
                query,
                field=rule.field,
                value=rule.value,
                reason=rule.reason,
                rule_id=rule.rule_id,
                confidence=rule.confidence,
            )
            for rule in _filter_suggestion_rules()
            if _filter_suggestion_rule_matches(
                rule,
                concepts=concepts,
                standards=standards,
                rule_ids=rule_ids,
                concept_candidates=concept_candidates,
            )
        ]
    )


def _filter_suggestion_rule_matches(
    rule: FilterSuggestionRule,
    *,
    concepts: list[str],
    standards: list[str],
    rule_ids: list[str],
    concept_candidates: list[RetrievalConceptCandidate],
) -> bool:
    match = rule.match
    candidate_domains = _dedupe(
        candidate.clinical_domain
        for candidate in concept_candidates
        if candidate.clinical_domain
    )
    candidate_standards = _dedupe(candidate.standard_system for candidate in concept_candidates)
    return any(
        (
            _has_intersection(concepts, match.any_concepts),
            _has_intersection(standards, match.any_standards),
            _has_intersection(rule_ids, match.any_rule_ids),
            _has_intersection(candidate_domains, match.any_candidate_domains),
            _has_intersection(candidate_standards, match.any_candidate_standards),
        )
    )


def _query_diagnostics(
    query: RetrievalQuery,
    *,
    concepts: list[str],
    standards: list[str],
    tokens: set[str],
) -> list[RetrievalQueryDiagnostic]:
    diagnostics: list[RetrievalQueryDiagnostic] = []
    applied_standard = str(query.filters.get("standard_system") or "")
    active_metadata_filters = _active_metadata_filter_names(query)
    suggested_standards = {
        standard_value
        for standard in standards
        for standard_value in [_standard_filter_value(standard)]
        if standard_value
    }
    for rule in _query_diagnostic_rules():
        if not _query_diagnostic_rule_matches(
            rule,
            query=query,
            concepts=concepts,
            tokens=tokens,
            applied_standard=applied_standard,
            active_metadata_filters=active_metadata_filters,
            suggested_standards=suggested_standards,
        ):
            continue
        diagnostics.append(
            RetrievalQueryDiagnostic(
                code=rule.code,
                severity=rule.severity,
                message=_format_query_diagnostic_template(
                    rule.message,
                    applied_standard=applied_standard,
                    active_metadata_filters=active_metadata_filters,
                    suggested_standards=suggested_standards,
                ),
                suggested_action=_format_query_diagnostic_template(
                    rule.suggested_action,
                    applied_standard=applied_standard,
                    active_metadata_filters=active_metadata_filters,
                    suggested_standards=suggested_standards,
                ),
                metadata=_query_diagnostic_metadata(
                    rule.code,
                    query=query,
                    applied_standard=applied_standard,
                    active_metadata_filters=active_metadata_filters,
                    suggested_standards=suggested_standards,
                    concepts=concepts,
                    standards=standards,
                    token_count=len(_tokens(query.query)),
                ),
            )
        )
    return diagnostics


def _query_diagnostic_metadata(
    code: str,
    *,
    query: RetrievalQuery,
    applied_standard: str,
    active_metadata_filters: list[str],
    suggested_standards: set[str],
    concepts: list[str],
    standards: list[str],
    token_count: int,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "rule_code": code,
        "query_token_count": token_count,
    }
    if active_metadata_filters:
        metadata["active_metadata_filters"] = list(active_metadata_filters)
        metadata["active_metadata_filter_count"] = len(active_metadata_filters)
    if applied_standard:
        metadata["applied_standard"] = applied_standard
    if suggested_standards:
        metadata["suggested_standards"] = sorted(suggested_standards)
    if concepts:
        metadata["detected_concepts"] = list(concepts)
    if standards:
        metadata["detected_standards"] = list(standards)
    if query.fields:
        metadata["fields"] = list(query.fields)
    for field_name, value in {
        "schema_id": query.schema_id,
        "detected_format": query.detected_format,
        "resource_type": query.resource_type,
    }.items():
        if value:
            metadata[field_name] = value
    return metadata


def _query_profile(
    *,
    concepts: list[str],
    standards: list[str],
    rule_ids: list[str],
    tokens: set[str],
    candidate_domains: list[str],
    candidate_standards: list[str],
) -> RetrievalQueryProfile | None:
    matched = [
        rule
        for rule in _query_profile_rules()
        if _query_profile_rule_matches(
            rule,
            concepts=concepts,
            standards=standards,
            rule_ids=rule_ids,
            tokens=tokens,
            candidate_domains=candidate_domains,
            candidate_standards=candidate_standards,
        )
    ]
    if not matched:
        return None
    matched.sort(key=lambda rule: (rule.priority, rule.profile_id))
    selected = matched[0]
    return RetrievalQueryProfile(
        profile_id=selected.profile_id,
        label=selected.label,
        route=selected.route,
        complexity=selected.complexity,
        retrieval_mode=selected.retrieval_mode,
        description=selected.description,
        suggested_filters=dict(selected.suggested_filters),
        rule_ids=[rule.rule_id for rule in matched],
    )


def _query_profile_rule_matches(
    rule: QueryProfileRule,
    *,
    concepts: list[str],
    standards: list[str],
    rule_ids: list[str],
    tokens: set[str],
    candidate_domains: list[str],
    candidate_standards: list[str],
) -> bool:
    match = rule.match
    checks = [
        _has_intersection(concepts, match.any_concepts),
        _has_intersection(standards, match.any_standards),
        _has_intersection(rule_ids, match.any_rule_ids),
        _has_intersection(tokens, match.any_tokens),
        _has_intersection(candidate_domains, match.any_candidate_domains),
        _has_intersection(candidate_standards, match.any_candidate_standards),
    ]
    return any(checks)


def _query_aspects(
    *,
    concepts: list[str],
    standards: list[str],
    rule_ids: list[str],
    tokens: set[str],
    candidate_domains: list[str],
    candidate_standards: list[str],
) -> list[RetrievalQueryAspect]:
    matched = [
        rule
        for rule in _query_aspect_rules()
        if _query_aspect_rule_matches(
            rule,
            concepts=concepts,
            standards=standards,
            rule_ids=rule_ids,
            tokens=tokens,
            candidate_domains=candidate_domains,
            candidate_standards=candidate_standards,
        )
    ]
    matched.sort(key=lambda rule: (rule.priority, rule.aspect_id))
    return [
        RetrievalQueryAspect(
            aspect_id=rule.aspect_id,
            label=rule.label,
            question=rule.question,
            rationale=rule.rationale,
            priority=rule.priority,
            rule_id=rule.rule_id,
            suggested_terms=list(rule.suggested_terms),
            suggested_filters=dict(rule.suggested_filters),
        )
        for rule in matched
    ]


def _query_transformation_variant_details(
    query: RetrievalQuery,
    *,
    concepts: list[str],
    standards: list[str],
    rule_ids: list[str],
    tokens: set[str],
    candidate_domains: list[str],
    candidate_standards: list[str],
    query_profile: RetrievalQueryProfile | None,
    query_aspects: list[RetrievalQueryAspect],
) -> list[RetrievalQueryVariant]:
    matched = [
        rule
        for rule in _query_transformation_rules()
        if _query_transformation_enabled(rule)
        and _query_transformation_rule_matches(
            rule,
            concepts=concepts,
            standards=standards,
            rule_ids=rule_ids,
            tokens=tokens,
            candidate_domains=candidate_domains,
            candidate_standards=candidate_standards,
            query_profile=query_profile,
        )
    ]
    matched.sort(key=lambda rule: (rule.priority, rule.rule_id))
    variants: list[RetrievalQueryVariant] = []
    for rule in matched:
        variant = _render_query_transformation_template(
            rule.variant_template,
            query=query,
            concepts=concepts,
            standards=standards,
            query_profile=query_profile,
            query_aspects=query_aspects,
        )
        if not variant:
            continue
        variants.append(
            RetrievalQueryVariant(
                variant=variant,
                source="query_transformation_rule",
                reason=rule.reason,
                metadata={
                    "rule_id": rule.rule_id,
                    "strategy": rule.strategy,
                    "priority": rule.priority,
                    "requires_hyde_enabled": rule.requires_hyde_enabled,
                },
            )
        )
    return variants


def _query_transformation_rule_matches(
    rule: QueryTransformationRule,
    *,
    concepts: list[str],
    standards: list[str],
    rule_ids: list[str],
    tokens: set[str],
    candidate_domains: list[str],
    candidate_standards: list[str],
    query_profile: RetrievalQueryProfile | None,
) -> bool:
    profile_ids = [query_profile.profile_id] if query_profile else []
    profile_routes = [query_profile.route] if query_profile else []
    match = rule.match
    checks = [
        _has_intersection(concepts, match.any_concepts),
        _has_intersection(standards, match.any_standards),
        _has_intersection(rule_ids, match.any_rule_ids),
        _has_intersection(tokens, match.any_tokens),
        _has_intersection(profile_ids, match.any_profile_ids),
        _has_intersection(profile_routes, match.any_profile_routes),
        _has_intersection(candidate_domains, match.any_candidate_domains),
        _has_intersection(candidate_standards, match.any_candidate_standards),
    ]
    return any(checks)


def _query_transformation_enabled(rule: QueryTransformationRule) -> bool:
    if rule.requires_hyde_enabled:
        return _env_flag("OJT_RETRIEVAL_ENABLE_HYDE")
    return rule.enabled


def _render_query_transformation_template(
    template: str,
    *,
    query: RetrievalQuery,
    concepts: list[str],
    standards: list[str],
    query_profile: RetrievalQueryProfile | None,
    query_aspects: list[RetrievalQueryAspect],
) -> str:
    values = {
        "query": query.query,
        "fields": " ".join(query.fields),
        "schema_id": query.schema_id or "",
        "detected_format": query.detected_format or "",
        "resource_type": query.resource_type or "",
        "concepts": " ".join(concepts),
        "standards": " ".join(standards),
        "profile_id": query_profile.profile_id if query_profile else "",
        "profile_label": query_profile.label if query_profile else "",
        "profile_route": query_profile.route if query_profile else "",
        "retrieval_mode": query_profile.retrieval_mode if query_profile else "",
        "aspects": " ".join(aspect.label for aspect in query_aspects),
        "aspect_terms": " ".join(
            term for aspect in query_aspects for term in aspect.suggested_terms
        ),
    }
    rendered = template.format_map(_SafeTemplateValues(values))
    return " ".join(rendered.split())


class _SafeTemplateValues(dict):
    def __missing__(self, key: str) -> str:
        return ""


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _query_aspect_rule_matches(
    rule: QueryAspectRule,
    *,
    concepts: list[str],
    standards: list[str],
    rule_ids: list[str],
    tokens: set[str],
    candidate_domains: list[str],
    candidate_standards: list[str],
) -> bool:
    match = rule.match
    checks = [
        _has_intersection(concepts, match.any_concepts),
        _has_intersection(standards, match.any_standards),
        _has_intersection(rule_ids, match.any_rule_ids),
        _has_intersection(tokens, match.any_tokens),
        _has_intersection(candidate_domains, match.any_candidate_domains),
        _has_intersection(candidate_standards, match.any_candidate_standards),
    ]
    return any(checks)


def _retrieval_tasks(
    query: RetrievalQuery,
    *,
    aspects: list[RetrievalQueryAspect],
    hints: list[RetrievalSearchHint],
    variants: list[RetrievalQueryVariant],
    filter_suggestions: list[RetrievalFilterSuggestion],
    standards: list[str],
) -> list[RetrievalSearchTask]:
    tasks: list[RetrievalSearchTask] = []
    variant_lookup = _aspect_variant_lookup(variants)
    global_filters = _filter_suggestions_as_dict(filter_suggestions)

    for aspect in aspects:
        task_filters = {**global_filters, **dict(aspect.suggested_filters)}
        aspect_variants = variant_lookup.get(aspect.aspect_id, [])
        tasks.append(
            RetrievalSearchTask(
                task_id=f"local:{aspect.aspect_id}",
                label=aspect.label,
                target="local_corpus",
                action_type="run_local_search",
                query=aspect_variants[0] if aspect_variants else aspect.question,
                rationale=aspect.rationale,
                priority=aspect.priority,
                required=True,
                aspect_id=aspect.aspect_id,
                query_variants=aspect_variants[:3],
                standards=standards,
                suggested_filters=task_filters,
                metadata={"rule_id": aspect.rule_id},
            )
        )

    if not tasks:
        tasks.append(
            RetrievalSearchTask(
                task_id="local:primary",
                label="Primary evidence search",
                target="local_corpus",
                action_type="run_local_search",
                query=query.query,
                rationale="Search the trusted local corpus with the normalized user query.",
                priority=1,
                required=True,
                query_variants=[variant.variant for variant in variants[:3]],
                standards=standards,
                suggested_filters=global_filters,
            )
        )

    next_priority = max((task.priority for task in tasks), default=0) + 1
    for index, hint in enumerate(hints, start=0):
        tasks.append(
            RetrievalSearchTask(
                task_id=f"external:{hint.target}:{index + 1}",
                label=f"{_human_label(hint.target)} follow-up",
                target="external_medical_index",
                action_type="open_external_url" if hint.url else "copy_query",
                query=hint.query,
                rationale=hint.rationale,
                priority=next_priority + index,
                required=False,
                search_hint_target=hint.target,
                standards=standards,
                suggested_filters=global_filters,
                warnings=list(hint.warnings),
                metadata={
                    "url": hint.url,
                    "target": hint.target,
                },
            )
        )

    tasks.sort(key=lambda task: (task.priority, task.target, task.task_id))
    return tasks[:8]


def _aspect_variant_lookup(
    variants: list[RetrievalQueryVariant],
) -> dict[str, list[str]]:
    lookup: dict[str, list[str]] = {}
    for variant in variants:
        aspect_id = variant.metadata.get("aspect_id")
        if not isinstance(aspect_id, str) or not aspect_id:
            continue
        lookup.setdefault(aspect_id, []).append(variant.variant)
    return {aspect_id: _dedupe(items) for aspect_id, items in lookup.items()}


def _filter_suggestions_as_dict(
    suggestions: list[RetrievalFilterSuggestion],
) -> dict[str, str]:
    filters: dict[str, str] = {}
    for suggestion in suggestions:
        if suggestion.applied:
            continue
        filters.setdefault(suggestion.field, suggestion.value)
    return filters


def _human_label(value: str) -> str:
    return " ".join(part for part in re.split(r"[_\W]+", value) if part).title()


def _search_hints(
    query: RetrievalQuery,
    *,
    concepts: list[str],
    standards: list[str],
    concept_candidates: list[RetrievalConceptCandidate],
) -> list[RetrievalSearchHint]:
    hints: list[RetrievalSearchHint] = []
    concept_set = set(concepts)
    standard_set = set(standards)
    if "biomedical_literature_search" in concept_set or "MeSH" in standard_set:
        hints.append(
            _pubmed_search_hint(
                query,
                concepts=concepts,
                concept_candidates=concept_candidates,
            )
        )
    if "clinical_trial_search" in concept_set or "ClinicalTrials.gov" in standard_set:
        hints.append(_clinicaltrials_search_hint(query, concept_candidates=concept_candidates))
    if "regulatory_drug_safety_search" in concept_set or "openFDA" in standard_set:
        hints.extend(_openfda_search_hints(query, concept_candidates=concept_candidates))
    if "fhir_allergyintolerance_profile" in concept_set:
        hints.append(_allergyintolerance_search_hint(query))
    if (
        "fhir_observation_profile" in concept_set
        or "fhir_condition_profile" in concept_set
        or "fhir_allergyintolerance_profile" in concept_set
        or query.resource_type
    ):
        hints.append(_fhir_search_hint(query))
    if "LOINC" in standard_set:
        hints.append(_loinc_search_hint(query, concept_candidates=concept_candidates))
    if "UCUM" in standard_set:
        hints.append(_ucum_search_hint(query, concept_candidates=concept_candidates))
    return hints


def _pubmed_search_hint(
    query: RetrievalQuery,
    *,
    concepts: list[str],
    concept_candidates: list[RetrievalConceptCandidate],
) -> RetrievalSearchHint:
    terms = _pubmed_term_groups(
        query,
        concepts=concepts,
        concept_candidates=concept_candidates,
    )
    text_query = " AND ".join(terms) if terms else query.query
    target = _search_hint_target("pubmed")
    return RetrievalSearchHint(
        target=target.target,
        query=text_query,
        url=f"https://pubmed.ncbi.nlm.nih.gov/?term={quote_plus(text_query)}",
        rationale=target.rationale,
        warnings=list(target.warnings),
    )


def _loinc_search_terms(
    query: RetrievalQuery,
    *,
    concept_candidates: list[RetrievalConceptCandidate],
) -> list[str]:
    terms = _dedupe(
        [
            *(
                candidate.display_name
                for candidate in concept_candidates
                if candidate.standard_system == "LOINC"
            ),
            *(
                alias
                for candidate in concept_candidates
                if candidate.standard_system == "LOINC"
                for alias in candidate.matched_aliases[:2]
            ),
            *(
                field
                for field in query.fields
                if field.lower() in {"lab_name", "test_name", "code", "loinc_code"}
            ),
        ]
    )
    return terms[:5]


def _ucum_unit_candidates(
    query: RetrievalQuery,
    *,
    concept_candidates: list[RetrievalConceptCandidate],
) -> list[str]:
    metadata_units = [
        unit
        for candidate in concept_candidates
        for units in [candidate.metadata.get("preferred_units")]
        if isinstance(units, list)
        for unit in units
        if isinstance(unit, str) and unit.strip()
    ]
    query_units = [
        token
        for token in _tokens(query.query)
        if _looks_like_unit_token(token)
    ]
    return _dedupe([*metadata_units, *query_units])[:5]


def _looks_like_unit_token(token: str) -> bool:
    normalized = token.strip()
    if not normalized:
        return False
    if normalized in {"mg/dl", "mmol/l", "umol/l", "ng/ml", "g/dl", "ml/min"}:
        return True
    return any(character in normalized for character in {"/", "%"})


def _fhir_search_hint(query: RetrievalQuery) -> RetrievalSearchHint:
    resource_type = query.resource_type or "Observation"
    resource_seed = _fhir_search_resource(resource_type)
    parameter_examples = _fhir_parameter_examples(
        resource_seed,
        query_fields=query.fields,
    )
    if parameter_examples:
        template = " ; ".join(example["example"] for example in parameter_examples[:3])
    elif resource_type.lower() == "observation":
        template = (
            "Observation?code=<loinc-code>&subject=Patient/<id>&date=ge<yyyy-mm-dd>"
        )
    else:
        template = f"{resource_type}?_text=<clinical-text>&_profile=<profile-url>"
    target = _search_hint_target("fhir")
    return RetrievalSearchHint(
        target=target.target,
        query=template,
        rationale=target.rationale,
        warnings=list(target.warnings),
        metadata={
            "resource_type": resource_type,
            "registry_version": _fhir_search_registry_version(),
            "clinical_domain": resource_seed.clinical_domain if resource_seed else None,
            "parameter_examples": parameter_examples,
            "lineage_followup": [
                {
                    "parameter": "_revinclude=Provenance:target",
                    "purpose": "Return Provenance resources that point at the matched clinical resources when the server supports this join.",
                },
                {
                    "parameter": "_revinclude=AuditEvent:entity",
                    "purpose": "Return access/use audit events tied to the matched entity when supported by the concrete server.",
                },
            ],
            "capability_warning": (
                "Verify the concrete FHIR server CapabilityStatement before execution."
            ),
        },
    )


def _allergyintolerance_search_hint(query: RetrievalQuery) -> RetrievalSearchHint:
    resource_seed = _fhir_search_resource("AllergyIntolerance")
    parameter_examples = _fhir_parameter_examples(
        resource_seed,
        query_fields=query.fields,
    )
    template = (
        " ; ".join(example["example"] for example in parameter_examples[:4])
        if parameter_examples
        else "AllergyIntolerance?patient=<patient-id>&code=<substance-or-finding-code>"
    )
    target = _search_hint_target("allergyintolerance")
    return RetrievalSearchHint(
        target=target.target,
        query=template,
        rationale=target.rationale,
        warnings=list(target.warnings),
        metadata={
            "resource_type": "AllergyIntolerance",
            "registry_version": _fhir_search_registry_version(),
            "clinical_domain": resource_seed.clinical_domain if resource_seed else "allergy",
            "parameter_examples": parameter_examples,
            "capability_warning": (
                "Verify the concrete FHIR server CapabilityStatement before execution."
            ),
        },
    )


def _loinc_search_hint(
    query: RetrievalQuery,
    *,
    concept_candidates: list[RetrievalConceptCandidate],
) -> RetrievalSearchHint:
    target = _search_hint_target("loinc")
    terms = _loinc_search_terms(query, concept_candidates=concept_candidates)
    text_query = " ".join(terms) if terms else query.query
    encoded_query = quote_plus(text_query)
    return RetrievalSearchHint(
        target=target.target,
        query=f"GET /searchapi/loincs?query={encoded_query}&rows=20&offset=0",
        rationale=target.rationale,
        warnings=list(target.warnings),
        metadata={
            "api_base_url": "https://loinc.regenstrief.org/searchapi",
            "authentication_required": True,
            "scope_endpoints": [
                "/searchapi/loincs",
                "/searchapi/answerlists",
                "/searchapi/parts",
                "/searchapi/groups",
            ],
            "parameter_examples": [
                {
                    "name": "query",
                    "type": "string",
                    "target_field": "LOINC search text",
                    "example": f"query={encoded_query}",
                    "standard_systems": ["LOINC"],
                    "matched_dataset_field": bool(query.fields),
                },
                {
                    "name": "rows",
                    "type": "integer",
                    "target_field": "result page size",
                    "example": "rows=20",
                    "standard_systems": ["LOINC"],
                    "matched_dataset_field": False,
                },
                {
                    "name": "offset",
                    "type": "integer",
                    "target_field": "result page offset",
                    "example": "offset=0",
                    "standard_systems": ["LOINC"],
                    "matched_dataset_field": False,
                },
            ],
            "selected_terms": terms,
            "capability_warning": "LOINC Search API authentication and endpoint scope must be configured before execution.",
        },
    )


def _ucum_search_hint(
    query: RetrievalQuery,
    *,
    concept_candidates: list[RetrievalConceptCandidate],
) -> RetrievalSearchHint:
    target = _search_hint_target("ucum")
    unit_candidates = _ucum_unit_candidates(query, concept_candidates=concept_candidates)
    code = unit_candidates[0] if unit_candidates else "<unit-code>"
    encoded_code = quote_plus(code)
    validation_path = (
        "/ucum-fhir/R4/CodeSystem/$validate-code?"
        f"url=http://unitsofmeasure.org&code={encoded_code}&_format=application/fhir+json"
    )
    return RetrievalSearchHint(
        target=target.target,
        query=f"GET {validation_path}",
        url=f"https://ucum.nlm.nih.gov{validation_path}" if unit_candidates else None,
        rationale=target.rationale,
        warnings=list(target.warnings),
        metadata={
            "api_base_url": "https://ucum.nlm.nih.gov",
            "operation": "FHIR CodeSystem $validate-code",
            "launchable": bool(unit_candidates),
            "parameter_examples": [
                {
                    "name": "url",
                    "type": "uri",
                    "target_field": "CodeSystem URL",
                    "example": "url=http://unitsofmeasure.org",
                    "standard_systems": ["UCUM", "FHIR"],
                    "matched_dataset_field": False,
                },
                {
                    "name": "code",
                    "type": "code",
                    "target_field": "source unit string",
                    "example": f"code={encoded_code}",
                    "standard_systems": ["UCUM"],
                    "matched_dataset_field": "unit" in {field.lower() for field in query.fields},
                },
                {
                    "name": "_format",
                    "type": "mime-type",
                    "target_field": "response format",
                    "example": "_format=application/fhir+json",
                    "standard_systems": ["FHIR"],
                    "matched_dataset_field": False,
                },
            ],
            "selected_unit_candidates": unit_candidates,
            "capability_warning": "URL encode unit strings before execution and preserve the original source unit for audit.",
        },
    )


def _clinicaltrials_search_hint(
    query: RetrievalQuery,
    *,
    concept_candidates: list[RetrievalConceptCandidate],
) -> RetrievalSearchHint:
    condition_terms = [
        candidate.display_name
        for candidate in concept_candidates
        if candidate.standard_system == "MeSH"
        and (candidate.clinical_domain or "") == "literature"
        and "metformin" not in candidate.display_name.lower()
    ]
    intervention_terms = [
        candidate.display_name
        for candidate in concept_candidates
        if candidate.standard_system == "RxNorm"
        or (candidate.clinical_domain or "") == "medication"
    ]
    params: list[tuple[str, str]] = []
    if condition_terms:
        params.append(("query.cond", _join_external_terms(condition_terms, limit=2)))
    if intervention_terms:
        params.append(("query.intr", _join_external_terms(intervention_terms, limit=2)))
    if not params:
        params.append(("query.term", _fallback_external_query(query.query)))
    params.extend(
        [
            ("filter.overallStatus", "RECRUITING,NOT_YET_RECRUITING,ACTIVE_NOT_RECRUITING"),
            ("pageSize", "10"),
            ("format", "json"),
        ]
    )
    query_string = "&".join(f"{key}={quote_plus(value)}" for key, value in params)
    url = f"https://clinicaltrials.gov/api/v2/studies?{query_string}"
    target = _search_hint_target("clinicaltrials_gov")
    return RetrievalSearchHint(
        target=target.target,
        query=url,
        url=url,
        rationale=target.rationale,
        warnings=list(target.warnings),
    )


def _openfda_search_hints(
    query: RetrievalQuery,
    *,
    concept_candidates: list[RetrievalConceptCandidate],
) -> list[RetrievalSearchHint]:
    medication_term = _first_medication_term(query, concept_candidates)
    if not medication_term:
        medication_term = _fallback_external_query(query.query)
    encoded_drug = quote_plus(f'"{medication_term}"')
    label_search = f"openfda.generic_name:{encoded_drug}"
    if "boxed warning" in query.query.lower():
        label_search = f"{label_search}+AND+_exists_:boxed_warning"
    label_url = (
        "https://api.fda.gov/drug/label.json?"
        f"search={label_search}&sort=effective_time:desc&limit=5"
    )
    event_url = (
        "https://api.fda.gov/drug/event.json?"
        f"search=patient.drug.openfda.generic_name:{encoded_drug}&limit=10"
    )
    label_target = _search_hint_target("openfda_drug_label")
    event_target = _search_hint_target("openfda_drug_event")
    return [
        RetrievalSearchHint(
            target=label_target.target,
            query=label_url,
            url=label_url,
            rationale=label_target.rationale,
            warnings=list(label_target.warnings),
        ),
        RetrievalSearchHint(
            target=event_target.target,
            query=event_url,
            url=event_url,
            rationale=event_target.rationale,
            warnings=list(event_target.warnings),
        ),
    ]


def _pubmed_term_groups(
    query: RetrievalQuery,
    *,
    concepts: list[str],
    concept_candidates: list[RetrievalConceptCandidate],
) -> list[str]:
    groups: list[str] = []
    concept_set = set(concepts)
    for candidate in concept_candidates:
        aliases = [candidate.display_name, *candidate.matched_aliases][:4]
        if candidate.standard_system == "MeSH" and candidate.code:
            groups.append(
                f'("{candidate.display_name}"[mh] OR {_tiab_or_group(aliases)})'
            )
            continue
        if "biomedical_literature_search" in concept_set:
            groups.append(_tiab_or_group(aliases))
    if "hba1c_laboratory_test" in concept_set:
        groups.append('("hba1c"[tiab] OR "hemoglobin a1c"[tiab] OR "glycated hemoglobin"[tiab])')
    if "unit_normalization" in concept_set:
        groups.append('("unit"[tiab] OR "units"[tiab] OR "valueQuantity"[tiab])')
    if "medication_normalization" in concept_set:
        groups.append('("medication"[tiab] OR "drug"[tiab] OR "RxNorm"[tiab])')
    if _has_any_token(query.query, {"systematic", "meta-analysis", "guideline", "trial"}):
        groups.append(
            '("systematic review"[pt] OR "meta-analysis"[pt] OR guideline[tiab] OR trial[tiab])'
        )
    if not groups:
        token_terms = [
            token
            for token in _tokens(query.query)
            if len(token) > 2 and token not in {"and", "the", "for", "with"}
        ][:6]
        if token_terms:
            groups.append(" AND ".join(f"{token}[tiab]" for token in token_terms))
    return _dedupe(groups)


def _join_external_terms(terms: list[str], *, limit: int) -> str:
    return " ".join(_dedupe(terms)[:limit])


def _fallback_external_query(text: str) -> str:
    stopwords = {
        "and",
        "the",
        "for",
        "with",
        "api",
        "search",
        "clinical",
        "trial",
        "trials",
        "openfda",
        "fda",
        "adverse",
        "event",
        "events",
        "label",
        "drug",
        "safety",
        "recruiting",
        "eligibility",
    }
    terms = [
        token
        for token in _tokens(text)
        if len(token) > 2 and token not in stopwords
    ][:6]
    return " ".join(terms) if terms else text.strip()


def _first_medication_term(
    query: RetrievalQuery,
    concept_candidates: list[RetrievalConceptCandidate],
) -> str:
    for candidate in concept_candidates:
        if candidate.standard_system == "RxNorm" or (candidate.clinical_domain or "") == "medication":
            return candidate.display_name
    return ""


def _tiab_or_group(terms: list[str]) -> str:
    normalized = _dedupe(
        " ".join(term.split())
        for term in terms
        if term and term.strip()
    )
    return " OR ".join(f'"{term}"[tiab]' for term in normalized)


def _has_any_token(text: str, candidates: set[str]) -> bool:
    tokens = set(_tokens(text))
    lowered = text.lower()
    return bool(tokens.intersection(candidates)) or any(
        candidate in lowered for candidate in candidates if " " in candidate or "-" in candidate
    )


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _is_low_specificity_query(query: RetrievalQuery, *, tokens: set[str]) -> bool:
    if query.fields or query.schema_id or query.resource_type or query.detected_format:
        return False
    if any(
        query.filters.get(key)
        for key in ("clinical_domain", "standard_system", "source_type", "source_id")
    ):
        return False
    return len(tokens) < 3


def _active_metadata_filter_names(query: RetrievalQuery) -> list[str]:
    filter_names = [
        key
        for key in (
            "clinical_domain",
            "standard_system",
            "source_type",
            "source_id",
            "trust_level",
        )
        if query.filters.get(key)
    ]
    contextual_scope = [
        ("schema_id", query.schema_id),
        ("detected_format", query.detected_format),
        ("resource_type", query.resource_type),
    ]
    filter_names.extend(name for name, value in contextual_scope if value)
    return sorted(filter_names)


def _is_overconstrained_metadata_query(
    query: RetrievalQuery,
    *,
    concepts: list[str],
    tokens: set[str],
) -> bool:
    del concepts, tokens
    active_metadata_filters = _active_metadata_filter_names(query)
    if len(active_metadata_filters) < 3:
        return False
    if query.fields or query.schema_id or query.resource_type or query.detected_format:
        return False
    if _has_query_text_clinical_context(query):
        return False
    return len(_tokens(query.query)) < 4


def _has_query_text_clinical_context(query: RetrievalQuery) -> bool:
    haystack = query.query.lower()
    tokens = set(_tokens(haystack))
    if not tokens:
        return False
    if _concept_candidates(haystack=haystack, tokens=tokens):
        return True
    return any(
        _rule_matches(rule, haystack=haystack, tokens=tokens)
        for rule in _query_expansion_rules()
    )


def _query_diagnostic_rule_matches(
    rule: QueryDiagnosticRule,
    *,
    query: RetrievalQuery,
    concepts: list[str],
    tokens: set[str],
    applied_standard: str,
    active_metadata_filters: list[str],
    suggested_standards: set[str],
) -> bool:
    if rule.condition == "low_specificity_query":
        return _is_low_specificity_query(query, tokens=tokens)
    if rule.condition == "no_healthcare_concept_detected":
        return not concepts
    if rule.condition == "overconstrained_metadata_filters":
        return _is_overconstrained_metadata_query(query, concepts=concepts, tokens=tokens)
    if rule.condition == "standard_filter_conflicts_with_query":
        return bool(
            applied_standard
            and suggested_standards
            and applied_standard not in suggested_standards
        )
    return False


def _format_query_diagnostic_template(
    template: str,
    *,
    applied_standard: str,
    active_metadata_filters: list[str],
    suggested_standards: set[str],
) -> str:
    suggested = ", ".join(sorted(suggested_standards)) or "none"
    active_filters = ", ".join(active_metadata_filters) or "none"
    return template.format(
        active_filters=active_filters,
        applied_standard=applied_standard or "none",
        filter_count=len(active_metadata_filters),
        suggested_standards=suggested,
    )


def _suggestion(
    query: RetrievalQuery,
    *,
    field: str,
    value: str,
    reason: str,
    rule_id: str,
    confidence: float,
) -> RetrievalFilterSuggestion:
    return RetrievalFilterSuggestion(
        field=field,
        value=value,
        reason=reason,
        rule_id=rule_id,
        confidence=confidence,
        applied=str(query.filters.get(field) or "") == value,
    )


def _standard_filter_value(standard: str) -> str | None:
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
        return standard
    if standard == "OJTFlow policy":
        return "ojtflow_policy"
    if standard == "OJTFlow schema":
        return "ojtflow_schema"
    return None


def _has_intersection(left: Iterable[str], right: Iterable[str]) -> bool:
    right_set = {value.lower() for value in right}
    return bool(right_set and {value.lower() for value in left}.intersection(right_set))


def _dedupe_suggestions(
    suggestions: list[RetrievalFilterSuggestion],
) -> list[RetrievalFilterSuggestion]:
    deduped: list[RetrievalFilterSuggestion] = []
    seen: set[tuple[str, str]] = set()
    for suggestion in suggestions:
        key = (suggestion.field, suggestion.value)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(suggestion)
    return deduped


def _dedupe(values: Iterable[object]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = " ".join(str(value).split())
        key = normalized.lower()
        if normalized and key not in seen:
            seen.add(key)
            deduped.append(normalized)
    return deduped
