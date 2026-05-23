# OJTFlow API Contract v0

All public endpoints return the same envelope:

```json
{
  "data": {},
  "error": null
}
```

Default persistence uses Postgres plus local file-backed artifacts:

```text
OJT_STORAGE_BACKEND=postgres
OJT_DATABASE_URL=postgresql://ojtflow:ojtflow@localhost:5432/ojtflow
OJT_DATA_DIR=var
```

Schema migrations live in:

```text
sql/postgres/migrations/
```

Apply migrations manually with:

```bash
PYTHONPATH=src /home/tcuong1000/.ostwin/.venv/bin/python -m ojtflow.infrastructure.storage.migrate
```

Errors use:

```json
{
  "data": null,
  "error": {
    "code": "request_validation_error",
    "message": "Request validation failed",
    "details": {},
    "workflow_id": null
  }
}
```

## Workflow

`POST /api/v1/workflows`

Request:

```json
{
  "instruction": "Clean this CSV, convert it to JSON, and explain anomalies.",
  "data": "date,patient_id,lab_name,value,unit\n2026-01-01,P001,HbA1c,7.4,%\n2026/01/02,P002,HbA1c,,\n",
  "input_format": "csv",
  "target_format": "json",
  "schema_id": "lab_result_v1",
  "require_human_review": true
}
```

Response data is a `WorkflowState`. Important fields:

- `workflow_id`
- `status`
- `steps`
- `input`
- `profile`
- `retrieved_context`
- `validation_report`
- `transformation_plan`
- `review`
- `output`
- `explanation`
- `handoff_context`
- `audit_event_refs`

`GET /api/v1/workflows/{workflow_id}` returns the current `WorkflowState`.

`GET /api/v1/workflows/{workflow_id}/events` returns append-only workflow events.

## Review

`POST /api/v1/review/{review_id}`

```json
{
  "decision": "approve",
  "decided_by": "demo_user",
  "payload": {}
}
```

Allowed decisions:

- `approve`
- `approve_with_edits`
- `reject`
- `clarify`
- `cancel`

## Direct Conversion

`POST /api/v1/convert`

```json
{
  "data": "a,b\n1,2\n",
  "input_format": "csv",
  "target_format": "json"
}
```

Response data includes:

- `detected_format`
- `output_format`
- `output`
- `metadata.output_hash`
- `metadata.diff_summary`
- `metadata.warnings`

## Direct Validation

`POST /api/v1/validate`

```json
{
  "data": "date,patient_id,lab_name,value,unit\n2026/01/02,P002,HbA1c,,\n",
  "input_format": "csv",
  "schema_id": "lab_result_v1"
}
```

Response data includes:

- `profile`
- `validation_report.valid`
- `validation_report.issues`
- `validation_report.requires_review`

## FHIR-Like Profile

`POST /api/v1/fhir/profile`

```json
{
  "data": "{\"resourceType\":\"Observation\",\"status\":\"final\"}"
}
```

This endpoint performs lightweight FHIR-like profiling only. It does not perform full HL7 FHIR validation.

Response data includes:

- `profile.is_fhir_like`
- `profile.resource_type`
- `profile.resource_counts`
- `profile.handoff_context`
- `evidence`

## OCR Evidence Stub

`POST /api/v1/ocr/evidence`

```json
{
  "fields": [
    {
      "page": 1,
      "name": "patient_id",
      "value": "P001",
      "bbox": [0, 0, 10, 10],
      "confidence": 0.72,
      "source_ref": "storage://doc/demo"
    }
  ]
}
```

Response data includes normalized OCR fields and `Evidence(source_type="ocr_box")`.
Fields with confidence below `0.8` require review.
