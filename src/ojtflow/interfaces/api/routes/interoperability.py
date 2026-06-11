"""Healthcare interoperability routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ojtflow.config import Settings
from ojtflow.interfaces.api.deps import get_api_settings
from ojtflow.interfaces.api.limits import enforce_inline_text_limit
from ojtflow.interfaces.api.responses import ok
from ojtflow.interfaces.api.schemas import (
    BulkFhirNdjsonExportRequest,
    BulkFhirNdjsonImportRequest,
    DicomMetadataProfileRequest,
    DocumentReferenceMapRequest,
    Hl7V2MapRequest,
)
from ojtflow.interoperability.adapters import (
    build_document_reference,
    export_clinical_package_as_bulk_fhir_ndjson,
    map_dicom_to_imaging_study,
    map_hl7_v2_lab_observations,
    parse_bulk_fhir_ndjson,
    profile_dicom_metadata,
)

router = APIRouter(tags=["interoperability"])


@router.post("/interoperability/fhir/bulk/import")
async def import_bulk_fhir_ndjson(
    request: BulkFhirNdjsonImportRequest,
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Parse FHIR Bulk Data NDJSON into lightweight resource records."""

    enforce_inline_text_limit(request.data, settings)
    allowed = set(request.allowed_resource_types) if request.allowed_resource_types else None
    return ok(
        parse_bulk_fhir_ndjson(
            request.data,
            source_ref=request.source_ref,
            allowed_resource_types=allowed,
        )
    )


@router.post("/interoperability/fhir/bulk/export-package")
async def export_bulk_fhir_package(request: BulkFhirNdjsonExportRequest) -> dict:
    """Export a ClinicalPackage as grouped Bulk FHIR NDJSON files."""

    return ok(
        export_clinical_package_as_bulk_fhir_ndjson(
            request.package,
            require_approval=request.require_approval,
        )
    )


@router.post("/interoperability/hl7v2/observations")
async def map_hl7_v2_observations(
    request: Hl7V2MapRequest,
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Parse an HL7 v2 ORU-style message and map OBX rows to Observations."""

    enforce_inline_text_limit(request.data, settings)
    return ok(map_hl7_v2_lab_observations(request.data, source_ref=request.source_ref))


@router.post("/interoperability/dicom/metadata")
async def dicom_metadata_profile(request: DicomMetadataProfileRequest) -> dict:
    """Profile DICOM metadata and return an ImagingStudy-like mapping."""

    profile = profile_dicom_metadata(request.metadata, source_ref=request.source_ref)
    return ok(
        {
            "profile": profile,
            "imaging_study": map_dicom_to_imaging_study(profile),
        }
    )


@router.post("/interoperability/document-reference")
async def document_reference_mapping(request: DocumentReferenceMapRequest) -> dict:
    """Build a DocumentReference-like resource for an uploaded or extracted artifact."""

    return ok(
        build_document_reference(
            document_id=request.document_id,
            filename=request.filename,
            content_type=request.content_type,
            source_ref=request.source_ref,
            description=request.description,
            status=request.status,
        )
    )
