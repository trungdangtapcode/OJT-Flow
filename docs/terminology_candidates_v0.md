# Terminology Candidates v0

## Purpose

OJTFlow needs terminology scaffolding before it can safely normalize clinical
meaning. V0 now emits review-gated terminology and unit contracts inside
`ClinicalPackage`:

- `clinical_package.terminology_candidates`
- `clinical_package.unit_validations`

The app still preserves source text. It does not automatically replace lab
names with LOINC codes or source units with normalized UCUM codes.

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

## Verification

Run:

```bash
python -m pytest tests/test_workflow_service.py::test_clean_lab_workflow_builds_clinical_package_with_field_provenance tests/test_workflow_service.py::test_review_gated_lab_workflow_clinical_package_carries_review_and_issues -q
```
