from pathlib import Path
import json

import pytest

from ojtflow.application.workflow_service import WorkflowService
from ojtflow.core.contracts.enums import DataFormat, ReviewDecision, WorkflowStatus
from ojtflow.core.errors import ArtifactIntegrityError, NotFoundError, PolicyBlockedError
from ojtflow.data_tools.hashing import sha256_text
from ojtflow.infrastructure.retrieval.static import (
    StaticKnowledgeRepository,
    StaticRetrievalRepository,
)
from ojtflow.infrastructure.storage.in_memory import (
    InMemoryDatasetStore,
    InMemoryEventRepository,
    InMemoryWorkflowRepository,
)


ROOT = Path(__file__).resolve().parents[1]


def make_service() -> WorkflowService:
    return WorkflowService(
        datasets=InMemoryDatasetStore(),
        workflows=InMemoryWorkflowRepository(),
        events=InMemoryEventRepository(),
        knowledge=StaticKnowledgeRepository(ROOT / "knowledge"),
        retrieval=StaticRetrievalRepository(ROOT / "knowledge"),
    )


def _resource_by_type(package, resource_type: str):
    return next(
        record
        for record in package.clinical_bundle.resources
        if record.resource_type == resource_type
    )


def test_workflow_pauses_for_review_then_completes_after_approval() -> None:
    service = make_service()
    text = (ROOT / "data/fixtures/structured/lab_results_messy.csv").read_text()

    workflow = service.start_workflow(
        instruction="Clean this CSV, convert it to JSON, and explain anomalies.",
        data=text,
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
        schema_id="lab_result_v1",
        require_human_review=True,
    )

    assert workflow.status == WorkflowStatus.NEEDS_HUMAN_REVIEW
    assert workflow.review is not None
    assert workflow.transformation_plan is not None
    assert workflow.validation_report is not None
    assert workflow.retrieved_context
    assert workflow.handoff_context["retrieval_trace"]["strategy"] == "static_hybrid_rrf"
    assert workflow.handoff_context["retrieval_trace"]["safety_flags"] == [
        "sensitive_field_context"
    ]
    retrieval_events = [
        event
        for event in service.list_events(workflow.workflow_id)
        if event.event_type.value == "retrieval.completed"
    ]
    assert retrieval_events[-1].metadata["safety_flags"] == ["sensitive_field_context"]

    completed = service.submit_review(
        workflow.review.review_id,
        ReviewDecision.APPROVE,
        decided_by="usr_workflow_test",
    )

    assert completed.status == WorkflowStatus.COMPLETED
    assert completed.output is not None
    assert completed.output.transformation is not None
    assert completed.explanation is not None
    assert completed.explanation.intended_use.startswith("Support data validation")


