"""Document parsing routes — file upload endpoints.

These endpoints accept multipart file uploads and pipe them through the
extraction + parsing pipeline (markitdown / minerU → text → workflow).

Requires:
    pip install 'ojtflow[parsing]'       # markitdown
    pip install 'ojtflow[parsing-full]'  # markitdown + minerU
"""

from __future__ import annotations

import base64
import binascii
import inspect
import io
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import StreamingResponse
from pydantic import Field

from ojtflow.application.document_intake_service import DocumentIntakeService
from ojtflow.application.governance_service import GovernanceService
from ojtflow.application.workflow_service import WorkflowService
from ojtflow.config import Settings
from ojtflow.core.contracts.artifacts import (
    ArtifactAccessEvent,
    ParsingPipelineTrace,
    UploadedArtifact,
)
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.core.contracts.base import ContractModel, NonBlankStr
from ojtflow.core.contracts.enums import DataFormat
from ojtflow.core.contracts.jobs import BackgroundJob
from ojtflow.core.contracts.redaction import RedactionPreview
from ojtflow.core.errors import UnsupportedUploadError, UploadTooLargeError
from ojtflow.core.ids import new_id
from ojtflow.core.policy.abuse_cost_policy import (
    load_abuse_cost_policy,
    require_batch_ingestion_budget,
)
from ojtflow.data_tools.redaction import build_redaction_preview
from ojtflow.data_tools.extract import (
    Extractor,
    available_extractors,
    sanitize_upload_filename,
    source_format_for_filename,
    supported_extensions,
    validate_extractor_choice,
)
from ojtflow.interfaces.api.limits import enforce_inline_text_limit
from ojtflow.interfaces.api.deps import (
    get_api_settings,
    get_document_intake_service,
    get_governance_service,
    get_workflow_service,
    require_authentication,
)
from ojtflow.interfaces.api.responses import ok, raise_for_failed_workflow
from ojtflow.interfaces.api.schemas import RedactionPreviewRequest

router = APIRouter(tags=["parse"])

CLIPBOARD_IMAGE_EXTENSIONS = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


class ExtractedDocumentResponse(ContractModel):
    filename: str
    source_format: str
    extractor_used: str
    page_count: int | None = None
    char_count: int
    word_count: int
    text: str
    warnings: list[str]
    artifact_id: str | None = None
    job_id: str | None = None
    trace_id: str | None = None
    text_dataset_id: str | None = None
    text_storage_ref: str | None = None
    source: str | None = None


class UploadParseJobResponse(ContractModel):
    job: BackgroundJob
    artifact: UploadedArtifact
    trace: ParsingPipelineTrace | None = None
    extracted_document: ExtractedDocumentResponse | None = None


class UploadParseJobEnvelope(ContractModel):
    data: UploadParseJobResponse
    error: None = None


class BatchUploadParseResponse(ContractModel):
    batch_id: str
    case_id: str | None = None
    project_id: str | None = None
    items: list[UploadParseJobResponse]


class BatchUploadParseEnvelope(ContractModel):
    data: BatchUploadParseResponse
    error: None = None


class ClipboardImageParseRequest(ContractModel):
    data_base64: str = Field(
        min_length=1,
        description="Base64-encoded image bytes from the clipboard.",
    )
    filename: str | None = Field(
        default=None,
        description="Optional original clipboard filename; inferred from MIME type if absent.",
    )
    mime_type: str = Field(
        default="image/png",
        description="Clipboard image MIME type.",
    )
    extractor: str = Field(
        default=Extractor.AUTO,
        description="Extraction engine: auto, markitdown, mineru, openai_vision, or tesseract.",
    )
    execute_now: bool = Field(
        default=True,
        description="Run immediately in local sync mode; false leaves a queued durable job.",
    )
    include_extracted_document: bool = Field(
        default=True,
        description="Return extracted text in the response when execute_now succeeds.",
    )


class ArtifactEnvelope(ContractModel):
    data: UploadedArtifact
    error: None = None


