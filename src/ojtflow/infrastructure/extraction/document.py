"""Adapter for the existing deterministic document extraction pipeline."""

from __future__ import annotations

from ojtflow.data_tools.extract import ExtractionResult, extract_document


class LocalDocumentExtractor:
    """Run installed local/OCR extractors through the shared extraction function."""

    def extract(
        self,
        *,
        data: bytes,
        filename: str,
        prefer: str = "auto",
    ) -> ExtractionResult:
        return extract_document(data, filename, prefer=prefer)
