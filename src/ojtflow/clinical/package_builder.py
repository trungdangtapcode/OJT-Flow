"""ClinicalPackage v0 builder for governed FHIR-like workflow output."""

from __future__ import annotations

import re
from typing import Any

from ojtflow.clinical.terminology import terminology_candidates_for_lab_records
from ojtflow.core.contracts.clinical import (
    ClinicalBundle,
    ClinicalFieldProvenance,
    ClinicalOperationOutcome,
    ClinicalOperationOutcomeIssue,
    ClinicalPackage,
    ClinicalPackageRawInput,
    ClinicalProvenanceRecord,
    ClinicalResourceRecord,
)
from ojtflow.core.contracts.data import ParsedData
from ojtflow.core.contracts.enums import DataFormat
from ojtflow.core.contracts.issue import SourceLocation
from ojtflow.core.contracts.workflow import WorkflowState
from ojtflow.fhir.profile import load_fhir_resource_profile_catalog


def build_clinical_package(
    *,
    workflow: WorkflowState,
    parsed: ParsedData,
    schema_id: str | None,
    output_ref: str | None = None,
) -> ClinicalPackage | None:
    """Build a canonical clinical package when the parsed data has a known mapping."""

    if workflow.input is None:
        return None
    resources: list[ClinicalResourceRecord] = []
    warnings: list[str] = []
    terminology_candidates = []
    unit_validations = []
    if schema_id == "lab_result_v1":
        resources = _lab_result_resources(parsed, workflow)
        terminology_candidates, unit_validations = terminology_candidates_for_lab_records(parsed)
        if not resources:
            warnings.append("No lab_result_v1 records were available for FHIR-like mapping.")
    elif _is_fhir_like_payload(parsed):
        resources = _preserve_fhir_like_resources(parsed)
    else:
        return None

    entry = [_bundle_entry(record) for record in resources]
    output_refs = [output_ref] if output_ref else []
    evidence = list(workflow.retrieved_context)
    fhir_profile_context = _fhir_profile_context(resources)
    return ClinicalPackage(
        workflow_id=workflow.workflow_id,
        raw_input=ClinicalPackageRawInput(
            dataset_ref=workflow.input.dataset_ref,
            input_hash=workflow.input.input_hash,
            declared_format=workflow.input.declared_format,
            detected_format=workflow.input.detected_format,
        ),
        clinical_bundle=ClinicalBundle(entry=entry, resources=resources),
        operation_outcome=_operation_outcome_from_workflow(workflow),
        validation_report_id=(
            workflow.validation_report.report_id if workflow.validation_report else None
        ),
        evidence=evidence,
        terminology_candidates=terminology_candidates,
        unit_validations=unit_validations,
        provenance=_package_provenance(
            workflow=workflow,
            resources=resources,
            evidence_ids=[item.evidence_id for item in evidence],
            terminology_candidate_ids=[
                item.candidate_id for item in terminology_candidates
            ],
            unit_validation_ids=[item.validation_id for item in unit_validations],
            output_refs=output_refs,
        ),
        review=workflow.review.model_dump(mode="json") if workflow.review else None,
        audit_event_refs=list(workflow.audit_event_refs),
        output_refs=output_refs,
        handoff_context={
            "graphner_ready": bool(resources),
            "rag_query_terms": _rag_query_terms(resources, workflow),
            "schema_id": schema_id,
            "resource_types": sorted({record.resource_type for record in resources}),
            "resource_count": len(resources),
            "operation_outcome_issue_count": (
                len(workflow.validation_report.issues) if workflow.validation_report else 0
            ),
            "terminology_candidate_count": len(terminology_candidates),
            "unit_validation_count": len(unit_validations),
            "terminology_candidates": [
                item.model_dump(mode="json") for item in terminology_candidates
            ],
            "unit_validations": [
                item.model_dump(mode="json") for item in unit_validations
            ],
            "fhir_like": True,
            "fhir_compliance": "fhir_like_not_validated",
            **fhir_profile_context,
        },
        warnings=[*warnings, *_package_warnings(resources)],
    )