def test_clean_lab_workflow_builds_clinical_package_with_field_provenance() -> None:
    service = make_service()
    text = "date,patient_id,lab_name,value,unit\n2026-01-01,P001,HbA1c,7.4,%\n"

    workflow = service.start_workflow(
        instruction="Convert this lab row into a governed clinical package.",
        data=text,
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
        schema_id="lab_result_v1",
        require_human_review=False,
    )

    assert workflow.status == WorkflowStatus.COMPLETED
    package = workflow.clinical_package
    assert package is not None
    assert package.package_type == "ojtflow_clinical_package"
    assert package.schema_version == "clinical_package.v0"
    assert package.raw_input.detected_format == DataFormat.CSV
    assert package.clinical_bundle.resourceType == "Bundle"
    resource_types = {record.resource_type for record in package.clinical_bundle.resources}
    assert {
        "Patient",
        "Observation",
        "DiagnosticReport",
        "DocumentReference",
    }.issubset(resource_types)

    patient = _resource_by_type(package, "Patient")
    assert patient.resource["id"] == "P001"
    assert patient.resource["identifier"][0]["value"] == "P001"
    assert {
        "Patient.resourceType",
        "Patient.id",
        "Patient.identifier[0].value",
    }.issubset({item.target_path for item in patient.field_provenance})

    observation = _resource_by_type(package, "Observation")
    assert observation.resource_type == "Observation"
    assert observation.resource["subject"]["reference"] == "Patient/P001"
    assert observation.resource["code"]["text"] == "HbA1c"
    assert observation.resource["valueQuantity"]["value"] == 7.4
    assert observation.resource["valueQuantity"]["unit"] == "%"
    field_paths = {item.target_path for item in observation.field_provenance}
    assert {
        "Observation.resourceType",
        "Observation.id",
        "Observation.status",
        "Observation.subject.reference",
        "Observation.effectiveDateTime",
        "Observation.code.text",
        "Observation.valueQuantity.value",
        "Observation.valueQuantity.unit",
    }.issubset(field_paths)
    unit_provenance = next(
        item
        for item in observation.field_provenance
        if item.target_path == "Observation.valueQuantity.unit"
    )
    assert unit_provenance.location is not None
    assert unit_provenance.location.row == 2
    assert unit_provenance.location.field == "unit"
    report = _resource_by_type(package, "DiagnosticReport")
    assert report.resource["subject"]["reference"] == "Patient/P001"
    assert report.resource["result"] == [
        {"reference": f"Observation/{observation.resource_id}"}
    ]
    assert {
        "DiagnosticReport.resourceType",
        "DiagnosticReport.id",
        "DiagnosticReport.status",
        "DiagnosticReport.code.text",
        "DiagnosticReport.subject.reference",
        "DiagnosticReport.result",
        "DiagnosticReport.effectiveDateTime",
    }.issubset({item.target_path for item in report.field_provenance})
    document = _resource_by_type(package, "DocumentReference")
    assert document.resource["status"] == "current"
    assert document.resource["subject"]["reference"] == "Patient/P001"
    assert document.resource["content"][0]["attachment"]["url"] == workflow.input.dataset_ref
    assert {
        "DocumentReference.resourceType",
        "DocumentReference.id",
        "DocumentReference.status",
        "DocumentReference.type.text",
        "DocumentReference.content[0].attachment.url",
        "DocumentReference.subject.reference",
    }.issubset({item.target_path for item in document.field_provenance})
    assert all(record.field_provenance for record in package.clinical_bundle.resources)
    assert package.operation_outcome.resourceType == "OperationOutcome"
    assert any(issue.code == "possible_phi" for issue in package.operation_outcome.issue)
    assert len(package.terminology_candidates) == 1
    loinc = package.terminology_candidates[0]
    assert loinc.standard_system == "LOINC"
    assert loinc.code == "4548-4"
    assert loinc.requires_review is True
    assert len(package.unit_validations) == 1
    assert package.unit_validations[0].status == "valid"
    assert package.unit_validations[0].normalized_unit == "%"
    gate_types = {gate.gate_type for gate in package.semantic_normalization_gates}
    assert {"lab_name", "unit", "date", "patient_identifier"}.issubset(gate_types)
    assert all(gate.requires_review for gate in package.semantic_normalization_gates)
    assert all(gate.blocks_automatic_change for gate in package.semantic_normalization_gates)
    lab_gate = next(
        gate
        for gate in package.semantic_normalization_gates
        if gate.gate_type == "lab_name"
    )
    assert lab_gate.proposed_system == "LOINC"
    assert lab_gate.proposed_code == "4548-4"
    unit_gate = next(
        gate for gate in package.semantic_normalization_gates if gate.gate_type == "unit"
    )
    assert unit_gate.proposed_system == "UCUM"
    assert unit_gate.proposed_code == "%"
    assert package.output_refs == [workflow.output.transformation.output_ref]
    assert package.audit_event_refs == workflow.audit_event_refs
    assert package.handoff_context["terminology_candidate_count"] == 1
    assert package.handoff_context["unit_validation_count"] == 1
    assert package.handoff_context["semantic_normalization_gate_count"] == len(
        package.semantic_normalization_gates
    )
    assert set(package.handoff_context["semantic_normalization_gate_types"]) == gate_types
    assert package.handoff_context["fhir_compliance"] == "fhir_like_not_validated"
    assert package.handoff_context["fhir_profile_registry_version"] == (
        "fhir_like_resource_profiles.v0"
    )
    assert package.handoff_context["fhir_resource_profile_ids"]["Observation"] == (
        "ojtflow_fhir_like_observation_lab_v0"
    )
    assert "DiagnosticReport" in package.handoff_context["fhir_search_parameters_by_resource"]
    map_provenance = next(
        item for item in package.provenance if item.activity == "map"
    )
    assert set(map_provenance.metadata["semantic_normalization_gate_ids"]) == {
        gate.gate_id for gate in package.semantic_normalization_gates
    }
    assert "FHIR-like package has not been validated" in package.warnings[0]
    assert any("Semantic normalization candidates require human review" in warning for warning in package.warnings)


