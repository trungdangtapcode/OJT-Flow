"""Deterministic clinical query analysis for retrieval."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from ojtflow.core.contracts.retrieval import (
    RetrievalFilterSuggestion,
    RetrievalQuery,
    RetrievalQueryAnalysis,
)

QUERY_TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9_./%-]*", re.IGNORECASE)


@dataclass(frozen=True)
class QueryExpansionRule:
    """One auditable query expansion rule."""

    rule_id: str
    concept: str
    triggers: tuple[str, ...]
    expanded_terms: tuple[str, ...]
    standards: tuple[str, ...]
    variant: str


CLINICAL_EXPANSION_RULES: tuple[QueryExpansionRule, ...] = (
    QueryExpansionRule(
        rule_id="lab_observation_identity",
        concept="laboratory_observation_identity",
        triggers=("lab", "laboratory", "lab_name", "test", "observation", "result"),
        expanded_terms=(
            "laboratory test identifier",
            "lab name normalization",
            "observation code",
            "LOINC code",
        ),
        standards=("LOINC",),
        variant="LOINC laboratory observation test identifiers lab_name code",
    ),
    QueryExpansionRule(
        rule_id="hba1c_lab_test",
        concept="hba1c_laboratory_test",
        triggers=("hba1c", "a1c", "hemoglobin a1c", "glycated hemoglobin"),
        expanded_terms=(
            "HbA1c",
            "hemoglobin A1c",
            "glycated hemoglobin",
            "laboratory observation value",
        ),
        standards=("LOINC", "FHIR"),
        variant="HbA1c hemoglobin A1c glycated hemoglobin laboratory Observation code value unit",
    ),
    QueryExpansionRule(
        rule_id="unit_normalization",
        concept="unit_normalization",
        triggers=(
            "unit",
            "units",
            "missing unit",
            "mg/dl",
            "mmol/l",
            "%",
            "percent",
            "valuequantity",
        ),
        expanded_terms=(
            "UCUM computable unit",
            "ambiguous unit",
            "missing unit",
            "valueQuantity unit",
        ),
        standards=("UCUM", "FHIR"),
        variant="UCUM computable units valueQuantity unit code missing ambiguous units",
    ),
    QueryExpansionRule(
        rule_id="fhir_observation_profile",
        concept="fhir_observation_profile",
        triggers=(
            "fhir",
            "observation",
            "resourcetype",
            "valuequantity",
            "effectivedatetime",
        ),
        expanded_terms=(
            "FHIR Observation",
            "resourceType",
            "subject",
            "effective date",
            "valueQuantity",
        ),
        standards=("FHIR",),
        variant="FHIR Observation resource status code subject effectiveDateTime valueQuantity",
    ),
    QueryExpansionRule(
        rule_id="csv_tabular_quality",
        concept="csv_tabular_quality",
        triggers=(
            "csv",
            "row",
            "rows",
            "column",
            "columns",
            "malformed",
            "missing cells",
            "extra cells",
        ),
        expanded_terms=(
            "malformed row",
            "extra cell",
            "missing cell",
            "parse report",
            "tabular conversion",
        ),
        standards=("OJTFlow schema",),
        variant="CSV malformed rows extra cells missing cells parse report conversion data quality",
    ),
    QueryExpansionRule(
        rule_id="phi_review_context",
        concept="sensitive_identifier_review",
        triggers=("patient_id", "patient identifier", "mrn", "dob", "ssn", "identifier"),
        expanded_terms=(
            "sensitive identifier",
            "PHI review",
            "human review",
            "patient identifier",
        ),
        standards=("OJTFlow policy",),
        variant="patient identifiers sensitive fields PHI human review governance",
    ),
)


def analyze_query(query: RetrievalQuery) -> RetrievalQueryAnalysis:
    """Return deterministic query analysis and healthcare-aware variants."""

    base_variants = _base_query_variants(query)
    haystack = _query_haystack(query)
    tokens = set(_tokens(haystack))
    matched_rules = [
        rule
        for rule in CLINICAL_EXPANSION_RULES
        if _rule_matches(rule, haystack=haystack, tokens=tokens)
    ]
    concepts = _dedupe(rule.concept for rule in matched_rules)
    expanded_terms = _dedupe(term for rule in matched_rules for term in rule.expanded_terms)
    standards = _dedupe(standard for rule in matched_rules for standard in rule.standards)
    rule_ids = _dedupe(rule.rule_id for rule in matched_rules)
    variants = _dedupe(
        [
            *base_variants,
            *(rule.variant for rule in matched_rules),
            _standards_variant(standards),
            _expanded_terms_variant(expanded_terms),
        ]
    )
    return RetrievalQueryAnalysis(
        detected_concepts=concepts,
        expanded_terms=expanded_terms,
        standards=standards,
        rule_ids=rule_ids,
        query_variants=variants,
        filter_suggestions=_filter_suggestions(query, concepts, standards, rule_ids),
    )


def _base_query_variants(query: RetrievalQuery) -> list[str]:
    variants = [query.query]
    if query.fields:
        fields_text = " ".join(query.fields)
        variants.append(fields_text)
        variants.append(f"healthcare fields {fields_text} validation units terminology")
    if query.schema_id:
        variants.append(f"{query.schema_id} schema required fields validation")
    if query.resource_type:
        variants.append(f"FHIR {query.resource_type} resource profile required shape")
    if query.detected_format:
        variants.append(f"{query.detected_format} parsing conversion data quality")
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


def _standards_variant(standards: list[str]) -> str:
    if not standards:
        return ""
    return f"healthcare standards grounding {' '.join(standards)}"


def _expanded_terms_variant(expanded_terms: list[str]) -> str:
    if not expanded_terms:
        return ""
    return " ".join(expanded_terms)


def _filter_suggestions(
    query: RetrievalQuery,
    concepts: list[str],
    standards: list[str],
    rule_ids: list[str],
) -> list[RetrievalFilterSuggestion]:
    suggestions: list[RetrievalFilterSuggestion] = []
    concept_set = set(concepts)
    if concept_set.intersection(
        {
            "laboratory_observation_identity",
            "hba1c_laboratory_test",
            "unit_normalization",
            "fhir_observation_profile",
        }
    ):
        suggestions.append(
            _suggestion(
                query,
                field="clinical_domain",
                value="laboratory",
                reason="Detected laboratory observation context.",
                rule_id="suggest_laboratory_domain",
                confidence=0.92,
            )
        )
    for standard in standards:
        standard_value = _standard_filter_value(standard)
        if not standard_value:
            continue
        suggestions.append(
            _suggestion(
                query,
                field="standard_system",
                value=standard_value,
                reason=f"Detected {standard_value} standard context.",
                rule_id=f"suggest_standard_{standard_value.lower()}",
                confidence=0.86,
            )
        )
    if "phi_review_context" in rule_ids:
        suggestions.append(
            _suggestion(
                query,
                field="standard_system",
                value="ojtflow_policy",
                reason="Detected sensitive identifier review context.",
                rule_id="suggest_governance_policy",
                confidence=0.78,
            )
        )
    return _dedupe_suggestions(suggestions)


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
    if standard in {"FHIR", "LOINC", "UCUM", "RxNorm", "OMOP"}:
        return standard
    if standard == "OJTFlow policy":
        return "ojtflow_policy"
    if standard == "OJTFlow schema":
        return "ojtflow_schema"
    return None


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
