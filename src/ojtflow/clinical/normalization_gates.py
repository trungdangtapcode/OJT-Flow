"""Semantic normalization review gates for clinical package construction."""

from __future__ import annotations

from typing import Any

from ojtflow.clinical.terminology import MEDICATION_FIELDS
from ojtflow.core.contracts.clinical import (
    ClinicalSemanticNormalizationGate,
    ClinicalSemanticNormalizationGateType,
)
from ojtflow.core.contracts.data import ParsedData
from ojtflow.core.contracts.issue import SourceLocation
from ojtflow.core.contracts.terminology import (
    TerminologyCandidate,
    UnitValidationResult,
)


DATE_FIELDS = ("date", "effective_date", "observed_at", "collected_at")
PATIENT_IDENTIFIER_FIELDS = ("patient_id", "patient_identifier", "mrn")
LAB_NAME_FIELDS = ("lab_name", "test_name", "loinc_name")
DIAGNOSIS_FIELDS = ("diagnosis", "condition", "finding", "problem", "problem_name")
PROCEDURE_FIELDS = ("procedure", "procedure_name")
TERMINOLOGY_TARGETS: dict[ClinicalSemanticNormalizationGateType, tuple[str, str]] = {
    "lab_name": ("Observation", "Observation.code.coding"),
    "diagnosis": ("Condition", "Condition.code.coding"),
    "medication": (
        "MedicationStatement",
        "MedicationStatement.medicationCodeableConcept.coding",
    ),
    "procedure": ("Procedure", "Procedure.code.coding"),
}


def build_semantic_normalization_gates(
    *,
    parsed: ParsedData,
    terminology_candidates: list[TerminologyCandidate],
    unit_validations: list[UnitValidationResult],
) -> list[ClinicalSemanticNormalizationGate]:
    """Build review gates for clinical semantic changes before applying them."""

    gates: list[ClinicalSemanticNormalizationGate] = []
    gates.extend(_terminology_candidate_gates(terminology_candidates))
    gates.extend(_unit_gates(unit_validations))
    gates.extend(_record_field_gates(parsed, terminology_candidates))
    return gates


def _terminology_candidate_gates(
    candidates: list[TerminologyCandidate],
) -> list[ClinicalSemanticNormalizationGate]:
    gates: list[ClinicalSemanticNormalizationGate] = []
    for candidate in candidates:
        gate_type = _gate_type_for_candidate(candidate)
        if gate_type is None:
            continue
        target_resource_type, target_path = TERMINOLOGY_TARGETS[gate_type]
        gates.append(
            ClinicalSemanticNormalizationGate(
                gate_type=gate_type,
                source_field=candidate.source_field,
                source_value=candidate.source_value,
                target_resource_type=target_resource_type,
                target_path=target_path,
                location=candidate.location,
                candidate_id=candidate.candidate_id,
                proposed_system=candidate.standard_system,
                proposed_code=candidate.code,
                proposed_display=candidate.display,
                confidence=candidate.confidence,
                reason=(
                    f"Reviewer approval is required before replacing source "
                    f"{candidate.source_field} text with {candidate.standard_system} "
                    "coding."
                ),
                metadata={
                    "matched_aliases": candidate.matched_aliases,
                    "candidate_status": candidate.status,
                    "candidate_requires_review": candidate.requires_review,
                    "source_uri": candidate.source_uri,
                },
            )
        )
    return gates


def _unit_gates(
    unit_validations: list[UnitValidationResult],
) -> list[ClinicalSemanticNormalizationGate]:
    gates: list[ClinicalSemanticNormalizationGate] = []
    for unit in unit_validations:
        gates.append(
            ClinicalSemanticNormalizationGate(
                gate_type="unit",
                source_field=unit.source_field,
                source_value=unit.source_unit,
                target_resource_type="Observation",
                target_path="Observation.valueQuantity.code",
                location=unit.location,
                unit_validation_id=unit.validation_id,
                proposed_system=unit.standard_system,
                proposed_code=unit.normalized_unit,
                proposed_display=_metadata_text(unit.metadata.get("display")),
                proposed_value=unit.normalized_unit,
                confidence=unit.confidence,
                reason=(
                    "Reviewer approval is required before applying UCUM code "
                    "normalization to valueQuantity."
                ),
                metadata={
                    "unit_status": unit.status,
                    "unit_requires_review": unit.requires_review,
                    "message": unit.message,
                    "preferred_units": unit.metadata.get("preferred_units", []),
                },
            )
        )
    return gates


