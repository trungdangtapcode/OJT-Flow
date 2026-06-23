"""Rule-based parsers."""

from __future__ import annotations

import csv
import json
import re
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
        records = _extract_fixed_width_lab_results(text)
        if records:
            content = {"lab_results": records, "raw": text}
            warnings.append(
                f"Extracted {len(records)} lab result record"
                f"{'' if len(records) == 1 else 's'} from fixed-width OCR text."
            )
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


def _extract_fixed_width_lab_results(text: str) -> list[dict[str, Any]]:
    """Extract lab_result_v1-style rows from OCR text tables.

    This handles fixed-width OCR output such as:
        TEST VALUE UNIT FLAG
        HBA1C 7.4 % HIGH
        GLUCOSE 182 MG/DL HIGH

    It is intentionally narrow: the parser only activates inside a lab-results
    section or after a TEST/VALUE/UNIT header, and it does not fabricate missing
    patient IDs or dates.
    """

    lines = [line.strip() for line in text.splitlines()]
    start_index = _lab_results_start_index(lines)
    if start_index is None:
        return []

    visit_date = _extract_lab_visit_date(text)
    patient_id = _extract_lab_patient_id(text)
    records: list[dict[str, Any]] = []
    seen_data = False
    miss_count = 0

    for offset, line in enumerate(lines[start_index:], start=start_index + 1):
        if not line:
            if seen_data:
                miss_count += 1
            continue
        if _is_lab_section_boundary(line):
            if seen_data:
                break
            continue
        if _is_lab_table_header(line):
            continue

        record = _parse_fixed_width_lab_line(line)
        if record is None:
            if seen_data:
                miss_count += 1
                if miss_count >= 2:
                    break
            continue

        seen_data = True
        miss_count = 0
        record["date"] = visit_date
        record["patient_id"] = patient_id
        record["_source_row"] = offset
        records.append(record)

    return records


def _lab_results_start_index(lines: list[str]) -> int | None:
    for index, line in enumerate(lines):
        normalized = _ocr_normalize_upper(line)
        if "LAB RESULTS" in normalized or "LABORATORY RESULTS" in normalized:
            return index + 1
        if _is_lab_table_header(line):
            return index + 1
    return None


def _is_lab_table_header(line: str) -> bool:
    normalized = _ocr_normalize_upper(line)
    return (
        "TEST" in normalized
        and "VALUE" in normalized
        and ("UNIT" in normalized or "UNITS" in normalized)
    )


def _is_lab_section_boundary(line: str) -> bool:
    normalized = _ocr_normalize_upper(line)
    boundaries = (
        "MEDICATION",
        "ASSESSMENT",
        "PLAN",
        "PROBLEM LIST",
        "DIAGNOSIS",
        "FOLLOW UP",
        "SIGNED",
        "PROVIDER",
        "VISIT INFORMATION",
        "PATIENT INFORMATION",
    )
    return any(normalized.startswith(boundary) for boundary in boundaries)


def _parse_fixed_width_lab_line(line: str) -> dict[str, Any] | None:
    tokens = line.replace("|", " ").split()
    if len(tokens) < 3:
        return None

    value_index = next(
        (index for index, token in enumerate(tokens[1:], start=1) if _is_numeric_token(token)),
        None,
    )
    if value_index is None or value_index == 0 or value_index + 1 >= len(tokens):
        return None

    lab_name = " ".join(tokens[:value_index]).strip(" :-")
    value = _normalize_number_token(tokens[value_index])
    unit, consumed = _parse_lab_unit(tokens[value_index + 1 :])
    if not lab_name or unit is None:
        return None

    flag_tokens = tokens[value_index + 1 + consumed :]
    record: dict[str, Any] = {
        "lab_name": _normalize_lab_name(lab_name),
        "value": value,
        "unit": unit,
    }
    if flag_tokens:
        record["flag"] = " ".join(flag_tokens)
    return record


def _parse_lab_unit(tokens: list[str]) -> tuple[str | None, int]:
    if not tokens:
        return None, 0
    first = tokens[0].strip()
    if first == "%" or _looks_like_unit(first):
        return first.upper(), 1
    if len(tokens) >= 3 and _looks_like_unit(tokens[0]) and tokens[1] == "/" and _looks_like_unit(tokens[2]):
        return f"{tokens[0]}/{tokens[2]}".upper(), 3
    return None, 0


def _looks_like_unit(value: str) -> bool:
    normalized = value.strip().upper()
    if not normalized:
        return False
    known_units = {
        "%",
        "MG/DL",
        "MMOL/L",
        "G/DL",
        "MG/L",
        "UG/ML",
        "NG/ML",
        "U/L",
        "IU/L",
        "MEQ/L",
        "FL",
        "PG",
        "K/UL",
        "10^3/UL",
    }
    return normalized in known_units or bool(re.fullmatch(r"[A-Z%][A-Z0-9^/%.\-]*", normalized))


def _is_numeric_token(value: str) -> bool:
    return bool(re.fullmatch(r"[<>]?\d+(?:[.,]\d+)?", value.strip()))


def _normalize_number_token(value: str) -> str:
    return value.strip().replace(",", ".")


def _normalize_lab_name(value: str) -> str:
    aliases = {
        "HBAIC": "HBA1C",
        "HBALC": "HBA1C",
        "HBAI C": "HBA1C",
    }
    normalized = " ".join(value.strip().upper().split())
    return aliases.get(normalized, normalized)


def _extract_lab_visit_date(text: str) -> str:
    patterns = (
        r"\bVISIT\s+DATE[:\s]+(\d{4}-\d{2}-\d{2})\b",
        r"\bCOLLECT(?:ED|ION)?\s+DATE[:\s]+(\d{4}-\d{2}-\d{2})\b",
        r"\bOBSERVATION\s+DATE[:\s]+(\d{4}-\d{2}-\d{2})\b",
        r"\bDATE[:\s]+(\d{4}-\d{2}-\d{2})\b",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return ""


def _extract_lab_patient_id(text: str) -> str:
    patterns = (
        r"\bMRN[:\s]+([A-Z0-9][A-Z0-9\-]{2,})\b",
        r"\bPATIENT\s+ID[:\s]+([A-Z0-9][A-Z0-9\-]{2,})\b",
        r"\bPATIENT_ID[:\s]+([A-Z0-9][A-Z0-9\-]{2,})\b",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).upper()
    return ""


def _ocr_normalize_upper(value: str) -> str:
    return " ".join(value.upper().replace(":", " ").replace("|", " ").split())


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
