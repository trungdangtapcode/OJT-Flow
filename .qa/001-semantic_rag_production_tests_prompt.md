# QA Prompt: Production Semantic RAG Regression Tests

Write tests for the current production RAG policy without reintroducing fake
providers or lexical fallback.

Required test coverage:

- Production config rejects `OJT_EMBEDDING_PROVIDER=rule-based`.
- Production config rejects missing `OJT_EMBEDDING_PROVIDER`.
- Production config rejects missing `OJT_EMBEDDING_MODEL`.
- Production config rejects fake/mock/stub/hash/test/lexical provider and model names.
- Production config rejects `OJT_RETRIEVAL_MODE=lexical`, `keyword`, `fulltext`, `bm25`, and `hybrid`.
- Production config rejects non-Postgres storage for pilot/production RAG.
- Production config rejects OpenAI embeddings without `OJT_OPENAI_API_KEY` or `OPENAI_API_KEY`.
- Production source cannot import or reference `Rule-basedEmbeddingProvider`.
- `build_embedding_provider` never returns a rule-based/null/fake provider.
- `PostgresRetrievalRepository._load_candidate_chunks` calls the embedding provider for the user query.
- `PostgresRetrievalRepository._load_candidate_chunks` executes SQL containing `embedding <=> %s::vector`.
- `PostgresRetrievalRepository._load_candidate_chunks` does not execute SQL containing `websearch_to_tsquery`, `to_tsvector`, `plainto_tsquery`, `ts_rank`, `LIKE`, `ILIKE`, trigram, or BM25.
- Missing pgvector column raises `DependencyUnavailableError` with `code="VECTOR_INDEX_UNAVAILABLE"`.
- Dimension mismatch raises `DependencyUnavailableError` with `code="VECTOR_INDEX_DIMENSION_MISMATCH"`.
- Empty vector index raises `DependencyUnavailableError` with `code="SEMANTIC_VECTOR_INDEX_EMPTY"`.
- Stale embedding generation raises `DependencyUnavailableError` with `code="SEMANTIC_INDEX_REINDEX_REQUIRED"`.
- Replacing vector SQL with lexical/full-text SQL makes the test fail.
- Replacing real embedding provider metadata with hash/rule-based/fake metadata makes the test fail.
- `scripts/verify_no_fake_ai_in_production` passes on the fixed tree and fails on injected forbidden terms.
- Static test fails if `allow_rule_based_fallback` appears in production source.
- Static test fails if `_rule_based_plan` or `rule_based_plan` appears in production source.
- Runtime test verifies planner failure raises `OJTFlowError` or `DependencyUnavailableError`.
- Runtime test verifies LLM synthesis failure raises and does not return a generated/template answer.
- Runtime test verifies missing planner/provider raises `DependencyUnavailableError`.
- Runtime test verifies no production `AssistantService` object has an
  `allow_rule_based_fallback` attribute.

Do not use synthetic test results as accuracy claims. These are regression and
guardrail tests only.
