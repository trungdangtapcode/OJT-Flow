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

from ojtflow.core.contracts.retrieval import (
    RetrievalConceptCandidate,
    RetrievalFilterSuggestion,
    RetrievalQuery,
    RetrievalQueryAnalysis,
    RetrievalQueryDiagnostic,
    RetrievalSearchHint,
)

QUERY_TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9_./%-]*", re.IGNORECASE)
DEFAULT_MEDICAL_CONCEPT_REGISTRY = (
    Path(__file__).resolve().parents[4] / "knowledge" / "terminologies" / "medical_concepts.json"
)


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
    QueryExpansionRule(
        rule_id="medication_normalization",
        concept="medication_normalization",
        triggers=("medication", "medications", "drug", "drugs", "rxnorm", "ndc", "dose"),
        expanded_terms=(
            "RxNorm normalized medication concept",
            "drug code mapping",
            "medication terminology",
            "dose form",
        ),
        standards=("RxNorm",),
        variant="RxNorm medication drug normalized concept code dose form",
    ),
    QueryExpansionRule(
        rule_id="observational_analytics_export",
        concept="observational_analytics_export",
        triggers=("omop", "cdm", "analytics", "cohort", "observational"),
        expanded_terms=(
            "OMOP Common Data Model",
            "observational health data",
            "analytics export",
            "source evidence preservation",
        ),
        standards=("OMOP",),
        variant="OMOP Common Data Model observational health analytics export mapping",
    ),
    QueryExpansionRule(
        rule_id="biomedical_literature_search",
        concept="biomedical_literature_search",
        triggers=(
            "pubmed",
            "medline",
            "mesh",
            "literature",
            "paper",
            "papers",
            "study",
            "studies",
            "trial",
            "systematic review",
            "meta-analysis",
            "guideline",
            "evidence",
        ),
        expanded_terms=(
            "MeSH subject heading",
            "PubMed automatic term mapping",
            "title abstract text words",
            "publication type filter",
        ),
        standards=("MeSH",),
        variant="PubMed MEDLINE MeSH title abstract systematic review clinical trial evidence",
    ),
)


def analyze_query(query: RetrievalQuery) -> RetrievalQueryAnalysis:
    """Return deterministic query analysis and healthcare-aware variants."""

    base_variants = _base_query_variants(query)
    haystack = _query_haystack(query)
    tokens = set(_tokens(haystack))
    concept_candidates = _concept_candidates(haystack=haystack, tokens=tokens)
    matched_rules = [
        rule
        for rule in CLINICAL_EXPANSION_RULES
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
    variants = _dedupe(
        [
            *base_variants,
            *(rule.variant for rule in matched_rules),
            *_concept_candidate_variants(concept_candidates),
            _standards_variant(standards),
            _expanded_terms_variant(expanded_terms),
        ]
    )
    return RetrievalQueryAnalysis(
        detected_concepts=concepts,
        concept_candidates=concept_candidates,
        expanded_terms=expanded_terms,
        standards=standards,
        rule_ids=rule_ids,
        query_variants=variants,
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


def _concept_candidate_variants(
    candidates: list[RetrievalConceptCandidate],
) -> list[str]:
    return [
        " ".join(
            value
            for value in [
                candidate.display_name,
                candidate.standard_system,
                candidate.code or "",
                " ".join(candidate.matched_aliases),
                candidate.clinical_domain or "",
            ]
            if value
        )
        for candidate in candidates
    ]


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
    concept_candidates: list[RetrievalConceptCandidate],
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
    ) or {"LOINC", "UCUM"}.intersection(standards):
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
    for domain in _dedupe(
        candidate.clinical_domain
        for candidate in concept_candidates
        if candidate.clinical_domain
    ):
        suggestions.append(
            _suggestion(
                query,
                field="clinical_domain",
                value=domain,
                reason=f"Detected {domain} controlled-vocabulary concept.",
                rule_id=f"suggest_domain_{domain}",
                confidence=0.82,
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


def _query_diagnostics(
    query: RetrievalQuery,
    *,
    concepts: list[str],
    standards: list[str],
    tokens: set[str],
) -> list[RetrievalQueryDiagnostic]:
    diagnostics: list[RetrievalQueryDiagnostic] = []
    if _is_low_specificity_query(query, tokens=tokens):
        diagnostics.append(
            RetrievalQueryDiagnostic(
                code="low_specificity_query",
                severity="warning",
                message="Retrieval query has limited context for healthcare evidence ranking.",
                suggested_action=(
                    "Add a schema, resource type, clinical domain, standard, or field list."
                ),
            )
        )
    if not concepts:
        diagnostics.append(
            RetrievalQueryDiagnostic(
                code="no_healthcare_concept_detected",
                severity="info",
                message="No healthcare retrieval concept matched deterministic query rules.",
                suggested_action=(
                    "Use explicit terms such as FHIR, LOINC, UCUM, RxNorm, OMOP, MeSH, "
                    "lab, unit, medication, literature, or patient identifier when relevant."
                ),
            )
        )
    applied_standard = str(query.filters.get("standard_system") or "")
    suggested_standards = {
        standard_value
        for standard in standards
        for standard_value in [_standard_filter_value(standard)]
        if standard_value
    }
    if applied_standard and suggested_standards and applied_standard not in suggested_standards:
        diagnostics.append(
            RetrievalQueryDiagnostic(
                code="standard_filter_conflicts_with_query",
                severity="warning",
                message=(
                    f"Applied standard_system={applied_standard} does not match detected "
                    f"query standards: {', '.join(sorted(suggested_standards))}."
                ),
                suggested_action=(
                    "Remove the standard filter or choose one of the detected standard filters."
                ),
            )
        )
    return diagnostics


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
    return RetrievalSearchHint(
        target="pubmed",
        query=text_query,
        rationale=(
            "Use PubMed automatic term mapping for broad discovery, then verify "
            "MeSH translations and title/abstract text-word coverage."
        ),
        warnings=[
            "Confirm preferred MeSH headings in PubMed Search Details or the MeSH database before using this as a final literature strategy.",
            "Quoted phrases, field tags, and wildcards can change PubMed automatic term mapping behavior.",
        ],
    )


def _fhir_search_hint(query: RetrievalQuery) -> RetrievalSearchHint:
    resource_type = query.resource_type or "Observation"
    if resource_type.lower() == "observation":
        template = (
            "Observation?code=<loinc-code>&subject=Patient/<id>&date=ge<yyyy-mm-dd>"
        )
        rationale = (
            "FHIR Observation search should bind lab concepts through code, subject, "
            "and date parameters after validated source fields are available."
        )
    else:
        template = f"{resource_type}?_text=<clinical-text>&_profile=<profile-url>"
        rationale = (
            "FHIR resource search should start with resource-specific parameters and "
            "only fall back to _text when structured fields are unavailable."
        )
    return RetrievalSearchHint(
        target="fhir",
        query=template,
        rationale=rationale,
        warnings=[
            "This is a template only; replace placeholders with validated identifiers, codes, and dates.",
            "FHIR servers vary in which optional resource search parameters they implement.",
        ],
    )


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
    if standard in {"FHIR", "LOINC", "UCUM", "RxNorm", "OMOP", "MeSH"}:
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
