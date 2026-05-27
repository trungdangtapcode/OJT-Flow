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

import io
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from ojtflow.core.errors import ToolExecutionError


# Map file extension → source format label
EXTENSION_FORMAT: dict[str, str] = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".doc": "doc",
    ".xlsx": "xlsx",
    ".xls": "xls",
    ".pptx": "pptx",
    ".ppt": "ppt",
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
    MARKITDOWN = "markitdown"
    MINERU = "mineru"
    AUTO = "auto"


@dataclass
class ExtractionResult:
    """Output of document extraction."""

    text: str
    extractor_used: str       # "markitdown" | "mineru"
    source_format: str        # "pdf" | "image" | "docx" | ...
    filename: str
    page_count: int | None = None
    warnings: list[str] = field(default_factory=list)


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
            "auto"       — try markitdown first, fall back to minerU.
            "markitdown" — markitdown only (lighter, handles most formats).
            "mineru"     — minerU only (better for complex PDFs with tables/formulas).

    Returns:
        ExtractionResult with extracted text and metadata.

    Raises:
        ToolExecutionError: if extraction fails and no fallback is available.
        ImportError: if the required library is not installed.
    """
    suffix = Path(filename).suffix.lower()
    source_format = EXTENSION_FORMAT.get(suffix, "unknown")
    warnings: list[str] = []

    if source_format == "unknown":
        warnings.append(
            f"Unrecognized file extension '{suffix}'. Attempting extraction anyway."
        )

    if prefer == Extractor.MINERU:
        return _extract_mineru(data, filename, source_format, warnings)

    if prefer == Extractor.MARKITDOWN:
        return _extract_markitdown(data, filename, source_format, warnings)

    # AUTO: try markitdown first, fall back to minerU
    markitdown_error: Exception | None = None
    try:
        return _extract_markitdown(data, filename, source_format, list(warnings))
    except ImportError as exc:
        markitdown_error = exc
        warnings.append("markitdown not installed, falling back to minerU.")
    except ToolExecutionError as exc:
        markitdown_error = exc
        warnings.append(f"markitdown failed ({exc}), falling back to minerU.")

    try:
        return _extract_mineru(data, filename, source_format, warnings)
    except ImportError:
        raise ImportError(
            "No document extractor is available. Install at least one:\n"
            "  pip install 'ojtflow[parsing]'       # markitdown\n"
            "  pip install 'ojtflow[parsing-full]'  # markitdown + minerU\n"
            f"Original markitdown error: {markitdown_error}"
        ) from markitdown_error
    except ToolExecutionError as exc:
        raise ToolExecutionError(
            f"Both markitdown and minerU failed to extract '{filename}'. "
            f"minerU error: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# markitdown extractor
# ---------------------------------------------------------------------------

def _extract_markitdown(
    data: bytes,
    filename: str,
    source_format: str,
    warnings: list[str],
) -> ExtractionResult:
    try:
        from markitdown import MarkItDown  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "markitdown is not installed. Run: pip install 'ojtflow[parsing]'"
        ) from exc

    md = MarkItDown()
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

    return ExtractionResult(
        text=text,
        extractor_used=Extractor.MARKITDOWN,
        source_format=source_format,
        filename=filename,
        warnings=warnings,
    )


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
    return available


def supported_extensions() -> list[str]:
    """Return all file extensions the extraction pipeline recognises."""
    return sorted(EXTENSION_FORMAT.keys())
