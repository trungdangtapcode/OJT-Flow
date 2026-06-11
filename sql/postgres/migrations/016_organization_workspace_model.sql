create table if not exists ojtflow.organizations (
    organization_id text primary key,
    slug text not null unique,
    display_name text not null,
    status text not null default 'active',
    created_by_user_id text not null references ojtflow.users(user_id),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    attributes jsonb not null default '{}'::jsonb,
    constraint organizations_status_check
        check (status in ('active', 'disabled'))
);

create index if not exists idx_organizations_created_by
    on ojtflow.organizations(created_by_user_id, created_at desc);

create table if not exists ojtflow.organization_memberships (
    membership_id text primary key,
    organization_id text not null references ojtflow.organizations(organization_id)
        on delete cascade,
    user_id text not null references ojtflow.users(user_id)
        on delete cascade,
    role_key text not null,
    status text not null default 'active',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint organization_memberships_status_check
        check (status in ('active', 'disabled', 'invited')),
    unique (organization_id, user_id)
);

create index if not exists idx_org_memberships_user_status
    on ojtflow.organization_memberships(user_id, status, created_at);

create index if not exists idx_org_memberships_org_role
    on ojtflow.organization_memberships(organization_id, role_key, status);

create table if not exists ojtflow.organization_groups (
    group_id text primary key,
    organization_id text not null references ojtflow.organizations(organization_id)
        on delete cascade,
    slug text not null,
    display_name text not null,
    description text not null default '',
    role_keys jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (organization_id, slug)
);

create index if not exists idx_org_groups_org_slug
    on ojtflow.organization_groups(organization_id, slug);

create table if not exists ojtflow.organization_group_memberships (
    group_id text not null references ojtflow.organization_groups(group_id)
        on delete cascade,
    organization_id text not null references ojtflow.organizations(organization_id)
        on delete cascade,
    user_id text not null references ojtflow.users(user_id)
        on delete cascade,
    created_at timestamptz not null default now(),
    primary key (group_id, user_id)
);

create index if not exists idx_org_group_memberships_org_user
    on ojtflow.organization_group_memberships(organization_id, user_id);

create table if not exists ojtflow.workspace_settings (
    organization_id text primary key references ojtflow.organizations(organization_id)
        on delete cascade,
    settings_json jsonb not null default '{}'::jsonb,
    version integer not null default 1,
    updated_by_user_id text references ojtflow.users(user_id),
    updated_at timestamptz not null default now(),
    constraint workspace_settings_version_check
        check (version >= 1)
);
