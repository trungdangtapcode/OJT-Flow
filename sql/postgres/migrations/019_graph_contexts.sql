create table if not exists ojtflow.graph_contexts (
    graph_id text primary key,
    owner_user_id text,
    workflow_id text,
    request_id text,
    search_signature text,
    query_text text not null,
    resource_type text,
    fields_json jsonb not null,
    node_count integer not null,
    edge_count integer not null,
    triple_count integer not null,
    graph_json jsonb not null,
    record_json jsonb not null,
    created_at timestamptz not null,
    check (node_count >= 0),
    check (edge_count >= 0),
    check (triple_count >= 0)
);

create index if not exists idx_graph_contexts_owner_created
    on ojtflow.graph_contexts(owner_user_id, created_at desc);

create index if not exists idx_graph_contexts_workflow_created
    on ojtflow.graph_contexts(workflow_id, created_at desc);

create index if not exists idx_graph_contexts_search_signature
    on ojtflow.graph_contexts(search_signature);
