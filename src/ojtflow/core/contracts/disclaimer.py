"""Clinical/legal disclaimer policy contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel, NonBlankStr


DisclaimerSeverity = Literal["info", "caution", "critical"]
DisclaimerSurface = Literal[
    "global",
    "assistant",
    "workbench",
    "workflows",
    "workflow_detail",
    "reviews",
    "retrieval",
    "audit",
    "schemas",
    "settings",
    "help",
]


class DisclaimerMessage(ContractModel):
    surface_id: DisclaimerSurface
    title: NonBlankStr
    message: NonBlankStr
    severity: DisclaimerSeverity
    review_required: bool = True
    prohibited_uses: list[NonBlankStr] = Field(default_factory=list)
    human_review_text: NonBlankStr
    evidence_text: NonBlankStr


class DisclaimerPolicy(ContractModel):
    version: NonBlankStr = "disclaimer_policy.v1"
    intended_use: NonBlankStr
    non_diagnostic_statement: NonBlankStr
    human_review_requirement: NonBlankStr
    prohibited_uses: list[NonBlankStr] = Field(min_length=1)
    surfaces: list[DisclaimerMessage] = Field(min_length=1)
