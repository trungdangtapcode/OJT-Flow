"""Document extraction: PDF, DOCX, images → text via markitdown or minerU.

Usage:
    from ojtflow.data_tools.extract import extract_document, Extractor

    with open("report.pdf", "rb") as f:
        result = extract_document(f.read(), "report.pdf")
    print(result.text)

Install dependencies:
    pip install "ojtflow[parsing]"          # markitdown only
    pip install "ojtflow[parsing-full]"     # markitdown + minerU (magic-pdf)
"""

from __future__ import annotations

import base64
import io
import os
import shutil
import subprocess
import tempfile
from collections.abc import Collection
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from ojtflow.config import OPENAI_VISION_MODEL, get_settings
from ojtflow.core.errors import (
    DependencyUnavailableError,
    PolicyBlockedError,
    ToolExecutionError,
    UnsupportedUploadError,
)
from ojtflow.core.policy.abuse_cost_policy import (
    load_abuse_cost_policy,
    markitdown_ocr_allowed,
    require_openai_vision_budget,
)
from ojtflow.core.policy.external_provider_policy import (
    external_provider_policy_from_settings,
    require_external_provider_handoff,
)


# Map file extension → source format label
EXTENSION_FORMAT: dict[str, str] = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".xlsx": "xlsx",
    ".xls": "xls",
    ".pptx": "pptx",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".tiff": "image",
    ".tif": "image",
    ".bmp": "image",
    ".gif": "image",
    ".webp": "image",
    ".html": "html",
    ".htm": "html",
    ".md": "markdown",
    ".txt": "text",
    ".csv": "csv",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
}


class Extractor:
    DIRECT_TEXT = "direct_text"
    MARKITDOWN = "markitdown"
    MINERU = "mineru"
    OPENAI_VISION = "openai_vision"
    TESSERACT = "tesseract"
    AUTO = "auto"


ALLOWED_EXTRACTORS = {
    Extractor.AUTO,
    Extractor.MARKITDOWN,
    Extractor.MINERU,
    Extractor.OPENAI_VISION,
    Extractor.TESSERACT,
}
MAX_UPLOAD_FILENAME_BYTES = 255
OCR_SENSITIVE_FORMATS = {"pdf", "docx", "pptx", "xlsx", "xls", "image"}
DIRECT_TEXT_FORMATS = {"csv", "json", "yaml", "markdown", "text", "html"}
PDF_OCR_MAX_PAGES = 3
PDF_RENDER_DPI = 200
PDF_RENDER_TIMEOUT_SECONDS = 45


def sanitize_upload_filename(
    filename: str | None,
    allowed_extensions: Collection[str] | None = None,
) -> str:
    """Return a safe basename for an uploaded file or raise a policy error."""

    candidate = (filename or "").strip()
    if not candidate:
        raise UnsupportedUploadError("Uploaded file is missing a filename.")
    if "\x00" in candidate or "/" in candidate or "\\" in candidate:
        raise UnsupportedUploadError("Uploaded filename must not contain path separators.")
    if candidate in {".", ".."}:
        raise UnsupportedUploadError("Uploaded filename is invalid.")
    if len(candidate.encode("utf-8")) > MAX_UPLOAD_FILENAME_BYTES:
        raise UnsupportedUploadError(
            f"Uploaded filename exceeds {MAX_UPLOAD_FILENAME_BYTES} bytes."
        )
    allowed = {extension.lower() for extension in (allowed_extensions or EXTENSION_FORMAT)}
    suffix = Path(candidate).suffix.lower()
    if suffix not in EXTENSION_FORMAT or suffix not in allowed:
        raise UnsupportedUploadError(
            f"Unsupported upload extension '{suffix or '<none>'}'."
        )
    return candidate


def source_format_for_filename(
    filename: str,
    allowed_extensions: Collection[str] | None = None,
) -> str:
    """Return the configured source format for a sanitized filename."""

    safe_filename = sanitize_upload_filename(filename, allowed_extensions=allowed_extensions)
    return EXTENSION_FORMAT[Path(safe_filename).suffix.lower()]