def test_clinical_package_export_builds_bundle_and_reloads_losslessly() -> None:
    service = make_service()
    text = "date,patient_id,lab_name,value,unit\n2026-01-01,P001,HbA1c,7.4,%\n"

    workflow = service.start_workflow(
        instruction="Convert this lab row into an exportable clinical package.",
        data=text,
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
        schema_id="lab_result_v1",
        require_human_review=False,
    )

    package_export = service.export_workflow_clinical_package(workflow.workflow_id)
    assert package_export.approved_for_export is True
    assert package_export.workflow_id == workflow.workflow_id
    assert package_export.package_hash
    assert package_export.fhir_like_bundle_hash
    assert package_export.fhir_like_bundle["resourceType"] == "Bundle"
    exported_resource_types = {
        entry["resource"]["resourceType"]
        for entry in package_export.fhir_like_bundle["entry"]
    }
    assert {
        "Patient",
        "Observation",
        "DiagnosticReport",
        "DocumentReference",
        "OperationOutcome",
        "Provenance",
    }.issubset(exported_resource_types)
    assert package_export.evidence_count == len(workflow.clinical_package.evidence)
    assert package_export.provenance_count == len(workflow.clinical_package.provenance)

    validation = service.validate_clinical_package_import(
        package_export.model_dump(mode="json")
    )
    assert validation.valid is True
    assert validation.package_hash == package_export.package_hash
    assert validation.fhir_like_bundle_hash == package_export.fhir_like_bundle_hash
    assert validation.clinical_package is not None
    assert validation.clinical_package.package_id == workflow.clinical_package.package_id
    assert validation.provenance_count == len(workflow.clinical_package.provenance)
    assert validation.evidence_count == len(workflow.clinical_package.evidence)

    tampered = package_export.model_dump(mode="json")
    tampered["clinical_package"]["workflow_id"] = "wf_tampered"
    tampered_validation = service.validate_clinical_package_import(tampered)
    assert tampered_validation.valid is False
    assert any(issue.code == "package_hash_mismatch" for issue in tampered_validation.issues)


def test_clinical_package_adds_rxnorm_and_snomed_candidates_for_extra_fields() -> None:
    service = make_service()
    text = (
        "date,patient_id,lab_name,value,unit,medication,diagnosis\n"
        "2026-01-01,P001,HbA1c,7.4,%,metformin,type 2 diabetes\n"
    )

    workflow = service.start_workflow(
        instruction="Create clinical terminology candidates for this lab row.",
        data=text,
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
        schema_id="lab_result_v1",
        require_human_review=False,
    )

    assert workflow.clinical_package is not None
    candidates = {
        (candidate.standard_system, candidate.source_field): candidate
        for candidate in workflow.clinical_package.terminology_candidates
    }
    rxnorm = candidates[("RxNorm", "medication")]
    assert rxnorm.code == "6809"
    assert rxnorm.metadata["normalization_policy"] == "review_required_no_auto_replacement"
    assert rxnorm.requires_review is True

    snomed = candidates[("SNOMED CT", "diagnosis")]
    assert snomed.code == "44054006"
    assert snomed.metadata["implementation_status"] == "placeholder_contract"
    assert "license" in snomed.metadata["license_note"].lower()
    assert snomed.requires_review is True
    gates = {
        gate.gate_type: gate
        for gate in workflow.clinical_package.semantic_normalization_gates
    }
    assert gates["medication"].proposed_system == "RxNorm"
    assert gates["medication"].candidate_id == rxnorm.candidate_id
    assert gates["diagnosis"].proposed_system == "SNOMED CT"
    assert gates["diagnosis"].candidate_id == snomed.candidate_id