def _lab_result_resources(
    parsed: ParsedData,
    workflow: WorkflowState,
) -> list[ClinicalResourceRecord]:
    if not parsed.records:
        return []
    source_ref = workflow.input.dataset_ref if workflow.input else parsed.source_ref
    patients = _lab_result_patients(parsed)
    observations = _lab_result_observations(parsed)
    reports = _lab_result_diagnostic_reports(parsed, patients=patients, observations=observations)
    document = _lab_result_document_reference(
        parsed,
        patients=patients,
        source_ref=source_ref,
    )
    return [*patients, *observations, *reports, document]


def _lab_result_patients(parsed: ParsedData) -> list[ClinicalResourceRecord]:
    patients: dict[str, ClinicalResourceRecord] = {}
    for index, record in enumerate(parsed.records, start=1):
        source_row = _source_row(record, fallback=index)
        patient_id = _text(record.get("patient_id"))
        resource_id = _safe_fhir_id(patient_id, fallback="unknown")
        if resource_id in patients:
            continue
        warnings: list[str] = []
        if not patient_id:
            warnings.append("missing_patient_identifier")
        resource = {
            "resourceType": "Patient",
            "id": resource_id,
            "identifier": [{"value": patient_id}] if patient_id else [],
        }
        field_provenance = [
            _constant_provenance(
                target_path="Patient.resourceType",
                parsed=parsed,
                source_row=source_row,
                note="Generated FHIR-like resourceType for Patient.",
            ),
            _field_provenance(
                target_path="Patient.id",
                record=record,
                field="patient_id",
                parsed=parsed,
                source_row=source_row,
                note="Mapped patient_id to FHIR-like Patient.id without identity normalization.",
                review_required=not patient_id,
            ),
            _field_provenance(
                target_path="Patient.identifier[0].value",
                record=record,
                field="patient_id",
                parsed=parsed,
                source_row=source_row,
                note="Mapped patient_id to FHIR-like Patient.identifier value without normalization.",
                review_required=not patient_id,
            ),
        ]
        patients[resource_id] = ClinicalResourceRecord(
            resource_id=resource_id,
            resource_type="Patient",
            resource=resource,
            field_provenance=field_provenance,
            source_row=source_row,
            review_required=bool(warnings),
            warnings=warnings,
        )
    return list(patients.values())


def _lab_result_observations(parsed: ParsedData) -> list[ClinicalResourceRecord]:
    records: list[ClinicalResourceRecord] = []
    for index, record in enumerate(parsed.records, start=1):
        source_row = _source_row(record, fallback=index)
        resource_id = f"observation-{source_row}"
        patient_id = _text(record.get("patient_id"))
        patient_resource_id = _safe_fhir_id(patient_id, fallback="unknown")
        lab_name = _text(record.get("lab_name")) or "Unknown lab"
        date_value = _text(record.get("date"))
        unit = _text(record.get("unit"))
        numeric_value = _numeric(record.get("value"))
        value_quantity: dict[str, Any] = {
            "value": numeric_value,
            "unit": unit,
        }
        if unit:
            value_quantity["system"] = "http://unitsofmeasure.org"
            value_quantity["code"] = unit
        resource = {
            "resourceType": "Observation",
            "id": resource_id,
            "status": "final",
            "code": {"text": lab_name},
            "subject": {"reference": f"Patient/{patient_resource_id}"},
            "effectiveDateTime": date_value,
            "valueQuantity": value_quantity,
        }
        warnings: list[str] = []
        if not patient_id:
            warnings.append("missing_patient_identifier")
        if not date_value:
            warnings.append("missing_effective_date")
        if numeric_value is None:
            warnings.append("missing_or_non_numeric_value")
        if not unit:
            warnings.append("missing_unit_requires_review")
        field_provenance = [
            _constant_provenance(
                target_path="Observation.resourceType",
                parsed=parsed,
                source_row=source_row,
                note="Generated FHIR-like resourceType for Observation.",
            ),
            _derived_provenance(
                target_path="Observation.id",
                parsed=parsed,
                source_row=source_row,
                note="Derived stable Observation.id from the parsed source row.",
            ),
            _constant_provenance(
                target_path="Observation.status",
                parsed=parsed,
                source_row=source_row,
                note="Defaulted Observation.status to final for parsed lab result rows.",
            ),
            _field_provenance(
                target_path="Observation.subject.reference",
                record=record,
                field="patient_id",
                parsed=parsed,
                source_row=source_row,
                note="Mapped patient_id to FHIR-like subject reference without identity normalization.",
            ),
            _field_provenance(
                target_path="Observation.effectiveDateTime",
                record=record,
                field="date",
                parsed=parsed,
                source_row=source_row,
                note="Mapped source date to FHIR-like effectiveDateTime.",
            ),
            _field_provenance(
                target_path="Observation.code.text",
                record=record,
                field="lab_name",
                parsed=parsed,
                source_row=source_row,
                note="Mapped lab_name to code.text; LOINC coding remains review-gated.",
            ),
            _field_provenance(
                target_path="Observation.valueQuantity.value",
                record=record,
                field="value",
                parsed=parsed,
                source_row=source_row,
                note="Mapped source value to valueQuantity.value when numeric.",
            ),
            _field_provenance(
                target_path="Observation.valueQuantity.unit",
                record=record,
                field="unit",
                parsed=parsed,
                source_row=source_row,
                note="Mapped source unit to valueQuantity.unit; UCUM validation remains review-gated.",
                review_required=not unit,
            ),
        ]
        records.append(
            ClinicalResourceRecord(
                resource_id=resource_id,
                resource_type="Observation",
                resource=resource,
                field_provenance=field_provenance,
                source_row=source_row,
                review_required=bool(warnings),
                warnings=warnings,
            )
        )
    return records


