create table if not exists ojtflow.audit_records (
    audit_id text primary key,
    owner_user_id text,
    workflow_id text references ojtflow.workflows(workflow_id),
    assistant_session_id text,
    assistant_message_id text,
    request_id text,
    action text not null,
    actor_id text not null,
    actor_type text not null,
    status text not null,
    input_hash text,
    output_hash text,
    workflow_event_refs jsonb not null default '[]'::jsonb,
    metadata jsonb not null default '{}'::jsonb,
    record_json jsonb not null,
    timestamp timestamptz not null
);

alter table ojtflow.audit_records
    add constraint audit_records_workflow_event_refs_array
    check (jsonb_typeof(workflow_event_refs) = 'array');

alter table ojtflow.audit_records
    add constraint audit_records_metadata_object
    check (jsonb_typeof(metadata) = 'object');

alter table ojtflow.audit_records
    add constraint audit_records_record_object
    check (jsonb_typeof(record_json) = 'object');

create index if not exists idx_audit_records_owner_timestamp
    on ojtflow.audit_records(owner_user_id, timestamp desc);

create index if not exists idx_audit_records_workflow_timestamp
    on ojtflow.audit_records(workflow_id, timestamp desc);

create index if not exists idx_audit_records_session_timestamp
    on ojtflow.audit_records(assistant_session_id, timestamp desc);

create index if not exists idx_audit_records_action_timestamp
    on ojtflow.audit_records(action, timestamp desc);
