"""Terminology candidate and unit validation contracts."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel, NonBlankStr
from ojtflow.core.contracts.issue import SourceLocation
from ojtflow.core.ids import new_id


TerminologyCandidateStatus = Literal[
    "candidate",
    "review_required",
    "accepted",
    "rejected",
]

UnitValidationStatus = Literal[
    "valid",
    "missing",
    "unknown",
    "not_preferred",
]


class TerminologyCandidate(ContractModel):
    """Review-gated terminology candidate for a source clinical value."""

    candidate_id: NonBlankStr = Field(default_factory=lambda: new_id("term"))
    source_field: NonBlankStr
    source_value: NonBlankStr
    standard_system: NonBlankStr
    code: NonBlankStr
    display: NonBlankStr
    confidence: float = Field(ge=0.0, le=1.0)
    matched_aliases: list[NonBlankStr] = Field(default_factory=list)
    source_uri: NonBlankStr | None = None
    location: SourceLocation | None = None
    status: TerminologyCandidateStatus = "review_required"
    requires_review: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class UnitValidationResult(ContractModel):
    """UCUM-like unit validation result for one source value."""

    validation_id: NonBlankStr = Field(default_factory=lambda: new_id("unit"))
    source_field: NonBlankStr
    source_unit: str
    normalized_unit: str | None = None
    standard_system: NonBlankStr = "UCUM"
    status: UnitValidationStatus
    confidence: float = Field(ge=0.0, le=1.0)
    message: NonBlankStr
    location: SourceLocation | None = None
    requires_review: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
