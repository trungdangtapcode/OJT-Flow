-- Durable uploaded artifact registry and document extraction traces.

create table if not exists ojtflow.uploaded_artifacts (
    artifact_id text primary key,
    owner_user_id text not null,
    filename text not null,
    mime_type text not null,
    extension text not null,
    byte_size bigint not null,
    sha256 text not null,
    source text not null,
    storage_ref text not null,
    dataset_id text references ojtflow.datasets(dataset_id),
    duplicate_of_artifact_id text references ojtflow.uploaded_artifacts(artifact_id),
    retention_policy jsonb not null default '{}'::jsonb,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null,
    constraint uploaded_artifacts_byte_size_check check (byte_size >= 0),
    constraint uploaded_artifacts_sha256_check check (sha256 ~ '^[a-f0-9]{64}$'),
    constraint uploaded_artifacts_source_check check (
        source in ('upload', 'clipboard', 'assistant_attachment', 'api')
    ),
    constraint uploaded_artifacts_retention_object check (
        jsonb_typeof(retention_policy) = 'object'
    ),
    constraint uploaded_artifacts_metadata_object check (jsonb_typeof(metadata) = 'object')
);

create index if not exists idx_uploaded_artifacts_owner_created
    on ojtflow.uploaded_artifacts(owner_user_id, created_at desc);

create index if not exists idx_uploaded_artifacts_owner_hash
    on ojtflow.uploaded_artifacts(owner_user_id, sha256, byte_size);

create index if not exists idx_uploaded_artifacts_duplicate_of
    on ojtflow.uploaded_artifacts(duplicate_of_artifact_id)
    where duplicate_of_artifact_id is not null;

create table if not exists ojtflow.document_parse_traces (
    trace_id text primary key,
    artifact_id text not null references ojtflow.uploaded_artifacts(artifact_id)
        on delete cascade,
    owner_user_id text not null,
    job_id text references ojtflow.background_jobs(job_id),
    trace_json jsonb not null,
    created_at timestamptz not null,
    completed_at timestamptz,
    constraint document_parse_traces_json_object check (jsonb_typeof(trace_json) = 'object')
);

create index if not exists idx_document_parse_traces_artifact_created
    on ojtflow.document_parse_traces(owner_user_id, artifact_id, created_at desc);

create index if not exists idx_document_parse_traces_job
    on ojtflow.document_parse_traces(job_id)
    where job_id is not null;
