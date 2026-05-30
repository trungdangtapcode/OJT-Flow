"""Document parsing routes — file upload endpoints.

These endpoints accept multipart file uploads and pipe them through the
extraction + parsing pipeline (markitdown / minerU → text → workflow).

Requires:
    pip install 'ojtflow[parsing]'       # markitdown
    pip install 'ojtflow[parsing-full]'  # markitdown + minerU
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile

from ojtflow.application.workflow_service import WorkflowService
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
from ojtflow.interfaces.api.deps import get_workflow_service
from ojtflow.interfaces.api.responses import ok

router = APIRouter(tags=["parse"])

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
UPLOAD_READ_CHUNK_BYTES = 1024 * 1024


async def _read_upload_bytes(file: UploadFile) -> tuple[bytes, str, str]:
    """Validate and read an uploaded file without trusting client metadata."""

    filename = sanitize_upload_filename(file.filename)
    source_format = source_format_for_filename(filename)
    extractor_bytes = bytearray()

    while True:
        chunk = await file.read(UPLOAD_READ_CHUNK_BYTES)
        if not chunk:
            break
        extractor_bytes.extend(chunk)
        if len(extractor_bytes) > MAX_UPLOAD_BYTES:
            raise UploadTooLargeError(
                f"Uploaded file exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit."
            )

    if not extractor_bytes:
        raise UnsupportedUploadError("Uploaded file is empty.")

    return bytes(extractor_bytes), filename, source_format


@router.post("/parse/upload/workflow")
async def upload_and_start_workflow(
    file: UploadFile = File(..., description="Document file to parse (PDF, DOCX, image, …)"),
    instruction: str = Form(
        default="Extract and explain the content of this document.",
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
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    """Upload a document file and start a full workflow.

    The file is extracted to text (OCR if needed), then validated,
    transformed, and explained — same pipeline as the JSON workflow endpoint.

    Returns the same `WorkflowState` envelope as `POST /api/v1/workflows`.
    """
    extractor = validate_extractor_choice(extractor)
    file_bytes, filename, _source_format = await _read_upload_bytes(file)

    workflow = service.start_workflow_from_file(
        instruction=instruction,
        file_bytes=file_bytes,
        filename=filename,
        target_format=target_format,
        schema_id=schema_id,
        require_human_review=require_human_review,
        prefer_extractor=extractor,
    )
    return ok(workflow)


@router.post("/parse/extract")
async def extract_only(
    file: UploadFile = File(..., description="Document file to extract text from."),
    extractor: str = Form(
        default=Extractor.AUTO,
        description="Extraction engine: 'auto' | 'markitdown' | 'mineru'.",
    ),
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

    extractor = validate_extractor_choice(extractor)
    file_bytes, filename, _source_format = await _read_upload_bytes(file)

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
async def list_extractors() -> dict:
    """Return which extraction engines are installed and available."""
    return ok(
        {
            "available": available_extractors(),
            "supported_extensions": supported_extensions(),
        }
    )
