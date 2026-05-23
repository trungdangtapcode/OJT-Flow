"""Risk and review-gate policy rules."""

from __future__ import annotations

from ojtflow.core.contracts.data import TransformationPlan, ValidationReport
from ojtflow.core.contracts.enums import Severity

SENSITIVE_FIELD_TOKENS = {
    "patient",
    "name",
    "address",
    "phone",
    "email",
    "insurance",
    "diagnosis",
    "medication",
    "medical_history",
    "ssn",
}

PROMPT_INJECTION_PATTERNS = (
    "ignore previous",
    "ignore all previous",
    "system prompt",
    "developer message",
    "follow these instructions",
    "do not tell the user",
)


def review_required(report: ValidationReport, plan: TransformationPlan | None = None) -> bool:
    """Return whether findings or planned actions require human review."""

    if report.requires_review:
        return True
    if any(issue.requires_review for issue in report.issues):
        return True
    if any(issue.severity in {Severity.ERROR, Severity.CRITICAL} for issue in report.issues):
        return True
    return bool(plan and (plan.requires_review or any(action.requires_review for action in plan.actions)))


def looks_sensitive_field(field_name: str) -> bool:
    """Heuristic high-recall sensitive field detector for MVP fixtures."""

    normalized = field_name.lower().replace("-", "_").replace(" ", "_")
    return any(token in normalized for token in SENSITIVE_FIELD_TOKENS)


def contains_prompt_injection(text: str) -> bool:
    """Flag suspicious instruction-like text embedded in data or retrieved context."""

    lowered = text.lower()
    return any(pattern in lowered for pattern in PROMPT_INJECTION_PATTERNS)

