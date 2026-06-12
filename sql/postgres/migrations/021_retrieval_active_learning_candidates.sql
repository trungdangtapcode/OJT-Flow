create table if not exists ojtflow.retrieval_active_learning_candidates (
    candidate_id text primary key,
    owner_user_id text not null,
    candidate_key text not null,
    query_hash text not null,
    query_text text not null,
    source_kind text not null,
    trigger_reason text not null,
    priority text not null,
    status text not null default 'open',
    evidence_id text,
    source_id text,
    source_type text,
    source_version text,
    run_id text,
    workflow_id text,
    judgment_id text,
    claim_id text,
    support_status text,
    suggested_expected_evidence_ids jsonb not null default '[]'::jsonb,
    suggested_filters jsonb not null default '{}'::jsonb,
    benchmark_metadata jsonb not null default '{}'::jsonb,
    metadata jsonb not null default '{}'::jsonb,
    reviewer_user_id text,
    reviewer_note text,
    reviewed_at timestamptz,
    created_at timestamptz not null,
    updated_at timestamptz not null,
    unique(owner_user_id, candidate_key),
    check (source_kind in (
        'low_confidence_retrieval',
        'unsupported_claim',
        'reviewer_correction',
        'weak_support',
        'negative_judgment'
    )),
    check (priority in ('low', 'normal', 'high', 'critical')),
    check (status in ('open', 'accepted', 'rejected', 'promoted', 'archived')),
    check (
        support_status is null
        or support_status in ('strong', 'partial', 'weak', 'unsupported')
    )
);

create index if not exists idx_active_learning_owner_status_updated
    on ojtflow.retrieval_active_learning_candidates(owner_user_id, status, updated_at desc);

create index if not exists idx_active_learning_owner_kind_updated
    on ojtflow.retrieval_active_learning_candidates(owner_user_id, source_kind, updated_at desc);

create index if not exists idx_active_learning_owner_priority_updated
    on ojtflow.retrieval_active_learning_candidates(owner_user_id, priority, updated_at desc);
