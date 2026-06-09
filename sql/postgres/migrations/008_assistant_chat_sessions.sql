-- Persist Assistant chat sessions and ordered messages.

create table if not exists ojtflow.assistant_chat_sessions (
    session_id text primary key,
    owner_user_id text not null,
    title text not null,
    message_count integer not null default 0,
    archived_at timestamptz,
    created_at timestamptz not null,
    updated_at timestamptz not null,
    constraint assistant_chat_sessions_title_check check (length(trim(title)) > 0),
    constraint assistant_chat_sessions_message_count_check check (message_count >= 0),
    constraint assistant_chat_sessions_updated_after_created check (updated_at >= created_at)
);

create index if not exists idx_assistant_sessions_owner_updated
    on ojtflow.assistant_chat_sessions(owner_user_id, updated_at desc);

create index if not exists idx_assistant_sessions_owner_archived
    on ojtflow.assistant_chat_sessions(owner_user_id, archived_at, updated_at desc);

create table if not exists ojtflow.assistant_chat_messages (
    message_id text primary key,
    session_id text not null references ojtflow.assistant_chat_sessions(session_id)
        on delete cascade,
    owner_user_id text not null,
    role text not null,
    content text not null,
    workflow_refs jsonb not null default '[]'::jsonb,
    payload jsonb not null default '{}'::jsonb,
    created_at timestamptz not null,
    constraint assistant_chat_messages_role_check check (
        role in ('user', 'assistant', 'system', 'tool')
    ),
    constraint assistant_chat_messages_workflow_refs_array check (
        jsonb_typeof(workflow_refs) = 'array'
    ),
    constraint assistant_chat_messages_payload_object check (jsonb_typeof(payload) = 'object')
);

create index if not exists idx_assistant_messages_session_created
    on ojtflow.assistant_chat_messages(session_id, created_at, message_id);

create index if not exists idx_assistant_messages_owner_created
    on ojtflow.assistant_chat_messages(owner_user_id, created_at desc);

create index if not exists idx_assistant_messages_workflow_refs
    on ojtflow.assistant_chat_messages using gin (workflow_refs);