def test_clinical_package_adds_procedure_normalization_gate_without_candidate() -> None:
    service = make_service()
    text = (
        "date,patient_id,lab_name,value,unit,procedure\n"
        "2026-01-01,P001,HbA1c,7.4,%,unmapped procedure text\n"
    )

    workflow = service.start_workflow(
        instruction="Create review gates for procedure normalization.",
        data=text,
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
        schema_id="lab_result_v1",
        require_human_review=False,
    )

    assert workflow.clinical_package is not None
    procedure_gate = next(
        gate
        for gate in workflow.clinical_package.semantic_normalization_gates
        if gate.gate_type == "procedure"
    )
    assert procedure_gate.source_field == "procedure"
    assert procedure_gate.target_resource_type == "Procedure"
    assert procedure_gate.target_path == "Procedure.code.coding"
    assert procedure_gate.candidate_id is None
    assert procedure_gate.metadata["candidate_status"] == "not_found"
    assert procedure_gate.requires_review is True


def test_review_gated_lab_workflow_clinical_package_carries_review_and_issues() -> None:
    service = make_service()
    text = (ROOT / "data/fixtures/structured/lab_results_messy.csv").read_text()

    workflow = service.start_workflow(
        instruction="Prepare this lab CSV for review.",
        data=text,
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
        schema_id="lab_result_v1",
        require_human_review=True,
    )

    assert workflow.status == WorkflowStatus.NEEDS_HUMAN_REVIEW
    package = workflow.clinical_package
    assert package is not None
    assert package.review is not None
    assert package.review["status"] == "pending"
    assert package.output_refs == []
    assert any(issue.code == "missing_unit" for issue in package.operation_outcome.issue)
    assert any(result.status == "missing" for result in package.unit_validations)
    assert any(candidate.standard_system == "LOINC" for candidate in package.terminology_candidates)
    assert any(record.review_required for record in package.clinical_bundle.resources)
    assert any(
        "missing_unit_requires_review" in record.warnings
        for record in package.clinical_bundle.resources
    )
    assert package.audit_event_refs == workflow.audit_event_refs


def test_validate_data_rejects_missing_requested_schema() -> None:
    service = make_service()

    with pytest.raises(NotFoundError) as exc_info:
        service.validate_data(
            data="date,patient_id,lab_name,value,unit\n2026-01-01,P001,HbA1c,7.1,%\n",
            declared_format=DataFormat.CSV,
            schema_id="missing_lab_schema",
        )

    assert exc_info.value.details["schema_id"] == "missing_lab_schema"


def test_workflow_fails_before_retrieval_when_requested_schema_is_missing() -> None:
    service = make_service()
    text = (ROOT / "data/fixtures/structured/lab_results_messy.csv").read_text()

    workflow = service.start_workflow(
        instruction="Clean this CSV and validate it with a strict schema.",
        data=text,
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
        schema_id="missing_lab_schema",
        require_human_review=True,
    )

    assert workflow.status == WorkflowStatus.FAILED
    assert workflow.failure is not None
    assert workflow.failure.code == "not_found"
    assert workflow.failure.details["schema_id"] == "missing_lab_schema"
    assert workflow.validation_report is None
    assert workflow.output is None
    assert not any(step.name == "retrieval" for step in workflow.steps)
    assert any(
        event.event_type.value == "workflow.failed"
        for event in service.list_events(workflow.workflow_id)
    )


def test_workflow_output_read_rejects_corrupted_artifact_content() -> None:
    service = make_service()
    text = (ROOT / "data/fixtures/structured/lab_results_messy.csv").read_text()

    workflow = service.start_workflow(
        instruction="Clean this CSV, convert it to JSON, and explain anomalies.",
        data=text,
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
        schema_id="lab_result_v1",
        require_human_review=True,
    )
    completed = service.submit_review(
        workflow.review.review_id,
        ReviewDecision.APPROVE,
        decided_by="usr_workflow_test",
    )
    output_ref = completed.output.transformation.output_ref
    assert output_ref is not None
    assert service.get_workflow_output(completed.workflow_id).output_hash == (
        completed.output.transformation.output_hash
    )

    service.datasets._text_by_ref[output_ref] = "tampered output"

    with pytest.raises(ArtifactIntegrityError, match="integrity verification"):
        service.get_workflow_output(completed.workflow_id)


