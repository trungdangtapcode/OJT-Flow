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


def parse_data(text: str, data_format: DataFormat, source_ref: str | None = None) -> ParsedData:
    """Parse text into a normalized ParsedData object."""

    if data_format == DataFormat.JSON:
        return _parse_json(text, source_ref)
    if data_format == DataFormat.YAML:
        return _parse_yaml(text, source_ref)
    if data_format == DataFormat.CSV:
        return _parse_csv(text, source_ref)
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
