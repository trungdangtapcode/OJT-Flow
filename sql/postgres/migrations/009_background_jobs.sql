-- Durable background job state for sync local runner and future queue-backed workers.

create table if not exists ojtflow.background_jobs (
    job_id text primary key,
    owner_user_id text not null,
    job_type text not null,
    status text not null,
    input jsonb not null default '{}'::jsonb,
    output jsonb not null default '{}'::jsonb,
    error jsonb,
    progress jsonb not null default '{"current":0,"total":null,"message":""}'::jsonb,
    attempts integer not null default 0,
    max_attempts integer not null default 1,
    created_at timestamptz not null,
    updated_at timestamptz not null,
    started_at timestamptz,
    completed_at timestamptz,
    constraint background_jobs_type_check check (
        job_type in (
            'retrieval_reindex',
            'file_parse',
            'ocr_extract',
            'embedding_reindex',
            'external_ingest',
            'export_package'
        )
    ),
    constraint background_jobs_status_check check (
        status in ('queued', 'running', 'succeeded', 'failed', 'cancelled')
    ),
    constraint background_jobs_attempts_check check (attempts >= 0),
    constraint background_jobs_max_attempts_check check (max_attempts >= 1),
    constraint background_jobs_progress_object check (jsonb_typeof(progress) = 'object'),
    constraint background_jobs_input_object check (jsonb_typeof(input) = 'object'),
    constraint background_jobs_output_object check (jsonb_typeof(output) = 'object'),
    constraint background_jobs_error_object check (
        error is null or jsonb_typeof(error) = 'object'
    ),
    constraint background_jobs_updated_after_created check (updated_at >= created_at)
);

create index if not exists idx_background_jobs_owner_updated
    on ojtflow.background_jobs(owner_user_id, updated_at desc);

create index if not exists idx_background_jobs_owner_status
    on ojtflow.background_jobs(owner_user_id, status, updated_at desc);

create index if not exists idx_background_jobs_type_status
    on ojtflow.background_jobs(job_type, status, updated_at desc);
