-- OJTFlow backend v0 PostgreSQL schema.
-- This migration is intentionally SQL-first so the operational contract is
-- inspectable without reading Python adapter code.

create schema if not exists ojtflow;

create table if not exists ojtflow.schema_migrations (
    version text primary key,
    name text not null,
    checksum text not null,
    applied_at timestamptz not null default now()
);

create table if not exists ojtflow.workflows (
    workflow_id text primary key,
    status text not null,
    schema_version text not null,
    review_id text,
    state_json jsonb not null,
    created_at timestamptz not null,
    updated_at timestamptz not null,
    constraint workflows_review_id_unique unique (review_id),
    constraint workflows_status_check check (
        status in (
            'created',
            'running',
            'needs_human_review',
            'approved',
            'rejected',
            'completed',
            'failed',
            'cancelled'
        )
    ),
    constraint workflows_updated_after_created check (updated_at >= created_at),
    constraint workflows_state_is_object check (jsonb_typeof(state_json) = 'object')
);

create index if not exists idx_workflows_status
    on ojtflow.workflows(status);

create index if not exists idx_workflows_review_id
    on ojtflow.workflows(review_id)
    where review_id is not null;

create index if not exists idx_workflows_updated_at
    on ojtflow.workflows(updated_at desc);

create index if not exists idx_workflows_state_json_gin
    on ojtflow.workflows using gin(state_json);

create table if not exists ojtflow.datasets (
    dataset_id text primary key,
    workflow_id text references ojtflow.workflows(workflow_id)
        on delete set null,
    source_kind text not null,
    declared_format text,
    detected_format text,
    byte_size bigint not null,
    sha256 text not null,
    storage_ref text not null unique,
    created_at timestamptz not null default now(),
    constraint datasets_source_kind_check check (
        source_kind in ('inline', 'upload', 'generated', 'fixture')
    ),
    constraint datasets_byte_size_check check (byte_size >= 0),
    constraint datasets_sha256_check check (sha256 ~ '^[0-9a-f]{64}$')
);

create index if not exists idx_datasets_workflow_id
    on ojtflow.datasets(workflow_id);

create index if not exists idx_datasets_sha256
    on ojtflow.datasets(sha256);

create table if not exists ojtflow.workflow_events (
    event_id text primary key,
    workflow_id text not null references ojtflow.workflows(workflow_id)
        on delete cascade,
    timestamp timestamptz not null,
    actor_type text not null,
    actor_id text not null,
    event_type text not null,
    severity text not null,
    summary text not null,
    input_refs jsonb not null default '[]'::jsonb,
    output_refs jsonb not null default '[]'::jsonb,
    event_json jsonb not null,
    constraint workflow_events_actor_type_check check (
        actor_type in ('user', 'agent', 'tool', 'system')
    ),
    constraint workflow_events_severity_check check (
        severity in ('info', 'warning', 'error', 'critical')
    ),
    constraint workflow_events_event_type_check check (
        event_type in (
            'workflow.created',
            'workflow.started',
            'agent.started',
            'agent.completed',
            'agent.failed',
            'tool.called',
            'tool.completed',
            'tool.failed',
            'retrieval.completed',
            'validation.completed',
            'review.requested',
            'review.decided',
            'transformation.completed',
            'explanation.completed',
            'workflow.completed',
            'workflow.failed'
        )
    ),
    constraint workflow_events_input_refs_array check (jsonb_typeof(input_refs) = 'array'),
    constraint workflow_events_output_refs_array check (jsonb_typeof(output_refs) = 'array'),
    constraint workflow_events_event_json_object check (jsonb_typeof(event_json) = 'object')
);

create index if not exists idx_workflow_events_workflow_timestamp
    on ojtflow.workflow_events(workflow_id, timestamp, event_id);

create index if not exists idx_workflow_events_type
    on ojtflow.workflow_events(event_type);

create index if not exists idx_workflow_events_event_json_gin
    on ojtflow.workflow_events using gin(event_json);

create table if not exists ojtflow.reviews (
    review_id text primary key,
    workflow_id text not null references ojtflow.workflows(workflow_id)
        on delete cascade,
    status text not null,
    trigger text not null,
    review_json jsonb not null,
    decided_by text,
    decided_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint reviews_status_check check (
        status in (
            'pending',
            'approved',
            'approved_with_edits',
            'rejected',
            'clarification_requested',
            'cancelled'
        )
    ),
    constraint reviews_decision_consistency_check check (
        (status = 'pending' and decided_by is null and decided_at is null)
        or (status <> 'pending')
    ),
    constraint reviews_review_json_object check (jsonb_typeof(review_json) = 'object')
);

create index if not exists idx_reviews_workflow_id
    on ojtflow.reviews(workflow_id);

create index if not exists idx_reviews_status
    on ojtflow.reviews(status);

create table if not exists ojtflow.evidence (
    evidence_id text primary key,
    workflow_id text references ojtflow.workflows(workflow_id)
        on delete cascade,
    source_type text not null,
    source_id text not null,
    source_version text,
    claim text not null,
    confidence double precision,
    trust_level text not null,
    evidence_json jsonb not null,
    created_at timestamptz not null default now(),
    constraint evidence_source_type_check check (
        source_type in (
            'input_data',
            'schema',
            'data_dictionary',
            'transformation_example',
            'validation_report',
            'tool_output',
            'human_decision',
            'audit_event',
            'ocr_box',
            'dicom_metadata',
            'image_mask',
            'video_track'
        )
    ),
    constraint evidence_trust_level_check check (
        trust_level in ('approved', 'internal', 'user_provided', 'untrusted')
    ),
    constraint evidence_confidence_check check (
        confidence is null or (confidence >= 0 and confidence <= 1)
    ),
    constraint evidence_json_object check (jsonb_typeof(evidence_json) = 'object')
);

create index if not exists idx_evidence_workflow_id
    on ojtflow.evidence(workflow_id);

create index if not exists idx_evidence_source
    on ojtflow.evidence(source_type, source_id);

create index if not exists idx_evidence_json_gin
    on ojtflow.evidence using gin(evidence_json);