def validate_extractor_choice(prefer: str) -> str:
    """Validate and normalize an extractor choice from API/user input."""

    normalized = prefer.strip().lower()
    if normalized not in ALLOWED_EXTRACTORS:
        raise UnsupportedUploadError(
            "Unsupported extractor "
            f"'{prefer}'. Expected one of: auto, markitdown, mineru, "
            "openai_vision, tesseract."
        )
    return normalized


@dataclass
class ExtractionResult:
    """Output of document extraction."""

    text: str
    extractor_used: str       # "direct_text" | "markitdown" | "mineru" | "openai_vision" | "tesseract"
    source_format: str        # "pdf" | "image" | "docx" | ...
    filename: str
    page_count: int | None = None
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)


def extract_document(
    data: bytes,
    filename: str,
    prefer: str = Extractor.AUTO,
) -> ExtractionResult:
    """Extract text from a document file.

    Args:
        data: Raw file bytes.
        filename: Original filename — used for extension detection.
        prefer: Which extractor to use.
            "auto"       — direct text for text-like files, real OCR for images,
                           markitdown for document formats.
            "markitdown" — markitdown only (lighter, handles most formats).
            "mineru"     — minerU only (better for complex PDFs with tables/formulas).

    Returns:
        ExtractionResult with extracted text and metadata.

    Raises:
        ToolExecutionError: if extraction fails.
        ImportError: if the required library is not installed.
    """
    safe_filename = sanitize_upload_filename(filename)
    prefer = validate_extractor_choice(prefer)
    suffix = Path(safe_filename).suffix.lower()
    source_format = EXTENSION_FORMAT[suffix]
    warnings: list[str] = []

    if prefer == Extractor.AUTO and source_format in DIRECT_TEXT_FORMATS:
        return _extract_direct_text(data, safe_filename, source_format, warnings)

    if prefer == Extractor.AUTO and source_format == "image":
        return _extract_image_auto(data, safe_filename, source_format, warnings)

    if prefer == Extractor.AUTO and source_format == "pdf":
        return _extract_pdf_auto(data, safe_filename, source_format, warnings)

    if prefer == Extractor.MINERU:
        return _extract_mineru(data, safe_filename, source_format, warnings)

    if prefer == Extractor.MARKITDOWN:
        return _extract_markitdown(data, safe_filename, source_format, warnings)

    if prefer == Extractor.OPENAI_VISION:
        result = _extract_openai_vision(
            data=data,
            filename=safe_filename,
            source_format=source_format,
            warnings=warnings,
            require_configured=True,
        )
        if result is None:
            raise ToolExecutionError(
                "OpenAI vision OCR could not extract this file. "
                "Check API key, model, MIME type, and provider response."
            )
        return result

    if prefer == Extractor.TESSERACT:
        result = _extract_tesseract(
            data=data,
            filename=safe_filename,
            source_format=source_format,
            warnings=warnings,
            require_installed=True,
        )
        if result is None:
            raise ToolExecutionError(
                "Tesseract OCR could not extract this file. "
                "Check image format, pytesseract, Pillow, and tesseract binary setup."
            )
        return result

    result = _extract_markitdown(data, safe_filename, source_format, list(warnings))
    if source_format == "image" and not result.text.strip():
        raise ToolExecutionError(
            "markitdown returned empty image text. Select the tesseract or "
            "openai_vision extractor explicitly for OCR."
        )
    return result


def _extract_direct_text(
    data: bytes,
    filename: str,
    source_format: str,
    warnings: list[str],
) -> ExtractionResult:
    """Extract text-like uploads without optional document/OCR dependencies."""

    for encoding in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            text = data.decode(encoding)
            if encoding != "utf-8-sig":
                warnings.append(f"Decoded text upload using {encoding}.")
            break
        except UnicodeDecodeError:
            continue
    else:
        raise UnsupportedUploadError(
            f"Could not decode text upload '{filename}'. Use UTF-8, UTF-16, or CP1252."
        )
    return ExtractionResult(
        text=text,
        extractor_used=Extractor.DIRECT_TEXT,
        source_format=source_format,
        filename=filename,
        warnings=warnings,
        metadata={
            "provider": "local",
            "engine": "direct_text_decoder",
            "external_provider": False,
            "cost_tracking": {
                "billable": False,
                "basis": "local byte-to-text decoding only",
            },
        },
    )


