"""FHIR-like profiling endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from ojtflow.fhir.profile import profile_fhir_like
from ojtflow.interfaces.api.responses import ok
from ojtflow.interfaces.api.schemas import FhirProfileRequest

router = APIRouter(tags=["fhir"])


@router.post("/fhir/profile")
def fhir_profile(request: FhirProfileRequest) -> dict:
    profile = profile_fhir_like(request.data)
    return ok(profile)

