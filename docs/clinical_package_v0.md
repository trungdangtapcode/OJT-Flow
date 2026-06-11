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

`lab_result_v1` records map to a small FHIR-like package:

- `Patient`: one resource per distinct `patient_id`
- `Observation`: one atomic lab result per source row
- `DiagnosticReport`: one grouped lab report per patient
- `DocumentReference`: one pointer to the governed source dataset artifact

- `patient_id` -> `Observation.subject.reference`
- `date` -> `Observation.effectiveDateTime`
- `lab_name` -> `Observation.code.text`
- `value` -> `Observation.valueQuantity.value`
- `unit` -> `Observation.valueQuantity.unit`

Generated resource fields receive `ClinicalFieldProvenance` with target path,
source field/value when available, source row/column/source ref, derivation
status, and explanatory note. Source-backed fields use `source`, generated IDs
and cross-resource references use `derived`, fixed FHIR-like constants use
`defaulted`, and missing sensitive identity links use `review_required`.
Missing or non-numeric clinical fields do not get silently normalized; they set
review warnings.

FHIR-like JSON submitted directly is preserved as package resources with a
warning that full HL7 validation has not run.

## FHIR-Like Profile Registry

Supported resource families are declared in:

`knowledge/fhir/resource_profiles.json`

The registry defines the lightweight OJTFlow profile ID, FHIR release, source
URL, required fields, required-any groups, search parameter hints, and
governance notes for:

- `Patient`
- `Observation`
- `DiagnosticReport`
- `DocumentReference`

Workflow clinical packages copy registry metadata into
`clinical_package.handoff_context` as `fhir_profile_registry_version`,
`fhir_resource_profile_ids`, `fhir_profile_sources`, and
`fhir_search_parameters_by_resource`. This gives retrieval, Graph-NER, export,
and reviewer UI code the same search hints without hardcoding them in React or
tool code.

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

## Export And Reload

Completed workflows can export their clinical package through:

`GET /api/v1/workflows/{workflow_id}/clinical-package/export`

The response data is an `ojtflow_clinical_package_export` envelope containing:

- `clinical_package`: the canonical OJTFlow package with evidence, review,
  audit refs, output refs, terminology candidates, units, and provenance
- `fhir_like_bundle`: a cleaner FHIR-like `Bundle` projection for downstream
  interoperability handoff
- `package_hash`: SHA-256 hash of canonical package JSON
- `fhir_like_bundle_hash`: SHA-256 hash of canonical Bundle JSON
- `approved_for_export`: whether the package passed the review/export rule
- counts for resources, evidence, provenance, and OperationOutcome issues

By default, export requires a completed workflow and an export-approved package.
Packages with pending review, rejected review, or resources that still require
review are blocked unless the caller explicitly disables approval enforcement
for inspection.

Reload validation is available through:

`POST /api/v1/interoperability/clinical-package/validate-import`

It rehydrates the package, validates required shape, verifies package and Bundle
hashes when present, checks that Bundle entries include all package resources,
and returns the typed package without writing to storage. This gives downstream
ETL or interoperability code a deterministic way to prove that an exported
package can be loaded without dropping evidence or provenance.

## Workflow Detail UI

Workflow Detail includes a `Clinical package` tab for operators and reviewers.
It separates:

- terminology candidates by source text, candidate code, confidence, source
  terminology, and reviewer state
- unit validation by source unit, normalized unit, standard system, confidence,
  and review requirement
- package summary, resource counts, OperationOutcome-like issues, and package
  warnings
- raw source fields and values mapped to generated FHIR-like resource fields
  with derivation state, evidence IDs, notes, and generated resource JSON

The tab repeats the v0 boundary clearly: output is FHIR-like and must not be
treated as HL7 FHIR compliant until a real target validator accepts it.

## Verification

Run:

```bash
python -m pytest tests/test_workflow_service.py::test_clean_lab_workflow_builds_clinical_package_with_field_provenance tests/test_workflow_service.py::test_clinical_package_export_builds_bundle_and_reloads_losslessly tests/test_workflow_service.py::test_review_gated_lab_workflow_clinical_package_carries_review_and_issues tests/test_workflow_service.py::test_fhir_like_workflow_adds_profile_evidence_and_handoff_context -q
npm --prefix frontend run build
```