def _record_field_gates(
    parsed: ParsedData,
    candidates: list[TerminologyCandidate],
) -> list[ClinicalSemanticNormalizationGate]:
    gates: list[ClinicalSemanticNormalizationGate] = []
    candidate_keys = {
        (_location_row(candidate.location), candidate.source_field)
        for candidate in candidates
    }
    for index, record in enumerate(parsed.records, start=1):
        source_row = _source_row(record, fallback=index)
        for field in DATE_FIELDS:
            value = _text(record.get(field))
            if value:
                gates.append(
                    _field_gate(
                        gate_type="date",
                        record=record,
                        field=field,
                        source_row=source_row,
                        parsed=parsed,
                        target_resource_type="Observation",
                        target_path="Observation.effectiveDateTime",
                        proposed_system="ISO-8601",
                        proposed_value=value,
                        reason=(
                            "Reviewer approval is required before canonicalizing "
                            "source dates into clinical effectiveDateTime values."
                        ),
                        metadata={
                            "target_format": "YYYY-MM-DD or full ISO-8601 date/time",
                            "source_format": "source_text",
                        },
                    )
                )
                break
        for field in PATIENT_IDENTIFIER_FIELDS:
            value = _text(record.get(field))
            if value:
                gates.append(
                    _field_gate(
                        gate_type="patient_identifier",
                        record=record,
                        field=field,
                        source_row=source_row,
                        parsed=parsed,
                        target_resource_type="Patient",
                        target_path="Patient.identifier[0].value",
                        proposed_value=value,
                        reason=(
                            "Reviewer approval is required before identity "
                            "normalization, deduplication, or crosswalk mapping."
                        ),
                        metadata={
                            "identity_policy": "preserve_source_identifier_until_reviewed",
                        },
                    )
                )
                break
        gates.extend(
            _missing_candidate_gates(
                parsed=parsed,
                record=record,
                source_row=source_row,
                candidate_keys=candidate_keys,
            )
        )
    return gates


def _missing_candidate_gates(
    *,
    parsed: ParsedData,
    record: dict[str, Any],
    source_row: int,
    candidate_keys: set[tuple[int | None, str]],
) -> list[ClinicalSemanticNormalizationGate]:
    gates: list[ClinicalSemanticNormalizationGate] = []
    field_sets: tuple[
        tuple[ClinicalSemanticNormalizationGateType, tuple[str, ...], str, str, str],
        ...,
    ] = (
        (
            "lab_name",
            LAB_NAME_FIELDS,
            "Observation",
            "Observation.code.coding",
            (
                "No terminology candidate was found; reviewer approval is "
                "required before assigning a lab code."
            ),
        ),
        (
            "medication",
            MEDICATION_FIELDS,
            "MedicationStatement",
            "MedicationStatement.medicationCodeableConcept.coding",
            (
                "No terminology candidate was found; reviewer approval is "
                "required before assigning a medication code."
            ),
        ),
        (
            "diagnosis",
            DIAGNOSIS_FIELDS,
            "Condition",
            "Condition.code.coding",
            (
                "No terminology candidate was found; reviewer approval is "
                "required before assigning a diagnosis code."
            ),
        ),
        (
            "procedure",
            PROCEDURE_FIELDS,
            "Procedure",
            "Procedure.code.coding",
            "No terminology candidate was found; reviewer approval is required before assigning a procedure code.",
        ),
    )
    for gate_type, fields, target_resource_type, target_path, reason in field_sets:
        for field in fields:
            value = _text(record.get(field))
            if not value:
                continue
            if (source_row, field) in candidate_keys or (None, field) in candidate_keys:
                break
            gates.append(
                _field_gate(
                    gate_type=gate_type,
                    record=record,
                    field=field,
                    source_row=source_row,
                    parsed=parsed,
                    target_resource_type=target_resource_type,
                    target_path=target_path,
                    reason=reason,
                    metadata={"candidate_status": "not_found"},
                )
            )
            break
    return gates


def _field_gate(
    *,
    gate_type: ClinicalSemanticNormalizationGateType,
    record: dict[str, Any],
    field: str,
    source_row: int,
    parsed: ParsedData,
    target_resource_type: str,
    target_path: str,
    reason: str,
    proposed_system: str | None = None,
    proposed_value: Any | None = None,
    metadata: dict[str, Any] | None = None,
) -> ClinicalSemanticNormalizationGate:
    return ClinicalSemanticNormalizationGate(
        gate_type=gate_type,
        source_field=field,
        source_value=record.get(field),
        target_resource_type=target_resource_type,
        target_path=target_path,
        location=SourceLocation(
            row=source_row,
            column=field,
            field=field,
            source_ref=parsed.source_ref,
        ),
        proposed_system=proposed_system,
        proposed_value=record.get(field) if proposed_value is None else proposed_value,
        reason=reason,
        metadata=metadata or {},
    )


def _gate_type_for_candidate(
    candidate: TerminologyCandidate,
) -> ClinicalSemanticNormalizationGateType | None:
    if candidate.source_field in LAB_NAME_FIELDS or candidate.standard_system == "LOINC":
        return "lab_name"
    if candidate.source_field in MEDICATION_FIELDS or candidate.standard_system == "RxNorm":
        return "medication"
    if candidate.source_field in PROCEDURE_FIELDS:
        return "procedure"
    if candidate.source_field in DIAGNOSIS_FIELDS:
        return "diagnosis"
    if (
        candidate.standard_system == "SNOMED CT"
        and candidate.source_field not in {"allergy", "allergy_name"}
    ):
        return "diagnosis"
    return None


def _source_row(record: dict[str, Any], *, fallback: int) -> int:
    value = record.get("_source_row")
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _location_row(location: SourceLocation | None) -> int | None:
    return location.row if location else None


def _text(value: Any) -> str:
    return str(value).strip() if value not in (None, "") else ""


def _metadata_text(value: Any) -> str | None:
    text = _text(value)
    return text or None
