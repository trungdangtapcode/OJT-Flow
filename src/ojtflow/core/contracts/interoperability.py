"""Healthcare interoperability contracts for Month 7 adapters."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel, NonBlankStr
from ojtflow.core.contracts.clinical import ClinicalResourceRecord
from ojtflow.core.contracts.enums import DataFormat


FhirBulkResourceType = Literal[
    "Patient",
    "Observation",
    "DiagnosticReport",
    "DocumentReference",
    "Provenance",
    "AuditEvent",
    "ImagingStudy",
]


class BulkFhirNdjsonResource(ContractModel):
    line_number: int = Field(ge=1)
    resource_type: NonBlankStr
    resource_id: NonBlankStr | None = None
    resource: dict[str, Any]
    warnings: list[NonBlankStr] = Field(default_factory=list)


class BulkFhirNdjsonImportReport(ContractModel):
    format: Literal[DataFormat.NDJSON] = DataFormat.NDJSON
    source_ref: NonBlankStr | None = None
    resource_count: int = Field(ge=0)
    resource_counts: dict[str, int] = Field(default_factory=dict)
    resources: list[BulkFhirNdjsonResource] = Field(default_factory=list)
    rejected_line_count: int = Field(ge=0)
    warnings: list[NonBlankStr] = Field(default_factory=list)


class BulkFhirNdjsonExportFile(ContractModel):
    resource_type: NonBlankStr
    filename: NonBlankStr
    ndjson: str
    resource_count: int = Field(ge=0)
    output_hash: NonBlankStr


class BulkFhirNdjsonExportPackage(ContractModel):
    package_id: NonBlankStr
    workflow_id: NonBlankStr
    approved_for_export: bool
    files: list[BulkFhirNdjsonExportFile] = Field(default_factory=list)
    resource_count: int = Field(ge=0)
    warnings: list[NonBlankStr] = Field(default_factory=list)


class Hl7V2Segment(ContractModel):
    segment_id: NonBlankStr
    index: int = Field(ge=1)
    fields: list[str] = Field(default_factory=list)
    raw: NonBlankStr


class Hl7V2Message(ContractModel):
    field_separator: NonBlankStr = "|"
    encoding_characters: NonBlankStr = "^~\\&"
    segments: list[Hl7V2Segment] = Field(default_factory=list)
    segment_counts: dict[str, int] = Field(default_factory=dict)
    message_type: NonBlankStr | None = None
    patient_id: NonBlankStr | None = None
    warnings: list[NonBlankStr] = Field(default_factory=list)


class Hl7V2ObservationMapping(ContractModel):
    message: Hl7V2Message
    observations: list[ClinicalResourceRecord] = Field(default_factory=list)
    warnings: list[NonBlankStr] = Field(default_factory=list)


class DicomMetadataProfile(ContractModel):
    study_instance_uid: NonBlankStr | None = None
    series_instance_uid: NonBlankStr | None = None
    sop_instance_uid: NonBlankStr | None = None
    modality: NonBlankStr | None = None
    laterality: NonBlankStr | None = None
    accession_number: NonBlankStr | None = None
    patient_id_present: bool = False
    deidentification_status: Literal["deidentified", "identified", "unknown"] = "unknown"
    source_ref: NonBlankStr | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    warnings: list[NonBlankStr] = Field(default_factory=list)


class ImagingStudyMapping(ContractModel):
    profile: DicomMetadataProfile
    resource: ClinicalResourceRecord
    warnings: list[NonBlankStr] = Field(default_factory=list)


class DocumentReferenceMapping(ContractModel):
    resource: ClinicalResourceRecord
    warnings: list[NonBlankStr] = Field(default_factory=list)
