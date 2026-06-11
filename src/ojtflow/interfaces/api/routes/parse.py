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
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from pydantic import Field

from ojtflow.application.document_intake_service import DocumentIntakeService
from ojtflow.application.workflow_service import WorkflowService
from ojtflow.config import Settings
from ojtflow.core.contracts.artifacts import ParsingPipelineTrace, UploadedArtifact
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.core.contracts.base import ContractModel, NonBlankStr
from ojtflow.core.contracts.enums import DataFormat
from ojtflow.core.contracts.jobs import BackgroundJob
from ojtflow.core.errors import UnsupportedUploadError, UploadTooLargeError
from ojtflow.data_tools.extract import (
    Extractor,
    available_extractors,
    sanitize_upload_filename,
    source_format_for_filename,
    supported_extensions,
    validate_extractor_choice,
)
from ojtflow.interfaces.api.deps import (
    get_api_settings,
    get_document_intake_service,
    get_workflow_service,
    require_authentication,
)
from ojtflow.interfaces.api.responses import ok, raise_for_failed_workflow

router = APIRouter(tags=["parse"])

CLIPBOARD_IMAGE_EXTENSIONS = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


class UploadParseJobResponse(ContractModel):
    job: BackgroundJob
    artifact: UploadedArtifact
    trace: ParsingPipelineTrace | None = None


class UploadParseJobEnvelope(ContractModel):
    data: UploadParseJobResponse
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


class ArtifactEnvelope(ContractModel):
    data: UploadedArtifact
    error: None = None


class ArtifactsEnvelope(ContractModel):
    data: list[UploadedArtifact]
    error: None = None


class ParseTracesEnvelope(ContractModel):
    data: list[ParsingPipelineTrace]
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
    settings: Settings = Depends(get_api_settings),
    intake: DocumentIntakeService = Depends(get_document_intake_service),
) -> dict:
    """Persist an upload as an artifact and create a traceable file-parse job."""

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
    return ok(
        UploadParseJobResponse(
            job=job,
            artifact=artifact,
            trace=_trace_from_job(job),
        )
    )


@router.post("/parse/clipboard/images/jobs", response_model=UploadParseJobEnvelope)
async def create_clipboard_image_parse_job(
    request: ClipboardImageParseRequest,
    http_request: Request,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    settings: Settings = Depends(get_api_settings),
    intake: DocumentIntakeService = Depends(get_document_intake_service),
) -> dict:
    """Persist a pasted clipboard image as an artifact and create a parse job."""

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
        UploadParseJobResponse(
            job=job,
            artifact=artifact,
            trace=_trace_from_job(job),
        )
    )


@router.get("/parse/artifacts", response_model=ArtifactsEnvelope)
async def list_uploaded_artifacts(
    limit: int = 100,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    intake: DocumentIntakeService = Depends(get_document_intake_service),
) -> dict:
    """List uploaded artifacts owned by the authenticated user."""

    return ok(
        intake.list_artifacts(
            owner_user_id=authenticated.user.user_id,
            limit=limit,
        )
    )


@router.get("/parse/artifacts/{artifact_id}", response_model=ArtifactEnvelope)
async def get_uploaded_artifact(
    artifact_id: NonBlankStr,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    intake: DocumentIntakeService = Depends(get_document_intake_service),
) -> dict:
    """Return metadata for one uploaded artifact."""

    return ok(
        intake.get_artifact(
            owner_user_id=authenticated.user.user_id,
            artifact_id=artifact_id,
        )
    )


@router.get("/parse/artifacts/{artifact_id}/traces", response_model=ParseTracesEnvelope)
async def list_uploaded_artifact_traces(
    artifact_id: NonBlankStr,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    intake: DocumentIntakeService = Depends(get_document_intake_service),
) -> dict:
    """Return extraction traces for one uploaded artifact."""

    return ok(
        intake.list_traces(
            owner_user_id=authenticated.user.user_id,
            artifact_id=artifact_id,
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
    service: WorkflowService = Depends(get_workflow_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Upload a document file and start a full workflow.

    The file is extracted to text (OCR if needed), then validated,
    transformed, and explained — same pipeline as the JSON workflow endpoint.

    Returns the same `WorkflowState` envelope as `POST /api/v1/workflows`.
    """
    instruction = _required_form_text("instruction", instruction)
    extractor = validate_extractor_choice(extractor)
    schema_id = _optional_form_text(schema_id)
    file_bytes, filename, _source_format = await _read_upload_bytes(file, settings)

    workflow = service.start_workflow_from_file(
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

    del authenticated
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
) -> dict:
    """Return which extraction engines are installed and available."""
    del authenticated
    return ok(
        {
            "available": available_extractors(),
            "supported_extensions": supported_extensions(),
        }
    )
