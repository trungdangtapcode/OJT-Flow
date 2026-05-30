-- OJTFlow retrieval v0 PostgreSQL schema.
-- Provides lexical retrieval everywhere and pgvector acceleration when the
-- extension is installed in the active Postgres image.

create schema if not exists ojtflow;

do $$
begin
    create extension if not exists vector;
exception
    when undefined_file then
        raise notice 'pgvector extension is unavailable; using lexical retrieval and JSON embeddings only';
end $$;

alter table ojtflow.datasets
    drop constraint if exists datasets_source_kind_check;

alter table ojtflow.datasets
    add constraint datasets_source_kind_check check (
        source_kind in (
            'inline',
            'upload',
            'uploaded_file_raw',
            'uploaded_file_extracted_text',
            'binary',
            'generated',
            'fixture'
        )
    );

alter table ojtflow.evidence
    drop constraint if exists evidence_source_type_check;

alter table ojtflow.evidence
    add constraint evidence_source_type_check check (
        source_type in (
            'input_data',
            'schema',
            'data_dictionary',
            'healthcare_standard',
            'terminology_system',
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
    );

create table if not exists ojtflow.knowledge_documents (
    source_id text primary key,
    source_type text not null,
    title text not null,
    source_version text,
    trust_level text not null,
    clinical_domain text,
    standard_system text,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint knowledge_documents_source_type_check check (
        source_type in (
            'schema',
            'data_dictionary',
            'healthcare_standard',
            'terminology_system',
            'transformation_example',
            'tool_output'
        )
    ),
    constraint knowledge_documents_trust_level_check check (
        trust_level in ('approved', 'internal', 'user_provided', 'untrusted')
    ),
    constraint knowledge_documents_metadata_object check (jsonb_typeof(metadata) = 'object')
);

create table if not exists ojtflow.knowledge_chunks (
    chunk_id text primary key,
    source_id text not null references ojtflow.knowledge_documents(source_id)
        on delete cascade,
    source_type text not null,
    title text not null,
    source_version text,
    trust_level text not null,
    clinical_domain text,
    standard_system text,
    content text not null,
    locator jsonb not null default '{}'::jsonb,
    metadata jsonb not null default '{}'::jsonb,
    embedding_json jsonb,
    search_vector tsvector generated always as (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(source_id, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(standard_system, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(content, '')), 'C')
    ) stored,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint knowledge_chunks_source_type_check check (
        source_type in (
            'schema',
            'data_dictionary',
            'healthcare_standard',
            'terminology_system',
            'transformation_example',
            'tool_output'
        )
    ),
    constraint knowledge_chunks_trust_level_check check (
        trust_level in ('approved', 'internal', 'user_provided', 'untrusted')
    ),
    constraint knowledge_chunks_locator_object check (jsonb_typeof(locator) = 'object'),
    constraint knowledge_chunks_metadata_object check (jsonb_typeof(metadata) = 'object'),
    constraint knowledge_chunks_embedding_array check (
        embedding_json is null or jsonb_typeof(embedding_json) = 'array'
    )
);

create index if not exists idx_knowledge_documents_type
    on ojtflow.knowledge_documents(source_type, standard_system);

create index if not exists idx_knowledge_chunks_source
    on ojtflow.knowledge_chunks(source_id);

create index if not exists idx_knowledge_chunks_domain
    on ojtflow.knowledge_chunks(clinical_domain, standard_system);

create index if not exists idx_knowledge_chunks_search_vector
    on ojtflow.knowledge_chunks using gin(search_vector);

do $$
begin
    if exists (select 1 from pg_type where typname = 'vector') then
        execute 'alter table ojtflow.knowledge_chunks add column if not exists embedding vector(64)';
        execute 'create index if not exists idx_knowledge_chunks_embedding_hnsw on ojtflow.knowledge_chunks using hnsw (embedding vector_cosine_ops)';
    end if;
end $$;