def test_review_resume_rejects_corrupted_input_artifact_content() -> None:
    service = make_service()
    text = (ROOT / "data/fixtures/structured/lab_results_messy.csv").read_text()

    workflow = service.start_workflow(
        instruction="Clean this CSV, convert it to JSON, and explain anomalies.",
        data=text,
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
        schema_id="lab_result_v1",
        require_human_review=True,
    )
    input_ref = workflow.input.dataset_ref

    service.datasets._text_by_ref[input_ref] = text.replace("P001", "P999")

    with pytest.raises(ArtifactIntegrityError, match="input artifact"):
        service.submit_review(
            workflow.review.review_id,
            ReviewDecision.APPROVE,
            decided_by="usr_workflow_test",
        )

    failed = service.get_workflow(workflow.workflow_id)
    assert failed.status == WorkflowStatus.FAILED
    assert "ArtifactIntegrityError" in failed.risk_flags
    assert failed.output is None
    assert any(event.event_type.value == "workflow.failed" for event in service.list_events(workflow.workflow_id))


def test_review_approval_records_structured_failure_when_resume_tool_fails() -> None:
    service = make_service()
    text = (ROOT / "data/fixtures/structured/lab_results_messy.csv").read_text()

    workflow = service.start_workflow(
        instruction="Clean this CSV.",
        data=text,
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
    )
    bad_json = "{not valid json"
    service.datasets._text_by_ref[workflow.input.dataset_ref] = bad_json
    workflow.input.input_hash = sha256_text(bad_json)
    workflow.input.declared_format = DataFormat.JSON
    service.workflows.save(workflow)

    failed = service.submit_review(
        workflow.review.review_id,
        ReviewDecision.APPROVE,
        decided_by="usr_workflow_test",
    )

    assert failed.status == WorkflowStatus.FAILED
    assert failed.failure is not None
    assert failed.failure.code == "tool_execution_error"
    assert failed.failure.error_type == "ToolExecutionError"
    assert "Invalid JSON" in failed.failure.message
    assert failed.review.status.value == "approved"
    assert failed.output is None
    assert any(event.event_type.value == "workflow.failed" for event in service.list_events(workflow.workflow_id))


def test_failed_workflow_records_structured_failure_contract() -> None:
    service = make_service()

    workflow = service.start_workflow(
        instruction="Parse this JSON.",
        data="{not valid json",
        declared_format=DataFormat.JSON,
        target_format=DataFormat.JSON,
        require_human_review=True,
    )

    assert workflow.status == WorkflowStatus.FAILED
    assert workflow.failure is not None
    assert workflow.failure.code == "tool_execution_error"
    assert workflow.failure.error_type == "ToolExecutionError"
    assert "Invalid JSON" in workflow.failure.message
    assert "ToolExecutionError" in workflow.risk_flags
    assert workflow.output is None
    assert any(event.event_type.value == "workflow.failed" for event in service.list_events(workflow.workflow_id))


def test_review_rejection_cancels_workflow() -> None:
    service = make_service()
    text = (ROOT / "data/fixtures/structured/lab_results_messy.csv").read_text()

    workflow = service.start_workflow(
        instruction="Clean this CSV.",
        data=text,
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
    )

    cancelled = service.submit_review(
        workflow.review.review_id,
        ReviewDecision.REJECT,
        decided_by="usr_workflow_test",
    )
    assert cancelled.status == WorkflowStatus.CANCELLED