def _extract_image_auto(
    data: bytes,
    filename: str,
    source_format: str,
    warnings: list[str],
) -> ExtractionResult:
    """Select a real configured OCR provider for image uploads."""

    result = _extract_openai_vision(
        data=data,
        filename=filename,
        source_format=source_format,
        warnings=warnings,
        require_configured=False,
    )
    if result is not None:
        return result

    result = _extract_tesseract(
        data=data,
        filename=filename,
        source_format=source_format,
        warnings=warnings,
        require_installed=False,
    )
    if result is not None and result.text.strip():
        return result

    raise DependencyUnavailableError(
        "Image OCR is unavailable. Configure OpenAI vision OCR or install "
        "Pillow, pytesseract, and the tesseract binary.",
        details={
            "code": "IMAGE_OCR_UNAVAILABLE",
            "filename": filename,
            "source_format": source_format,
            "providers_attempted": [Extractor.OPENAI_VISION, Extractor.TESSERACT],
            "warnings": list(warnings),
            "fallback_attempted": False,
        },
    )


def _extract_pdf_auto(
    data: bytes,
    filename: str,
    source_format: str,
    warnings: list[str],
) -> ExtractionResult:
    """Extract scanned PDFs by rendering pages and OCRing the real page images."""

    page_images = _render_pdf_pages_to_png(data, filename, warnings)
    if not page_images:
        raise DependencyUnavailableError(
            "Scanned PDF OCR is unavailable. Install poppler/pdftoppm and configure "
            "OpenAI vision OCR, or select a real PDF extractor explicitly.",
            details={
                "code": "PDF_OCR_UNAVAILABLE",
                "filename": filename,
                "source_format": source_format,
                "renderer": "pdftoppm",
                "ocr_provider": Extractor.OPENAI_VISION,
                "warnings": list(warnings),
                "fallback_attempted": False,
            },
        )

    page_results: list[tuple[int, ExtractionResult]] = []
    stem = Path(filename).stem
    for page_number, page_data in enumerate(page_images, start=1):
        page_warnings: list[str] = []
        result = _extract_openai_vision(
            data=page_data,
            filename=f"{stem}-page-{page_number}.png",
            source_format="image",
            warnings=page_warnings,
            require_configured=False,
        )
        warnings.extend(f"page {page_number}: {warning}" for warning in page_warnings)
        if result is not None and result.text.strip():
            page_results.append((page_number, result))

    if not page_results:
        raise DependencyUnavailableError(
            "Scanned PDF OCR is unavailable. PDF pages rendered successfully, but no "
            "configured OCR provider returned text.",
            details={
                "code": "PDF_OCR_UNAVAILABLE",
                "filename": filename,
                "source_format": source_format,
                "renderer": "pdftoppm",
                "rendered_page_count": len(page_images),
                "ocr_provider": Extractor.OPENAI_VISION,
                "warnings": list(warnings),
                "fallback_attempted": False,
            },
        )

    text = "\n\n".join(
        f"[page {page_number}]\n{result.text.strip()}"
        for page_number, result in page_results
    )
    metadata = dict(page_results[0][1].metadata)
    metadata.update(
        {
            "provider": "openai",
            "model": page_results[0][1].metadata.get("model"),
            "external_provider": True,
            "pdf_renderer": "pdftoppm",
            "pdf_render_dpi": PDF_RENDER_DPI,
            "rendered_page_count": len(page_images),
            "ocr_page_count": len(page_results),
            "source_format_original": "pdf",
            "fallback_attempted": False,
        }
    )
    return ExtractionResult(
        text=text,
        extractor_used=Extractor.OPENAI_VISION,
        source_format=source_format,
        filename=filename,
        page_count=len(page_images),
        warnings=warnings,
        metadata=metadata,
    )


