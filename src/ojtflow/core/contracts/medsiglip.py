"""Contracts for the MedSigLIP medical image encoder service."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator

from ojtflow.core.contracts.base import ContractModel, NonBlankStr


class MedSiglipImageInput(ContractModel):
    """One inline image submitted to the MedSigLIP service."""

    image_base64: NonBlankStr
    mime_type: NonBlankStr = "image/png"
    source_ref: NonBlankStr | None = None

    @field_validator("mime_type")
    @classmethod
    def _validate_mime_type(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {
            "image/png",
            "image/jpeg",
            "image/jpg",
            "image/webp",
            "image/tiff",
            "image/bmp",
            "image/gif",
        }:
            raise ValueError("mime_type must be a supported image media type")
        return "image/jpeg" if normalized == "image/jpg" else normalized


class MedSiglipClassificationRequest(ContractModel):
    """Zero-shot image classification request for MedSigLIP."""

    images: list[MedSiglipImageInput] = Field(min_length=1, max_length=8)
    candidate_labels: list[NonBlankStr] = Field(min_length=1, max_length=100)
    include_embeddings: bool = False

    @field_validator("candidate_labels")
    @classmethod
    def _dedupe_candidate_labels(cls, value: list[str]) -> list[str]:
        labels: list[str] = []
        seen: set[str] = set()
        for item in value:
            label = item.strip()
            key = label.casefold()
            if key in seen:
                continue
            seen.add(key)
            labels.append(label)
        if not labels:
            raise ValueError("candidate_labels must include at least one non-blank label")
        return labels


class MedSiglipPrediction(ContractModel):
    """One candidate label score."""

    label: NonBlankStr
    score: float = Field(ge=0.0, le=1.0)


class MedSiglipImageClassification(ContractModel):
    """Classification output for one image."""

    image_index: int = Field(ge=0)
    source_ref: str | None = None
    predictions: list[MedSiglipPrediction]
    image_embedding: list[float] | None = None


class MedSiglipClassificationResult(ContractModel):
    """MedSigLIP zero-shot classification result."""

    model: NonBlankStr
    device: NonBlankStr
    classifications: list[MedSiglipImageClassification]
    text_embeddings: list[list[float]] | None = None
    elapsed_ms: float = Field(ge=0.0)
    limitations: list[str] = Field(default_factory=list)


class MedSiglipServiceStatus(ContractModel):
    """Sanitized model service status."""

    status: Literal["ok", "disabled", "unavailable"]
    enabled: bool
    model: str
    base_url_configured: bool
    service_url: str | None = None
    device: str | None = None
    detail: str | None = None
