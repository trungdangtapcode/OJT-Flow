# pgvector Index Management

This guide covers OJTFlow retrieval index operations for Postgres deployments that use pgvector.

## Current Default

The Postgres retrieval adapter supports:

- lexical candidate retrieval through generated `search_vector`
- JSON embedding fallback for environments without pgvector
- pgvector `vector(384)` storage when the extension is available
- HNSW cosine index for vector candidate retrieval
- per-query `hnsw.ef_search` tuning through `OJT_RETRIEVAL_HNSW_EF_SEARCH`

The Docker stack uses `pgvector/pgvector:pg16`, so the vector column and HNSW index are expected to be available in normal local and demo deployments.

## Reindex Requirement

Run retrieval reindex whenever any of these change:

- `OJT_EMBEDDING_PROVIDER`
- `OJT_EMBEDDING_MODEL`
- `OJT_EMBEDDING_DIMENSIONS`
- local Hugging Face model files
- corpus source files or source-adapter metadata

OJTFlow stamps indexed chunks with an `embedding_generation_id` derived from provider, model, and dimension count. If search sees stored candidates from an older generation, the retrieval trace warns operators to run reindex.

## HNSW Defaults

HNSW is the default large-recall index for the current v0 shape:

```sql
create index if not exists idx_knowledge_chunks_embedding_hnsw
on ojtflow.knowledge_chunks
using hnsw (embedding vector_cosine_ops);
```

Query-time recall is controlled by:

```sql
select set_config('hnsw.ef_search', '100', true);
```

Use a higher value when retrieval misses relevant evidence. Use a lower value when latency is the stricter constraint.

## IVFFlat Migration Path

For very large corpora, evaluate IVFFlat when:

- corpus size grows enough that HNSW build time or memory becomes operationally expensive
- the workload can tolerate periodic index retraining
- ingestion happens in controlled batches

Example candidate migration:

```sql
create index concurrently idx_knowledge_chunks_embedding_ivfflat
on ojtflow.knowledge_chunks
using ivfflat (embedding vector_cosine_ops)
with (lists = 100);
```

Operational notes:

- Build IVFFlat after enough representative rows exist.
- Tune `lists` by corpus size and recall targets.
- Use `probes` at query time during evaluation.
- Keep HNSW until IVFFlat recall and latency are verified against retrieval benchmarks.

Example probe setting:

```sql
select set_config('ivfflat.probes', '10', true);
```

## Large-Corpus Rollout

Use this rollout path:

1. Load corpus into runtime storage, not git.
2. Create or approve corpus source adapters with license metadata.
3. Run ingestion into `knowledge_documents` and `knowledge_chunks`.
4. Run `POST /api/v1/retrieval/reindex`.
5. Check `/api/v1/retrieval/integrity`.
6. Run retrieval evaluation cases for recall, MRR, nDCG, source diversity, and unsupported-claim rate.
7. Compare HNSW and IVFFlat on the same benchmark set.
8. Freeze index settings for demo or production release.

Do not switch index strategy only because one query is slow. Use benchmark evidence and corpus-level metrics.
