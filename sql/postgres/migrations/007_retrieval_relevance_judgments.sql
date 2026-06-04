-- Durable retrieval relevance judgments for search-quality evaluation.
-- Judgments are scoped to the authenticated user and keyed by normalized query
-- hash plus evidence ID so rerunning the same query can reload prior labels.

create table if not exists ojtflow.retrieval_relevance_judgments (
    judgment_id text primary key,
    owner_user_id text not null,
    query_hash text not null,
    query_text text not null,
    evidence_id text not null,
    source_id text,
    source_type text,
    source_version text,
    run_id text,
    search_signature text,
    value text not null,
    rating integer not null,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null,
    updated_at timestamptz not null,
    constraint retrieval_judgments_owner_query_evidence_unique
        unique (owner_user_id, query_hash, evidence_id),
    constraint retrieval_judgments_query_hash_check
        check (query_hash ~ '^[0-9a-f]{64}$'),
    constraint retrieval_judgments_value_check
        check (value in ('relevant', 'partial', 'not_relevant')),
    constraint retrieval_judgments_rating_check
        check (rating >= 0 and rating <= 3),
    constraint retrieval_judgments_metadata_object
        check (jsonb_typeof(metadata) = 'object'),
    constraint retrieval_judgments_updated_after_created
        check (updated_at >= created_at)
);

create index if not exists idx_retrieval_judgments_owner_updated
    on ojtflow.retrieval_relevance_judgments(owner_user_id, updated_at desc);

create index if not exists idx_retrieval_judgments_owner_query
    on ojtflow.retrieval_relevance_judgments(owner_user_id, query_hash, updated_at desc);

create index if not exists idx_retrieval_judgments_owner_run
    on ojtflow.retrieval_relevance_judgments(owner_user_id, run_id, updated_at desc)
    where run_id is not null;

create index if not exists idx_retrieval_judgments_source
    on ojtflow.retrieval_relevance_judgments(source_id, source_type);
