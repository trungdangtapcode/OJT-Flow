# RBAC Roles v0

## Purpose

F120 defines the enterprise role catalog that F121 uses for ownership and
authorization enforcement. The v0 policy is data-driven and visible through the
backend API so the frontend, assistant, MCP tooling, and future admin screens do
not duplicate role semantics.

Source of truth:

- `knowledge/governance/rbac_roles.json`

Loader:

- `src/ojtflow/infrastructure/governance_rbac.py`

Contracts:

- `RbacPolicy`
- `RbacRoleDefinition`
- `RbacPermissionDefinition`

API:

- `GET /api/v1/governance/rbac-policy`

## Roles

The catalog defines these workspace roles:

- `viewer`: read-only workspace inspection.
- `operator`: run governed workflow operations and create review-gated work.
- `reviewer`: inspect and create review follow-up work.
- `data-steward`: manage data quality, schema, terminology, evidence, and
  approved exports.
- `admin`: manage users, groups, settings, and high-risk workspace policy.
- `auditor`: read-only compliance and audit visibility.
- `owner`: bootstrap system role for the first workspace owner, equivalent to
  admin in v0 and not normally assignable.

## Permission Scopes

The policy uses string permission scopes such as:

- `data:read`
- `data:profile`
- `data:validate`
- `data:transform`
- `data:export`
- `retrieval:read`
- `review:read`
- `review:write`
- `audit:read`
- `settings:read`
- `settings:write`
- `users:read`
- `users:write`
- `admin:read`
- `admin:write`

The loader rejects duplicate role keys, duplicate permission scopes, and role
references to unknown permission scopes.

## Effective Permissions

`WorkspaceDetail` now includes:

- `effective_role_keys`
- `effective_permission_scopes`

These are computed from the user's organization membership role plus any group
role keys for groups that include the user.

## Boundary

F120 defines and exposes RBAC policy. F121 applies it through
`GovernanceService.require_permission(...)` at API boundaries for workflows,
reviews, artifacts, source inventory, runtime settings, audit records, and
exports. Owned resources are still scoped by backend session user ID.

Detailed enforcement map:

- `docs/ownership_authorization_v0.md`

## Verification

```bash
python -m pytest tests/test_governance.py \
  tests/test_api.py::test_runtime_settings_write_requires_settings_permission \
  tests/test_api.py::test_retrieval_reindex_requires_admin_write_permission \
  -q
```