def _render_pdf_pages_to_png(
    data: bytes,
    filename: str,
    warnings: list[str],
) -> list[bytes]:
    """Render the first PDF pages to PNG bytes using the host poppler binary."""

    renderer = shutil.which("pdftoppm")
    if renderer is None:
        warnings.append("pdftoppm is not installed; scanned PDF pages cannot be rendered.")
        return []

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir_path = Path(tmp_dir)
        input_path = tmp_dir_path / sanitize_upload_filename(filename)
        output_prefix = tmp_dir_path / "page"
        input_path.write_bytes(data)
        command = [
            renderer,
            "-png",
            "-r",
            str(PDF_RENDER_DPI),
            "-f",
            "1",
            "-l",
            str(PDF_OCR_MAX_PAGES),
            str(input_path),
            str(output_prefix),
        ]
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=PDF_RENDER_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            warnings.append(f"pdftoppm failed while rendering scanned PDF pages: {exc}")
            return []

        if completed.returncode != 0:
            stderr = (completed.stderr or completed.stdout or "").strip()
            warnings.append(
                "pdftoppm failed while rendering scanned PDF pages"
                + (f": {stderr[:300]}" if stderr else ".")
            )
            return []

        page_paths = sorted(tmp_dir_path.glob("page-*.png"))
        if not page_paths:
            warnings.append("pdftoppm rendered no PNG pages from the uploaded PDF.")
            return []
        return [path.read_bytes() for path in page_paths]