def test_review_decision_cannot_be_applied_twice() -> None:
    service = make_service()
    text = (ROOT / "data/fixtures/structured/lab_results_messy.csv").read_text()

    workflow = service.start_workflow(
        instruction="Clean this CSV.",
        data=text,
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
    )

    completed = service.submit_review(
        workflow.review.review_id,
        ReviewDecision.APPROVE,
        decided_by="usr_workflow_test",
    )
    output_ref = completed.output.transformation.output_ref

    with pytest.raises(PolicyBlockedError, match="already decided"):
        service.submit_review(
            workflow.review.review_id,
            ReviewDecision.REJECT,
            decided_by="usr_workflow_test",
        )

    unchanged = service.get_workflow(completed.workflow_id)
    assert unchanged.status == WorkflowStatus.COMPLETED
    assert unchanged.review.decision == ReviewDecision.APPROVE
    assert unchanged.output.transformation.output_ref == output_ref
    review_events = [
        event for event in service.list_events(completed.workflow_id)
        if event.event_type.value == "review.decided"
    ]
    assert len(review_events) == 1


def test_clarify_keeps_review_pending_and_allows_later_approval() -> None:
    service = make_service()
    text = (ROOT / "data/fixtures/structured/lab_results_messy.csv").read_text()

    workflow = service.start_workflow(
        instruction="Clean this CSV.",
        data=text,
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
    )

    clarified = service.submit_review(
        workflow.review.review_id,
        ReviewDecision.CLARIFY,
        decided_by="usr_workflow_test",
        payload={"question": "Confirm unit normalization before approving."},
    )

    assert clarified.status == WorkflowStatus.NEEDS_HUMAN_REVIEW
    assert clarified.review.status.value == "pending"
    assert clarified.review.decision is None
    assert clarified.review.clarification_requests[0]["requested_by"] == "usr_workflow_test"
    assert clarified.output is None
    human_review_steps = [step for step in clarified.steps if step.name == "human_review"]
    assert human_review_steps[-1].status == "pending"

    completed = service.submit_review(
        workflow.review.review_id,
        ReviewDecision.APPROVE,
        decided_by="usr_workflow_test",
    )

    assert completed.status == WorkflowStatus.COMPLETED
    assert completed.review.status.value == "approved"
    assert completed.review.decision == ReviewDecision.APPROVE
    assert completed.review.clarification_requests
    assert completed.output is not None


def test_review_decision_must_be_allowed_by_review_contract() -> None:
    service = make_service()
    text = (ROOT / "data/fixtures/structured/lab_results_messy.csv").read_text()

    workflow = service.start_workflow(
        instruction="Clean this CSV.",
        data=text,
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
    )
    workflow.review.allowed_decisions = [ReviewDecision.REJECT]
    service.workflows.save(workflow)

    with pytest.raises(PolicyBlockedError, match="not allowed"):
        service.submit_review(
            workflow.review.review_id,
            ReviewDecision.APPROVE,
            decided_by="usr_workflow_test",
        )

    unchanged = service.get_workflow(workflow.workflow_id)
    assert unchanged.status == WorkflowStatus.NEEDS_HUMAN_REVIEW
    assert unchanged.review.status.value == "pending"
    assert unchanged.output is None


def test_approve_with_edits_requires_explicit_action_payload() -> None:
    service = make_service()
    text = (ROOT / "data/fixtures/structured/lab_results_messy.csv").read_text()

    workflow = service.start_workflow(
        instruction="Clean this CSV.",
        data=text,
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
    )

    with pytest.raises(PolicyBlockedError, match="explicit edited transformation actions"):
        service.submit_review(
            workflow.review.review_id,
            ReviewDecision.APPROVE_WITH_EDITS,
            decided_by="usr_workflow_test",
            payload={},
        )

    unchanged = service.get_workflow(workflow.workflow_id)
    assert unchanged.status == WorkflowStatus.NEEDS_HUMAN_REVIEW
    assert unchanged.review.status.value == "pending"
    assert unchanged.review.decision is None
    assert unchanged.output is None


