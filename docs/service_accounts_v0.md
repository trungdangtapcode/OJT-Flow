# Service Accounts v0

## Purpose

F122 adds automation identities for ingestion jobs, CI, and non-browser clients.
Service accounts authenticate with bearer tokens but are still attached to an
organization workspace and evaluated through the same RBAC policy as users.

## Model

A service account has:

- `account_id`
- `user_id`
- `organization_id`
- `slug`
- `display_name`
- `role_key`
- `status`
- `created_by_user_id`
- timestamps and `last_used_at`

Service accounts are backed by normal `users` rows with
`google_sub = service-account:{account_id}`. This lets existing owner-scoped
repositories use `AuthenticatedSession.user.user_id` without a second identity
path.

## Token Rules

`POST /api/v1/auth/service-accounts` returns the raw bearer token once. The
backend stores only the SHA-256 token hash in the existing `sessions` table.

Token prefix:

```text
ojt_sa_
```

Default token lifetime comes from:

```text
OJT_SERVICE_ACCOUNT_TOKEN_TTL_SECONDS=7776000
```

The default service account role comes from:

```text
OJT_SERVICE_ACCOUNT_DEFAULT_ROLE_KEY=operator
```

## API

`POST /api/v1/auth/service-accounts`

Requires an authenticated user with `users:write`.

Request:

```json
{
  "slug": "nightly-ingestion",
  "display_name": "Nightly Ingestion",
  "role_key": "operator",
  "token_ttl_seconds": 3600
}
```

Response:

```json
{
  "data": {
    "service_account": {
      "account_id": "svc_example",
      "slug": "nightly-ingestion",
      "role_key": "operator",
      "status": "active"
    },
    "token_type": "bearer",
    "access_token": "ojt_sa_...",
    "expires_at": "2026-06-12T00:00:00+00:00"
  },
  "error": null
}
```

`GET /api/v1/auth/service-accounts`

Requires `users:read` and returns service accounts in the caller's current
organization unless `organization_id` is supplied and the caller is also a
member of that organization.

## Authorization Behavior

Service-account tokens resolve to:

```json
{
  "identity_type": "service_account",
  "service_account": {
    "slug": "nightly-ingestion",
    "role_key": "operator"
  }
}
```

After authentication, routes use the same `GovernanceService.require_permission`
checks as human users. For example, an `operator` service account can list
workflows and run validation-oriented tools, but cannot refresh retrieval
indexes because that requires `admin:write`.

## Storage

Postgres migration:

- `sql/postgres/migrations/017_service_accounts.sql`

SQLite and memory backends create equivalent tables/records for local
development and tests.

## Non-Goals

This v0 does not implement token rotation history, named token inventory,
ownership transfer, SCIM, service-account disable APIs, or per-token scopes.
Those should build on this identity foundation instead of creating another
authentication path.

## Verification

```bash
python -m pytest \
  tests/test_auth_service.py::test_auth_service_issues_service_account_token \
  tests/test_api.py::test_service_account_token_authenticates_with_workspace_role \
  tests/test_postgres_migrations.py \
  -q
```