def _extract_openai_vision(
    *,
    data: bytes,
    filename: str,
    source_format: str,
    warnings: list[str],
    require_configured: bool = False,
) -> ExtractionResult | None:
    """Use OpenAI vision as an explicitly selected OCR provider."""

    api_key = _openai_api_key()
    if not api_key:
        warning = "OpenAI vision OCR is not configured; set OJT_OPENAI_API_KEY."
        warnings.append(warning)
        if require_configured:
            raise ToolExecutionError(warning)
        return None
    mime_type = _image_mime_type(filename)
    if not mime_type:
        warning = (
            "OpenAI vision OCR supports PNG, JPEG, WEBP, and non-animated GIF images."
        )
        warnings.append(warning)
        if require_configured:
            raise UnsupportedUploadError(warning)
        return None

    model = _openai_vision_model()
    require_openai_vision_budget(
        _abuse_cost_policy(),
        surface="openai_vision_ocr",
        byte_count=len(data),
    )
    try:
        policy_decision = _require_openai_vision_allowed(
            source_format=source_format,
            filename=filename,
            model=model,
            adapter="openai_vision",
        )
    except PolicyBlockedError as exc:
        warning = f"OpenAI vision OCR blocked by external-provider policy: {exc}"
        warnings.append(warning)
        if require_configured:
            raise ToolExecutionError(warning, details=exc.details) from exc
        return None
    base_url = (os.getenv("OJT_LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
    timeout_seconds = float(os.getenv("OJT_LLM_TIMEOUT_SECONDS", "30.0"))
    image_url = f"data:{mime_type};base64,{base64.b64encode(data).decode('ascii')}"
    payload = {
        "model": model,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "Transcribe all readable text from this image exactly as OCR "
                            "plain text for a healthcare data workflow. Preserve the "
                            "original line order, labels, values, units, identifiers, and "
                            "table text. Do not summarize, do not add bullets that are not "
                            "visible, do not add parsed fields, and do not add notes unless "
                            "a word is genuinely unreadable. If no text is visible, state "
                            "only that no OCR text was found."
                        ),
                    },
                    {"type": "input_image", "image_url": image_url, "detail": "high"},
                ],
            }
        ],
    }

    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.post(
                f"{base_url}/responses",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
    except httpx.HTTPError as exc:
        warnings.append(f"OpenAI vision OCR failed: {exc}")
        return None

    if response.status_code >= 400:
        warnings.append(
            "OpenAI vision OCR failed with status "
            f"{response.status_code}: {response.text[:300]}"
        )
        return None

    text = _openai_response_text(response.json()).strip()
    if not text:
        warnings.append("OpenAI vision OCR returned empty text.")
        return None

    return ExtractionResult(
        text=text,
        extractor_used=Extractor.OPENAI_VISION,
        source_format=source_format,
        filename=filename,
        warnings=warnings,
        metadata={
            "provider": "openai",
            "model": model,
            "external_provider": True,
            "cost_tracking": {
                "billable": True,
                "basis": "vision model image input plus generated text output",
            },
            "phi_handling": (
                "Image bytes are sent to the configured OpenAI-compatible vision "
                "provider. Use redaction/review policy before enabling on PHI."
            ),
            "external_provider_policy": policy_decision.model_dump(mode="json"),
        },
    )


def _extract_tesseract(
    *,
    data: bytes,
    filename: str,
    source_format: str,
    warnings: list[str],
    require_installed: bool,
) -> ExtractionResult | None:
    """Use local Tesseract OCR for image attachments when installed."""

    if source_format != "image":
        warning = "Tesseract OCR currently supports image uploads only."
        warnings.append(warning)
        if require_installed:
            raise UnsupportedUploadError(warning)
        return None

    try:
        from PIL import Image  # type: ignore[import]
        import pytesseract  # type: ignore[import]
    except ImportError as exc:
        if require_installed:
            raise ImportError(
                "Tesseract OCR requires optional dependencies: pillow and pytesseract."
            ) from exc
        return None

    try:
        with Image.open(io.BytesIO(data)) as image:
            text = pytesseract.image_to_string(image) or ""
    except Exception as exc:
        if require_installed:
            raise ToolExecutionError(f"Tesseract OCR failed for '{filename}': {exc}") from exc
        warnings.append(f"Tesseract OCR failed: {exc}")
        return None

    if not text.strip():
        warnings.append("Tesseract OCR returned empty text.")
        if not require_installed:
            return None

    return ExtractionResult(
        text=text,
        extractor_used=Extractor.TESSERACT,
        source_format=source_format,
        filename=filename,
        warnings=warnings,
        metadata={
            "provider": "local",
            "engine": "tesseract",
            "external_provider": False,
            "cost_tracking": {
                "billable": False,
                "basis": "local CPU/GPU execution only",
            },
            "phi_handling": (
                "Image bytes stay on the application host. Validate host storage, "
                "logs, and retention policy before processing PHI."
            ),
        },
    )


def _image_mime_type(filename: str) -> str | None:
    suffix = Path(filename).suffix.lower()
    if suffix == ".png":
        return "image/png"
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".webp":
        return "image/webp"
    if suffix == ".gif":
        return "image/gif"
    return None


def _openai_api_key() -> str | None:
    return os.getenv("OJT_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")


def _openai_vision_model() -> str:
    try:
        model = get_settings().llm_vision_model
    except Exception:
        model = (
            os.getenv("OJT_LLM_VISION_MODEL")
            or os.getenv("OJT_OPENAI_VISION_MODEL")
            or os.getenv("OJT_LLM_MODEL")
            or OPENAI_VISION_MODEL
        )
    if model == "chat-latest":
        return OPENAI_VISION_MODEL
    return model


def _abuse_cost_policy():
    settings = get_settings()
    return load_abuse_cost_policy(settings.resolved_abuse_cost_policy_path)


def _require_openai_vision_allowed(
    *,
    source_format: str,
    filename: str,
    model: str,
    adapter: str,
):
    settings = get_settings()
    return require_external_provider_handoff(
        external_provider_policy_from_settings(settings),
        surface="openai_vision_ocr",
        text=None,
        contains_phi=None,
        metadata={
            "provider": "openai",
            "adapter": adapter,
            "model": model,
            "source_format": source_format,
            "filename": filename,
        },
    )


def _env_bool(name: str, *, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _openai_response_text(payload: object) -> str:
    if not isinstance(payload, dict):
        return ""
    output_text = payload.get("output_text")
    if isinstance(output_text, str):
        return output_text
    chunks: list[str] = []
    for item in payload.get("output", []) if isinstance(payload.get("output"), list) else []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []) if isinstance(item.get("content"), list) else []:
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                chunks.append(content["text"])
    return "\n".join(chunks)


# ---------------------------------------------------------------------------
# markitdown extractor
# ---------------------------------------------------------------------------

def _extract_markitdown(
    data: bytes,
    filename: str,
    source_format: str,
    warnings: list[str],
) -> ExtractionResult:
    filename = sanitize_upload_filename(filename)
    try:
        from markitdown import MarkItDown  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "markitdown is not installed. Run: pip install 'ojtflow[parsing]'"
        ) from exc

    deferred_warnings: list[str] = []
    md = _build_markitdown_converter(
        MarkItDown=MarkItDown,
        byte_count=len(data),
        source_format=source_format,
        deferred_warnings=deferred_warnings,
    )
    suffix = Path(filename).suffix

    # markitdown reliably detects format from file extension on a real path
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)

    try:
        result = md.convert(str(tmp_path))
        text: str = result.text_content or ""
    except Exception as exc:
        raise ToolExecutionError(
            f"markitdown could not extract '{filename}': {exc}"
        ) from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    if not text.strip():
        warnings.append(
            "markitdown returned empty text. "
            "The file may be a scanned image without OCR or an encrypted PDF."
        )
        warnings.extend(deferred_warnings)

    return ExtractionResult(
        text=text,
        extractor_used=Extractor.MARKITDOWN,
        source_format=source_format,
        filename=filename,
        warnings=warnings,
    )


