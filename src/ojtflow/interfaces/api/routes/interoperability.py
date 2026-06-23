"""Healthcare interoperability routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ojtflow.application.workflow_service import WorkflowService
from ojtflow.config import Settings
from ojtflow.interfaces.api.deps import get_api_settings, get_workflow_service
from ojtflow.interfaces.api.limits import enforce_inline_text_limit
from ojtflow.interfaces.api.responses import ok
from ojtflow.interfaces.api.schemas import (
    BulkFhirNdjsonExportRequest,
    BulkFhirNdjsonImportRequest,
    ClinicalPackageImportValidationRequest,
    DicomMetadataProfileRequest,
    DocumentReferenceMapRequest,
    EtlExportPackageRequest,
    ExternalApiCacheMetadataRequest,
    ExternalLinkLaunchRequest,
    Hl7V2MapRequest,
    OmopPreviewRequest,
    SourceIngestionApprovalPreviewRequest,
)
from ojtflow.interoperability.analytics import (
    build_etl_export_package,
    build_external_api_cache_metadata,
    build_omop_export_preview,
    evaluate_source_ingestion_candidate,
    launch_external_link,
    load_cohort_research_workflow,
    load_dqd_compatibility,
    load_external_api_cache_policy,
    load_external_link_launchers,
    load_external_source_connectors,
    load_omop_mapping_profile,
    load_omop_vocabulary_candidate_catalog,
    load_source_ingestion_approval_policy,
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


@router.get("/interoperability/analytics/omop/mapping-profile")
async def omop_mapping_profile(settings: Settings = Depends(get_api_settings)) -> dict:
    """Return the data-driven OMOP preview mapping profile."""

    return ok(load_omop_mapping_profile(settings.resolved_knowledge_dir))


@router.post("/interoperability/analytics/omop/preview")
async def omop_export_preview(
    request: OmopPreviewRequest,
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Preview how a ClinicalPackage maps into OMOP target tables."""

    return ok(
        build_omop_export_preview(
            request.package,
            profile=load_omop_mapping_profile(settings.resolved_knowledge_dir),
            vocabulary_catalog=load_omop_vocabulary_candidate_catalog(
                settings.resolved_knowledge_dir
            ),
        )
    )


@router.get("/interoperability/analytics/omop/dqd-compatibility")
async def dqd_compatibility(settings: Settings = Depends(get_api_settings)) -> dict:
    """Return OHDSI Data Quality Dashboard compatibility notes."""

    return ok(load_dqd_compatibility(settings.resolved_knowledge_dir))


@router.get("/interoperability/analytics/cohort-research-workflow")
async def cohort_research_workflow(settings: Settings = Depends(get_api_settings)) -> dict:
    """Return the cohort/research workflow concept and non-CDS boundaries."""

    return ok(load_cohort_research_workflow(settings.resolved_knowledge_dir))


@router.get("/interoperability/external/connectors")
async def external_source_connectors(settings: Settings = Depends(get_api_settings)) -> dict:
    """Return the governed external source connector registry."""

    return ok(load_external_source_connectors(settings.resolved_knowledge_dir))


@router.get("/interoperability/external/cache-policy")
async def external_api_cache_policy(settings: Settings = Depends(get_api_settings)) -> dict:
    """Return external API cache metadata and invalidation policy."""

    return ok(load_external_api_cache_policy(settings.resolved_knowledge_dir))


@router.post("/interoperability/external/cache/metadata")
async def external_api_cache_metadata(
    request: ExternalApiCacheMetadataRequest,
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Build rule-based metadata for an external API cache entry."""

    return ok(
        build_external_api_cache_metadata(
            policy=load_external_api_cache_policy(settings.resolved_knowledge_dir),
            connector_id=request.connector_id,
            endpoint_url=request.endpoint_url,
            query=request.query,
            source_release_version=request.source_release_version,
            response_text=request.response_text,
            fetched_at=request.fetched_at,
            metadata=request.metadata,
        )
    )


@router.get("/interoperability/external/ingestion-approval-policy")
async def source_ingestion_approval_policy(
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Return source ingestion approval policy before indexing external documents."""

    return ok(load_source_ingestion_approval_policy(settings.resolved_knowledge_dir))


@router.post("/interoperability/external/ingestion/approval-preview")
async def source_ingestion_approval_preview(
    request: SourceIngestionApprovalPreviewRequest,
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Preview whether an external source candidate may become searchable."""

    connectors = load_external_source_connectors(settings.resolved_knowledge_dir)
    return ok(
        evaluate_source_ingestion_candidate(
            policy=load_source_ingestion_approval_policy(settings.resolved_knowledge_dir),
            connector_ids={connector.connector_id for connector in connectors.connectors},
            connector_id=request.connector_id,
            document_id=request.document_id,
            source_url=request.source_url,
            source_release_version=request.source_release_version,
            license_accepted=request.license_accepted,
            reviewer_approved=request.reviewer_approved,
            contains_phi=request.contains_phi,
        )
    )


@router.get("/interoperability/external/link-launchers")
async def external_link_launchers(settings: Settings = Depends(get_api_settings)) -> dict:
    """Return transparent external source link launchers."""

    return ok(load_external_link_launchers(settings.resolved_knowledge_dir))


@router.post("/interoperability/external/link-launch")
async def external_link_launch(
    request: ExternalLinkLaunchRequest,
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Build a transparent external source URL without fetching or ingesting content."""

    return ok(
        launch_external_link(
            catalog=load_external_link_launchers(settings.resolved_knowledge_dir),
            launcher_id=request.launcher_id,
            query=request.query,
        )
    )


@router.post("/interoperability/export/etl-package")
async def etl_export_package(
    request: EtlExportPackageRequest,
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Build a provenance-preserving ETL manifest for analytics teams."""

    preview = build_omop_export_preview(
        request.package,
        profile=load_omop_mapping_profile(settings.resolved_knowledge_dir),
        vocabulary_catalog=load_omop_vocabulary_candidate_catalog(
            settings.resolved_knowledge_dir
        ),
    )
    return ok(
        build_etl_export_package(
            request.package,
            preview=preview,
            include_resources=request.include_resources,
        )
    )


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


@router.post("/interoperability/clinical-package/validate-import")
async def validate_clinical_package_import(
    request: ClinicalPackageImportValidationRequest,
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    """Validate that an OJTFlow clinical package export can be reloaded."""

    return ok(
        service.validate_clinical_package_import(
            request.payload,
            require_hash_match=request.require_hash_match,
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
