# Release And Performance Readiness v0

This package implements the first Month 8 release/scale readiness layer. It is
not a production SLO program yet; it creates the contracts, scripts, and CI
gates needed to measure and block obvious regressions.

## Implemented Scope

- F156 load smoke scenarios for workflow creation, retrieval search, assistant
  stream, upload parsing, reindexing, and readiness.
- F157 performance budgets for p95 latency, first stream event, and smoke error
  ratio.
- F158 observability dashboard signal contract. This is a dashboard spec, not a
  hosted dashboard renderer.
- F162 CI gates for backend tests, frontend build, Docker build, retrieval eval,
  PHI log scan, repo hygiene, and performance smoke.
- F173 deployment smoke command that prints the public URL, frontend status, API
  health, authenticated readiness/config/retrieval checks, and sanitized status
  details.

## Data-Driven Catalogs

Operational gates live in trusted knowledge files:

- `knowledge/operations/performance_budgets.json`
- `knowledge/operations/load_smoke_plan.json`
- `knowledge/operations/observability_dashboard.json`
- `knowledge/operations/release_gates.json`
- `knowledge/operations/deployment_smoke_plan.json`

Runtime API endpoints expose these catalogs to authenticated admins:

- `GET /api/v1/runtime/performance-budgets`
- `GET /api/v1/runtime/load-smoke-plan`
- `GET /api/v1/runtime/observability-dashboard`
- `GET /api/v1/runtime/release-gates`
- `GET /api/v1/runtime/deployment-smoke-plan`

## Performance Smoke

Run local ASGI smoke without a running server:

```bash
OJT_STORAGE_BACKEND=memory PYTHONPATH=src python scripts/performance-smoke.py --mode asgi
```

The smoke runner uses the public API routes and measures:

- workflow creation;
- retrieval search;
- assistant first stream event;
- small upload parse job;
- retrieval reindex job;
- runtime readiness.

The JSON mode is suitable for CI artifacts:

```bash
OJT_STORAGE_BACKEND=memory PYTHONPATH=src python scripts/performance-smoke.py --mode asgi --json
```

For a running API:

```bash
PYTHONPATH=src python scripts/performance-smoke.py \
  --mode http \
  --base-url "$OJT_API_URL" \
  --bearer-token "$OJT_SMOKE_BEARER_TOKEN"
```

## Deployment Smoke

Run against local or deployed services:

```bash
PYTHONPATH=src python scripts/deployment-smoke.py \
  --frontend-url "$OJT_FRONTEND_URL" \
  --api-url "$OJT_API_URL" \
  --public-url "$OJT_PUBLIC_URL" \
  --bearer-token "$OJT_SMOKE_BEARER_TOKEN"
```

The output begins with:

```text
OJTFlow deployment smoke
  Public URL: ...
```

Authenticated API checks fail unless `OJT_SMOKE_BEARER_TOKEN` or
`OJT_SMOKE_COOKIE` is provided. For local frontend/API-only checks, use
`--allow-missing-auth`; that mode is not release-candidate evidence.

## CI And Release Gates

`.github/workflows/ci.yml` now runs:

- backend tests;
- raw-PHI log scan;
- retrieval evaluation;
- performance smoke;
- frontend build;
- Docker API/frontend builds.

`scripts/release-check.sh` also runs performance smoke before frontend build and
Docker/E2E checks.

## Observability Contract

The observability dashboard spec defines required panels and signals for:

- API latency and error rate;
- workflow throughput and step duration;
- assistant streaming and tool errors;
- retrieval quality and freshness;
- background jobs;
- governance/security;
- LLM/OCR cost controls.

Remaining Month 8 observability work:

- wire OpenTelemetry spans;
- export metrics to a production backend;
- build or configure a hosted dashboard;
- add worker queue metrics when queue-backed jobs exist.

## Verification

```bash
OJT_STORAGE_BACKEND=memory PYTHONPATH=src pytest -q \
  tests/test_operations_readiness.py \
  tests/test_api.py::test_api_contract_doc_covers_current_route_surface \
  tests/test_api.py::test_api_v1_route_handlers_use_response_envelopes \
  tests/test_api.py::test_private_api_routes_have_auth_dependency \
  tests/test_api.py::test_runtime_routes_use_api_settings_dependency

OJT_STORAGE_BACKEND=memory PYTHONPATH=src python scripts/performance-smoke.py --mode asgi
PYTHONPATH=src python scripts/deployment-smoke.py --allow-missing-auth --json

PYTHONPATH=src python -m py_compile \
  src/ojtflow/core/contracts/operations.py \
  src/ojtflow/infrastructure/operations.py \
  src/ojtflow/interfaces/api/routes/runtime.py \
  scripts/performance-smoke.py \
  scripts/deployment-smoke.py
```
