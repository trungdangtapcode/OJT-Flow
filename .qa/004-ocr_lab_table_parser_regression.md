# QA Request: OCR Lab Table Parser Regression

Please add regression coverage for scanned lab-result OCR workflows.

Scope:

- Do not mock the parser result.
- Use OCR/extracted plain text shaped like the live smoke PDF output:

```text
RIVER CITY HOSPITAL
DIABETES FOLLOW-UP VISIT SUMMARY
PATIENT MAYA TRAN
DOB 1978-04-12 MRN MRN-004219
VISIT DATE 2026-06-11
LAB RESULTS
TEST VALUE UNIT FLAG
HBA1C 7.4 % HIGH
GLUCOSE 182 MG/DL HIGH
CREATININE 0.9 MG/DL NORMAL
LDL 138 MG/DL HIGH
MEDICATIONS
METFORMIN 1000 MG BID
```

Expected:

- `parse_data(..., DataFormat.MARKDOWN)` returns four structured records.
- Each record has `date`, `patient_id`, `lab_name`, `value`, and `unit`.
- The parser stops at `MEDICATIONS` and does not create a `METFORMIN` lab row.
- `profile_data` includes the required `lab_result_v1` fields.
- `validate_against_schema` does not emit `missing_required_field`,
  `missing_value`, or `missing_unit` for the four lab rows.
- It is acceptable for validation to warn that `patient_id` may contain
  sensitive data.

Also add a workflow-level regression if practical:

- Start workflow from a scanned/OCR text fixture that resembles the PDF output.
- Confirm the review gate shows proposed actions from actual lab rows, not from
  a single `_text` markdown fallback record.

