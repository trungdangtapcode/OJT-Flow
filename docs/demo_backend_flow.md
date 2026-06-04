# Demo Backend Flow

Use this exact flow for the backend v0 demo.

## Start Full Docker Stack

```bash
docker compose up --build
```

Use `docker-compose up --build` if your machine has Docker Compose v1.

Default backend storage:

- Postgres: `postgresql://ojtflow:ojtflow@localhost:5432/ojtflow`
- Redis session cache for Postgres deployments: `redis://localhost:6379/0`
- input files: `var/datasets/`
- generated outputs: `var/outputs/`

This starts the API on `http://127.0.0.1:8000`.

## Start Local API Against Docker Postgres

Start Postgres:

```bash
docker compose up -d postgres
```

Use `docker-compose up -d postgres` if your machine has Docker Compose v1.

Migrations run automatically when the API constructs Postgres repositories. You
can also run them explicitly before the API for a release/demo readiness check:

```bash
PYTHONPATH=src python -m ojtflow.infrastructure.storage.migrate
```

Run API:

```bash
PYTHONPATH=src python -m uvicorn ojtflow.interfaces.api.app:app --host 127.0.0.1 --port 8000
```

To force memory storage for temporary demos:

```bash
OJT_STORAGE_BACKEND=memory PYTHONPATH=src python -m uvicorn ojtflow.interfaces.api.app:app --host 127.0.0.1 --port 8000
```

To use the SQLite fallback:

```bash
OJT_STORAGE_BACKEND=sqlite PYTHONPATH=src python -m uvicorn ojtflow.interfaces.api.app:app --host 127.0.0.1 --port 8000
```

## Scenario

Fixture:

```text
data/fixtures/structured/lab_results_messy.csv
```

Request:

```json
{
  "instruction": "Clean this CSV, convert it to JSON, and explain anomalies.",
  "input_format": "csv",
  "target_format": "json",
  "schema_id": "lab_result_v1",
  "require_human_review": true
}
```

Expected behavior:

1. Workflow is created with `owner_user_id` from the authenticated session and persisted.
2. Input is stored by file reference and hash.
3. Parser detects CSV and profiles fields.
4. The requested schema profile is loaded from the `GET /api/v1/schemas`
   inventory. A missing named profile fails the workflow with a structured
   `not_found` error before retrieval or validation. Use `schema_id: null` only
   for explicit no-schema runs.
5. Retrieval returns trusted lab evidence.
   In Postgres mode, retrieval uses seeded healthcare knowledge chunks with
   full-text search, deterministic vector scoring, fusion, and reranking.
6. Validation flags PHI-like patient ID, date inconsistency, missing value, and missing unit.
7. Transformation plan is created.
8. Safety gate pauses the workflow for human review.
9. Review approval resumes the workflow even after service restart.
10. Deterministic conversion creates JSON output under `var/outputs/`.
11. `GET /api/v1/workflows/{workflow_id}/output` returns the generated
    content, hash, byte size, warnings, and conversion metadata for UI preview
    and download.
12. Explanation includes supported claims and medical limitations.
13. Event timeline and workflow steps remain persisted.

## Review Approval

```json
{
  "decision": "approve"
}
```

Reviewer identity is taken from the authenticated session and persisted into
the review state plus the `review.decided` audit event.

Review lookup and approval are scoped to the workflow owner. If another
authenticated user guesses the `review_id`, the API returns `not_found` and does
not disclose the workflow.

## Demo Talking Points

- The LLM is not required for deterministic conversion.
- Review gates block semantic changes.
- Workflow queues, reviews, stats, events, and output artifacts are scoped to
  the authenticated user.
- Events are append-only audit trace.
- Steps are UI/progress state.
- Postgres/local files make the backend restart-safe; SQLite remains a local fallback
  with the same workflow and auth repository contracts.
- FHIR and OCR are hook points, not overclaimed medical automation.
- FHIR-like JSON workflow inputs are profiled inside the main workflow path and
  emit `handoff_context.fhir_profile` plus `handoff_context.fhir_handoff` for
  later Graph-NER/RAG integration.
- Retrieval evidence is traceable through `retrieved_context` and
  `handoff_context.retrieval_trace`.
