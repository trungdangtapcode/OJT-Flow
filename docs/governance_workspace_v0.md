# Governance Workspace v0

## Purpose

F119 introduces the durable tenant/workspace backbone for enterprise use:
organizations, user memberships, role keys, groups, group membership, and
workspace-level settings.

This is the foundation for later RBAC and ownership enforcement. F119 creates
and exposes the model; F120 and F121 will enforce fine-grained permissions and
resource ownership across workflows, reviews, artifacts, chat, retrieval, and
admin surfaces.

## Source Of Truth

Contracts:

- `src/ojtflow/core/contracts/governance.py`

Service:

- `src/ojtflow/application/governance_service.py`

Repositories:

- `src/ojtflow/infrastructure/storage/governance_memory.py`
- `src/ojtflow/infrastructure/storage/governance_sqlite.py`
- `src/ojtflow/infrastructure/storage/governance_postgres.py`

Data-driven defaults:

- `knowledge/governance/workspace_defaults.json`

Postgres migration:

- `sql/postgres/migrations/016_organization_workspace_model.sql`

## API

All routes require an authenticated backend session and return the standard
`{data, error}` envelope.

- `GET /api/v1/organizations/current`
  - Returns the current user's workspace.
  - Creates a default workspace if the user has no organization membership.
- `GET /api/v1/organizations`
  - Lists workspaces visible to the user.
- `PATCH /api/v1/organizations/{organization_id}/settings`
  - Deep-merges a settings patch into the workspace settings document.
  - Increments the settings version.
- `POST /api/v1/organizations/{organization_id}/groups`
  - Creates an organization group for future RBAC and workflow assignment.

## Data Model

- `organizations`: enterprise tenant/workspace container.
- `organization_memberships`: user membership with a `role_key`.
- `organization_groups`: named groups with role keys.
- `organization_group_memberships`: user membership in groups.
- `workspace_settings`: versioned JSON settings for review, data handling,
  retrieval, and assistant behavior.

Role keys are stored now but not yet interpreted as authorization decisions.
That is intentional. The next roadmap item, F120, defines RBAC roles and maps
role keys to permissions.

## Verification

```bash
python -m pytest tests/test_governance.py tests/test_postgres_migrations.py -q
```

## Extension Rules

- Add new workspace defaults in `knowledge/governance/workspace_defaults.json`
  instead of hardcoding settings in the service.
- Keep settings as versioned JSON until policy contracts stabilize.
- Do not enforce cross-resource ownership in this layer; F121 owns that rollout.
- Do not store real customer, PHI, or secret values in governance defaults.