def _build_markitdown_converter(
    *,
    MarkItDown,
    byte_count: int = 0,
    source_format: str,
    deferred_warnings: list[str],
):
    if not _markitdown_ocr_enabled(source_format):
        return MarkItDown(enable_plugins=False)

    if not markitdown_ocr_allowed(_abuse_cost_policy(), byte_count=byte_count):
        deferred_warnings.append(
            "MarkItDown OCR plugin disabled by abuse/cost policy for this file size."
        )
        return MarkItDown(enable_plugins=False)

    api_key = _openai_api_key()
    if not api_key:
        deferred_warnings.append(
            "MarkItDown OCR plugin is enabled but no OpenAI API key is configured."
        )
        return MarkItDown(enable_plugins=False)

    try:
        _require_openai_vision_allowed(
            source_format=source_format,
            filename="markitdown-ocr",
            model=_openai_vision_model(),
            adapter="markitdown_ocr",
        )
    except PolicyBlockedError as exc:
        deferred_warnings.append(
            f"MarkItDown OCR plugin blocked by external-provider policy: {exc}"
        )
        return MarkItDown(enable_plugins=False)

    try:
        from openai import OpenAI  # type: ignore[import]
    except ImportError:
        deferred_warnings.append(
            "MarkItDown OCR plugin is enabled but the OpenAI client is not installed."
        )
        return MarkItDown(enable_plugins=False)

    kwargs = {
        "api_key": api_key,
    }
    base_url = os.getenv("OJT_LLM_BASE_URL")
    if base_url:
        kwargs["base_url"] = base_url.rstrip("/")

    return MarkItDown(
        enable_plugins=True,
        llm_client=OpenAI(**kwargs),
        llm_model=_openai_vision_model(),
        llm_prompt=(
            "Extract all readable text for a healthcare data workflow. Preserve "
            "tables, field names, units, identifiers, uncertainty, and warnings."
        ),
    )


def _markitdown_ocr_enabled(source_format: str) -> bool:
    if source_format not in OCR_SENSITIVE_FORMATS:
        return False
    return _env_bool("OJT_MARKITDOWN_OCR_ENABLED", default=True)


# ---------------------------------------------------------------------------
# minerU (magic-pdf) extractor
# ---------------------------------------------------------------------------

