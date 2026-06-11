"""Dataset profiling."""

from __future__ import annotations

from datetime import date
from typing import Any

from ojtflow.core.contracts.data import DataProfile, FieldProfile, ParsedData
from ojtflow.core.contracts.enums import DataFormat
from ojtflow.core.policy.risk_rules import looks_sensitive_field
from ojtflow.data_tools.phi import classify_parsed_data


def profile_data(parsed: ParsedData) -> DataProfile:
    """Build a lightweight profile over parsed records."""

    if parsed.format == DataFormat.MARKDOWN:
        return _profile_markdown(parsed)

    records = parsed.records
    fields = _ordered_fields(records, parsed)
    profiles: list[FieldProfile] = []

    for field in fields:
        values = [record.get(field) for record in records]
        non_empty_values = [value for value in values if value not in (None, "")]
        samples = [str(value) for value in non_empty_values[:5]]
        inferred_types = sorted({_infer_type(value) for value in non_empty_values}) or ["empty"]
        confidence = 1.0 if len(inferred_types) == 1 else max(0.35, 1.0 / len(inferred_types))
        profiles.append(
            FieldProfile(
                name=field,
                normalized_name=_normalize(field),
                inferred_types=inferred_types,
                sample_values=samples,
                missing_count=len(values) - len(non_empty_values),
                non_empty_count=len(non_empty_values),
                unique_count=len({str(value) for value in non_empty_values}),
                confidence=confidence,
                possible_phi=looks_sensitive_field(field),
            )
        )

    return DataProfile(
        format=parsed.format,
        row_count=len(records) if records else _non_record_count(parsed.content),
        column_count=len(fields),
        fields=profiles,
        phi_classification=classify_parsed_data(parsed),
        warnings=parsed.parser_warnings,
    )


def _profile_markdown(parsed: ParsedData) -> DataProfile:
    """Profile unstructured markdown / document text.

    If markdown tables were extracted, profile them like structured data.
    Otherwise return document-level metrics.
    """
    content = parsed.content or {}

    # Case 1: tables were extracted — profile like structured records
    if parsed.records and "_text" not in parsed.records[0]:
        return DataProfile(
            format=parsed.format,
            row_count=len(parsed.records),
            column_count=len(parsed.records[0]) - 1 if parsed.records else 0,  # exclude _source_row
            fields=[
                FieldProfile(
                    name=field,
                    normalized_name=_normalize(field),
                    inferred_types=["string"],
                    sample_values=[str(r.get(field, "")) for r in parsed.records[:5] if r.get(field) is not None],
                    missing_count=sum(1 for r in parsed.records if r.get(field) in (None, "")),
                    non_empty_count=sum(1 for r in parsed.records if r.get(field) not in (None, "")),
                    unique_count=len({str(r.get(field, "")) for r in parsed.records}),
                    confidence=0.75,
                    possible_phi=looks_sensitive_field(field),
                )
                for field in [k for k in (parsed.records[0].keys() if parsed.records else []) if k != "_source_row"]
            ],
            phi_classification=classify_parsed_data(parsed),
            warnings=parsed.parser_warnings,
        )

    # Case 2: unstructured text — report document-level metrics as pseudo-fields
    raw = content.get("raw", "") if isinstance(content, dict) else ""
    word_count = content.get("word_count", len(raw.split())) if isinstance(content, dict) else len(raw.split())
    line_count = content.get("line_count", len(raw.splitlines())) if isinstance(content, dict) else len(raw.splitlines())

    pseudo_fields = [
        FieldProfile(
            name="_word_count",
            normalized_name="_word_count",
            inferred_types=["integer"],
            sample_values=[str(word_count)],
            non_empty_count=1,
            unique_count=1,
            confidence=1.0,
        ),
        FieldProfile(
            name="_line_count",
            normalized_name="_line_count",
            inferred_types=["integer"],
            sample_values=[str(line_count)],
            non_empty_count=1,
            unique_count=1,
            confidence=1.0,
        ),
    ]
    return DataProfile(
        format=parsed.format,
        row_count=1,
        column_count=0,
        fields=pseudo_fields,
        phi_classification=classify_parsed_data(parsed),
        warnings=parsed.parser_warnings,
    )


def _ordered_fields(records: list[dict[str, Any]], parsed: ParsedData) -> list[str]:
    if records:
        fields: list[str] = []
        for record in records:
            for key in record:
                if key != "_source_row" and key not in fields:
                    fields.append(key)
        return fields
    if isinstance(parsed.content, dict):
        return [key for key in parsed.content if not key.startswith("_")]
    return []


def _non_record_count(content: Any) -> int:
    if isinstance(content, list):
        return len(content)
    if isinstance(content, dict):
        return 1
    return 0


def _normalize(field: str) -> str:
    return field.strip().lower().replace(" ", "_").replace("-", "_")


def _infer_type(value: Any) -> str:
    if value is None or value == "":
        return "empty"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    text = str(value).strip()
    try:
        int(text)
        return "integer"
    except ValueError:
        pass
    try:
        float(text)
        return "number"
    except ValueError:
        pass
    try:
        date.fromisoformat(text)
        return "date"
    except ValueError:
        return "string"
