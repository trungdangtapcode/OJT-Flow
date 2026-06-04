"""OCR evidence endpoint stub."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ojtflow.application.medical_evidence_service import MedicalEvidenceService
from ojtflow.config import Settings
from ojtflow.interfaces.api.deps import get_api_settings, get_medical_evidence_service
from ojtflow.interfaces.api.limits import enforce_inline_json_limit
from ojtflow.interfaces.api.responses import ok
from ojtflow.interfaces.api.schemas import OcrEvidenceRequest

router = APIRouter(tags=["ocr"])


@router.post("/ocr/evidence")
async def ocr_evidence(
    request: OcrEvidenceRequest,
    service: MedicalEvidenceService = Depends(get_medical_evidence_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    enforce_inline_json_limit(request.fields, settings, field_name="fields")
    return ok(service.normalize_ocr_evidence(request.fields))
