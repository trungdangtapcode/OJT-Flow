"""Multimodal medical evidence contracts reserved for later phases."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel, NonBlankStr
from ojtflow.core.ids import new_id


OcrBoxCoordinate = Annotated[float, Field(ge=0.0)]


class OcrEvidenceInput(ContractModel):
    page: int = Field(ge=1)
    name: NonBlankStr
    value: str
    bbox: list[OcrBoxCoordinate] = Field(
        min_length=4,
        max_length=4,
        description="OCR bounding box as [x, y, width, height] in source coordinates.",
    )
    confidence: float = Field(ge=0.0, le=1.0)
    source_ref: NonBlankStr
    normalized_to: str | None = None


class OcrField(ContractModel):
    field_id: str = Field(default_factory=lambda: new_id("ocr"))
    name: NonBlankStr
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    page: int = Field(ge=1)
    bbox: list[OcrBoxCoordinate] = Field(min_length=4, max_length=4)
    source_ref: NonBlankStr
    normalized_to: str | None = None
    requires_review: bool = False


class FhirProfile(ContractModel):
    profile_id: str = Field(default_factory=lambda: new_id("fhir"))
    is_fhir_like: bool
    resource_type: str | None = None
    resource_counts: dict[str, int] = Field(default_factory=dict)
    issues: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    handoff_context: dict = Field(default_factory=dict)
    profile_registry_version: str | None = None
    profiled_resource_types: list[str] = Field(default_factory=list)
    profile_issues: list[dict[str, Any]] = Field(default_factory=list)
    search_parameters: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    profile_evidence: list[dict[str, Any]] = Field(default_factory=list)


class FhirRequiredAnyGroup(ContractModel):
    group_id: NonBlankStr
    fields: list[NonBlankStr]
    message: NonBlankStr


class FhirSearchParameterSeed(ContractModel):
    name: NonBlankStr
    type: NonBlankStr
    target_field: NonBlankStr
    example: NonBlankStr
    standard_systems: list[NonBlankStr] = Field(default_factory=list)


class FhirResourceProfileSpec(ContractModel):
    resource_type: NonBlankStr
    profile_id: NonBlankStr
    clinical_domain: NonBlankStr
    source_url: NonBlankStr
    required_fields: list[NonBlankStr] = Field(default_factory=list)
    required_any: list[FhirRequiredAnyGroup] = Field(default_factory=list)
    search_parameters: list[FhirSearchParameterSeed] = Field(default_factory=list)
    governance_notes: list[NonBlankStr] = Field(default_factory=list)


class FhirResourceProfileCatalog(ContractModel):
    version: NonBlankStr
    fhir_release: NonBlankStr
    source: NonBlankStr
    disclaimer: NonBlankStr
    profiles: list[FhirResourceProfileSpec] = Field(default_factory=list)


class DicomReference(ContractModel):
    study_uid: str
    series_uid: str | None = None
    instance_uid: str | None = None
    frame_number: int | None = None
    deidentified: bool = True


class VisualEvidenceArtifact(ContractModel):
    artifact_id: str = Field(default_factory=lambda: new_id("vis"))
    artifact_type: str
    source_ref: str
    label: str
    artifact_ref: str
    confidence: float | None = None
    requires_clinician_review: bool = True
