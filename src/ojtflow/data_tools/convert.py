"""Rule-based conversions."""

from __future__ import annotations

import csv
import json
from datetime import date
from io import StringIO
from typing import Any

import yaml

from ojtflow.core.contracts.data import ParsedData, TransformationOutput, TransformationPlan
from ojtflow.core.contracts.enums import DataFormat
from ojtflow.core.errors import ToolExecutionError
from ojtflow.data_tools.hashing import sha256_text
from ojtflow.data_tools.phi import classify_text


def convert_data(
    parsed: ParsedData,
    target_format: DataFormat,
    plan: TransformationPlan | None = None,
) -> tuple[str, TransformationOutput]:
    """Convert parsed data to target format using approved rule-based actions."""

    normalized = _apply_plan(parsed.records, plan) if parsed.records else parsed.content
    warnings: list[str] = []
    if target_format == DataFormat.JSON:
        output_text = json.dumps(normalized, ensure_ascii=False, indent=2, sort_keys=True)
    elif target_format == DataFormat.YAML:
        output_text = yaml.safe_dump(normalized, sort_keys=True, allow_unicode=True)
    elif target_format == DataFormat.CSV:
        warnings.extend(_csv_warnings(normalized))
        output_text = _to_csv(normalized)
    else:
        raise ToolExecutionError(f"Unsupported target format: {target_format}")

    output = TransformationOutput(
        output_format=target_format,
        output_hash=sha256_text(output_text),
        preview=output_text[:1000],
        phi_classification=classify_text(
            output_text,
            target_type="generated_output",
            data_format=target_format,
        ),
        diff_summary=_diff_summary(parsed, normalized, plan),
        warnings=warnings,
    )
    return output_text, output


def _apply_plan(records: list[dict[str, Any]], plan: TransformationPlan | None) -> list[dict[str, Any]]:
    actions = plan.actions if plan else []
    normalize_date_fields = {
        action.field for action in actions if action.action == "normalize_date" and action.field
    }
    null_fields = {
        action.field
        for action in actions
        if action.action in {"preserve_missing_as_null", "preserve_missing_unit_as_null"} and action.field
    }
    mask_fields = {
        action.field for action in actions if action.action == "mask_sensitive_field_for_explanation" and action.field
    }

    output: list[dict[str, Any]] = []
    for record in records:
        converted: dict[str, Any] = {}
        for field, value in record.items():
            if field == "_source_row":
                continue
            new_value = value
            if field in normalize_date_fields and isinstance(value, str):
                new_value = _normalize_date(value)
            if field in null_fields and value == "":
                new_value = None
            if field in mask_fields and value not in (None, ""):
                new_value = "[MASKED]"
            converted[field] = new_value
        output.append(converted)
    return output


def _normalize_date(value: str) -> str:
    for separator in ("/", "."):
        if separator in value:
            candidate = value.replace(separator, "-")
            try:
                return date.fromisoformat(candidate).isoformat()
            except ValueError:
                return value
    return value


def _to_csv(content: Any) -> str:
    if not isinstance(content, list) or not all(isinstance(row, dict) for row in content):
        raise ToolExecutionError("CSV output requires a list of objects")
    if not content:
        return ""
    fields: list[str] = []
    for row in content:
        for key in row:
            if key not in fields:
                fields.append(key)
    stream = StringIO()
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows(content)
    return stream.getvalue()


def _csv_warnings(content: Any) -> list[str]:
    if not isinstance(content, list) or not all(isinstance(row, dict) for row in content):
        return []
    for row in content:
        if any(isinstance(value, dict | list) for value in row.values()):
            return ["nested JSON/YAML values may be lossy when flattened to CSV"]
    return []


def _diff_summary(
    parsed: ParsedData,
    normalized: Any,
    plan: TransformationPlan | None,
) -> dict[str, Any]:
    actions = plan.actions if plan else []
    return {
        "format_changed": True,
        "source_format": parsed.format.value,
        "target_row_count": len(normalized) if isinstance(normalized, list) else None,
        "actions_applied": [action.action for action in actions],
        "rows_preserved": len(normalized) if isinstance(normalized, list) else None,
        "values_modified_by_plan": sum(len(action.affected_rows) or 1 for action in actions),
    }
