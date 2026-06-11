-- Append-only access audit for uploaded artifact metadata and downloads.

create table if not exists ojtflow.artifact_access_events (
    event_id text primary key,
    artifact_id text not null references ojtflow.uploaded_artifacts(artifact_id)
        on delete cascade,
    owner_user_id text not null,
    actor_user_id text not null,
    action text not null,
    request_id text,
    event_json jsonb not null,
    created_at timestamptz not null,
    constraint artifact_access_events_action_check check (
        action in ('download', 'export_metadata', 'view_metadata')
    ),
    constraint artifact_access_events_json_object check (jsonb_typeof(event_json) = 'object')
);

create index if not exists idx_artifact_access_events_artifact_created
    on ojtflow.artifact_access_events(owner_user_id, artifact_id, created_at desc);

create index if not exists idx_artifact_access_events_actor_created
    on ojtflow.artifact_access_events(actor_user_id, created_at desc);
