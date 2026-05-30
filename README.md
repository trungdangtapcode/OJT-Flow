# OJTFlow

OJTFlow is a governed healthcare data workflow scaffold. The current implementation is the system backbone: typed contracts, deterministic data tools, workflow orchestration, review gates, audit events, static trusted knowledge, and FastAPI routes.

The product UI is a React/TypeScript operations console for both daily end users and B2B evaluators:

- Workbench for messy healthcare data intake.
- Workflow detail for status, steps, validation issues, review, output, explanation, evidence, and audit events.
- Review queue for pending human decisions.
- Schema registry read view.
- Audit and settings surfaces for B2B governance, integrations, and deployment posture.

## Architecture

The code follows a clean architecture shape:

```text
src/ojtflow/
  core/             pure contracts, enums, policies, errors
  data_tools/       deterministic parse/profile/validate/convert tools
  agents/           role-specific wrappers around deterministic services
  application/      workflow use cases and ports
  infrastructure/   Postgres, SQLite, in-memory, and static knowledge adapters
  interfaces/api/   FastAPI routes and request schemas
frontend/
  src/              React product UI and API client
  medical/          OCR/DICOM/visual evidence extension contracts
  mcp_servers/      planned MCP wrapper boundary
```

Dependency direction points inward to `core`. API, storage, retrieval, and future MCP/cloud/model integrations should be replaceable without changing domain contracts.

## Implemented Backbone

- Shared workflow state with status transitions.
- Append-only workflow event stream.
- Agent result contract.
- Issue, evidence, review, audit, and tool contracts.
- CSV/JSON/YAML format detection and parsing.
- Data profiling and schema validation.
- Conservative transformation plans that require review for semantic changes.
- Human review pause/resume flow.
- Google OAuth sign-in with Postgres-backed users/sessions and Redis session cache.
- Deterministic CSV-to-JSON conversion after approval.
- Evidence-grounded explanation report with medical intended-use limitation.
- Static trusted knowledge fixture for `lab_result_v1`.
- FastAPI routes for workflows, review, convert, validate, FHIR profile, OCR evidence, and health.
- React product console for workflow intake, review, schema, audit, and settings surfaces.

## Run Tests

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/tcuong1000/.ostwin/.venv/bin/python -m pytest
```

## Run With Docker

```bash
docker compose up --build
```

Use `docker-compose up --build` if your machine has Docker Compose v1.

This starts:

- `postgres` on `localhost:5432`
- `redis` on `localhost:6379`
- `api` on `localhost:8000`
- `frontend` on `localhost:5173`

The default backend storage is Postgres plus local file artifacts:

- `OJT_STORAGE_BACKEND=postgres`
- `OJT_DATABASE_URL=postgresql://ojtflow:ojtflow@localhost:5432/ojtflow`
- `OJT_REDIS_URL=redis://localhost:6379/0`
- `OJT_GOOGLE_CLIENT_ID=`
- `OJT_GOOGLE_CLIENT_SECRET=`
- `OJT_GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback`
- `OJT_GOOGLE_FRONTEND_REDIRECT_URI=http://localhost:5173/auth/callback`
- `OJT_AUTH_SESSION_TTL_SECONDS=604800`
- `OJT_AUTH_STATE_TTL_SECONDS=600`
- `OJT_DATA_DIR=var`
- `OJT_MAX_UPLOAD_BYTES=26214400`
- `OJT_UPLOAD_READ_CHUNK_BYTES=1048576`
- `OJT_ALLOWED_UPLOAD_EXTENSIONS=.pdf,.docx,.xlsx,.xls,.pptx,.png,.jpg,.jpeg,.tiff,.tif,.bmp,.gif,.webp,.html,.htm,.md,.txt,.csv,.json,.yaml,.yml`

The frontend proxies `/api/*` requests to the API container in Docker. No API keys or ADC credential files are committed; pass those through environment variables or mounted runtime credentials only.

## Document Upload Parsing

PR #1 adds upload parsing routes:

- `POST /api/v1/parse/extract`
- `POST /api/v1/parse/upload/workflow`
- `GET /api/v1/parse/extractors`
- `GET /api/v1/auth/google/url`
- `GET /api/v1/auth/google/callback`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/logout`

## Google OAuth Login

Create a Google OAuth client and set these callback URLs:

```text
http://localhost:8000/api/v1/auth/google/callback
http://localhost:5173/auth/callback
```

Then set:

```bash
OJT_GOOGLE_CLIENT_ID=...
OJT_GOOGLE_CLIENT_SECRET=...
OJT_GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
OJT_GOOGLE_FRONTEND_REDIRECT_URI=http://localhost:5173/auth/callback
```

Login flow:

1. The frontend calls `GET /api/v1/auth/google/url?redirect_uri=http://localhost:5173/auth/callback`.
2. Redirect the user to `data.authorization_url`.
3. Google redirects back to `/auth/callback` in the React app.
4. The backend creates/updates `ojtflow.users`, creates a hashed session in
   `ojtflow.sessions`, caches the session in Redis, and returns a bearer token.
5. Send `Authorization: Bearer <token>` to `GET /api/v1/auth/me` and
   `POST /api/v1/auth/logout`. The same header is required for workflow,
   parse, convert, validate, FHIR, and OCR API routes.

The API stores raw uploads as immutable artifacts and stores extracted markdown/text as derived artifacts for workflow parsing and review resume. Upload filenames, extensions, extractor names, empty files, and file sizes are validated server-side. See `docs/document_parsing_uploads.md` for supported extensions, dependency notes, and migration details.

## Run Frontend Locally Against API

Install and start the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

The local Vite server defaults to proxying API requests to `http://localhost:8000`. Override with:

```bash
VITE_API_PROXY_TARGET=http://127.0.0.1:8000 npm run dev
```

## Run API Locally Against Docker Postgres

Start Postgres:

```bash
docker compose up -d postgres
```

Use `docker-compose up -d postgres` if your machine has Docker Compose v1.

Run migrations:

```bash
PYTHONPATH=src /home/tcuong1000/.ostwin/.venv/bin/python -m ojtflow.infrastructure.storage.migrate
```

Run the API:

```bash
PYTHONPATH=src /home/tcuong1000/.ostwin/.venv/bin/python -m uvicorn ojtflow.interfaces.api.app:app --host 127.0.0.1 --port 8000
```

Use `OJT_STORAGE_BACKEND=sqlite` for a single-file local fallback, or
`OJT_STORAGE_BACKEND=memory` for short-lived tests.

Useful routes:

- `GET /health`
- `POST /api/v1/workflows`
- `GET /api/v1/workflows/{workflow_id}`
- `GET /api/v1/workflows/{workflow_id}/events`
- `GET /api/v1/reviews`
- `GET /api/v1/schemas`
- `POST /api/v1/review/{review_id}`
- `POST /api/v1/convert`
- `POST /api/v1/validate`
- `POST /api/v1/fhir/profile`
- `POST /api/v1/ocr/evidence`
- `POST /api/v1/parse/extract`
- `POST /api/v1/parse/upload/workflow`
- `GET /api/v1/parse/extractors`

## Golden Fixture

The main fixture is:

```text
data/fixtures/structured/lab_results_messy.csv
```

It proves the first vertical slice:

1. Parse a messy healthcare-style CSV.
2. Profile fields and detect sensitive identifiers.
3. Validate against `knowledge/schemas/lab_result_v1.schema.json`.
4. Flag missing values, date inconsistency, and PHI-like fields.
5. Pause for human review.
6. Resume after approval.
7. Convert to JSON.
8. Return explanation and audit events.
