"""Schema and policy validation tools."""

from __future__ import annotations

from datetime import date
from typing import Any

from ojtflow.core.contracts.data import DataProfile, ParsedData, ValidationReport
from ojtflow.core.contracts.enums import Severity
from ojtflow.core.contracts.issue import Issue, SourceLocation
from ojtflow.core.policy.risk_rules import contains_prompt_injection, looks_sensitive_field


def validate_against_schema(
    parsed: ParsedData,
    profile: DataProfile,
    schema: dict[str, Any] | None,
) -> ValidationReport:
    """Validate parsed data against a pragmatic JSON-Schema-like fixture."""

    issues: list[Issue] = []
    schema_id = schema.get("$id") if schema else None
    required = set(schema.get("required", [])) if schema else set()
    properties = schema.get("properties", {}) if schema else {}
    fields = {field.name for field in profile.fields}

    for required_field in sorted(required - fields):
        issues.append(
            Issue(
                kind="missing_required_field",
                severity=Severity.ERROR,
                message=f"Required field '{required_field}' is missing",
                location=SourceLocation(field=required_field, source_ref=parsed.source_ref),
                suggested_action="ask_user_or_select_another_schema",
                requires_review=True,
            )
        )

    for field_profile in profile.fields:
        if field_profile.possible_phi:
            issues.append(
                Issue(
                    kind="possible_phi",
                    severity=Severity.WARNING,
                    message=f"Field '{field_profile.name}' may contain sensitive healthcare data",
                    location=SourceLocation(field=field_profile.name, source_ref=parsed.source_ref),
                    suggested_action="consider_masking_before_export_or_explanation",
                    requires_review=True,
                )
            )
        if looks_sensitive_field(field_profile.name) and field_profile.name.lower() not in {"patient_id"}:
            continue

    for warning in profile.warnings:
        if warning.startswith("row "):
            issues.append(
                Issue(
                    kind="malformed_row",
                    severity=Severity.WARNING,
                    message=warning,
                    location=SourceLocation(source_ref=parsed.source_ref),
                    suggested_action="inspect_source_row_before_transforming",
                    requires_review=True,
                )
            )

    for row_number, record in enumerate(parsed.records, start=1):
        source_row = int(record.get("_source_row", row_number))
        if (
            record.get("unit") in (None, "")
            and (record.get("value") not in (None, "") or record.get("lab_name") not in (None, ""))
        ):
            issues.append(
                Issue(
                    kind="missing_unit",
                    severity=Severity.WARNING,
                    message=f"Lab value is present but unit is missing on row {source_row}",
                    location=SourceLocation(
                        row=source_row,
                        column="unit",
                        field="unit",
                        source_ref=parsed.source_ref,
                    ),
                    suggested_action="ask_user_or_clinician_for_unit_before_downstream_use",
                    requires_review=True,
                )
            )
        for field in required:
            if record.get(field) in (None, ""):
                issues.append(
                    Issue(
                        kind="missing_value",
                        severity=Severity.WARNING,
                        message=f"Required field '{field}' is empty on row {source_row}",
                        location=SourceLocation(
                            row=source_row,
                            column=field,
                            field=field,
                            source_ref=parsed.source_ref,
                        ),
                        suggested_action="ask_user_or_clinician_before_filling",
                        requires_review=True,
                    )
                )

        for field, value in record.items():
            if field == "_source_row":
                continue
            if isinstance(value, str) and contains_prompt_injection(value):
                issues.append(
                    Issue(
                        kind="prompt_injection_pattern",
                        severity=Severity.CRITICAL,
                        message=f"Potential prompt injection text found in field '{field}'",
                        location=SourceLocation(
                            row=source_row,
                            column=field,
                            field=field,
                            source_ref=parsed.source_ref,
                        ),
                        suggested_action="treat_cell_as_data_only",
                        requires_review=True,
                    )
                )

            field_schema = properties.get(field)
            if field_schema:
                issue = _validate_value(field, value, field_schema, source_row, parsed.source_ref)
                if issue:
                    issues.append(issue)

    severity_summary = {severity.value: 0 for severity in Severity}
    for issue in issues:
        severity_summary[issue.severity.value] += 1

    valid = not any(issue.severity in {Severity.ERROR, Severity.CRITICAL} for issue in issues)
    requires_review = any(issue.requires_review for issue in issues)
    schema_confidence = _schema_confidence(fields, required, set(properties)) if schema else None

    return ValidationReport(
        valid=valid,
        schema_id=schema_id,
        schema_confidence=schema_confidence,
        severity_summary=severity_summary,
        issues=issues,
        requires_review=requires_review,
    )


def _validate_value(
    field: str,
    value: Any,
    field_schema: dict[str, Any],
    source_row: int,
    source_ref: str | None,
) -> Issue | None:
    if value in (None, ""):
        return None

    expected_type = field_schema.get("type")
    if expected_type == "number":
        try:
            float(value)
        except (TypeError, ValueError):
            return Issue(
                kind="type_mismatch",
                severity=Severity.ERROR,
                message=f"Field '{field}' expected number but got '{value}'",
                location=SourceLocation(row=source_row, column=field, field=field, source_ref=source_ref),
                suggested_action="correct_value_or_schema",
                requires_review=True,
            )
    if field_schema.get("format") == "date":
        try:
            date.fromisoformat(str(value))
        except ValueError:
            return Issue(
                kind="date_format_inconsistency",
                severity=Severity.WARNING,
                message=f"Field '{field}' has non-ISO date '{value}' on row {source_row}",
                location=SourceLocation(row=source_row, column=field, field=field, source_ref=source_ref),
                suggested_action="normalize_date_after_human_review",
                requires_review=True,
                metadata={"value": value, "target_format": "YYYY-MM-DD"},
            )

    enum = field_schema.get("enum")
    if enum and value not in enum:
        return Issue(
            kind="invalid_enum",
            severity=Severity.WARNING,
            message=f"Field '{field}' value '{value}' is not in allowed values",
            location=SourceLocation(row=source_row, column=field, field=field, source_ref=source_ref),
            suggested_action="confirm_mapping_or_update_schema",
            requires_review=True,
        )

    return None


def _schema_confidence(fields: set[str], required: set[str], properties: set[str]) -> float:
    if not properties:
        return 0.0
    coverage = len(fields & properties) / len(properties)
    required_coverage = len(fields & required) / len(required) if required else 1.0
    return round((coverage * 0.6) + (required_coverage * 0.4), 3)