def test_approve_with_edits_applies_explicit_supported_actions() -> None:
    service = make_service()
    text = (ROOT / "data/fixtures/structured/lab_results_messy.csv").read_text()

    workflow = service.start_workflow(
        instruction="Clean this CSV.",
        data=text,
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
    )
    edited_action = {
        "action": "mask_sensitive_field_for_explanation",
        "field": "patient_id",
        "reason": "Keep patient identifiers masked in generated output.",
        "requires_review": True,
    }

    completed = service.submit_review(
        workflow.review.review_id,
        ReviewDecision.APPROVE_WITH_EDITS,
        decided_by="usr_workflow_test",
        payload={"actions": [edited_action]},
    )

    assert completed.status == WorkflowStatus.COMPLETED
    assert completed.review.status.value == "approved_with_edits"
    assert completed.review.decision == ReviewDecision.APPROVE_WITH_EDITS
    assert completed.review.decision_payload == {"actions": [edited_action]}
    assert [action.action for action in completed.transformation_plan.actions] == [
        "mask_sensitive_field_for_explanation"
    ]
    assert completed.output.transformation.diff_summary["actions_applied"] == [
        "mask_sensitive_field_for_explanation"
    ]
    assert "[MASKED]" in service.get_workflow_output(completed.workflow_id).content


def test_approve_with_edits_rejects_unsupported_actions() -> None:
    service = make_service()
    text = (ROOT / "data/fixtures/structured/lab_results_messy.csv").read_text()

    workflow = service.start_workflow(
        instruction="Clean this CSV.",
        data=text,
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
    )

    with pytest.raises(PolicyBlockedError, match="not supported"):
        service.submit_review(
            workflow.review.review_id,
            ReviewDecision.APPROVE_WITH_EDITS,
            decided_by="usr_workflow_test",
            payload={
                "actions": [
                    {
                        "action": "invent_new_lab_value",
                        "reason": "Unsupported semantic edit.",
                    }
                ]
            },
        )

    unchanged = service.get_workflow(workflow.workflow_id)
    assert unchanged.status == WorkflowStatus.NEEDS_HUMAN_REVIEW
    assert unchanged.review.status.value == "pending"
    assert unchanged.output is None


def test_review_decision_requires_explicit_reviewer_identity() -> None:
    service = make_service()
    text = (ROOT / "data/fixtures/structured/lab_results_messy.csv").read_text()

    workflow = service.start_workflow(
        instruction="Clean this CSV.",
        data=text,
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
    )

    with pytest.raises(PolicyBlockedError):
        service.submit_review(
            workflow.review.review_id,
            ReviewDecision.APPROVE,
            decided_by=" ",
        )


def test_workflow_service_scopes_queries_reviews_events_and_output_by_owner() -> None:
    service = make_service()
    text = (ROOT / "data/fixtures/structured/lab_results_messy.csv").read_text()

    workflow_a = service.start_workflow(
        instruction="Clean owner A CSV.",
        data=text,
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
        owner_user_id="usr_owner_a",
    )
    workflow_b = service.start_workflow(
        instruction="Clean owner B CSV.",
        data=text,
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
        owner_user_id="usr_owner_b",
    )

    assert workflow_a.owner_user_id == "usr_owner_a"
    assert workflow_b.owner_user_id == "usr_owner_b"
    assert [item.workflow_id for item in service.list_workflows(owner_user_id="usr_owner_a")] == [
        workflow_a.workflow_id
    ]
    assert service.list_workflow_summaries(owner_user_id="usr_owner_b").items[0].workflow_id == workflow_b.workflow_id
    assert service.workflow_stats(owner_user_id="usr_owner_a").total == 1
    assert service.workflow_stats(owner_user_id="usr_owner_b").total == 1
    assert service.list_reviews(owner_user_id="usr_owner_a")[0].review.review_id == workflow_a.review.review_id
    assert service.list_review_summaries(owner_user_id="usr_owner_b").items[0].review_id == workflow_b.review.review_id

    with pytest.raises(NotFoundError):
        service.get_workflow(workflow_a.workflow_id, owner_user_id="usr_owner_b")
    with pytest.raises(NotFoundError):
        service.list_events(workflow_a.workflow_id, owner_user_id="usr_owner_b")
    with pytest.raises(NotFoundError):
        service.submit_review(
            workflow_a.review.review_id,
            ReviewDecision.APPROVE,
            decided_by="usr_owner_b",
            owner_user_id="usr_owner_b",
        )

    completed = service.submit_review(
        workflow_a.review.review_id,
        ReviewDecision.APPROVE,
        decided_by="usr_owner_a",
        owner_user_id="usr_owner_a",
    )

    assert completed.status == WorkflowStatus.COMPLETED
    assert service.get_workflow_output(
        completed.workflow_id,
        owner_user_id="usr_owner_a",
    ).workflow_id == completed.workflow_id
    with pytest.raises(NotFoundError):
        service.get_workflow_output(
            completed.workflow_id,
            owner_user_id="usr_owner_b",
        )


