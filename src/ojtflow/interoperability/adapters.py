"""Deterministic healthcare interoperability adapters."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from typing import Any, Iterable

from ojtflow.core.contracts.clinical import (
    ClinicalFieldProvenance,
    ClinicalPackage,
    ClinicalResourceRecord,
)
from ojtflow.core.contracts.interoperability import (
    BulkFhirNdjsonExportFile,
    BulkFhirNdjsonExportPackage,
    BulkFhirNdjsonImportReport,
    BulkFhirNdjsonResource,
    DicomMetadataProfile,
    DocumentReferenceMapping,
    FhirBulkResourceType,
    Hl7V2Message,
    Hl7V2ObservationMapping,
    Hl7V2Segment,
    ImagingStudyMapping,
)
from ojtflow.core.contracts.issue import SourceLocation
from ojtflow.core.errors import ToolExecutionError
from ojtflow.data_tools.hashing import sha256_text


DEFAULT_BULK_FHIR_RESOURCE_TYPES: tuple[FhirBulkResourceType, ...] = (
    "Patient",
    "Observation",
    "DiagnosticReport",
    "DocumentReference",
    "Provenance",
    "AuditEvent",
    "ImagingStudy",
)


def parse_bulk_fhir_ndjson(
    text: str,
    *,
    source_ref: str | None = None,
    allowed_resource_types: set[str] | None = None,
) -> BulkFhirNdjsonImportReport:
    """Parse FHIR Bulk Data NDJSON resources with lightweight validation."""

    return validate_bulk_fhir_ndjson_lines(
        text.splitlines(),
        source_ref=source_ref,
        allowed_resource_types=allowed_resource_types,
    )


def validate_bulk_fhir_ndjson_lines(
    lines: Iterable[str],
    *,
    source_ref: str | None = None,
    allowed_resource_types: set[str] | None = None,
) -> BulkFhirNdjsonImportReport:
    """Validate an iterable of NDJSON lines without requiring a full file object."""

    allowed = allowed_resource_types or set(DEFAULT_BULK_FHIR_RESOURCE_TYPES)
    resources: list[BulkFhirNdjsonResource] = []
    warnings: list[str] = []
    rejected_line_count = 0
    counts: Counter[str] = Counter()
    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            resource = json.loads(stripped)
        except json.JSONDecodeError as exc:
            rejected_line_count += 1
            warnings.append(f"line {line_number} is not valid JSON: {exc.msg}")
            continue
        if not isinstance(resource, dict):
            rejected_line_count += 1
            warnings.append(f"line {line_number} is not a FHIR resource object")
            continue
        resource_type = str(resource.get("resourceType") or "").strip()
        if not resource_type:
            rejected_line_count += 1
            warnings.append(f"line {line_number} is missing resourceType")
            continue
        resource_warnings: list[str] = []
        if resource_type not in allowed:
            resource_warnings.append(f"resourceType {resource_type} is outside selected v0 scope")
        resource_id = _optional_text(resource.get("id"))
        if not resource_id:
            resource_warnings.append("resource id is missing")
        resources.append(
            BulkFhirNdjsonResource(
                line_number=line_number,
                resource_type=resource_type,
                resource_id=resource_id,
                resource=resource,
                warnings=resource_warnings,
            )
        )
        counts[resource_type] += 1
    if not resources:
        warnings.append("No FHIR resources were parsed from NDJSON input.")
    return BulkFhirNdjsonImportReport(
        source_ref=source_ref,
        resource_count=len(resources),
        resource_counts=dict(sorted(counts.items())),
        resources=resources,
        rejected_line_count=rejected_line_count,
        warnings=warnings,
    )


def export_clinical_package_as_bulk_fhir_ndjson(
    package: ClinicalPackage,
    *,
    require_approval: bool = True,
) -> BulkFhirNdjsonExportPackage:
    """Export approved clinical package resources as FHIR Bulk Data NDJSON files."""

    approved, approval_warnings = _clinical_package_export_approval(package)
    if require_approval and not approved:
        raise ToolExecutionError(
            "Clinical package is not approved for Bulk FHIR export.",
            details={"package_id": package.package_id, "warnings": approval_warnings},
        )

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in package.clinical_bundle.resources:
        grouped[record.resource_type].append(record.resource)

    files: list[BulkFhirNdjsonExportFile] = []
    for resource_type, resources in sorted(grouped.items()):
        ndjson = "\n".join(
            json.dumps(resource, separators=(",", ":"), sort_keys=True)
            for resource in resources
        )
        if ndjson:
            ndjson = f"{ndjson}\n"
        files.append(
            BulkFhirNdjsonExportFile(
                resource_type=resource_type,
                filename=f"{resource_type}.ndjson",
                ndjson=ndjson,
                resource_count=len(resources),
                output_hash=sha256_text(ndjson),
            )
        )

    return BulkFhirNdjsonExportPackage(
        package_id=package.package_id,
        workflow_id=package.workflow_id,
        approved_for_export=approved,
        files=files,
        resource_count=sum(file.resource_count for file in files),
        warnings=[
            *approval_warnings,
            "FHIR Bulk export is NDJSON-shaped and still FHIR-like until validated by a target implementation.",
        ],
    )


def parse_hl7_v2_message(text: str) -> Hl7V2Message:
    """Parse a starter HL7 v2 pipe-delimited message."""

    normalized = text.replace("\r\n", "\r").replace("\n", "\r")
    raw_segments = [segment for segment in normalized.split("\r") if segment.strip()]
    if not raw_segments:
        raise ToolExecutionError("HL7 v2 message is empty.")
    if not raw_segments[0].startswith("MSH"):
        raise ToolExecutionError("HL7 v2 message must start with MSH.")

    field_separator = raw_segments[0][3:4] or "|"
    segments: list[Hl7V2Segment] = []
    counts: Counter[str] = Counter()
    warnings: list[str] = []
    for index, raw in enumerate(raw_segments, start=1):
        parts = raw.split(field_separator)
        segment_id = parts[0].strip()
        if not segment_id:
            warnings.append(f"segment {index} is missing segment ID")
            continue
        fields = parts[1:]
        segments.append(Hl7V2Segment(segment_id=segment_id, index=index, fields=fields, raw=raw))
        counts[segment_id] += 1

    if "PID" not in counts:
        warnings.append("PID segment is missing")
    if "OBX" not in counts:
        warnings.append("OBX segment is missing")
    msh = _first_segment(segments, "MSH")
    pid = _first_segment(segments, "PID")
    return Hl7V2Message(
        field_separator=field_separator,
        encoding_characters=_field(msh, 1) or "^~\\&",
        segments=segments,
        segment_counts=dict(sorted(counts.items())),
        message_type=_component(_field(msh, 8), 0),
        patient_id=_component(_field(pid, 3), 0),
        warnings=warnings,
    )


def map_hl7_v2_lab_observations(text: str, *, source_ref: str | None = None) -> Hl7V2ObservationMapping:
    """Map HL7 v2 OBX segments into FHIR-like Observation records."""

    message = parse_hl7_v2_message(text)
    pid = _first_segment(message.segments, "PID")
    patient_id = _component(_field(pid, 3), 0) or "unknown"
    observations: list[ClinicalResourceRecord] = []
    for observation_index, obx in enumerate(
        [segment for segment in message.segments if segment.segment_id == "OBX"],
        start=1,
    ):
        observation_identifier = _field(obx, 3)
        value = _field(obx, 5)
        unit = _field(obx, 6)
        effective = _field(obx, 14) or _field(_first_segment(message.segments, "OBR"), 7)
        code = _component(observation_identifier, 0)
        display = _component(observation_identifier, 1) or code or "Unknown observation"
        resource_id = f"hl7v2-observation-{observation_index}"
        resource = {
            "resourceType": "Observation",
            "id": resource_id,
            "status": "final",
            "code": {"text": display},
            "subject": {"reference": f"Patient/{patient_id}"},
            "effectiveDateTime": _hl7_datetime_to_fhir_like(effective),
            "valueQuantity": {
                "value": _numeric(value),
                "unit": _component(unit, 1) or unit,
            },
        }
        if code:
            resource["code"]["coding"] = [
                {
                    "code": code,
                    "display": display,
                    "system": _hl7_coding_system(_component(observation_identifier, 2)),
                }
            ]
        warnings: list[str] = []
        if _numeric(value) is None:
            warnings.append("obx_value_is_not_numeric")
        if not unit:
            warnings.append("obx_unit_missing")
        observations.append(
            ClinicalResourceRecord(
                resource_id=resource_id,
                resource_type="Observation",
                resource=resource,
                field_provenance=[
                    _hl7_field_provenance("Observation.subject.reference", "PID-3", pid, source_ref),
                    _hl7_field_provenance("Observation.code", "OBX-3", obx, source_ref),
                    _hl7_field_provenance("Observation.valueQuantity.value", "OBX-5", obx, source_ref),
                    _hl7_field_provenance("Observation.valueQuantity.unit", "OBX-6", obx, source_ref),
                    _hl7_field_provenance("Observation.effectiveDateTime", "OBX-14", obx, source_ref),
                ],
                source_row=obx.index,
                review_required=bool(warnings),
                warnings=warnings,
            )
        )
    return Hl7V2ObservationMapping(
        message=message,
        observations=observations,
        warnings=(
            ["No OBX observations could be mapped."] if not observations else []
        ),
    )


def profile_dicom_metadata(
    metadata: dict[str, Any],
    *,
    source_ref: str | None = None,
) -> DicomMetadataProfile:
    """Profile DICOM metadata without reading pixel data."""

    normalized = {_normalize_key(key): value for key, value in metadata.items()}
    patient_id = _optional_text(
        _first_value(normalized, "PatientID", "patient_id", "00100020")
    )
    deidentification_status = "unknown"
    if _optional_text(_first_value(normalized, "PatientIdentityRemoved", "00120062")) in {
        "YES",
        "Yes",
        "yes",
        "true",
        "True",
    }:
        deidentification_status = "deidentified"
    elif patient_id:
        deidentification_status = "identified"

    profile = DicomMetadataProfile(
        study_instance_uid=_optional_text(
            _first_value(normalized, "StudyInstanceUID", "study_instance_uid", "0020000D")
        ),
        series_instance_uid=_optional_text(
            _first_value(normalized, "SeriesInstanceUID", "series_instance_uid", "0020000E")
        ),
        sop_instance_uid=_optional_text(
            _first_value(normalized, "SOPInstanceUID", "sop_instance_uid", "00080018")
        ),
        modality=_optional_text(_first_value(normalized, "Modality", "modality", "00080060")),
        laterality=_optional_text(
            _first_value(normalized, "Laterality", "ImageLaterality", "laterality", "00200062")
        ),
        accession_number=_optional_text(
            _first_value(normalized, "AccessionNumber", "accession_number", "00080050")
        ),
        patient_id_present=bool(patient_id),
        deidentification_status=deidentification_status,
        source_ref=source_ref,
        metadata={
            key: value
            for key, value in metadata.items()
            if key not in {"PixelData", "7FE00010"}
        },
    )
    warnings: list[str] = []
    for field_name in (
        "study_instance_uid",
        "series_instance_uid",
        "sop_instance_uid",
        "modality",
    ):
        if getattr(profile, field_name) is None:
            warnings.append(f"missing_{field_name}")
    if profile.patient_id_present and profile.deidentification_status != "deidentified":
        warnings.append("patient_identifier_present")
    profile.warnings = warnings
    return profile


def map_dicom_to_imaging_study(profile: DicomMetadataProfile) -> ImagingStudyMapping:
    """Map DICOM metadata into an ImagingStudy-like FHIR resource."""

    study_id = profile.study_instance_uid or "unknown-study"
    series_id = profile.series_instance_uid or "unknown-series"
    instance_id = profile.sop_instance_uid or "unknown-instance"
    resource = {
        "resourceType": "ImagingStudy",
        "id": _resource_id("imaging-study", study_id),
        "status": "available",
        "identifier": [{"system": "urn:dicom:uid", "value": study_id}],
        "series": [
            {
                "uid": series_id,
                "modality": {"code": profile.modality or "UNK"},
                "laterality": profile.laterality,
                "instance": [{"uid": instance_id, "sopClass": {}}],
            }
        ],
    }
    if profile.accession_number:
        resource["identifier"].append(
            {"type": {"text": "Accession Number"}, "value": profile.accession_number}
        )
    warnings = [
        *profile.warnings,
        "Pixel data is intentionally not parsed or exported by the v0 DICOM metadata mapper.",
    ]
    record = ClinicalResourceRecord(
        resource_id=str(resource["id"]),
        resource_type="ImagingStudy",
        resource=resource,
        field_provenance=[
            ClinicalFieldProvenance(
                target_path="ImagingStudy.identifier",
                source_field="StudyInstanceUID",
                source_value=profile.study_instance_uid,
                location=SourceLocation(source_ref=profile.source_ref),
                note="Mapped DICOM StudyInstanceUID to ImagingStudy identifier.",
            ),
            ClinicalFieldProvenance(
                target_path="ImagingStudy.series.uid",
                source_field="SeriesInstanceUID",
                source_value=profile.series_instance_uid,
                location=SourceLocation(source_ref=profile.source_ref),
                note="Mapped DICOM SeriesInstanceUID to ImagingStudy series UID.",
            ),
        ],
        review_required=bool(profile.warnings),
        warnings=warnings,
    )
    return ImagingStudyMapping(profile=profile, resource=record, warnings=warnings)


def build_document_reference(
    *,
    document_id: str,
    filename: str,
    content_type: str,
    source_ref: str,
    description: str | None = None,
    status: str = "current",
) -> DocumentReferenceMapping:
    """Build a DocumentReference-like resource for uploaded or extracted documents."""

    resource_id = _resource_id("document-reference", document_id)
    resource = {
        "resourceType": "DocumentReference",
        "id": resource_id,
        "status": status,
        "description": description or filename,
        "content": [
            {
                "attachment": {
                    "contentType": content_type,
                    "title": filename,
                    "url": source_ref,
                }
            }
        ],
    }
    record = ClinicalResourceRecord(
        resource_id=resource_id,
        resource_type="DocumentReference",
        resource=resource,
        field_provenance=[
            ClinicalFieldProvenance(
                target_path="DocumentReference.content.attachment.url",
                source_field="source_ref",
                source_value=source_ref,
                location=SourceLocation(source_ref=source_ref),
                note="Mapped uploaded or extracted document artifact reference to DocumentReference attachment URL.",
            )
        ],
        review_required=False,
        warnings=["DocumentReference is FHIR-like and has not been validated by a full HL7 validator."],
    )
    return DocumentReferenceMapping(resource=record, warnings=list(record.warnings))


def _clinical_package_export_approval(package: ClinicalPackage) -> tuple[bool, list[str]]:
    warnings: list[str] = []
    review_status = (package.review or {}).get("status")
    if review_status in {"approved", "approved_with_edits"}:
        return True, warnings
    if review_status:
        warnings.append(f"clinical package review status is {review_status}")
        return False, warnings
    if any(record.review_required for record in package.clinical_bundle.resources):
        warnings.append("clinical package has resources that still require review")
        return False, warnings
    warnings.append("clinical package has no explicit review record; export allowed because no resource is review-gated")
    return True, warnings


def _first_segment(segments: list[Hl7V2Segment], segment_id: str) -> Hl7V2Segment | None:
    return next((segment for segment in segments if segment.segment_id == segment_id), None)


def _field(segment: Hl7V2Segment | None, one_based_index: int) -> str:
    if segment is None:
        return ""
    index = one_based_index - 1
    if index < 0 or index >= len(segment.fields):
        return ""
    return segment.fields[index]


def _component(value: str, zero_based_index: int) -> str:
    parts = value.split("^")
    if zero_based_index < 0 or zero_based_index >= len(parts):
        return ""
    return parts[zero_based_index].strip()


def _hl7_field_provenance(
    target_path: str,
    source_field: str,
    segment: Hl7V2Segment | None,
    source_ref: str | None,
) -> ClinicalFieldProvenance:
    return ClinicalFieldProvenance(
        target_path=target_path,
        source_field=source_field,
        source_value=segment.raw if segment else None,
        location=SourceLocation(
            row=segment.index if segment else None,
            field=source_field,
            source_ref=f"{source_ref or 'hl7v2'}#{source_field}",
        ),
        note=f"Mapped HL7 v2 {source_field} into {target_path}.",
    )


def _hl7_datetime_to_fhir_like(value: str) -> str:
    clean = value.strip()
    if len(clean) >= 8 and clean[:8].isdigit():
        return f"{clean[:4]}-{clean[4:6]}-{clean[6:8]}"
    return clean


def _hl7_coding_system(value: str) -> str:
    normalized = value.strip().upper()
    if normalized == "LN":
        return "http://loinc.org"
    return normalized or "urn:oid:unknown"


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _numeric(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_key(value: str) -> str:
    return str(value).replace(" ", "").replace("_", "").lower()


def _first_value(metadata: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        normalized = _normalize_key(key)
        if normalized in metadata:
            return metadata[normalized]
    return None


def _resource_id(prefix: str, value: str) -> str:
    safe = "".join(character.lower() if character.isalnum() else "-" for character in value)
    safe = "-".join(part for part in safe.split("-") if part)
    return f"{prefix}-{safe[:48] or 'unknown'}"
