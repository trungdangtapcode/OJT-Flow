# OJTFlow v0 Release Candidate Checklist

Status: backend, API, retrieval, auth, storage, and frontend console are hardened
for a local demo release candidate.

Last full local gate: passed on 2026-06-04 01:32 UTC using the active
virtualenv Python and `scripts/release-check.sh`.

This file is a source-controlled freeze checklist, not a git tag. Treat a
release candidate as valid only after the full local release gate passes on the
current worktree.

Detailed evidence mapping lives in `docs/release_verification_matrix.md`.

## Required Gate

Run:

```bash
PYTHON_BIN=python scripts/release-check.sh
```

Set `PYTHON_BIN` to the active virtualenv Python when needed. The gate must
complete all steps successfully:

- [x] Python test suite.
- [x] Frontend TypeScript/Vite production build.
- [x] Docker stack rebuild for API, frontend, Postgres, and Redis.
- [x] Runtime frontend asset freshness check.
- [x] Browser Playwright E2E suite.
- [x] E2E artifact cleanup.
- [x] Postgres residue assertion for Playwright users/workflows.
- [x] Local Playwright report cleanup after successful E2E.
- [x] Git whitespace/conflict-marker hygiene.

## System Readiness

- [x] FastAPI app imports and registers all documented `/api/v1` routes.
- [x] All protected API routes require an authenticated backend session.
- [x] Public API routes return `{data, error}` envelopes except raw `GET /health`.
- [x] Unauthorized, validation, upload, policy, not-found, and unhandled errors
      return structured error envelopes without stack traces or secrets.
- [x] Runtime diagnostics return sanitized configuration and readiness checks.
- [x] `docs/api_contract_v0.md` covers the current route surface.
- [x] `docs/demo_backend_flow.md` describes the exact demo scenario.
- [x] `docs/testing_strategy.md` documents unit, integration, Docker, and
      browser E2E coverage.

## Persistence And Isolation

- [x] Postgres is the default production-like storage backend.
- [x] SQLite fallback remains available for local single-file runs.
- [x] Memory storage is limited to tests and short-lived demos.
- [x] Postgres migrations apply automatically when repositories are constructed.
- [x] Workflow, event, review, evidence, and dataset state survive service restart.
- [x] Input and output artifacts are stored under the configured data directory.
- [x] Public API responses redact local `file://` refs to opaque artifact handles.
- [x] Output reads verify recorded artifact hashes before serving content.
- [x] Review approval verifies input artifact hashes before resuming.
- [x] Workflow, review, event, summary, stats, retrieval-with-workflow, and output
      access are scoped to the authenticated owner.

## Healthcare Workflow Scope

- [x] Parser/converter/validation support deterministic CSV, JSON, and YAML.
- [x] CSV reports malformed rows, missing cells, extra cells, and source rows.
- [x] Conversion metadata includes source/target formats, row counts, output hash,
      lossiness, warnings, and applied actions.
- [x] Validation flags missing fields, type mismatches, malformed rows, date
      issues, missing units, sensitive/PHI-like fields, and prompt-injection
      patterns.
- [x] `lab_result_v1` remains the demo schema for healthcare lab-result records.
- [x] FHIR-like profiling detects `resourceType` and `Bundle.entry` shapes and
      emits handoff context without claiming full HL7 validation.
- [x] OCR evidence endpoint normalizes page/field/value/bounding-box/confidence
      payloads into evidence and gates low-confidence fields for review.
- [x] Graph-NER/RAG emits an auditable GraphRAG-lite handoff; do not claim clinical decision support
      or LLM retrieval agent until implemented and tested.

## Retrieval Readiness

- [x] Retrieval uses trusted healthcare knowledge inventory.
- [x] Postgres mode uses full-text search, deterministic vector scoring, fusion,
      and reranking where seeded data is available.
- [x] Retrieval traces expose strategy, query variants, filters, selected IDs,
      candidate counts, safety flags, and warnings.
- [x] Runtime readiness probes retrieval through the same service path used by
      workflows.
- [x] Retrieval query context is treated as data and flags prompt-injection or
      sensitive-field context.

## Frontend Readiness

- [x] Docker frontend serves a built static React bundle through nginx.
- [x] Frontend API calls stay behind the `src/api.ts` boundary.
- [x] Feature modules do not import sibling features directly.
- [x] Browser storage and direct cookie access are not used for auth/session state.
- [x] Session loss clears server-state cache and returns to the login gate.
- [x] Desktop and mobile route matrix has no horizontal page overflow.
- [x] Interactive controls are not clipped and maintain mobile tap targets.
- [x] Workflow queue, review queue, evidence, output, audit, schema, and settings
      surfaces are covered by real-browser E2E.
- [x] Google OAuth handoff reaches Google in-browser; human consent completion is
      manual and not automated with committed credentials.

## Secret And Artifact Hygiene

- [x] `.env` and `.env.*` remain ignored except `.env.example`.
- [x] Google OAuth, ADC, service-account, key, and certificate filenames remain
      ignored by git and Docker build contexts.
- [x] `plan/` is ignored and not tracked as source.
- [x] `var/`, `tmp/`, Playwright reports, frontend build outputs, bytecode,
      local screenshots, and LaTeX build artifacts remain ignored.
- [x] Source tree contains no committed OAuth client secrets, API tokens,
      private keys, local machine paths, or ADC material.
- [x] No secret, DSN password, local filesystem path, or stack trace appears in
      public runtime config/readiness/error responses.

## Freeze Rule

After this release candidate, changes should be limited to:

- correctness bugs
- failing test fixes
- documentation corrections
- demo-blocking reliability issues
- security or data-isolation fixes

Do not add new advanced AI modules, new model providers, or broad UI redesigns
on the demo branch until the release candidate is merged or explicitly reopened.
