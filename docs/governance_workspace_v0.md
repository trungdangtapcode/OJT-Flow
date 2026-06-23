# Governance Workspace v0

## Purpose

F119 introduces the durable tenant/workspace backbone for enterprise use:
organizations, user memberships, role keys, groups, group membership, and
workspace-level settings.

This is the foundation for RBAC and ownership enforcement. F119 creates and
exposes the model; F120 defines the role catalog; F121 applies permission
checks and owner scoping across workflows, reviews, artifacts, retrieval,
runtime, audit, and export surfaces.

## Source Of Truth

Contracts:

- `src/ojtflow/core/contracts/governance.py`

Service:

- `src/ojtflow/application/governance_service.py`

Repositories:

- `src/ojtflow/infrastructure/storage/governance_memory.py`
- `src/ojtflow/infrastructure/storage/governance_postgres.py`

Data-driven defaults:

- `knowledge/governance/workspace_defaults.json`
- `knowledge/governance/rbac_roles.json`

Postgres migration:

- `sql/postgres/migrations/016_organization_workspace_model.sql`

## API

All routes require an authenticated backend session and return the standard
`{data, error}` envelope.

- `GET /api/v1/organizations/current`
  - Returns the current user's workspace.
  - Creates a default workspace if the user has no organization membership.
- `GET /api/v1/governance/rbac-policy`
  - Returns the data-driven role and permission catalog.
  - Requires `settings:read`.
- `GET /api/v1/organizations`
  - Lists workspaces visible to the user.
- `PATCH /api/v1/organizations/{organization_id}/settings`
  - Deep-merges a settings patch into the workspace settings document.
  - Increments the settings version.
  - Requires `settings:write`.
- `POST /api/v1/organizations/{organization_id}/groups`
  - Creates an organization group for future RBAC and workflow assignment.
  - Requires `users:write`.

## Data Model

- `organizations`: enterprise tenant/workspace container.
- `organization_memberships`: user membership with a `role_key`.
- `organization_groups`: named groups with role keys.
- `organization_group_memberships`: user membership in groups.
- `workspace_settings`: versioned JSON settings for review, data handling,
  retrieval, and assistant behavior.

Role keys are mapped through `knowledge/governance/rbac_roles.json`. Workspace
responses include `effective_role_keys` and `effective_permission_scopes`.
Authorization enforcement across product resources is documented in
`docs/ownership_authorization_v0.md`.

## Verification

```bash
python -m pytest tests/test_governance.py tests/test_postgres_migrations.py -q
```

## Extension Rules

- Add new workspace defaults in `knowledge/governance/workspace_defaults.json`
  instead of hardcoding settings in the service.
- Keep settings as versioned JSON until policy contracts stabilize.
- Keep authorization checks centralized through `GovernanceService` rather than
  duplicating role logic in routes.
- Do not store real customer, PHI, or secret values in governance defaults.