def _lab_result_diagnostic_reports(
    parsed: ParsedData,
    *,
    patients: list[ClinicalResourceRecord],
    observations: list[ClinicalResourceRecord],
) -> list[ClinicalResourceRecord]:
    patient_ids = {patient.resource_id for patient in patients}
    observations_by_patient = {patient_id: [] for patient_id in patient_ids}
    row_by_patient: dict[str, dict[str, Any]] = {}
    for observation in observations:
        subject = observation.resource.get("subject", {})
        reference = subject.get("reference") if isinstance(subject, dict) else None
        patient_id = str(reference).split("/", 1)[1] if isinstance(reference, str) and "/" in reference else "unknown"
        observations_by_patient.setdefault(patient_id, []).append(observation)
        if patient_id not in row_by_patient:
            row = observation.source_row or 1
            row_by_patient[patient_id] = _record_for_source_row(parsed, row)

    reports: list[ClinicalResourceRecord] = []
    for patient_id, patient_observations in observations_by_patient.items():
        if not patient_observations:
            continue
        source_row = patient_observations[0].source_row or 1
        source_record = row_by_patient.get(patient_id, {})
        resource_id = f"diagnostic-report-{patient_id}"
        first_date = _text(source_record.get("date"))
        resource: dict[str, Any] = {
            "resourceType": "DiagnosticReport",
            "id": resource_id,
            "status": "final",
            "code": {"text": "Laboratory report"},
            "subject": {"reference": f"Patient/{patient_id}"},
            "result": [
                {"reference": f"Observation/{observation.resource_id}"}
                for observation in patient_observations
            ],
        }
        if first_date:
            resource["effectiveDateTime"] = first_date
        field_provenance = [
            _constant_provenance(
                target_path="DiagnosticReport.resourceType",
                parsed=parsed,
                source_row=source_row,
                note="Generated FHIR-like resourceType for DiagnosticReport.",
            ),
            _derived_provenance(
                target_path="DiagnosticReport.id",
                parsed=parsed,
                source_row=source_row,
                note="Derived DiagnosticReport.id from the Patient reference.",
            ),
            _constant_provenance(
                target_path="DiagnosticReport.status",
                parsed=parsed,
                source_row=source_row,
                note="Defaulted DiagnosticReport.status to final for grouped lab results.",
            ),
            _constant_provenance(
                target_path="DiagnosticReport.code.text",
                parsed=parsed,
                source_row=source_row,
                note="Defaulted DiagnosticReport.code.text to Laboratory report for grouped lab rows.",
            ),
            _field_provenance(
                target_path="DiagnosticReport.subject.reference",
                record=source_record,
                field="patient_id",
                parsed=parsed,
                source_row=source_row,
                note="Mapped patient_id to DiagnosticReport.subject reference.",
                review_required=patient_id == "unknown",
            ),
            _derived_provenance(
                target_path="DiagnosticReport.result",
                parsed=parsed,
                source_row=source_row,
                note="Derived DiagnosticReport.result references from generated Observation resources.",
            ),
        ]
        if first_date:
            field_provenance.append(
                _field_provenance(
                    target_path="DiagnosticReport.effectiveDateTime",
                    record=source_record,
                    field="date",
                    parsed=parsed,
                    source_row=source_row,
                    note="Mapped source date to DiagnosticReport.effectiveDateTime.",
                )
            )
        reports.append(
            ClinicalResourceRecord(
                resource_id=resource_id,
                resource_type="DiagnosticReport",
                resource=resource,
                field_provenance=field_provenance,
                source_row=source_row,
                review_required=patient_id == "unknown",
                warnings=["missing_patient_identifier"] if patient_id == "unknown" else [],
            )
        )
    return reports


