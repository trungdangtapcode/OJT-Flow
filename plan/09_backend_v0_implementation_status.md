# Backend v0 Implementation Status

This file updates the plan after the backend backbone solidification pass.

## Implemented

- FastAPI backend remains the public API layer.
- Pydantic contracts remain the source of truth.
- Postgres-backed persistence exists for workflows, events, and dataset metadata.
- Versioned SQL migrations exist under `sql/postgres/migrations/`.
- Docker Compose includes Postgres and API services.
- SQLite-backed persistence remains available as a local fallback.
- Local file-backed storage exists for raw inputs and generated outputs.
- Runtime config exists:
  - `OJT_STORAGE_BACKEND=postgres`
  - `OJT_DATABASE_URL=postgresql://ojtflow:ojtflow@localhost:5432/ojtflow`
  - `OJT_DATA_DIR=var`
- In-memory storage remains available for tests.
- Workflow state includes explicit `steps` separate from append-only audit events.
- Workflow state includes `handoff_context` for future Graph-NER/RAG wiring.
- Workflow failure handling persists failed state and emits failure events.
- API responses use a standard `{data, error}` envelope.
- API errors use `error.code`, `error.message`, `error.details`, and optional `workflow_id`.
- Parser/converter/validation are still deterministic and model-free.
- CSV parse reports now include missing/extra-cell warnings.
- Validation includes missing required fields, type mismatch, malformed rows, date issues, missing unit, PHI-like fields, and prompt-injection patterns.
- Conversion output includes metadata, output hash, diff summary, warnings, and actions applied.
- FHIR-like profile endpoint exists at `POST /api/v1/fhir/profile`.
- OCR evidence endpoint exists at `POST /api/v1/ocr/evidence`.
- Tool registry metadata exists before MCP wrapping.
- API contract docs exist in `docs/api_contract_v0.md`.
- Demo flow docs exist in `docs/demo_backend_flow.md`.
- Release checklist exists in `RELEASE_CANDIDATE.md`.

## Still Not Implemented

- Full HL7 FHIR validation.
- Real OCR engine.
- Real Graph-NER implementation.
- Real hybrid/vector RAG.
- MCP server wrappers.
- Object-store production adapters.
- Dedicated review UI.
- Model gateway or LLM reasoning layer.
- Release tag, because the repository is not initialized as a git repo.

## Verification

Latest verification command:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/tcuong1000/.ostwin/.venv/bin/python -m pytest
```

Latest result:

```text
7 passed
```

## Next Recommended Build

The next build should be the **real schema registry + retrieval baseline**:

1. Replace static evidence search with a small file-backed schema/document index.
2. Add lexical search over `knowledge/`.
3. Return retrieval runs with source IDs, scores, and warnings.
4. Keep the output as `Evidence[]` so the current workflow and explanation contracts do not change.

This should come before Graph-NER, MCP, or UI because those modules need trusted schema/context retrieval to be useful.
