# Ownership And Authorization v0

## Purpose

F121 applies the workspace RBAC catalog from `knowledge/governance/rbac_roles.json`
to owned product resources and operational surfaces. The goal is simple:
authenticated identity determines ownership, and RBAC scopes determine whether
the user can perform a class of operation.

## Ownership Model

Owned resources are always resolved with the backend session user ID. Clients do
not provide owner IDs.

- Workflows, workflow summaries, reviews, events, and output artifacts use
  `WorkflowState.owner_user_id`.
- Uploaded artifacts, parse traces, artifact access events, and raw downloads
  use `UploadedArtifact.owner_user_id`.
- Assistant sessions, assistant messages, and safe assistant memory use
  `owner_user_id` in the assistant repositories.
- Background jobs use `BackgroundJob.owner_user_id`.
- Retrieval relevance judgments use `owner_user_id`.
- Audit records are filtered by `owner_user_id`.

When a caller requests another user's owned resource, the service returns
`not_found` instead of exposing whether the ID exists.

## RBAC Enforcement

`GovernanceService.require_permission(user, permission_scope)` is the shared
authorization gate. It loads or creates the user's current workspace, computes
effective role keys and permission scopes, and raises `policy_blocked` when the
scope is missing.

Route-level enforcement in v0:

- Workflow create and document-to-workflow: `data:transform`
- Workflow list/detail/events/stats/schema registry: `data:read`
- Workflow output and raw artifact download/export: `data:export`
- Upload, extraction, clipboard image parsing, and redaction preview:
  `data:profile`
- Review queue reads: `review:read`
- Review decisions: `review:write`
- Retrieval search, planning, source inventory, presets, corpus manifests,
  search options, source policies, and strategy catalogs: `retrieval:read`
- Retrieval index refresh and retrieval reindex jobs: `admin:write`
- Retrieval integrity, runtime readiness, migration diagnostics, storage
  consistency, and repair plans: `admin:read`
- Runtime assistant/retrieval setting writes and workspace settings updates:
  `settings:write`
- Runtime config and RBAC policy reads: `settings:read`
- Organization group creation: `users:write`
- Audit record reads: `audit:read`

## API Error Shape

Permission failures use the standard API envelope:

```json
{
  "data": null,
  "error": {
    "code": "policy_blocked",
    "message": "Current user is not permitted to perform this operation.",
    "details": {
      "permission_scope": "settings:write",
      "role_keys": ["viewer"]
    },
    "workflow_id": null,
    "request_id": "req_example"
  }
}
```

## Explicit Non-Goals

F121 does not add organization membership management, role assignment APIs,
ownership transfer, row-level sharing, cross-organization delegation, or
service-account identities. Those are follow-up roadmap items.

Direct deterministic tool endpoints such as convert, validate, FHIR profile,
and OCR evidence are authenticated through router-level dependencies, but F121
does not add fine-grained RBAC scopes to those direct endpoints.

## Verification

Focused checks:

```bash
python -m pytest tests/test_governance.py \
  tests/test_api.py::test_runtime_settings_write_requires_settings_permission \
  tests/test_api.py::test_retrieval_reindex_requires_admin_write_permission \
  tests/test_workflow_service.py::test_workflow_service_scopes_queries_reviews_events_and_output_by_owner \
  -q
```
