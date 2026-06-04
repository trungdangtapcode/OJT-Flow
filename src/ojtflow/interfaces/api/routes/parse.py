"""Document parsing routes — file upload endpoints.

These endpoints accept multipart file uploads and pipe them through the
extraction + parsing pipeline (markitdown / minerU → text → workflow).

Requires:
    pip install 'ojtflow[parsing]'       # markitdown
    pip install 'ojtflow[parsing-full]'  # markitdown + minerU
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.exceptions import RequestValidationError

from ojtflow.application.workflow_service import WorkflowService
from ojtflow.config import Settings
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.core.contracts.enums import DataFormat
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
    get_workflow_service,
    require_authentication,
)
from ojtflow.interfaces.api.responses import ok, raise_for_failed_workflow

router = APIRouter(tags=["parse"])


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


@router.post("/parse/upload/workflow")
async def upload_and_start_workflow(
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
        description="Extraction engine: 'auto' | 'markitdown' | 'mineru'.",
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
    )
    raise_for_failed_workflow(workflow)
    return ok(workflow)


@router.post("/parse/extract")
async def extract_only(
    file: UploadFile = File(..., description="Document file to extract text from."),
    extractor: str = Form(
        default=Extractor.AUTO,
        description="Extraction engine: 'auto' | 'markitdown' | 'mineru'.",
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
