# ClinicalPackage v0

## Purpose

OJTFlow now emits a canonical `ClinicalPackage` inside workflow state when the
input can be represented as governed healthcare data. The package is an OJTFlow
envelope around FHIR-like resources plus validation, evidence, review,
provenance, audit references, output refs, and handoff context.

This is not full HL7 FHIR validation. The package explicitly marks its current
FHIR status as:

`fhir_like_not_validated`

## Workflow Field

`WorkflowState.clinical_package`

The field is optional so older workflow states remain loadable.

## Package Shape

The package includes:

- `raw_input`: dataset ref, input hash, declared format, detected format
- `clinical_bundle`: FHIR-like `Bundle` with generated/preserved resources
- `operation_outcome`: OperationOutcome-like issues from validation
- `evidence`: retrieval/FHIR/profile evidence linked to the workflow
- `terminology_candidates`: review-gated LOINC/RxNorm/etc. candidates
- `unit_validations`: UCUM-like unit validation results
- `provenance`: internal Provenance-like activity records
- `review`: human review state when present
- `audit_event_refs`: workflow audit event IDs
- `output_refs`: generated output artifact refs when completed
- `handoff_context`: Graph-NER/RAG/export hints
- `warnings`: package limitations and review warnings

## V0 Mapping

`lab_result_v1` records map to FHIR-like `Observation` resources:

- `patient_id` -> `Observation.subject.reference`
- `date` -> `Observation.effectiveDateTime`
- `lab_name` -> `Observation.code.text`
- `value` -> `Observation.valueQuantity.value`
- `unit` -> `Observation.valueQuantity.unit`

Every mapped field receives `ClinicalFieldProvenance` with target path, source
field/value, source row/column, source ref, derivation status, and explanatory
note. Missing or non-numeric clinical fields do not get silently normalized;
they set review warnings.

FHIR-like JSON submitted directly is preserved as package resources with a
warning that full HL7 validation has not run.

## Terminology And Units

For `lab_result_v1`, the package now emits review-gated LOINC candidates from:

`knowledge/terminologies/medical_concepts.json`

Unit validation uses the seed UCUM registry:

`knowledge/terminologies/ucum_units.json`

This is not a full terminology server. Candidates and unit results are scaffold
contracts for review and downstream evidence retrieval. Semantic replacement is
not automatic.

## OperationOutcome-Like Issues

Validation issues are copied into:

`clinical_package.operation_outcome.issue[]`

Each issue carries severity, code, diagnostics, expression, original issue ID,
source location, and review requirement.

## Verification

Run:

```bash
python -m pytest tests/test_workflow_service.py::test_clean_lab_workflow_builds_clinical_package_with_field_provenance tests/test_workflow_service.py::test_review_gated_lab_workflow_clinical_package_carries_review_and_issues tests/test_workflow_service.py::test_fhir_like_workflow_adds_profile_evidence_and_handoff_context -q
```
