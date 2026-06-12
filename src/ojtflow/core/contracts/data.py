"""Structured-data contracts used by tools, agents, and workflow state."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.contracts.enums import DataFormat
from ojtflow.core.contracts.issue import Issue
from ojtflow.core.contracts.phi import PhiClassification
from ojtflow.core.ids import new_id


class FormatDetection(ContractModel):
    """Result of deterministic format detection."""

    format: DataFormat
    confidence: float
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ParsedData(ContractModel):
    """Parsed data plus source-preserving metadata."""

    format: DataFormat
    content: Any
    records: list[dict[str, Any]] = Field(default_factory=list)
    source_ref: str | None = None
    parser_warnings: list[str] = Field(default_factory=list)


class FieldProfile(ContractModel):
    """Profile of one field or column."""

    name: str
    normalized_name: str
    inferred_types: list[str] = Field(default_factory=list)
    sample_values: list[str] = Field(default_factory=list)
    missing_count: int = 0
    non_empty_count: int = 0
    unique_count: int = 0
    confidence: float = 0.0
    possible_phi: bool = False


class DataProfile(ContractModel):
    """Dataset profile used for schema matching, validation, and explanation."""

    format: DataFormat
    row_count: int
    column_count: int
    fields: list[FieldProfile] = Field(default_factory=list)
    phi_classification: PhiClassification | None = None
    warnings: list[str] = Field(default_factory=list)


class ValidationReport(ContractModel):
    """Structured validation result."""

    report_id: str = Field(default_factory=lambda: new_id("val"))
    valid: bool
    schema_id: str | None = None
    schema_confidence: float | None = None
    severity_summary: dict[str, int] = Field(default_factory=dict)
    issues: list[Issue] = Field(default_factory=list)
    phi_classification: PhiClassification | None = None
    requires_review: bool = False


class TransformationAction(ContractModel):
    """One proposed or approved transformation action."""

    action_id: str = Field(default_factory=lambda: new_id("act"))
    action: str
    field: str | None = None
    affected_rows: list[int] = Field(default_factory=list)
    reason: str
    requires_review: bool = False
    parameters: dict[str, Any] = Field(default_factory=dict)


class TransformationPlan(ContractModel):
    """Plan built from validation findings and user intent."""

    plan_id: str = Field(default_factory=lambda: new_id("plan"))
    target_format: DataFormat
    actions: list[TransformationAction] = Field(default_factory=list)
    requires_review: bool = False


class TransformationOutput(ContractModel):
    """Output of deterministic transformation."""

    output_id: str = Field(default_factory=lambda: new_id("out"))
    output_format: DataFormat
    output_ref: str | None = None
    output_hash: str | None = None
    preview: str | None = None
    phi_classification: PhiClassification | None = None
    diff_summary: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class ExplanationReport(ContractModel):
    """Evidence-grounded explanation report."""

    explanation_id: str = Field(default_factory=lambda: new_id("exp"))
    answer_type: str = "data_transformation_explanation"
    intended_use: str = "Support data validation and review; not autonomous diagnosis"
    summary: str
    supported_claims: list[dict[str, Any]] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    data_quality_flags: list[str] = Field(default_factory=list)
    uncertainty: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
