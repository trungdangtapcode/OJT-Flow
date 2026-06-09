-- Persist Assistant SSE replay artifacts without inflating chat message counts.

create table if not exists ojtflow.assistant_stream_replays (
    stream_id text primary key,
    session_id text not null references ojtflow.assistant_chat_sessions(session_id)
        on delete cascade,
    owner_user_id text not null,
    status text not null,
    events jsonb not null default '[]'::jsonb,
    created_at timestamptz not null,
    completed_at timestamptz not null,
    constraint assistant_stream_replays_status_check check (
        status in ('completed', 'failed')
    ),
    constraint assistant_stream_replays_events_array check (jsonb_typeof(events) = 'array'),
    constraint assistant_stream_replays_completed_after_created check (
        completed_at >= created_at
    )
);

create index if not exists idx_assistant_stream_replays_session_created
    on ojtflow.assistant_stream_replays(session_id, created_at, stream_id);

create index if not exists idx_assistant_stream_replays_owner_created
    on ojtflow.assistant_stream_replays(owner_user_id, created_at desc);
