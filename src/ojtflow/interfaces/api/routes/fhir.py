"""FHIR-like profiling endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ojtflow.application.medical_evidence_service import MedicalEvidenceService
from ojtflow.config import Settings
from ojtflow.interfaces.api.deps import get_api_settings, get_medical_evidence_service
from ojtflow.interfaces.api.limits import enforce_inline_text_limit
from ojtflow.interfaces.api.responses import ok
from ojtflow.interfaces.api.schemas import FhirProfileRequest

router = APIRouter(tags=["fhir"])


@router.post("/fhir/profile")
async def fhir_profile(
    request: FhirProfileRequest,
    service: MedicalEvidenceService = Depends(get_medical_evidence_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    enforce_inline_text_limit(request.data, settings)
    return ok(service.profile_fhir_like(request.data))
