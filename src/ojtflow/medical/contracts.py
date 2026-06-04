"""Multimodal medical evidence contracts reserved for later phases."""

from __future__ import annotations

from typing import Annotated

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
