"""Risk and review-gate policy rules."""

from __future__ import annotations

from ojtflow.core.contracts.data import TransformationPlan, ValidationReport
from ojtflow.core.contracts.enums import Severity
from ojtflow.core.policy.phi_policy import matches_phi_field_policy
from ojtflow.core.policy.prompt_injection_policy import contains_prompt_injection_text

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

    return matches_phi_field_policy(field_name)


def contains_prompt_injection(text: str) -> bool:
    """Flag suspicious instruction-like text embedded in data or retrieved context."""

    return contains_prompt_injection_text(text)