class ArtifactExportResponse(ContractModel):
    artifact: UploadedArtifact
    traces: list[ParsingPipelineTrace]
    access_events: list[ArtifactAccessEvent]


class ArtifactExportEnvelope(ContractModel):
    data: ArtifactExportResponse
    error: None = None


class ArtifactAccessEventsEnvelope(ContractModel):
    data: list[ArtifactAccessEvent]
    error: None = None


class ArtifactsEnvelope(ContractModel):
    data: list[UploadedArtifact]
    error: None = None


class ParseTracesEnvelope(ContractModel):
    data: list[ParsingPipelineTrace]
    error: None = None


class RedactionPreviewEnvelope(ContractModel):
    data: RedactionPreview
    error: None = None


async def _read_upload_bytes(file: UploadFile, settings: Settings) -> tuple[bytes, str, str]:
    """Validate and read an uploaded file without trusting client metadata."""

    filename = sanitize_upload_filename(
        file.filename,
        allowed_extensions=settings.allowed_upload_extensions,
    )
    source_format = source_format_for_filename(
        filename,
        allowed_extensions=settings.allowed_upload_extensions,
    )
    extractor_bytes = bytearray()

    while True:
        chunk = await file.read(settings.upload_read_chunk_bytes)
        if not chunk:
            break
        extractor_bytes.extend(chunk)
        if len(extractor_bytes) > settings.max_upload_bytes:
            raise UploadTooLargeError(
                f"Uploaded file exceeds the {settings.max_upload_bytes} byte limit."
            )

    if not extractor_bytes:
        raise UnsupportedUploadError("Uploaded file is empty.")

    return bytes(extractor_bytes), filename, source_format


def _optional_form_text(value: str | None) -> str | None:
    """Normalize optional multipart form text while preserving blank-as-omitted UX."""

    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _required_form_text(field_name: str, value: str) -> str:
    normalized = value.strip()
    if normalized:
        return normalized
    raise RequestValidationError(
        [
            {
                "type": "string_too_short",
                "loc": ("body", field_name),
                "msg": "String should have at least 1 character",
                "input": value,
                "ctx": {"min_length": 1},
            }
        ]
    )


def _trace_from_job(job: BackgroundJob) -> ParsingPipelineTrace | None:
    trace = job.output.get("trace")
    if isinstance(trace, dict):
        return ParsingPipelineTrace.model_validate(trace)
    return None


def _upload_parse_job_response(
    *,
    intake: DocumentIntakeService,
    job: BackgroundJob,
    artifact: UploadedArtifact,
    include_extracted_document: bool = False,
) -> UploadParseJobResponse:
    trace = _trace_from_job(job)
    extracted = (
        intake.extracted_document_from_trace(artifact=artifact, trace=trace)
        if include_extracted_document
        else None
    )
    return UploadParseJobResponse(
        job=job,
        artifact=artifact,
        trace=trace,
        extracted_document=(
            ExtractedDocumentResponse.model_validate(extracted) if extracted else None
        ),
    )


