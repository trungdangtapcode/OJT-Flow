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
    RetrievalQuery,
    RetrievalQueryAnalysis,
    RetrievalQueryDiagnostic,
    RetrievalQueryProfile,
    RetrievalQueryVariant,
    RetrievalSearchHint,
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
DEFAULT_SEARCH_HINT_TARGET_REGISTRY = (
    Path(__file__).resolve().parents[4] / "knowledge" / "retrieval" / "search_hint_targets.json"
)

SUPPORTED_FILTER_SUGGESTION_FIELDS = {
    "clinical_domain",
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
class SearchHintTarget:
    """Operator-facing metadata for one external search target."""

    target: str
    label: str
    rationale: str
    warnings: tuple[str, ...]


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
    variant_details = _dedupe_query_variant_details(
        [
            *base_variants,
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
        ]
    )
    variants = [detail.variant for detail in variant_details]
    return RetrievalQueryAnalysis(
        detected_concepts=concepts,
        concept_candidates=concept_candidates,
        expanded_terms=expanded_terms,
        standards=standards,
        rule_ids=rule_ids,
        query_variants=variants,
        query_variant_details=variant_details,
        filter_suggestions=_filter_suggestions(
            query,
            concepts,
            standards,
            rule_ids,
            concept_candidates,
        ),
        diagnostics=_query_diagnostics(
            query,
            concepts=concepts,
            standards=standards,
            tokens=tokens,
        ),
        search_hints=_search_hints(
            query,
            concepts=concepts,
            standards=standards,
            concept_candidates=concept_candidates,
        ),
        query_profile=_query_profile(
            concepts=concepts,
            standards=standards,
            rule_ids=rule_ids,
            tokens=tokens,
            concept_candidates=concept_candidates,
        ),
    )


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
                    suggested_standards=suggested_standards,
                ),
                suggested_action=_format_query_diagnostic_template(
                    rule.suggested_action,
                    applied_standard=applied_standard,
                    suggested_standards=suggested_standards,
                ),
            )
        )
    return diagnostics


def _query_profile(
    *,
    concepts: list[str],
    standards: list[str],
    rule_ids: list[str],
    tokens: set[str],
    concept_candidates: list[RetrievalConceptCandidate],
) -> RetrievalQueryProfile | None:
    candidate_domains = [
        candidate.clinical_domain
        for candidate in concept_candidates
        if candidate.clinical_domain
    ]
    candidate_standards = [candidate.standard_system for candidate in concept_candidates]
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
    if "fhir_observation_profile" in concept_set or query.resource_type:
        hints.append(_fhir_search_hint(query))
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


def _fhir_search_hint(query: RetrievalQuery) -> RetrievalSearchHint:
    resource_type = query.resource_type or "Observation"
    if resource_type.lower() == "observation":
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
    if any(query.filters.get(key) for key in ("clinical_domain", "standard_system", "source_type")):
        return False
    return len(tokens) < 3


def _query_diagnostic_rule_matches(
    rule: QueryDiagnosticRule,
    *,
    query: RetrievalQuery,
    concepts: list[str],
    tokens: set[str],
    applied_standard: str,
    suggested_standards: set[str],
) -> bool:
    if rule.condition == "low_specificity_query":
        return _is_low_specificity_query(query, tokens=tokens)
    if rule.condition == "no_healthcare_concept_detected":
        return not concepts
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
    suggested_standards: set[str],
) -> str:
    suggested = ", ".join(sorted(suggested_standards)) or "none"
    return template.format(
        applied_standard=applied_standard or "none",
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
