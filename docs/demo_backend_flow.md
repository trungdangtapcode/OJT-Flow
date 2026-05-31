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

Run migrations:

```bash
PYTHONPATH=src /home/tcuong1000/.ostwin/.venv/bin/python -m ojtflow.infrastructure.storage.migrate
```

Run API:

```bash
PYTHONPATH=src /home/tcuong1000/.ostwin/.venv/bin/python -m uvicorn ojtflow.interfaces.api.app:app --host 127.0.0.1 --port 8000
```

To force memory storage for temporary demos:

```bash
OJT_STORAGE_BACKEND=memory PYTHONPATH=src /home/tcuong1000/.ostwin/.venv/bin/python -m uvicorn ojtflow.interfaces.api.app:app --host 127.0.0.1 --port 8000
```

To use the SQLite fallback:

```bash
OJT_STORAGE_BACKEND=sqlite PYTHONPATH=src /home/tcuong1000/.ostwin/.venv/bin/python -m uvicorn ojtflow.interfaces.api.app:app --host 127.0.0.1 --port 8000
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

1. Workflow is created and persisted.
2. Input is stored by file reference and hash.
3. Parser detects CSV and profiles fields.
4. Static retrieval returns trusted lab evidence.
5. Validation flags PHI-like patient ID, date inconsistency, missing value, and missing unit.
6. Transformation plan is created.
7. Safety gate pauses the workflow for human review.
8. Review approval resumes the workflow even after service restart.
9. Deterministic conversion creates JSON output under `var/outputs/`.
10. Explanation includes supported claims and medical limitations.
11. Event timeline and workflow steps remain persisted.

## Review Approval

```json
{
  "decision": "approve",
  "decided_by": "demo_user"
}
```

## Demo Talking Points

- The LLM is not required for deterministic conversion.
- Review gates block semantic changes.
- Events are append-only audit trace.
- Steps are UI/progress state.
- Postgres/local files make the backend restart-safe; SQLite remains a local fallback
  with the same workflow and auth repository contracts.
- FHIR and OCR are hook points, not overclaimed medical automation.
