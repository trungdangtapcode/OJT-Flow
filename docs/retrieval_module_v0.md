# Retrieval Module v0

OJTFlow retrieval v0 turns the old static evidence fixture into a replaceable,
healthcare-aware retrieval subsystem. It supports the workflow explanation and
review path; it does not generate clinical advice.

## Architecture

The application layer depends on a `RetrievalRepository` port. Workflow code
builds a `RetrievalQuery` from the user instruction, parsed field profile,
schema ID, and detected format, then stores returned evidence in
`WorkflowState.retrieved_context`.

Production Docker uses Postgres with:

- `ojtflow.knowledge_documents`
- `ojtflow.knowledge_chunks`
- generated `tsvector` search
- optional pgvector `vector(64)` and HNSW index when the extension is available
- JSON embeddings as a portable fallback

Memory and SQLite modes use the deterministic static retrieval repository so
tests and local demos do not require external services.

## Ranking

The retrieval pipeline is deterministic in v0:

1. Build query variants from instruction, fields, schema, format, and resource type.
2. Candidate chunks are filtered by trust level, clinical domain, standard system, or source type.
3. Lexical score uses token overlap and Postgres full-text search in Postgres mode.
4. Vector score uses a deterministic hash embedding provider unless disabled later.
5. Reciprocal Rank Fusion combines lexical and vector rankings.
6. Rerank boosts favor schema matches, field matches, approved sources, and relevant healthcare standards.

This is intentionally compatible with later HyDE, learned embeddings, GraphRAG,
RAPTOR, and terminology-service adapters without changing workflow contracts.

## Healthcare Sources

Seeded v0 sources include:

- OJTFlow lab schema and data dictionary
- human-review governance triggers
- CSV lab-to-JSON transformation pattern
- FHIR Observation R4 direction
- LOINC laboratory terminology direction
- UCUM unit terminology direction
- RxNorm medication terminology direction
- OMOP CDM analytics export direction

The implementation preserves original user data and records terminology evidence
without silently normalizing clinical concepts.

## API

Search:

```http
POST /api/v1/retrieval/search
```

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

List sources:

```http
GET /api/v1/retrieval/sources
```

Workflow output includes:

- `retrieved_context`
- `handoff_context.retrieval_trace`
- `handoff_context.retrieval_handoff`

## Configuration

```text
OJT_STORAGE_BACKEND=postgres
OJT_DATABASE_URL=postgresql://ojtflow:ojtflow@localhost:5432/ojtflow
OJT_EMBEDDING_PROVIDER=deterministic
OJT_EMBEDDING_MODEL=deterministic-hash-v0
OJT_EMBEDDING_DIMENSIONS=64
```

`OJT_EMBEDDING_PROVIDER=deterministic` is the only implemented provider in v0.
External ADC/model-backed embeddings should be added behind the provider
interface after retrieval quality tests exist.

## Verification

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/tcuong1000/.ostwin/.venv/bin/python -m pytest
cd frontend && npm run build
```

For Postgres:

```bash
docker compose up --build
```

The Docker image uses `pgvector/pgvector:pg16` so the optional vector column and
HNSW index are available. If pgvector is unavailable in a different deployment,
the migration keeps lexical retrieval and JSON embeddings operational.
