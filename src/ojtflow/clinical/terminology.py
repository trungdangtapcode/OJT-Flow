"""Deterministic terminology candidate and unit validation helpers."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from ojtflow.core.contracts.data import ParsedData
from ojtflow.core.contracts.issue import SourceLocation
from ojtflow.core.contracts.terminology import (
    TerminologyCandidate,
    UnitValidationResult,
)


DEFAULT_CONCEPT_REGISTRY = (
    Path(__file__).resolve().parents[3] / "knowledge" / "terminologies" / "medical_concepts.json"
)
DEFAULT_UCUM_UNIT_REGISTRY = (
    Path(__file__).resolve().parents[3] / "knowledge" / "terminologies" / "ucum_units.json"
)
CONCEPT_REGISTRY_ENV_VAR = "OJT_MEDICAL_CONCEPT_REGISTRY_PATH"
UCUM_UNIT_REGISTRY_ENV_VAR = "OJT_UCUM_UNIT_REGISTRY_PATH"
MEDICATION_FIELDS = (
    "medication",
    "medication_name",
    "drug",
    "drug_name",
    "rx",
)
SNOMED_CT_FIELDS = (
    "diagnosis",
    "condition",
    "finding",
    "problem",
    "problem_name",
    "procedure",
    "procedure_name",
    "allergy",
    "allergy_name",
)
SNOMED_CT_LICENSE_NOTE = (
    "SNOMED CT candidate only; verify deployment license and jurisdiction before "
    "production lookup, storage, export, or clinical use."
)


def terminology_candidates_for_lab_records(
    parsed: ParsedData,
) -> tuple[list[TerminologyCandidate], list[UnitValidationResult]]:
    """Generate review-gated terminology candidates and UCUM unit checks."""

    candidates: list[TerminologyCandidate] = []
    unit_results: list[UnitValidationResult] = []
    for row_index, record in enumerate(parsed.records, start=1):
        source_row = _source_row(record, fallback=row_index)
        lab_name = _text(record.get("lab_name"))
        loinc_candidate: TerminologyCandidate | None = None
        if lab_name:
            loinc_candidate = _concept_candidate_for_value(
                lab_name,
                source_field="lab_name",
                standard_system="LOINC",
                clinical_domains=("laboratory",),
                location=SourceLocation(
                    row=source_row,
                    column="lab_name",
                    field="lab_name",
                    source_ref=parsed.source_ref,
                ),
                metadata_overrides={
                    "source_note": (
                        "Candidate only; reviewer approval required before semantic "
                        "normalization."
                    )
                },
            )
            if loinc_candidate:
                candidates.append(loinc_candidate)
        candidates.extend(_field_candidates(record, parsed=parsed, source_row=source_row))
        unit_results.append(
            _unit_validation_for_record(
                record,
                source_row=source_row,
                parsed=parsed,
                candidate=loinc_candidate,
            )
        )
    return candidates, unit_results


def _field_candidates(
    record: dict[str, Any],
    *,
    parsed: ParsedData,
    source_row: int,
) -> list[TerminologyCandidate]:
    candidates: list[TerminologyCandidate] = []
    for field in MEDICATION_FIELDS:
        value = _text(record.get(field))
        if not value:
            continue
        candidate = _concept_candidate_for_value(
            value,
            source_field=field,
            standard_system="RxNorm",
            clinical_domains=("medication", "allergy"),
            location=SourceLocation(
                row=source_row,
                column=field,
                field=field,
                source_ref=parsed.source_ref,
            ),
            metadata_overrides={
                "implementation_status": "seed_registry_contract",
                "normalization_policy": "review_required_no_auto_replacement",
                "source_note": (
                    "RxNorm candidate only; reviewer approval required before "
                    "medication normalization."
                ),
            },
        )
        if candidate:
            candidates.append(candidate)
    for field in SNOMED_CT_FIELDS:
        value = _text(record.get(field))
        if not value:
            continue
        candidate = _concept_candidate_for_value(
            value,
            source_field=field,
            standard_system="SNOMED CT",
            clinical_domains=("problem_list", "condition", "finding", "procedure", "allergy"),
            location=SourceLocation(
                row=source_row,
                column=field,
                field=field,
                source_ref=parsed.source_ref,
            ),
            metadata_overrides={
                "implementation_status": "placeholder_contract",
                "license_note": SNOMED_CT_LICENSE_NOTE,
                "normalization_policy": "review_required_no_auto_replacement",
                "source_note": (
                    "SNOMED CT placeholder candidate only; final clinical "
                    "terminology assignment requires licensed lookup and review."
                ),
            },
        )
        if candidate:
            candidates.append(candidate)
    return candidates


def _concept_candidate_for_value(
    value: str,
    *,
    source_field: str,
    standard_system: str,
    clinical_domains: tuple[str, ...],
    location: SourceLocation,
    metadata_overrides: dict[str, Any] | None = None,
) -> TerminologyCandidate | None:
    normalized_value = _normalize(value)
    best: tuple[dict[str, Any], list[str], float] | None = None
    for concept in _concept_registry():
        if concept.get("standard_system") != standard_system:
            continue
        if clinical_domains and concept.get("clinical_domain") not in clinical_domains:
            continue
        aliases = [
            str(alias)
            for alias in concept.get("aliases", [])
            if isinstance(alias, str) and alias.strip()
        ]
        normalized_aliases = [_normalize(alias) for alias in aliases]
        matched_aliases = [
            alias for alias, normalized in zip(aliases, normalized_aliases, strict=True)
            if normalized == normalized_value
        ]
        confidence = 0.96
        if not matched_aliases:
            matched_aliases = [
                alias
                for alias, normalized in zip(aliases, normalized_aliases, strict=True)
                if normalized and (normalized in normalized_value or normalized_value in normalized)
            ]
            confidence = 0.78
        if not matched_aliases:
            continue
        if best is None or confidence > best[2]:
            best = (concept, matched_aliases, confidence)
    if best is None:
        return None
    concept, matched_aliases, confidence = best
    metadata = dict(concept.get("metadata") or {})
    metadata.update(
        {
            "concept_id": concept.get("concept_id"),
            "clinical_domain": concept.get("clinical_domain"),
        }
    )
    if standard_system == "LOINC":
        metadata["preferred_units"] = _preferred_units(concept)
        metadata["loinc_long_common_name"] = (concept.get("metadata") or {}).get(
            "loinc_long_common_name"
        )
    metadata.update(metadata_overrides or {})
    return TerminologyCandidate(
        source_field=source_field,
        source_value=value,
        standard_system=standard_system,
        code=str(concept["code"]),
        display=str(concept["display_name"]),
        confidence=confidence,
        matched_aliases=matched_aliases,
        source_uri=str(concept.get("source")) if concept.get("source") else None,
        location=location,
        metadata=metadata,
    )


def _unit_validation_for_record(
    record: dict[str, Any],
    *,
    source_row: int,
    parsed: ParsedData,
    candidate: TerminologyCandidate | None,
) -> UnitValidationResult:
    source_unit = _text(record.get("unit"))
    location = SourceLocation(
        row=source_row,
        column="unit",
        field="unit",
        source_ref=parsed.source_ref,
    )
    if not source_unit:
        return UnitValidationResult(
            source_field="unit",
            source_unit="",
            status="missing",
            confidence=1.0,
            message="Unit is missing; reviewer must confirm before downstream use.",
            location=location,
            requires_review=True,
        )
    unit = _unit_by_alias(source_unit)
    if unit is None:
        return UnitValidationResult(
            source_field="unit",
            source_unit=source_unit,
            status="unknown",
            confidence=0.2,
            message="Unit is not present in the configured UCUM seed registry.",
            location=location,
            requires_review=True,
        )
    preferred_units = (
        [str(item) for item in candidate.metadata.get("preferred_units", [])]
        if candidate
        else []
    )
    status = "valid"
    requires_review = False
    message = "Unit matched the configured UCUM seed registry."
    if preferred_units and unit["code"] not in preferred_units:
        status = "not_preferred"
        requires_review = True
        message = "Unit is valid in the seed registry but not preferred for the terminology candidate."
    return UnitValidationResult(
        source_field="unit",
        source_unit=source_unit,
        normalized_unit=str(unit["code"]),
        status=status,
        confidence=0.92,
        message=message,
        location=location,
        requires_review=requires_review,
        metadata={
            "display": unit.get("display"),
            "clinical_domains": unit.get("clinical_domains", []),
            "preferred_units": preferred_units,
        },
    )


@lru_cache(maxsize=4)
def _concept_registry() -> tuple[dict[str, Any], ...]:
    path = Path(os.environ.get(CONCEPT_REGISTRY_ENV_VAR) or DEFAULT_CONCEPT_REGISTRY)
    if not path.exists():
        return ()
    raw = json.loads(path.read_text(encoding="utf-8"))
    concepts = raw.get("concepts") if isinstance(raw, dict) else None
    if not isinstance(concepts, list):
        return ()
    return tuple(concept for concept in concepts if isinstance(concept, dict))


@lru_cache(maxsize=4)
def _ucum_units() -> tuple[dict[str, Any], ...]:
    path = Path(os.environ.get(UCUM_UNIT_REGISTRY_ENV_VAR) or DEFAULT_UCUM_UNIT_REGISTRY)
    if not path.exists():
        return ()
    raw = json.loads(path.read_text(encoding="utf-8"))
    units = raw.get("units") if isinstance(raw, dict) else None
    if not isinstance(units, list):
        return ()
    return tuple(unit for unit in units if isinstance(unit, dict) and unit.get("code"))


def _unit_by_alias(value: str) -> dict[str, Any] | None:
    normalized_value = _normalize_unit(value)
    for unit in _ucum_units():
        aliases = unit.get("aliases", [])
        if _normalize_unit(str(unit.get("code"))) == normalized_value:
            return unit
        if isinstance(aliases, list) and any(
            _normalize_unit(str(alias)) == normalized_value for alias in aliases
        ):
            return unit
    return None


def _preferred_units(concept: dict[str, Any]) -> list[str]:
    metadata = concept.get("metadata")
    preferred = metadata.get("preferred_units") if isinstance(metadata, dict) else None
    return [str(item) for item in preferred] if isinstance(preferred, list) else []


def _source_row(record: dict[str, Any], *, fallback: int) -> int:
    value = record.get("_source_row")
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _text(value: Any) -> str:
    return str(value).strip() if value not in (None, "") else ""


def _normalize(value: str) -> str:
    return " ".join(value.strip().lower().replace("_", " ").split())


def _normalize_unit(value: str) -> str:
    return value.strip().lower().replace(" ", "")
