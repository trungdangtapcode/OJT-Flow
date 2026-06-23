-- Workspace-scoped artifact metadata and object-storage refs.

alter table ojtflow.uploaded_artifacts
    add column if not exists organization_id text;

create index if not exists idx_uploaded_artifacts_org_created
    on ojtflow.uploaded_artifacts(organization_id, created_at desc)
    where organization_id is not null;

create index if not exists idx_uploaded_artifacts_org_hash
    on ojtflow.uploaded_artifacts(organization_id, sha256, byte_size)
    where organization_id is not null;

