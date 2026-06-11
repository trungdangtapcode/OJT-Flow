"""Workflow state contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.contracts.clinical import ClinicalPackage
from ojtflow.core.contracts.data import (
    DataProfile,
    ExplanationReport,
    TransformationOutput,
    TransformationPlan,
    ValidationReport,
)
from ojtflow.core.contracts.enums import DataFormat, WorkflowStatus
from ojtflow.core.contracts.evidence import Evidence
from ojtflow.core.contracts.review import HumanReview
from ojtflow.core.ids import new_id
from ojtflow.core.time import utc_now


class WorkflowInput(ContractModel):
    """Input references and format metadata."""

    dataset_ref: str
    input_hash: str
    declared_format: DataFormat | None = None
    detected_format: DataFormat = DataFormat.UNKNOWN


class WorkflowIntent(ContractModel):
    """Normalized user intent."""

    task_type: str = "structured_data_workflow"
    target_format: DataFormat | None = None
    requires_explanation: bool = True
    options: dict[str, Any] = Field(default_factory=dict)


class WorkflowOutput(ContractModel):
    """Final output references and report IDs."""

    transformation: TransformationOutput | None = None
    validation_report_id: str | None = None
    explanation_id: str | None = None


class WorkflowOutputArtifact(ContractModel):
    """User-readable generated artifact for a completed workflow."""

    workflow_id: str
    output_format: DataFormat
    output_hash: str | None = None
    byte_size: int
    content: str
    warnings: list[str] = Field(default_factory=list)
    diff_summary: dict[str, Any] = Field(default_factory=dict)


class WorkflowStep(ContractModel):
    """UI/progress-oriented workflow step separate from append-only audit events."""

    step_id: str = Field(default_factory=lambda: new_id("step"))
    name: str
    status: str
    started_at: str = Field(default_factory=lambda: utc_now().isoformat())
    completed_at: str | None = None
    summary: str
    output_ref: str | None = None
    issue_count: int = 0


class WorkflowFailure(ContractModel):
    """Structured failure recorded when a workflow cannot continue."""

    code: str
    message: str
    error_type: str
    details: dict[str, Any] = Field(default_factory=dict)
    failed_at: str = Field(default_factory=lambda: utc_now().isoformat())


class WorkflowState(ContractModel):
    """Single auditable source of truth for one workflow run."""

    workflow_id: str = Field(default_factory=lambda: new_id("wf"))
    owner_user_id: str | None = None
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())
    updated_at: str = Field(default_factory=lambda: utc_now().isoformat())
    status: WorkflowStatus = WorkflowStatus.CREATED
    schema_version: str = "workflow_state.v0"
    user_instruction: str
    input: WorkflowInput | None = None
    intent: WorkflowIntent = Field(default_factory=WorkflowIntent)
    steps: list[WorkflowStep] = Field(default_factory=list)
    profile: DataProfile | None = None
    schema_profile: dict[str, Any] | None = None
    retrieved_context: list[Evidence] = Field(default_factory=list)
    validation_report: ValidationReport | None = None
    transformation_plan: TransformationPlan | None = None
    review: HumanReview | None = None
    output: WorkflowOutput | None = None
    explanation: ExplanationReport | None = None
    clinical_package: ClinicalPackage | None = None
    failure: WorkflowFailure | None = None
    handoff_context: dict[str, Any] = Field(default_factory=dict)
    risk_flags: list[str] = Field(default_factory=list)
    audit_event_refs: list[str] = Field(default_factory=list)

    def touch(self) -> None:
        """Update the state timestamp."""

        self.updated_at = utc_now().isoformat()