def test_list_reviews_does_not_miss_pending_reviews_behind_non_review_workflows() -> None:
    service = make_service()
    text = (ROOT / "data/fixtures/structured/lab_results_messy.csv").read_text()
    owner_user_id = "usr_review_queue_owner"

    review_a = service.start_workflow(
        instruction="Review gated batch A.",
        data=text,
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
        require_human_review=True,
        owner_user_id=owner_user_id,
    )
    review_b = service.start_workflow(
        instruction="Review gated batch B.",
        data=text,
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
        require_human_review=True,
        owner_user_id=owner_user_id,
    )

    for index in range(6):
        service.start_workflow(
            instruction=f"Auto-complete non-review batch {index}.",
            data=text,
            declared_format=DataFormat.CSV,
            target_format=DataFormat.JSON,
            require_human_review=False,
            owner_user_id=owner_user_id,
        )

    pending = service.list_reviews(
        status="pending",
        limit=2,
        owner_user_id=owner_user_id,
    )
    all_reviews = service.list_reviews(
        status="all",
        limit=2,
        owner_user_id=owner_user_id,
    )

    assert {workflow.workflow_id for workflow in pending} == {
        review_a.workflow_id,
        review_b.workflow_id,
    }
    assert {workflow.workflow_id for workflow in all_reviews} == {
        review_a.workflow_id,
        review_b.workflow_id,
    }


def test_fhir_like_workflow_adds_profile_evidence_and_handoff_context() -> None:
    service = make_service()
    observation = {
        "resourceType": "Observation",
        "status": "final",
        "code": {"text": "HbA1c"},
        "subject": {"reference": "Patient/P001"},
        "effectiveDateTime": "2026-01-01",
        "valueQuantity": {"value": 7.4, "unit": "%", "system": "http://unitsofmeasure.org"},
    }

    workflow = service.start_workflow(
        instruction="Profile this FHIR-like Observation and explain its evidence.",
        data=json.dumps(observation),
        declared_format=DataFormat.JSON,
        target_format=DataFormat.JSON,
        schema_id=None,
        require_human_review=True,
    )

    assert workflow.status == WorkflowStatus.COMPLETED
    assert workflow.handoff_context["fhir_profile"]["is_fhir_like"] is True
    assert workflow.handoff_context["fhir_profile"]["resource_type"] == "Observation"
    assert workflow.handoff_context["fhir_profile"]["profile_registry_version"] == (
        "fhir_like_resource_profiles.v0"
    )
    assert workflow.handoff_context["fhir_profile"]["search_parameters"]["Observation"]
    assert workflow.handoff_context["fhir_handoff"]["graphner_ready"] is True
    assert workflow.handoff_context["fhir_handoff"]["profiled_resource_types"] == [
        "Observation"
    ]
    assert any(step.name == "fhir_profile" for step in workflow.steps)
    source_ids = {evidence.source_id for evidence in workflow.retrieved_context}
    assert "fhir_like:Observation" in source_ids
    assert "standard:fhir_observation_r4" in source_ids
    assert workflow.clinical_package is not None
    assert workflow.clinical_package.clinical_bundle.resources[0].resource_type == "Observation"
    assert workflow.clinical_package.clinical_bundle.resources[0].resource["code"]["text"] == "HbA1c"
    assert workflow.clinical_package.clinical_bundle.resources[0].warnings == [
        "fhir_like_resource_preserved_without_full_hl7_validation"
    ]
