-- Add explicit workflow ownership for authenticated enterprise workspaces.
-- Existing unowned local/demo workflows remain queryable only through internal
-- service calls that do not provide an owner filter.

alter table ojtflow.workflows
    add column if not exists owner_user_id text;

update ojtflow.workflows
set owner_user_id = state_json->>'owner_user_id'
where owner_user_id is null
  and state_json ? 'owner_user_id'
  and nullif(state_json->>'owner_user_id', '') is not null;

create index if not exists idx_workflows_owner_updated
    on ojtflow.workflows(owner_user_id, updated_at desc);

create index if not exists idx_workflows_owner_status_updated
    on ojtflow.workflows(owner_user_id, status, updated_at desc);