def _lab_result_document_reference(
    parsed: ParsedData,
    *,
    patients: list[ClinicalResourceRecord],
    source_ref: str | None,
) -> ClinicalResourceRecord:
    source_row = _source_row(parsed.records[0], fallback=1) if parsed.records else 1
    resource_id = "document-reference-source"
    patient_refs = [
        {"reference": f"Patient/{patient.resource_id}"}
        for patient in patients
        if patient.resource_id != "unknown"
    ]
    resource: dict[str, Any] = {
        "resourceType": "DocumentReference",
        "id": resource_id,
        "status": "current",
        "type": {"text": "Source dataset"},
        "content": [
            {
                "attachment": {
                    "url": source_ref or parsed.source_ref or "ojtflow://source/unavailable",
                    "title": "OJTFlow source dataset",
                }
            }
        ],
    }
    if len(patient_refs) == 1:
        resource["subject"] = patient_refs[0]
    elif patient_refs:
        resource["context"] = {"related": patient_refs}
    else:
        resource["context"] = {"related": []}
    return ClinicalResourceRecord(
        resource_id=resource_id,
        resource_type="DocumentReference",
        resource=resource,
        field_provenance=[
            _constant_provenance(
                target_path="DocumentReference.resourceType",
                parsed=parsed,
                source_row=source_row,
                note="Generated FHIR-like resourceType for DocumentReference.",
            ),
            _derived_provenance(
                target_path="DocumentReference.id",
                parsed=parsed,
                source_row=source_row,
                note="Derived DocumentReference.id for the workflow source artifact.",
            ),
            _constant_provenance(
                target_path="DocumentReference.status",
                parsed=parsed,
                source_row=source_row,
                note="Defaulted DocumentReference.status to current for the source artifact pointer.",
            ),
            _constant_provenance(
                target_path="DocumentReference.type.text",
                parsed=parsed,
                source_row=source_row,
                note="Defaulted DocumentReference.type.text to Source dataset.",
            ),
            _derived_provenance(
                target_path="DocumentReference.content[0].attachment.url",
                parsed=parsed,
                source_row=source_row,
                note="Linked DocumentReference content to the governed workflow input artifact reference.",
            ),
            _derived_provenance(
                target_path=(
                    "DocumentReference.subject.reference"
                    if len(patient_refs) == 1
                    else "DocumentReference.context.related"
                ),
                parsed=parsed,
                source_row=source_row,
                note="Linked DocumentReference subject/context to generated Patient resources.",
                review_required=not patient_refs,
            ),
        ],
        source_row=source_row,
        review_required=not patient_refs,
        warnings=["missing_patient_identifier"] if not patient_refs else [],
    )


