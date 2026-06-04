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
- optional pgvector `vector(384)` and HNSW index when the extension is available
- JSON embeddings as a portable fallback

Memory and SQLite modes use the static retrieval repository so tests and local
demos do not require database state. The static adapter still accepts configured
embedding providers for parity with Postgres mode.

## Ranking

The retrieval pipeline is auditable in v0:

1. Build query variants from instruction, fields, schema, format, and resource type.
2. Candidate chunks are filtered by trust level, clinical domain, standard system, or source type.
3. Lexical score uses token overlap and Postgres full-text search in Postgres mode.
4. Vector score uses the configured embedding provider:
   deterministic hash embeddings for offline tests, OpenAI semantic embeddings
   for CPU-safe production-like retrieval, or Hugging Face/SentenceTransformers
   embeddings for local GPU retrieval.
5. Reciprocal Rank Fusion combines lexical and vector rankings.
6. Rerank boosts favor schema matches, field matches, approved sources, and relevant healthcare standards.
7. Trace safety flags mark prompt-injection-like query text and sensitive field
   context without blocking retrieval.

The retrieval package now includes a `graph_context` handoff that extracts
entities and evidence triples from the retrieved claims. This is a
GraphRAG-lite context for validation/explanation workflows, not diagnosis,
treatment, triage, or medication advice.

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

Refresh indexed retrieval sources:

```http
POST /api/v1/retrieval/reindex
```

```json
{
  "include_seeded": true,
  "include_corpus": true
}
```

Direct retrieval requires an authenticated session. Requests without
`workflow_id` search the approved knowledge inventory. Requests with
`workflow_id` are scoped to the authenticated workflow owner and return
`not_found` for other users' workflow IDs.

Workflow output includes:

- `retrieved_context`
- `handoff_context.retrieval_trace`
- `handoff_context.retrieval_handoff`
- `handoff_context.retrieval_handoff.graph_context`

`graph_context` uses contract `graph_ner_handoff.v0` and includes:

- `nodes`: query, evidence, healthcare standard, clinical concept, and data-field nodes.
- `edges`: auditable relationships such as `supports`, `mentions_field`, and
  `requests_resource`.
- `triples`: source/evidence triples for downstream Graph-NER/RAG handoff.

`retrieval_trace.safety_flags` is deterministic and auditable. Current flags are:

- `prompt_injection_pattern_in_query`: the retrieval query or query context
  looks like instruction injection and must be treated as untrusted data.
- `sensitive_field_context`: the query fields include healthcare-sensitive
  identifiers such as patient fields. Retrieval continues, but downstream
  handoff code should avoid treating the query text as executable instruction.

## Configuration

```text
OJT_STORAGE_BACKEND=postgres
OJT_DATABASE_URL=postgresql://ojtflow:ojtflow@localhost:5432/ojtflow
OJT_KNOWLEDGE_DIR=knowledge
OJT_EMBEDDING_PROVIDER=deterministic
OJT_EMBEDDING_MODEL=deterministic-hash-v0
OJT_EMBEDDING_DIMENSIONS=64
```

`OJT_EMBEDDING_PROVIDER` supports `deterministic`, `openai`, and `huggingface`.
Deterministic mode is for tests and offline demos only. OpenAI mode uses the
Embeddings API and reads `OJT_OPENAI_API_KEY`, falling back to `OPENAI_API_KEY`
when the project-specific variable is not set. Hugging Face mode uses
SentenceTransformers locally and can run on GPU with `OJT_HF_EMBEDDING_DEVICE=cuda`.

Recommended OpenAI semantic retrieval settings:

```text
OJT_EMBEDDING_PROVIDER=openai
OJT_EMBEDDING_MODEL=text-embedding-3-small
OJT_EMBEDDING_DIMENSIONS=384
OJT_OPENAI_API_KEY=...
```

`text-embedding-3-small` is used with 384 dimensions to match the local
`embedding vector(384)` schema and keep storage/query cost lower than the
model's default 1536-dimensional output. Both provider and model are validated
during settings load so runtime diagnostics cannot claim a provider that the
retrieval adapter is not actually using.

Recommended local GPU retrieval settings:

```text
OJT_EMBEDDING_PROVIDER=huggingface
OJT_EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
OJT_EMBEDDING_DIMENSIONS=384
OJT_HF_EMBEDDING_DEVICE=cuda
OJT_HF_EMBEDDING_BATCH_SIZE=32
OJT_HF_EMBEDDING_CACHE_DIR=var/huggingface
```

Install local embedding dependencies with:

```bash
uv pip install -e '.[embeddings-local]'
```

Local trusted corpus files are read from `OJT_RETRIEVAL_CORPUS_DIRS`, defaulting
to `knowledge/corpus`. Supported corpus file extensions are `.md`, `.txt`,
`.json`, `.yaml`, `.yml`, and `.csv`. Reindexing is explicit through
`POST /api/v1/retrieval/reindex` so operators can control when model downloads,
embedding computation, and database vector updates happen.

`OJT_KNOWLEDGE_DIR` points at the trusted healthcare knowledge inventory used to
seed retrieval sources and schema evidence. Relative paths resolve from the
project root in local development; container deployments set an absolute path.
Named schema requests are strict. Workflow, validation, and direct retrieval
callers must use a profile returned by `GET /api/v1/schemas`, or set
`schema_id` to `null` for explicit no-schema processing. Missing requested
schemas fail before retrieval so the evidence package cannot imply a weaker
validation contract than the caller requested.

## Verification

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest
cd frontend && npm run build
```

For Postgres:

```bash
docker compose up --build
```

The Docker image uses `pgvector/pgvector:pg16` so the optional vector column and
HNSW index are available. If pgvector is unavailable in a different deployment,
the migration keeps lexical retrieval and JSON embeddings operational.
