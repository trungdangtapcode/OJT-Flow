"""Deterministic parsers."""

from __future__ import annotations

import csv
import json
from io import StringIO
from typing import Any

import yaml

from ojtflow.core.contracts.data import ParsedData
from ojtflow.core.contracts.enums import DataFormat
from ojtflow.core.errors import ToolExecutionError
from ojtflow.interoperability.adapters import parse_bulk_fhir_ndjson


def parse_data(text: str, data_format: DataFormat, source_ref: str | None = None) -> ParsedData:
    """Parse text into a normalized ParsedData object."""

    if data_format == DataFormat.JSON:
        return _parse_json(text, source_ref)
    if data_format == DataFormat.YAML:
        return _parse_yaml(text, source_ref)
    if data_format == DataFormat.CSV:
        return _parse_csv(text, source_ref)
    if data_format == DataFormat.NDJSON:
        return _parse_ndjson(text, source_ref)
    if data_format == DataFormat.MARKDOWN:
        return _parse_markdown(text, source_ref)
    # PDF/DOCX/IMAGE arrive here only if someone bypasses extraction; treat as markdown
    if data_format in (DataFormat.PDF, DataFormat.DOCX, DataFormat.IMAGE):
        return _parse_markdown(text, source_ref)
    raise ToolExecutionError(f"Unsupported format: {data_format}")


def _parse_json(text: str, source_ref: str | None) -> ParsedData:
    try:
        content = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ToolExecutionError(f"Invalid JSON: {exc.msg}") from exc

    records = content if isinstance(content, list) and all(isinstance(row, dict) for row in content) else []
    return ParsedData(format=DataFormat.JSON, content=content, records=records, source_ref=source_ref)


def _parse_yaml(text: str, source_ref: str | None) -> ParsedData:
    try:
        content = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ToolExecutionError(f"Invalid YAML: {exc}") from exc

    records = content if isinstance(content, list) and all(isinstance(row, dict) for row in content) else []
    return ParsedData(format=DataFormat.YAML, content=content, records=records, source_ref=source_ref)


def _parse_markdown(text: str, source_ref: str | None) -> ParsedData:
    """Parse markdown / unstructured text into ParsedData.

    Tries to extract any markdown tables as records.
    Falls back to treating the whole text as a single unstructured document.
    """
    warnings: list[str] = []
    records = _extract_markdown_tables(text)

    if records:
        content: Any = {"tables": records, "raw": text}
    else:
        # No tables found — represent as a single document record
        word_count = len(text.split())
        line_count = len(text.splitlines())
        content = {"raw": text, "word_count": word_count, "line_count": line_count}
        if text.strip():
            records = [{"_text": text, "_word_count": word_count, "_source_row": 1}]
            warnings.append(
                "No structured table found in markdown; treating document as a single record."
            )
        else:
            warnings.append("Extracted text is empty.")

    return ParsedData(
        format=DataFormat.MARKDOWN,
        content=content,
        records=records,
        source_ref=source_ref,
        parser_warnings=warnings,
    )


def _extract_markdown_tables(text: str) -> list[dict[str, Any]]:
    """Extract the first markdown table found in the text and return it as records.

    Markdown table format:
        | col1 | col2 |
        |------|------|
        | val1 | val2 |
    """
    lines = text.splitlines()
    header: list[str] | None = None
    records: list[dict[str, Any]] = []
    row_index = 2  # start at 2 to match CSV convention (_source_row)

    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            if header is not None and records:
                break  # table ended
            continue

        cells = [cell.strip() for cell in stripped.strip("|").split("|")]

        # Separator row (|---|---|)
        if all(set(cell.replace(":", "").replace("-", "")) == set() or cell.replace(":", "").replace("-", "") == "" for cell in cells):
            continue

        if header is None:
            header = cells
        else:
            if len(cells) != len(header):
                continue  # malformed row, skip
            record: dict[str, Any] = dict(zip(header, cells))
            record["_source_row"] = row_index
            records.append(record)
            row_index += 1

    return records


def _parse_csv(text: str, source_ref: str | None) -> ParsedData:
    stream = StringIO(text)
    warnings: list[str] = []
    try:
        sample = stream.read(2048)
        stream.seek(0)
        dialect = csv.Sniffer().sniff(sample)
    except csv.Error:
        dialect = csv.excel
        warnings.append("could not sniff CSV dialect; using comma delimiter")

    reader = csv.DictReader(stream, dialect=dialect)
    if not reader.fieldnames:
        raise ToolExecutionError("CSV header row is missing")

    records: list[dict[str, Any]] = []
    for data_row_index, row in enumerate(reader, start=2):
        clean_row: dict[str, Any] = {}
        if None in row:
            warnings.append(f"row {data_row_index} has extra cells")
            row.pop(None)
        for key, value in row.items():
            if value is None:
                warnings.append(f"row {data_row_index} is missing a value for column {key}")
            clean_row[key] = value
        clean_row["_source_row"] = data_row_index
        records.append(clean_row)

    content = {"fieldnames": reader.fieldnames, "records": records}
    return ParsedData(
        format=DataFormat.CSV,
        content=content,
        records=records,
        source_ref=source_ref,
        parser_warnings=warnings,
    )


def _parse_ndjson(text: str, source_ref: str | None) -> ParsedData:
    report = parse_bulk_fhir_ndjson(text, source_ref=source_ref)
    records = [
        {
            "resourceType": resource.resource_type,
            "id": resource.resource_id,
            "_source_row": resource.line_number,
            "_warnings": list(resource.warnings),
            "resource": resource.resource,
        }
        for resource in report.resources
    ]
    return ParsedData(
        format=DataFormat.NDJSON,
        content=report.model_dump(mode="json"),
        records=records,
        source_ref=source_ref,
        parser_warnings=report.warnings,
    )
