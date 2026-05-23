"""Dataset profiling."""

from __future__ import annotations

from datetime import date
from typing import Any

from ojtflow.core.contracts.data import DataProfile, FieldProfile, ParsedData
from ojtflow.core.policy.risk_rules import looks_sensitive_field


def profile_data(parsed: ParsedData) -> DataProfile:
    """Build a lightweight profile over parsed records."""

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