def _read_clipboard_image_bytes(
    request: ClipboardImageParseRequest,
    settings: Settings,
) -> tuple[bytes, str, str]:
    mime_type = request.mime_type.strip().lower()
    extension = CLIPBOARD_IMAGE_EXTENSIONS.get(mime_type)
    if extension is None:
        raise UnsupportedUploadError(
            "Clipboard image MIME type must be one of: image/png, image/jpeg, "
            "image/webp, image/gif."
        )
    raw_filename = request.filename.strip() if request.filename else ""
    filename = raw_filename or f"clipboard{extension}"
    if not Path(filename).suffix:
        filename = f"{filename}{extension}"
    filename = sanitize_upload_filename(
        filename,
        allowed_extensions=settings.allowed_upload_extensions,
    )
    try:
        data = base64.b64decode(request.data_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise UnsupportedUploadError("Clipboard image data must be valid base64.") from exc
    if not data:
        raise UnsupportedUploadError("Clipboard image data is empty.")
    if len(data) > settings.max_upload_bytes:
        raise UploadTooLargeError(
            f"Clipboard image exceeds the {settings.max_upload_bytes} byte limit."
        )
    return data, filename, mime_type


def _content_disposition_filename(filename: str) -> str:
    safe = sanitize_upload_filename(filename)
    return f"attachment; filename*=UTF-8''{quote(safe)}"


def _call_start_workflow_from_file(
    service: WorkflowService,
    **kwargs,
):
    """Call workflow file start while keeping lightweight route fakes compatible."""

    method = service.start_workflow_from_file
    signature = inspect.signature(method)
    if "request_id" not in signature.parameters:
        kwargs.pop("request_id", None)
    return method(**kwargs)


@router.post("/parse/upload/jobs", response_model=UploadParseJobEnvelope)
async def create_upload_parse_job(
    http_request: Request,
    file: UploadFile = File(..., description="Document file to persist and parse."),
    extractor: str = Form(
        default=Extractor.AUTO,
        description=(
            "Extraction engine: 'auto' | 'markitdown' | 'mineru' | "
            "'openai_vision' | 'tesseract'."
        ),
    ),
    execute_now: bool = Form(
        default=True,
        description="Run immediately in local sync mode; false leaves a queued durable job.",
    ),
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    settings: Settings = Depends(get_api_settings),
    intake: DocumentIntakeService = Depends(get_document_intake_service),
) -> dict:
    """Persist an upload as an artifact and create a traceable file-parse job."""

    governance.require_permission(user=authenticated.user, permission_scope="data:profile")
    extractor = validate_extractor_choice(extractor)
    file_bytes, filename, _source_format = await _read_upload_bytes(file, settings)
    artifact = intake.register_upload(
        owner_user_id=authenticated.user.user_id,
        filename=filename,
        mime_type=file.content_type or "application/octet-stream",
        data=file_bytes,
        source="upload",
        request_id=getattr(http_request.state, "request_id", None),
    )
    job = intake.create_parse_job(
        owner_user_id=authenticated.user.user_id,
        artifact_id=artifact.artifact_id,
        prefer_extractor=extractor,
        execute_now=execute_now,
        request_id=getattr(http_request.state, "request_id", None),
    )
    return ok(_upload_parse_job_response(intake=intake, job=job, artifact=artifact))


@router.post("/parse/upload/batch/jobs", response_model=BatchUploadParseEnvelope)
async def create_batch_upload_parse_jobs(
    http_request: Request,
    files: list[UploadFile] = File(..., description="Related document files to persist and parse."),
    extractor: str = Form(
        default=Extractor.AUTO,
        description=(
            "Extraction engine: 'auto' | 'markitdown' | 'mineru' | "
            "'openai_vision' | 'tesseract'."
        ),
    ),
    execute_now: bool = Form(
        default=False,
        description="Run parse jobs immediately in local sync mode; false leaves queued jobs.",
    ),
    case_id: str | None = Form(
        default=None,
        description="Optional case identifier shared by all files in this batch.",
    ),
    project_id: str | None = Form(
        default=None,
        description="Optional project identifier shared by all files in this batch.",
    ),
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    settings: Settings = Depends(get_api_settings),
    intake: DocumentIntakeService = Depends(get_document_intake_service),
) -> dict:
    """Persist multiple related uploads and create parse jobs under one batch ID."""

    governance.require_permission(user=authenticated.user, permission_scope="data:profile")
    extractor = validate_extractor_choice(extractor)
    if not files:
        raise UnsupportedUploadError("Batch upload must include at least one file.")
    if len(files) > settings.max_batch_upload_files:
        raise UploadTooLargeError(
            f"Batch upload supports at most {settings.max_batch_upload_files} files."
        )
    uploaded_files = [
        await _read_upload_bytes(file, settings)
        for file in files
    ]
    require_batch_ingestion_budget(
        load_abuse_cost_policy(settings.resolved_abuse_cost_policy_path),
        total_bytes=sum(len(file_bytes) for file_bytes, _filename, _source_format in uploaded_files),
    )
    batch_id = new_id("batch")
    items: list[UploadParseJobResponse] = []
    request_id = getattr(http_request.state, "request_id", None)
    normalized_case_id = _optional_form_text(case_id)
    normalized_project_id = _optional_form_text(project_id)
    for item, (file_bytes, filename, _source_format) in zip(files, uploaded_files, strict=True):
        artifact = intake.register_upload(
            owner_user_id=authenticated.user.user_id,
            filename=filename,
            mime_type=item.content_type or "application/octet-stream",
            data=file_bytes,
            source="upload",
            request_id=request_id,
            metadata={
                "batch_id": batch_id,
                "case_id": normalized_case_id,
                "project_id": normalized_project_id,
            },
        )
        job = intake.create_parse_job(
            owner_user_id=authenticated.user.user_id,
            artifact_id=artifact.artifact_id,
            prefer_extractor=extractor,
            execute_now=execute_now,
            request_id=request_id,
        )
        items.append(_upload_parse_job_response(intake=intake, job=job, artifact=artifact))
    return ok(
        BatchUploadParseResponse(
            batch_id=batch_id,
            case_id=normalized_case_id,
            project_id=normalized_project_id,
            items=items,
        )
    )


@router.post("/parse/clipboard/images/jobs", response_model=UploadParseJobEnvelope)
async def create_clipboard_image_parse_job(
    request: ClipboardImageParseRequest,
    http_request: Request,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    settings: Settings = Depends(get_api_settings),
    intake: DocumentIntakeService = Depends(get_document_intake_service),
) -> dict:
    """Persist a pasted clipboard image as an artifact and create a parse job."""

    governance.require_permission(user=authenticated.user, permission_scope="data:profile")
    extractor = validate_extractor_choice(request.extractor)
    image_bytes, filename, mime_type = _read_clipboard_image_bytes(request, settings)
    artifact = intake.register_upload(
        owner_user_id=authenticated.user.user_id,
        filename=filename,
        mime_type=mime_type,
        data=image_bytes,
        source="clipboard",
        request_id=getattr(http_request.state, "request_id", None),
    )
    job = intake.create_parse_job(
        owner_user_id=authenticated.user.user_id,
        artifact_id=artifact.artifact_id,
        prefer_extractor=extractor,
        execute_now=request.execute_now,
        request_id=getattr(http_request.state, "request_id", None),
    )
    return ok(
        _upload_parse_job_response(
            intake=intake,
            job=job,
            artifact=artifact,
            include_extracted_document=request.include_extracted_document,
        )
    )


@router.get("/parse/artifacts", response_model=ArtifactsEnvelope)
async def list_uploaded_artifacts(
    limit: int = 100,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    intake: DocumentIntakeService = Depends(get_document_intake_service),
) -> dict:
    """List uploaded artifacts owned by the authenticated user."""

    governance.require_permission(user=authenticated.user, permission_scope="data:read")
    return ok(
        intake.list_artifacts(
            owner_user_id=authenticated.user.user_id,
            limit=limit,
        )
    )


@router.get("/parse/artifacts/{artifact_id}", response_model=ArtifactEnvelope)
async def get_uploaded_artifact(
    http_request: Request,
    artifact_id: NonBlankStr,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    intake: DocumentIntakeService = Depends(get_document_intake_service),
) -> dict:
    """Return metadata for one uploaded artifact."""

    governance.require_permission(user=authenticated.user, permission_scope="data:read")
    artifact = intake.get_artifact(
        owner_user_id=authenticated.user.user_id,
        artifact_id=artifact_id,
    )
    intake.record_artifact_access(
        owner_user_id=authenticated.user.user_id,
        artifact_id=artifact.artifact_id,
        actor_user_id=authenticated.user.user_id,
        action="view_metadata",
        request_id=getattr(http_request.state, "request_id", None),
        metadata={"route": "get_uploaded_artifact"},
    )
    return ok(artifact)


@router.get("/parse/artifacts/{artifact_id}/download")
async def download_uploaded_artifact(
    http_request: Request,
    artifact_id: NonBlankStr,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    intake: DocumentIntakeService = Depends(get_document_intake_service),
):
    """Download raw uploaded artifact bytes after owner-scoped access check."""

    governance.require_permission(user=authenticated.user, permission_scope="data:export")
    artifact = intake.get_artifact(
        owner_user_id=authenticated.user.user_id,
        artifact_id=artifact_id,
    )
    data = intake.get_artifact_bytes(
        owner_user_id=authenticated.user.user_id,
        artifact_id=artifact.artifact_id,
    )
    intake.record_artifact_access(
        owner_user_id=authenticated.user.user_id,
        artifact_id=artifact.artifact_id,
        actor_user_id=authenticated.user.user_id,
        action="download",
        request_id=getattr(http_request.state, "request_id", None),
        metadata={"route": "download_uploaded_artifact", "byte_size": len(data)},
    )
    return StreamingResponse(
        io.BytesIO(data),
        media_type=artifact.mime_type,
        headers={
            "Content-Disposition": _content_disposition_filename(artifact.filename),
            "X-OJT-Artifact-ID": artifact.artifact_id,
        },
    )


@router.get("/parse/artifacts/{artifact_id}/export", response_model=ArtifactExportEnvelope)
async def export_uploaded_artifact_metadata(
    http_request: Request,
    artifact_id: NonBlankStr,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    intake: DocumentIntakeService = Depends(get_document_intake_service),
) -> dict:
    """Export artifact metadata, traces, and access events without raw bytes."""

    governance.require_permission(user=authenticated.user, permission_scope="data:export")
    artifact = intake.get_artifact(
        owner_user_id=authenticated.user.user_id,
        artifact_id=artifact_id,
    )
    intake.record_artifact_access(
        owner_user_id=authenticated.user.user_id,
        artifact_id=artifact.artifact_id,
        actor_user_id=authenticated.user.user_id,
        action="export_metadata",
        request_id=getattr(http_request.state, "request_id", None),
        metadata={"route": "export_uploaded_artifact_metadata"},
    )
    return ok(
        ArtifactExportResponse(
            artifact=artifact,
            traces=intake.list_traces(
                owner_user_id=authenticated.user.user_id,
                artifact_id=artifact.artifact_id,
            ),
            access_events=intake.list_artifact_access_events(
                owner_user_id=authenticated.user.user_id,
                artifact_id=artifact.artifact_id,
            ),
        )
    )


@router.get("/parse/artifacts/{artifact_id}/traces", response_model=ParseTracesEnvelope)
async def list_uploaded_artifact_traces(
    artifact_id: NonBlankStr,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    intake: DocumentIntakeService = Depends(get_document_intake_service),
) -> dict:
    """Return extraction traces for one uploaded artifact."""

    governance.require_permission(user=authenticated.user, permission_scope="data:read")
    return ok(
        intake.list_traces(
            owner_user_id=authenticated.user.user_id,
            artifact_id=artifact_id,
        )
    )


@router.get(
    "/parse/artifacts/{artifact_id}/access-events",
    response_model=ArtifactAccessEventsEnvelope,
)
async def list_uploaded_artifact_access_events(
    artifact_id: NonBlankStr,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    intake: DocumentIntakeService = Depends(get_document_intake_service),
) -> dict:
    """Return artifact access events for the owner."""

    governance.require_permission(user=authenticated.user, permission_scope="data:read")
    return ok(
        intake.list_artifact_access_events(
            owner_user_id=authenticated.user.user_id,
            artifact_id=artifact_id,
        )
    )


@router.post("/parse/redaction-preview", response_model=RedactionPreviewEnvelope)
async def preview_redaction(
    request: RedactionPreviewRequest,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Preview deterministic sensitive-data redaction before external provider use."""

    governance.require_permission(user=authenticated.user, permission_scope="data:profile")
    enforce_inline_text_limit(request.data, settings)
    return ok(
        build_redaction_preview(
            request.data,
            data_format=request.input_format,
            action_override=request.redaction_action,
        )
    )


@router.post("/parse/upload/workflow")
async def upload_and_start_workflow(
    http_request: Request,
    file: UploadFile = File(..., description="Document file to parse (PDF, DOCX, image, …)"),
    instruction: str = Form(
        ...,
        description="Natural-language instruction for the workflow.",
    ),
    target_format: DataFormat = Form(
        default=DataFormat.JSON,
        description="Desired output format.",
    ),
    schema_id: str | None = Form(
        default=None,
        description="Schema ID for validation (e.g. 'lab_result_v1'). Leave blank for unstructured docs.",
    ),
    require_human_review: bool = Form(
        default=True,
        description="Whether to pause for human review before transformation.",
    ),
    extractor: str = Form(
        default=Extractor.AUTO,
        description=(
            "Extraction engine: 'auto' | 'markitdown' | 'mineru' | "
            "'openai_vision' | 'tesseract'."
        ),
    ),
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    service: WorkflowService = Depends(get_workflow_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Upload a document file and start a full workflow.

    The file is extracted to text (OCR if needed), then validated,
    transformed, and explained — same pipeline as the JSON workflow endpoint.

    Returns the same `WorkflowState` envelope as `POST /api/v1/workflows`.
    """
    governance.require_permission(user=authenticated.user, permission_scope="data:transform")
    instruction = _required_form_text("instruction", instruction)
    extractor = validate_extractor_choice(extractor)
    schema_id = _optional_form_text(schema_id)
    file_bytes, filename, _source_format = await _read_upload_bytes(file, settings)

    workflow = _call_start_workflow_from_file(
        service,
        instruction=instruction,
        file_bytes=file_bytes,
        filename=filename,
        target_format=target_format,
        schema_id=schema_id,
        require_human_review=require_human_review,
        prefer_extractor=extractor,
        owner_user_id=authenticated.user.user_id,
        request_id=getattr(http_request.state, "request_id", None),
    )
    raise_for_failed_workflow(workflow)
    return ok(workflow)


@router.post("/parse/extract")
async def extract_only(
    file: UploadFile = File(..., description="Document file to extract text from."),
    extractor: str = Form(
        default=Extractor.AUTO,
        description=(
            "Extraction engine: 'auto' | 'markitdown' | 'mineru' | "
            "'openai_vision' | 'tesseract'."
        ),
    ),
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Extract text from a document without running the full workflow.

    Useful for previewing what the extraction pipeline produces before
    committing to a full workflow run.

    Returns:
        text: Extracted markdown / plain text.
        extractor_used: Which engine was used.
        source_format: Detected file format ("pdf", "image", …).
        page_count: Number of pages (PDF only, null otherwise).
        warnings: Any non-fatal extraction warnings.
    """
    from ojtflow.data_tools.extract import extract_document

    governance.require_permission(user=authenticated.user, permission_scope="data:profile")
    extractor = validate_extractor_choice(extractor)
    file_bytes, filename, _source_format = await _read_upload_bytes(file, settings)

    result = extract_document(file_bytes, filename, prefer=extractor)
    return ok(
        {
            "filename": result.filename,
            "source_format": result.source_format,
            "extractor_used": result.extractor_used,
            "page_count": result.page_count,
            "char_count": len(result.text),
            "word_count": len(result.text.split()),
            "text": result.text,
            "warnings": result.warnings,
        }
    )


@router.get("/parse/extractors")
async def list_extractors(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
) -> dict:
    """Return which extraction engines are installed and available."""
    governance.require_permission(user=authenticated.user, permission_scope="data:read")
    return ok(
        {
            "available": available_extractors(),
            "supported_extensions": supported_extensions(),
        }
    )
