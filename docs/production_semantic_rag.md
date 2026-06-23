# Production Semantic RAG

Production RAG requires real semantic embeddings and pgvector similarity search.
It must not run with fake, mock, rule-based, hash, lexical, keyword, random,
or test embedding providers.

## Required Configuration

```text
OJT_PRODUCT_MODE=production
OJT_STORAGE_BACKEND=postgres
OJT_RETRIEVAL_MODE=semantic_vector
OJT_RETRIEVAL_FRAMEWORK=custom
OJT_EMBEDDING_PROVIDER=openai
OJT_EMBEDDING_MODEL=text-embedding-3-small
OJT_EMBEDDING_DIMENSIONS=384
OJT_OPENAI_API_KEY=...
OJT_LLM_PROVIDER=openai
OJT_LLM_MODEL=chat-latest
```

Local model deployments may use:

```text
OJT_EMBEDDING_PROVIDER=huggingface
OJT_EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
OJT_EMBEDDING_DIMENSIONS=384
OJT_HF_EMBEDDING_DEVICE=cuda
```

## Retrieval Flow

1. Validate that the configured embedding provider/model is real.
2. Embed the user query with that provider.
3. Query `ojtflow.knowledge_chunks.embedding` with pgvector distance
   `embedding <=> query_vector`.
4. Return top chunks by vector distance.
5. Apply optional reranking only after semantic vector retrieval succeeds.
6. Generate answers only from retrieved context and cited evidence.

## Failure Policy

The server must fail startup/readiness or request handling when:

- embedding provider or model is missing;
- provider or model name contains fake/hash/mock/stub/test/rule-based terms;
- OpenAI embeddings are selected without an API key;
- production storage is not Postgres;
- retrieval mode is lexical, keyword, full-text, BM25, hybrid, or anything other
  than `semantic_vector`;
- pgvector column/index is unavailable;
- vector dimensions do not match the configured embedding provider;
- indexed vectors are empty or stale.

There is no production fallback to PostgreSQL full-text search, BM25, token
matching, `LIKE`/`ILIKE`, trigram search, JSON/Python vector reranking, or
static chunks.

## Reindex

After changing embedding provider, model, dimensions, chunking, or corpus files,
rebuild vectors:

```text
POST /api/v1/retrieval/reindex
```

If the API returns `SEMANTIC_INDEX_REINDEX_REQUIRED`, reindex before serving RAG
queries.

## Verification

Run:

```bash
scripts/verify_no_fake_ai_in_production
```

The script fails if production retrieval source/config contains fake provider
classes, hash embedding markers, full-text production RAG SQL, or forbidden
lexical fallback helpers.