def _extract_mineru(
    data: bytes,
    filename: str,
    source_format: str,
    warnings: list[str],
) -> ExtractionResult:
    try:
        import magic_pdf  # noqa: F401  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "minerU (magic-pdf) is not installed. "
            "Run: pip install 'ojtflow[parsing-full]'"
        ) from exc

    if source_format not in ("pdf", "image", "unknown"):
        warnings.append(
            f"minerU is optimized for PDF and images; got '{source_format}'. "
            "Consider using markitdown for this format."
        )

    page_count: int | None = None

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir_path = Path(tmp_dir)
        filename = sanitize_upload_filename(filename)
        input_path = tmp_dir_path / filename
        input_path.write_bytes(data)
        output_dir = tmp_dir_path / "output"
        output_dir.mkdir()
        images_dir = output_dir / "images"
        images_dir.mkdir()

        text = _run_mineru_pipeline(
            data=data,
            input_path=input_path,
            output_dir=output_dir,
            images_dir=images_dir,
            warnings=warnings,
        )

        # Try to get page count from pymupdf (bundled with magic-pdf)
        try:
            import fitz  # type: ignore[import]  # PyMuPDF bundled with magic-pdf

            doc = fitz.open(stream=io.BytesIO(data), filetype="pdf")
            page_count = len(doc)
            doc.close()
        except Exception:
            pass

    return ExtractionResult(
        text=text,
        extractor_used=Extractor.MINERU,
        source_format=source_format,
        filename=filename,
        page_count=page_count,
        warnings=warnings,
    )


def _run_mineru_pipeline(
    data: bytes,
    input_path: Path,
    output_dir: Path,
    images_dir: Path,
    warnings: list[str],
) -> str:
    """Run the magic-pdf pipeline and return extracted markdown text.

    magic-pdf API changes between minor versions. This function tries the
    dataset-based API (>=0.9) and falls back to the older do_parse CLI helper.
    """
    # Attempt 1: dataset API (magic-pdf >= 0.9)
    try:
        from magic_pdf.data.data_reader_writer import FileBasedDataWriter  # type: ignore[import]
        from magic_pdf.data.dataset import PymuDocDataset  # type: ignore[import]
        from magic_pdf.config.make_content_config import DropMode, MakeMode  # type: ignore[import]

        image_writer = FileBasedDataWriter(str(images_dir))
        ds = PymuDocDataset(data)

        # classify → parse → build unified format → render markdown
        pipe = ds.apply(
            lambda dataset: dataset.build_pipe(
                image_writer=image_writer,
                is_debug=False,
            )
        )
        pipe.pipe_classify()
        pipe.pipe_parse()
        pipe.pipe_mk_unified_format()

        md_content: str = pipe.pipe_mk_markdown(
            image_dir=str(images_dir),
            drop_mode=DropMode.NONE,
            md_make_mode=MakeMode.MM_MD,
        )
        return md_content or ""

    except (ImportError, AttributeError, TypeError):
        pass  # API not available in this version, try next approach

    # Attempt 2: high-level do_parse helper (older versions)
    try:
        from magic_pdf.tools.cli import do_parse  # type: ignore[import]
        from magic_pdf.data.data_reader_writer import FileBasedDataWriter  # type: ignore[import]

        do_parse(
            input_file=str(input_path),
            output_path=str(output_dir),
            method="auto",
        )
        # do_parse writes <stem>.md to output_dir
        md_files = list(output_dir.glob("*.md"))
        if md_files:
            return md_files[0].read_text(encoding="utf-8")

        warnings.append("minerU do_parse ran but produced no markdown file.")
        return ""

    except (ImportError, Exception) as exc:
        raise ToolExecutionError(
            f"minerU pipeline failed: {exc}. "
            "Check that magic-pdf is correctly installed and models are downloaded."
        ) from exc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def available_extractors() -> list[str]:
    """Return names of extractors that are importable in the current environment."""
    available: list[str] = []
    try:
        import markitdown  # noqa: F401  # type: ignore[import]
        available.append(Extractor.MARKITDOWN)
    except ImportError:
        pass
    try:
        import magic_pdf  # noqa: F401  # type: ignore[import]
        available.append(Extractor.MINERU)
    except ImportError:
        pass
    try:
        from PIL import Image  # noqa: F401  # type: ignore[import]
        import pytesseract  # noqa: F401  # type: ignore[import]
        available.append(Extractor.TESSERACT)
    except ImportError:
        pass
    if os.getenv("OJT_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY"):
        available.append(Extractor.OPENAI_VISION)
    return available


def supported_extensions() -> list[str]:
    """Return all file extensions the extraction pipeline recognises."""
    return sorted(EXTENSION_FORMAT.keys())