def _preserve_fhir_like_resources(parsed: ParsedData) -> list[ClinicalResourceRecord]:
    content = parsed.content
    payloads: list[dict[str, Any]]
    if isinstance(content, dict) and content.get("resourceType") == "Bundle":
        payloads = [
            entry["resource"]
            for entry in content.get("entry", [])
            if isinstance(entry, dict) and isinstance(entry.get("resource"), dict)
        ]
    elif isinstance(content, dict) and content.get("resourceType"):
        payloads = [content]
    else:
        payloads = []
    resources: list[ClinicalResourceRecord] = []
    for index, resource in enumerate(payloads, start=1):
        resource_type = str(resource.get("resourceType") or "Resource")
        resource_id = str(resource.get("id") or f"{resource_type.lower()}-{index}")
        resources.append(
            ClinicalResourceRecord(
                resource_id=resource_id,
                resource_type=resource_type,
                resource=dict(resource),
                field_provenance=[
                    ClinicalFieldProvenance(
                        target_path=f"{resource_type}",
                        location=SourceLocation(source_ref=parsed.source_ref),
                        derivation="source",
                        note="Preserved submitted FHIR-like resource without full HL7 validation.",
                    )
                ],
                review_required=False,
                warnings=["fhir_like_resource_preserved_without_full_hl7_validation"],
            )
        )
    return resources


def _field_provenance(
    *,
    target_path: str,
    record: dict[str, Any],
    field: str,
    parsed: ParsedData,
    source_row: int,
    note: str,
    review_required: bool = False,
) -> ClinicalFieldProvenance:
    value = record.get(field)
    return ClinicalFieldProvenance(
        target_path=target_path,
        source_field=field,
        source_value=value,
        location=SourceLocation(
            row=source_row,
            column=field,
            field=field,
            source_ref=parsed.source_ref,
        ),
        derivation="review_required" if review_required else "source",
        note=note,
    )


def _constant_provenance(
    *,
    target_path: str,
    parsed: ParsedData,
    source_row: int,
    note: str,
) -> ClinicalFieldProvenance:
    return ClinicalFieldProvenance(
        target_path=target_path,
        location=SourceLocation(row=source_row, source_ref=parsed.source_ref),
        derivation="defaulted",
        note=note,
    )


def _derived_provenance(
    *,
    target_path: str,
    parsed: ParsedData,
    source_row: int,
    note: str,
    review_required: bool = False,
) -> ClinicalFieldProvenance:
    return ClinicalFieldProvenance(
        target_path=target_path,
        location=SourceLocation(row=source_row, source_ref=parsed.source_ref),
        derivation="review_required" if review_required else "derived",
        note=note,
    )


def _operation_outcome_from_workflow(workflow: WorkflowState) -> ClinicalOperationOutcome:
    if workflow.validation_report is None:
        return ClinicalOperationOutcome(issue=[])
    return ClinicalOperationOutcome(
        issue=[
            ClinicalOperationOutcomeIssue(
                severity=issue.severity,
                code=issue.kind,
                diagnostics=issue.message,
                expression=_operation_outcome_expression(issue.location),
                issue_id=issue.issue_id,
                location=issue.location,
                requires_review=issue.requires_review,
            )
            for issue in workflow.validation_report.issues
        ]
    )


def _package_provenance(
    *,
    workflow: WorkflowState,
    resources: list[ClinicalResourceRecord],
    evidence_ids: list[str],
    terminology_candidate_ids: list[str],
    unit_validation_ids: list[str],
    output_refs: list[str],
) -> list[ClinicalProvenanceRecord]:
    input_ref = workflow.input.dataset_ref if workflow.input else None
    target_refs = [record.resource_id for record in resources]
    issue_ids = (
        [issue.issue_id for issue in workflow.validation_report.issues]
        if workflow.validation_report
        else []
    )
    records = [
        ClinicalProvenanceRecord(
            activity="parse",
            agent="parser_agent",
            target_refs=target_refs,
            source_refs=[input_ref] if input_ref else [],
            summary="Parsed workflow input before clinical package construction.",
        ),
        ClinicalProvenanceRecord(
            activity="validate",
            agent="validation_agent",
            target_refs=target_refs,
            source_refs=[input_ref] if input_ref else [],
            issue_ids=issue_ids,
            summary="Attached validation results as OperationOutcome-like issues.",
        ),
        ClinicalProvenanceRecord(
            activity="map",
            agent="clinical_package_builder",
            target_refs=target_refs,
            source_refs=[input_ref] if input_ref else [],
            evidence_ids=evidence_ids,
            summary="Mapped parsed healthcare data into FHIR-like package resources.",
            metadata={
                "terminology_candidate_ids": terminology_candidate_ids,
                "unit_validation_ids": unit_validation_ids,
            },
        ),
    ]
    if evidence_ids:
        records.append(
            ClinicalProvenanceRecord(
                activity="retrieve_evidence",
                agent="retrieval_agent",
                target_refs=target_refs,
                evidence_ids=evidence_ids,
                summary="Linked trusted retrieval evidence to the clinical package.",
            )
        )
    if workflow.review:
        records.append(
            ClinicalProvenanceRecord(
                activity="review",
                agent="review_agent",
                target_refs=target_refs,
                summary=f"Linked human review state: {workflow.review.status.value}.",
                metadata={"review_id": workflow.review.review_id},
            )
        )
    if output_refs:
        records.append(
            ClinicalProvenanceRecord(
                activity="transform",
                agent="transformation_agent",
                target_refs=target_refs,
                source_refs=output_refs,
                summary="Linked generated workflow output artifact to package.",
            )
        )
    return records


