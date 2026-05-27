"""Parser agent — handles both plain text and raw document files (PDF, DOCX, images)."""

from __future__ import annotations

from ojtflow.agents.base import Agent
from ojtflow.core.contracts.agent import AgentResult
from ojtflow.core.contracts.enums import AgentStatus, DataFormat
from ojtflow.data_tools.detect import detect_format
from ojtflow.data_tools.parse import parse_data
from ojtflow.data_tools.profile import profile_data


class ParserAgent(Agent):
    agent_id = "parser_agent"

    def run(
        self,
        text: str,
        declared_format: DataFormat | None,
        source_ref: str,
        *,
        file_bytes: bytes | None = None,
        filename: str | None = None,
        prefer_extractor: str = "auto",
    ) -> AgentResult:
        """Parse input into structured records and a data profile.

        When `file_bytes` + `filename` are supplied the agent first extracts
        text from the document (PDF, DOCX, image, …) using the configured
        extractor, then proceeds with the normal detection → parse → profile
        pipeline on the extracted text.

        Args:
            text: Raw text content (used directly when no file_bytes given).
            declared_format: Caller-declared format hint.
            source_ref: Storage reference for audit trail.
            file_bytes: Raw bytes of the uploaded file (optional).
            filename: Original filename, used for extension detection (optional).
            prefer_extractor: "auto" | "markitdown" | "mineru".
        """
        extraction_meta: dict = {}
        warnings: list[str] = []

        if file_bytes is not None and filename:
            text, extraction_meta, declared_format, warnings = self._extract(
                file_bytes, filename, declared_format, prefer_extractor
            )

        detection = detect_format(text, declared_format)
        parsed = parse_data(text, detection.format, source_ref=source_ref)

        # Merge extraction warnings into parser warnings
        if warnings:
            parsed.parser_warnings = warnings + parsed.parser_warnings

        profile = profile_data(parsed)

        summary = f"Parsed {detection.format.value} input with {profile.row_count} rows"
        if extraction_meta:
            extractor = extraction_meta.get("extractor_used", "")
            source_fmt = extraction_meta.get("source_format", "")
            summary = (
                f"Extracted {source_fmt} via {extractor}; "
                f"parsed {detection.format.value} with {profile.row_count} rows"
            )

        return self.result(
            AgentStatus.SUCCESS,
            summary,
            confidence=detection.confidence,
            data={
                "detection": detection,
                "parsed": parsed,
                "profile": profile,
                "extraction": extraction_meta,
            },
            next_recommended_action="retrieval_agent",
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract(
        self,
        file_bytes: bytes,
        filename: str,
        declared_format: DataFormat | None,
        prefer_extractor: str,
    ) -> tuple[str, dict, DataFormat | None, list[str]]:
        """Extract text from a document file and return (text, meta, format, warnings)."""
        from ojtflow.data_tools.extract import extract_document  # lazy import

        result = extract_document(file_bytes, filename, prefer=prefer_extractor)
        meta = {
            "extractor_used": result.extractor_used,
            "source_format": result.source_format,
            "filename": result.filename,
            "page_count": result.page_count,
        }
        # Honour declared_format if provided; otherwise keep None so detect_format() runs
        effective_format = declared_format
        if effective_format is None and result.source_format in ("pdf", "docx", "image"):
            # After extraction the content is markdown text
            effective_format = DataFormat.MARKDOWN

        return result.text, meta, effective_format, result.warnings
