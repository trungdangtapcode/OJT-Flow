# OJTFlow API Contract v0

All public endpoints return the same envelope:

```json
{
  "data": {},
  "error": null
}
```

All `/api/v1` workflow/data endpoints require an authenticated backend session.
Browser clients use the HTTP-only session cookie set by the Google callback.
API clients may use:

```text
Authorization: Bearer <access_token>
```

The exceptions are `GET /api/v1/auth/google/url` and
`GET /api/v1/auth/google/callback`, which are used to obtain the token.

Default persistence uses Postgres plus local file-backed artifacts:

```text
OJT_STORAGE_BACKEND=postgres
OJT_DATABASE_URL=postgresql://ojtflow:ojtflow@localhost:5432/ojtflow
OJT_REDIS_URL=redis://localhost:6379/0
OJT_DATA_DIR=var
OJT_AUTH_COOKIE_NAME=ojtflow_session
OJT_AUTH_COOKIE_SAMESITE=lax
OJT_EMBEDDING_PROVIDER=deterministic
OJT_EMBEDDING_MODEL=deterministic-hash-v0
OJT_EMBEDDING_DIMENSIONS=64
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

`handoff_context.retrieval_trace` records retrieval strategy, query variants,
filters, candidate count, selected evidence IDs, and retrieval warnings.

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

## Google OAuth Auth

`GET /api/v1/auth/google/url`

Returns:

- `authorization_url`: Google OAuth URL for redirecting the user.
- `state`: nonce cached by the backend and verified during callback.

The frontend passes:

```text
redirect_uri=http://localhost:5173/auth/callback
```

Swagger/API-only testing can omit `redirect_uri`, which uses the backend
callback:

```text
http://localhost:8000/api/v1/auth/google/callback
```

`GET /api/v1/auth/google/callback?code=...&state=...`

Exchanges the Google authorization code, verifies the identity token with
Google's verifier, creates or updates the user, creates a backend session, sets
an HTTP-only session cookie for browser clients, and returns:

- `token_type`
- `access_token`
- `expires_at`
- `user`

`GET /api/v1/auth/me`

Requires either the session cookie or:

```text
Authorization: Bearer <access_token>
```

Returns the active user and session metadata.

`POST /api/v1/auth/logout`

Requires the same session cookie or bearer token, revokes the persisted session,
clears the cache entry when present, and expires the browser cookie.

Structured unauthorized response:

```json
{
  "data": null,
  "error": {
    "code": "unauthorized",
    "message": "Missing authenticated session.",
    "details": {},
    "workflow_id": null
  }
}
```

## Retrieval Search

`POST /api/v1/retrieval/search`

```json
{
  "query": "HbA1c lab CSV missing units FHIR Observation",
  "top_k": 5,
  "schema_id": "lab_result_v1",
  "fields": ["date", "patient_id", "lab_name", "value", "unit"],
  "clinical_domain": "laboratory",
  "trust_level": "approved"
}
```

Response data is a `RetrievalPackage`:

- `hits[].evidence`
- `hits[].score`
- `hits[].lexical_score`
- `hits[].vector_score`
- `hits[].rerank_score`
- `hits[].matched_terms`
- `evidence`
- `trace.strategy`
- `trace.query_variants`
- `trace.filters_applied`
- `trace.candidates_seen`
- `trace.warnings`
- `handoff_context`

`GET /api/v1/retrieval/sources` returns available trusted retrieval sources,
including source type, version, trust level, clinical domain, standard system,
and chunk count.
