"""Clinical package contracts for governed healthcare workflow output."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel, NonBlankStr
from ojtflow.core.contracts.enums import DataFormat, Severity
from ojtflow.core.contracts.evidence import Evidence
from ojtflow.core.contracts.issue import SourceLocation
from ojtflow.core.contracts.terminology import (
    TerminologyCandidate,
    UnitValidationResult,
)
from ojtflow.core.ids import new_id
from ojtflow.core.time import utc_now


ClinicalProvenanceActivity = Literal[
    "parse",
    "profile",
    "validate",
    "map",
    "retrieve_evidence",
    "review",
    "transform",
    "explain",
]

ClinicalProvenanceDerivation = Literal[
    "source",
    "derived",
    "defaulted",
    "review_required",
    "unmapped",
]


class ClinicalPackageRawInput(ContractModel):
    """Raw workflow input identity inside a clinical package."""

    dataset_ref: NonBlankStr
    input_hash: NonBlankStr
    declared_format: DataFormat | None = None
    detected_format: DataFormat


class ClinicalFieldProvenance(ContractModel):
    """Source and derivation trace for one generated clinical resource field."""

    target_path: NonBlankStr
    source_field: str | None = None
    source_value: Any | None = None
    location: SourceLocation | None = None
    evidence_ids: list[NonBlankStr] = Field(default_factory=list)
    derivation: ClinicalProvenanceDerivation = "source"
    note: NonBlankStr


class ClinicalResourceRecord(ContractModel):
    """One generated or preserved FHIR-like resource plus field provenance."""

    resource_id: NonBlankStr
    resource_type: NonBlankStr
    resource: dict[str, Any]
    field_provenance: list[ClinicalFieldProvenance] = Field(default_factory=list)
    source_row: int | None = Field(default=None, ge=1)
    review_required: bool = False
    warnings: list[NonBlankStr] = Field(default_factory=list)


class ClinicalBundle(ContractModel):
    """FHIR-like bundle plus normalized resource records."""

    resourceType: Literal["Bundle"] = "Bundle"
    type: NonBlankStr = "collection"
    entry: list[dict[str, Any]] = Field(default_factory=list)
    resources: list[ClinicalResourceRecord] = Field(default_factory=list)


class ClinicalOperationOutcomeIssue(ContractModel):
    """FHIR OperationOutcome-like issue linked to validation issues."""

    severity: Severity
    code: NonBlankStr
    diagnostics: NonBlankStr
    expression: list[NonBlankStr] = Field(default_factory=list)
    issue_id: NonBlankStr | None = None
    location: SourceLocation | None = None
    requires_review: bool = False


class ClinicalOperationOutcome(ContractModel):
    """FHIR OperationOutcome-like validation summary for the package."""

    resourceType: Literal["OperationOutcome"] = "OperationOutcome"
    issue: list[ClinicalOperationOutcomeIssue] = Field(default_factory=list)


class ClinicalProvenanceRecord(ContractModel):
    """Internal Provenance-like activity record for package construction."""

    provenance_id: NonBlankStr = Field(default_factory=lambda: new_id("prov"))
    activity: ClinicalProvenanceActivity
    agent: NonBlankStr
    target_refs: list[NonBlankStr] = Field(default_factory=list)
    source_refs: list[NonBlankStr] = Field(default_factory=list)
    evidence_ids: list[NonBlankStr] = Field(default_factory=list)
    issue_ids: list[NonBlankStr] = Field(default_factory=list)
    occurred_at: NonBlankStr = Field(default_factory=lambda: utc_now().isoformat())
    summary: NonBlankStr
    metadata: dict[str, Any] = Field(default_factory=dict)


class ClinicalPackage(ContractModel):
    """Canonical OJTFlow envelope around FHIR-like resources and governance state."""

    package_type: Literal["ojtflow_clinical_package"] = "ojtflow_clinical_package"
    schema_version: NonBlankStr = "clinical_package.v0"
    package_id: NonBlankStr = Field(default_factory=lambda: new_id("cpkg"))
    workflow_id: NonBlankStr
    raw_input: ClinicalPackageRawInput
    clinical_bundle: ClinicalBundle
    operation_outcome: ClinicalOperationOutcome
    validation_report_id: NonBlankStr | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    terminology_candidates: list[TerminologyCandidate] = Field(default_factory=list)
    unit_validations: list[UnitValidationResult] = Field(default_factory=list)
    provenance: list[ClinicalProvenanceRecord] = Field(default_factory=list)
    review: dict[str, Any] | None = None
    audit_event_refs: list[NonBlankStr] = Field(default_factory=list)
    output_refs: list[NonBlankStr] = Field(default_factory=list)
    handoff_context: dict[str, Any] = Field(default_factory=dict)
    warnings: list[NonBlankStr] = Field(default_factory=list)
    created_at: NonBlankStr = Field(default_factory=lambda: utc_now().isoformat())
    updated_at: NonBlankStr = Field(default_factory=lambda: utc_now().isoformat())
