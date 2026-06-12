"""Generated output validation contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel, NonBlankStr


GeneratedOutputSurface = Literal[
    "assistant_plan",
    "assistant_summary",
    "assistant_stream_summary",
    "export_description",
]
GeneratedOutputValidationStatus = Literal["passed", "warning", "blocked"]


class GeneratedOutputValidationIssue(ContractModel):
    """One validation issue for model-generated text or plans."""

    code: NonBlankStr
    severity: Literal["warning", "error"]
    message: NonBlankStr
    field: NonBlankStr | None = None
    source_ref: NonBlankStr | None = None


class GeneratedOutputValidationResult(ContractModel):
    """Validation result for an LLM-generated output surface."""

    surface: GeneratedOutputSurface
    status: GeneratedOutputValidationStatus
    issue_count: int = Field(ge=0)
    issues: list[GeneratedOutputValidationIssue] = Field(default_factory=list)
    policy_version: NonBlankStr = "generated_output_validation.v1"
