# Testing Strategy

OJTFlow uses layered tests because the backend has separate risks at each boundary.

## Test Layers

1. Unit tests validate deterministic domain behavior without network or database state:
   parser/converter behavior, validation issues, retrieval ranking contracts, settings parsing,
   service state transitions, and storage adapter invariants.
2. Integration tests validate real adapter wiring:
   Postgres migrations, SQLite restart behavior, repository persistence, API response envelopes,
   auth session storage, and workflow/review round trips.
   Frontend architecture tests also run here because they validate source-level
   boundaries that keep features behind the API/server-state layer and prevent
   browser storage from becoming hidden auth or workflow state.
3. Real-stack smoke tests validate Docker runtime behavior:
   containers, Postgres extensions, Redis connectivity, migrations, API routes,
   and frontend serving. Source-level Docker runtime tests guard that the
   frontend image serves a built static bundle through nginx rather than a Vite
   development server.
4. Browser E2E tests validate the user-visible product flow:
   a real Chromium page signs in with a backend session cookie, creates a workflow, sees retrieval
   evidence, approves review, and verifies output/explanation/audit UI.

## Browser E2E Scope

The Playwright suite lives in `frontend/e2e`.

It covers:

- Authenticated app bootstrap through the same HTTP-only session cookie path used by the browser.
- Browser logout through the UI, including backend session revocation, cookie clearing,
  and return to the sign-in gate.
- Unauthenticated sign-in gate content, including one Google OAuth action, API/session/scope
  context, and the access-boundary heading used by the login surface.
- Runtime session expiry handling: if a session is revoked while the app is
  open, the next protected request clears React Query server-state cache and
  removes protected workflow UI.
- Workbench workflow creation through the Vite frontend and FastAPI proxy.
- Retrieval-backed workflow evidence using Postgres full-text/vector retrieval.
- Human review approval and completed output state in the UI.
- Server-backed workflow queue sorting and pagination request wiring.
- Desktop and mobile viewport containment across `/workflows`, `/reviews`,
  `/workbench`, `/audit`, `/schemas`, and `/settings` using both body and
  document scroll width checks, so wide tables or navigation cannot silently
  reintroduce horizontal page overflow.
- Direct workflow detail tabs on mobile, including the retrieval Evidence tab
  at a 320 px viewport. This protects against long workflow IDs, retrieval
  strategy names, evidence source IDs, and tab labels forcing horizontal
  overflow inside the detail inspector.
- Route-wide UI integrity checks for visible runtime error tokens and clipped
  interactive controls across the same desktop and mobile route matrix. This
  turns the manual screenshot audit into a permanent regression gate for the
  enterprise console.
- Authenticated shell accessibility checks: exactly one active navigation item
  exposes `aria-current="page"`, all icon-only navigation entries keep
  accessible labels, and mobile/narrow navigation plus header action targets
  stay at least 44 px in each tap dimension.
- Mobile tab target checks: visible workflow/detail tab triggers also stay at
  least 44 px in each tap dimension, using the same product standard as shell
  navigation. This is stricter than WCAG 2.2 AA's 24 px minimum and protects
  dense review/evidence tabs on narrow clinical-workflow screens.
- Google OAuth handoff from the real browser to `accounts.google.com`.

The OAuth test intentionally stops at Google. The app can generate the OAuth URL and navigate to
Google, but completing consent requires a real human Google account session and should not be
automated with committed credentials.

Loading-state tests should gate network routes with explicit release promises
or `waitForResponse` assertions. Do not use fixed browser sleeps such as
`waitForTimeout` or delayed `setTimeout` route handlers; those hide races and
make the Docker E2E gate dependent on local timing.

Workflow-creating E2E tests register the workflow IDs they create and delete
those workflow rows, review rows, events, evidence rows, dataset rows, local
dataset files, and synthetic Playwright auth users/sessions after each test.
That keeps repeated browser runs from polluting the local Postgres dashboard
with test workflow or auth-session noise.

## Run

Run the full local release check:

```bash
PYTHON_BIN=python scripts/release-check.sh
```

The script runs backend tests, frontend build, Docker stack rebuild, runtime
asset freshness, browser E2E, E2E cleanup, a Postgres residue assertion for
Playwright test users/workflows, successful-run local Playwright report cleanup,
and both `git diff --check` and `git diff --cached --check`. Set
`PYTHON_BIN` to your active virtualenv Python when needed. Use
`OJT_RELEASE_CHECK_SKIP_DOCKER_BUILD=1` only if the Docker stack is already
rebuilt from the current source, and `OJT_RELEASE_CHECK_SKIP_E2E=1` only for a
narrow local compile/test pass.

Start the real stack:

```bash
docker compose up -d --build
```

The API applies pending Postgres migrations automatically on startup. Run
`docker compose exec -T api python -m ojtflow.infrastructure.storage.migrate`
as an additional release check when you want explicit migration output.

Run backend tests:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest
```

Run browser E2E:

```bash
cd frontend
npm run runtime:assert-current
npm run e2e:install
npm run e2e
```

`runtime:assert-current` compares the built `med-frontend` Docker image with
the index served by the Docker frontend at `OJT_RUNTIME_BASE_URL` or
`http://localhost:5173`. It catches stale nginx containers whose hashed asset
names no longer match the image produced by the current Docker build. Rebuild
with `docker compose up -d --build frontend` when this check fails. Override
the expected image with `OJT_EXPECTED_FRONTEND_IMAGE`, or compare against a
host-local build with `OJT_EXPECTED_FRONTEND_INDEX=dist/index.html` when needed.

Clean interrupted-run E2E residue:

```bash
cd frontend
npm run e2e:cleanup
```

The cleanup command emits parseable JSON with deleted workflow, dataset,
event, review, evidence, dataset-file, auth-session, and auth-user counts.
It removes Postgres users whose `google_sub` starts with `playwright-`, which
covers both normal E2E sessions (`playwright-e2e-*`) and ad hoc browser or
visual audit sessions created during manual verification.
The release check then queries Postgres from the API container and fails if
any workflow marked with the `Playwright E2E:` instruction prefix or any
`playwright-*` user remains.
When browser E2E succeeds, release check also removes local `frontend/test-results`
and `frontend/playwright-report` output. When browser E2E fails, those local
artifacts are intentionally preserved for trace and screenshot debugging.

Use headed mode when debugging:

```bash
cd frontend
npm run e2e:headed
```

`OJT_E2E_BASE_URL` defaults to `http://localhost:5173` so the browser callback
matches the local Google OAuth redirect URI. `OJT_E2E_SESSION_TOKEN`
can be supplied to reuse an existing backend session; otherwise the E2E helper
creates a temporary Postgres-backed session through the API container. Reused
sessions are not cleaned by the E2E suite because they are externally owned.
