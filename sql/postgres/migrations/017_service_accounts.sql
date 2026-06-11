-- Service account identities for automation, ingestion jobs, and CI.
-- Raw bearer tokens are never stored; active tokens reuse hashed session rows.

create table if not exists ojtflow.service_accounts (
    account_id text primary key,
    user_id text not null unique references ojtflow.users(user_id)
        on delete cascade,
    organization_id text not null references ojtflow.organizations(organization_id)
        on delete cascade,
    slug text not null,
    display_name text not null,
    role_key text not null,
    status text not null default 'active',
    created_by_user_id text not null references ojtflow.users(user_id),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    last_used_at timestamptz,
    constraint service_accounts_status_check
        check (status in ('active', 'disabled')),
    unique (organization_id, slug)
);

create index if not exists idx_service_accounts_org_status
    on ojtflow.service_accounts(organization_id, status, created_at);

create index if not exists idx_service_accounts_user
    on ojtflow.service_accounts(user_id);
