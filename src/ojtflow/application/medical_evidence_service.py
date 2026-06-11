"""Application service for healthcare evidence adapters."""

from __future__ import annotations

from ojtflow.core.contracts.enums import EvidenceSourceType, TrustLevel
from ojtflow.core.contracts.evidence import Evidence
from ojtflow.fhir.profile import profile_fhir_like
from ojtflow.medical.contracts import OcrEvidenceInput, OcrField

OCR_LOW_CONFIDENCE_THRESHOLD = 0.8


class MedicalEvidenceService:
    """Own lightweight FHIR-like and OCR evidence contracts outside web routes."""

    def profile_fhir_like(self, data: str) -> dict:
        return profile_fhir_like(data)

    def normalize_ocr_evidence(self, fields: list[OcrEvidenceInput]) -> dict:
        normalized_fields: list[OcrField] = []
        evidence: list[Evidence] = []
        for item in fields:
            requires_review = item.confidence < OCR_LOW_CONFIDENCE_THRESHOLD
            field = OcrField(
                name=item.name,
                value=item.value,
                confidence=item.confidence,
                page=item.page,
                bbox=item.bbox,
                source_ref=item.source_ref,
                normalized_to=item.normalized_to,
                requires_review=requires_review,
            )
            normalized_fields.append(field)
            evidence.append(
                Evidence(
                    source_type=EvidenceSourceType.OCR_BOX,
                    source_id=f"ocr:{field.field_id}",
                    source_version="ocr_evidence.v0",
                    claim=f"OCR extracted field '{field.name}' from page {field.page}",
                    locator={
                        "page": field.page,
                        "bbox": field.bbox,
                        "field": field.name,
                        "source_ref": field.source_ref,
                    },
                    confidence=field.confidence,
                    trust_level=TrustLevel.USER_PROVIDED,
                )
            )
        return {
            "fields": normalized_fields,
            "evidence": evidence,
            "requires_review": any(field.requires_review for field in normalized_fields),
        }