def _bundle_entry(record: ClinicalResourceRecord) -> dict[str, Any]:
    return {
        "fullUrl": f"urn:uuid:{record.resource_id}",
        "resource": record.resource,
    }


def _operation_outcome_expression(location: SourceLocation | None) -> list[str]:
    if location is None:
        return []
    if location.field:
        return [location.field]
    if location.column:
        return [location.column]
    return []


def _rag_query_terms(resources: list[ClinicalResourceRecord], workflow: WorkflowState) -> list[str]:
    terms = sorted({record.resource_type for record in resources})
    if workflow.validation_report:
        terms.extend(sorted({issue.kind for issue in workflow.validation_report.issues})[:8])
    return terms


def _fhir_profile_context(resources: list[ClinicalResourceRecord]) -> dict[str, Any]:
    catalog = load_fhir_resource_profile_catalog()
    profiles_by_type = {profile.resource_type: profile for profile in catalog.profiles}
    resource_types = sorted({record.resource_type for record in resources})
    profile_ids: dict[str, str] = {}
    profile_sources: dict[str, str] = {}
    search_parameters_by_resource: dict[str, list[dict[str, Any]]] = {}
    for resource_type in resource_types:
        profile = profiles_by_type.get(resource_type)
        if profile is None:
            continue
        profile_ids[resource_type] = profile.profile_id
        profile_sources[resource_type] = profile.source_url
        search_parameters_by_resource[resource_type] = [
            parameter.model_dump(mode="json")
            for parameter in profile.search_parameters
        ]
    return {
        "fhir_profile_registry_version": catalog.version,
        "fhir_release": catalog.fhir_release,
        "fhir_resource_profile_ids": profile_ids,
        "fhir_profile_sources": profile_sources,
        "fhir_search_parameters_by_resource": search_parameters_by_resource,
    }


def _package_warnings(resources: list[ClinicalResourceRecord]) -> list[str]:
    warnings = ["FHIR-like package has not been validated by a full HL7 FHIR validator."]
    if any(record.review_required for record in resources):
        warnings.append("One or more generated resources require human review.")
    return warnings


def _is_fhir_like_payload(parsed: ParsedData) -> bool:
    return isinstance(parsed.content, dict) and bool(parsed.content.get("resourceType"))


def _source_row(record: dict[str, Any], *, fallback: int) -> int:
    value = record.get("_source_row")
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _record_for_source_row(parsed: ParsedData, source_row: int) -> dict[str, Any]:
    for record in parsed.records:
        if _source_row(record, fallback=-1) == source_row:
            return record
    return parsed.records[0] if parsed.records else {}


FHIR_ID_PATTERN = re.compile(r"[^A-Za-z0-9.-]+")


def _safe_fhir_id(value: str, *, fallback: str) -> str:
    normalized = FHIR_ID_PATTERN.sub("-", value.strip()).strip("-.")
    if not normalized:
        return fallback
    return normalized[:64]


def _text(value: Any) -> str:
    return str(value).strip() if value not in (None, "") else ""


def _numeric(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
