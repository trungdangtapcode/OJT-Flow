"""OCR evidence endpoint stub."""

from __future__ import annotations

from fastapi import APIRouter

from ojtflow.core.contracts.enums import EvidenceSourceType, TrustLevel
from ojtflow.core.contracts.evidence import Evidence
from ojtflow.interfaces.api.responses import ok
from ojtflow.interfaces.api.schemas import OcrEvidenceRequest
from ojtflow.medical.contracts import OcrField

router = APIRouter(tags=["ocr"])


@router.post("/ocr/evidence")
def ocr_evidence(request: OcrEvidenceRequest) -> dict:
    fields: list[OcrField] = []
    evidence: list[Evidence] = []
    for item in request.fields:
        requires_review = item.confidence < 0.8
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
        fields.append(field)
        evidence.append(
            Evidence(
                source_type=EvidenceSourceType.OCR_BOX,
                source_id=f"ocr:{field.field_id}",
                source_version="ocr_stub.v0",
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
    return ok(
        {
            "fields": fields,
            "evidence": evidence,
            "requires_review": any(field.requires_review for field in fields),
        }
    )

