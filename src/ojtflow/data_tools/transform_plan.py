"""Build reviewable transformation plans from validation reports."""

from __future__ import annotations

from ojtflow.core.contracts.data import TransformationAction, TransformationPlan, ValidationReport
from ojtflow.core.contracts.enums import DataFormat


def build_transformation_plan(
    report: ValidationReport,
    target_format: DataFormat,
) -> TransformationPlan:
    """Create a conservative transformation plan from validation issues."""

    actions: list[TransformationAction] = []

    for issue in report.issues:
        if issue.kind == "date_format_inconsistency":
            actions.append(
                TransformationAction(
                    action="normalize_date",
                    field=issue.location.field if issue.location else None,
                    affected_rows=[issue.location.row] if issue.location and issue.location.row else [],
                    reason=issue.message,
                    requires_review=True,
                    parameters={
                        "target_format": issue.metadata.get("target_format", "YYYY-MM-DD"),
                        "original_value": issue.metadata.get("value"),
                    },
                )
            )
        elif issue.kind == "missing_value":
            actions.append(
                TransformationAction(
                    action="preserve_missing_as_null",
                    field=issue.location.field if issue.location else None,
                    affected_rows=[issue.location.row] if issue.location and issue.location.row else [],
                    reason=issue.message,
                    requires_review=True,
                )
            )
        elif issue.kind == "missing_unit":
            actions.append(
                TransformationAction(
                    action="preserve_missing_unit_as_null",
                    field=issue.location.field if issue.location else "unit",
                    affected_rows=[issue.location.row] if issue.location and issue.location.row else [],
                    reason=issue.message,
                    requires_review=True,
                )
            )
        elif issue.kind == "possible_phi":
            actions.append(
                TransformationAction(
                    action="mask_sensitive_field_for_explanation",
                    field=issue.location.field if issue.location else None,
                    reason=issue.message,
                    requires_review=True,
                )
            )

    return TransformationPlan(
        target_format=target_format,
        actions=actions,
        requires_review=any(action.requires_review for action in actions),
    )
