# Terminology Candidates v0

## Purpose

OJTFlow needs terminology scaffolding before it can safely normalize clinical
meaning. V0 now emits review-gated terminology and unit contracts inside
`ClinicalPackage`:

- `clinical_package.terminology_candidates`
- `clinical_package.unit_validations`
- `clinical_package.semantic_normalization_gates`

The app still preserves source text. It does not automatically replace lab
names with LOINC codes, source units with normalized UCUM codes, medication
text with RxNorm RxCUIs, or diagnosis/finding text with SNOMED CT concepts.

Semantic normalization gates make that policy machine-readable. Each gate links
the source value to the target FHIR-like path that would change meaning, such as
`Observation.code.coding`, `Observation.valueQuantity.code`,
`Patient.identifier[0].value`, `Condition.code.coding`,
`MedicationStatement.medicationCodeableConcept.coding`, or
`Procedure.code.coding`.

## LOINC Candidates

For `lab_result_v1`, `lab_name` is matched against:

`knowledge/terminologies/medical_concepts.json`

The output is `TerminologyCandidate` with:

- source field/value
- standard system
- candidate code/display
- confidence
- matched aliases
- source URI
- source location
- review status
- metadata such as preferred units

Example: `HbA1c` maps to LOINC candidate `4548-4`, but remains
`review_required`.

## RxNorm Medication Candidates

Medication-like fields are matched against the same data-driven concept
registry:

- `medication`
- `medication_name`
- `drug`
- `drug_name`
- `rx`

The output is still `TerminologyCandidate`. RxNorm candidates carry metadata
such as `identifier_type`, `clinical_domain`, and
`normalization_policy=review_required_no_auto_replacement`.

Example: `metformin` maps to RxNorm candidate RxCUI `6809`, but remains
`review_required`.

## SNOMED CT Placeholder Candidates

Diagnosis/finding/problem/procedure/allergy fields emit SNOMED CT placeholder
candidates when the configured seed registry has a match:

- `diagnosis`
- `condition`
- `finding`
- `problem`
- `problem_name`
- `procedure`
- `procedure_name`
- `allergy`
- `allergy_name`

SNOMED CT support is deliberately license-aware. Candidates carry
`implementation_status=placeholder_contract`, a license note, source URI, and
review-required status. Production deployments must verify SNOMED CT licensing
for the jurisdiction and use a real licensed terminology lookup before clinical
use or export.

## UCUM Unit Validation

Units are checked against:

`knowledge/terminologies/ucum_units.json`

The output is `UnitValidationResult` with:

- source unit
- normalized seed UCUM code
- status: `valid`, `missing`, `unknown`, or `not_preferred`
- confidence
- source location
- review requirement
- metadata

The registry is intentionally labeled as a seed list. Production validation
requires an official UCUM service or full UCUM library.

## Review Gate Behavior

For `lab_result_v1`, OJTFlow emits review gates for lab names, units, dates,
patient identifiers, diagnoses, medications, and procedures when those fields
are present. A gate can reference a terminology candidate, a unit validation
result, or a missing-candidate condition. Missing candidates are still useful:
they explicitly prevent unreviewed code assignment when the configured
terminology registry has no match.

The gate contract is intentionally separate from raw package export approval.
Source-preserving packages can move through downstream review/export flows, but
automatic semantic replacement remains blocked until a reviewer approves the
specific gate.

## Verification

Run:

```bash
python -m pytest tests/test_workflow_service.py::test_clean_lab_workflow_builds_clinical_package_with_field_provenance tests/test_workflow_service.py::test_clinical_package_adds_rxnorm_and_snomed_candidates_for_extra_fields tests/test_workflow_service.py::test_clinical_package_adds_procedure_normalization_gate_without_candidate tests/test_workflow_service.py::test_review_gated_lab_workflow_clinical_package_carries_review_and_issues -q
```
