"""Multimodal medical evidence contracts reserved for later phases."""

from __future__ import annotations

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.ids import new_id


class OcrField(ContractModel):
    field_id: str = Field(default_factory=lambda: new_id("ocr"))
    name: str
    value: str
    confidence: float
    page: int
    bbox: list[float]
    source_ref: str
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
