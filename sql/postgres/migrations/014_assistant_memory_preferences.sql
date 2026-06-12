-- Persist only policy-allowlisted operational Assistant preferences.

create table if not exists ojtflow.assistant_memory_preferences (
    owner_user_id text not null,
    key text not null,
    value jsonb not null,
    category text not null,
    source text not null,
    policy_version text not null,
    created_at timestamptz not null,
    updated_at timestamptz not null,
    primary key (owner_user_id, key),
    constraint assistant_memory_preferences_source_check check (
        source in ('user', 'system', 'admin')
    ),
    constraint assistant_memory_preferences_updated_after_created check (
        updated_at >= created_at
    )
);

create index if not exists idx_assistant_memory_owner_updated
    on ojtflow.assistant_memory_preferences(owner_user_id, updated_at desc);
