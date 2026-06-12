"""Validation for LLM-generated plans and display text."""

from __future__ import annotations

from collections.abc import Iterable

from ojtflow.core.contracts.assistant import AssistantPlan
from ojtflow.core.contracts.generated_output import (
    GeneratedOutputSurface,
    GeneratedOutputValidationIssue,
    GeneratedOutputValidationResult,
)
from ojtflow.core.policy.prompt_injection_policy import contains_prompt_injection_text


POLICY_VERSION = "generated_output_validation.v1"


def validate_assistant_plan_output(
    plan: AssistantPlan,
    *,
    allowed_tool_names: Iterable[str],
) -> GeneratedOutputValidationResult:
    """Validate a generated Assistant plan before execution/display."""

    allowed = set(allowed_tool_names)
    issues: list[GeneratedOutputValidationIssue] = []
    if contains_prompt_injection_text(plan.message, surface="generated_output"):
        issues.append(
            GeneratedOutputValidationIssue(
                code="prompt_injection_in_plan_message",
                severity="error",
                message="LLM plan message contains prompt-injection-like text.",
                field="message",
            )
        )
    for index, tool_call in enumerate(plan.tool_calls):
        if tool_call.tool_name not in allowed:
            issues.append(
                GeneratedOutputValidationIssue(
                    code="unknown_tool_name",
                    severity="error",
                    message="LLM plan referenced a tool outside the backend allowlist.",
                    field=f"tool_calls[{index}].tool_name",
                )
            )
        if contains_prompt_injection_text(tool_call.rationale, surface="generated_output"):
            issues.append(
                GeneratedOutputValidationIssue(
                    code="prompt_injection_in_tool_rationale",
                    severity="error",
                    message="LLM tool rationale contains prompt-injection-like text.",
                    field=f"tool_calls[{index}].rationale",
                )
            )
    return _result("assistant_plan", issues)


def validate_generated_text_output(
    text: str,
    *,
    surface: GeneratedOutputSurface,
    source_ref: str | None = None,
) -> GeneratedOutputValidationResult:
    """Validate generated display/export text before exposing or storing it."""

    issues: list[GeneratedOutputValidationIssue] = []
    if contains_prompt_injection_text(text, surface="generated_output"):
        issues.append(
            GeneratedOutputValidationIssue(
                code="prompt_injection_in_generated_text",
                severity="error",
                message="Generated text contains prompt-injection-like text.",
                source_ref=source_ref,
            )
        )
    return _result(surface, issues)


def validation_warning(result: GeneratedOutputValidationResult) -> str:
    """Return a compact user-facing warning for failed generated output validation."""

    issue_text = "; ".join(issue.code for issue in result.issues) or "unknown_issue"
    return (
        f"LLM generated output failed validation for {result.surface}: "
        f"{issue_text}."
    )


def _result(
    surface: GeneratedOutputSurface,
    issues: list[GeneratedOutputValidationIssue],
) -> GeneratedOutputValidationResult:
    blocked = any(issue.severity == "error" for issue in issues)
    warning = bool(issues)
    return GeneratedOutputValidationResult(
        surface=surface,
        status="blocked" if blocked else "warning" if warning else "passed",
        issue_count=len(issues),
        issues=issues,
        policy_version=POLICY_VERSION,
    )
