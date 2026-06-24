# OJTFlow

OJTFlow is a governed healthcare data workflow scaffold. The current implementation is the system backbone: typed contracts, rule-based data tools, workflow orchestration, review gates, audit events, static trusted knowledge, and FastAPI routes.

The product UI is a React/TypeScript operations console for both daily end users and B2B evaluators:

- Workbench for messy healthcare data intake.
- Assistant for natural-language access to retrieval, validation, conversion,
  FHIR profiling, review/workflow inspection, and gated workflow creation.
- Workflow detail for status, steps, validation issues, review, output, explanation, evidence, and audit events.
- Retrieval console for trusted healthcare search, reindexing, ranking trace, and graph handoff inspection.
- Review queue for pending human decisions.
- Schema registry read view.
- Audit and settings surfaces for B2B governance, integrations, and deployment posture.

## Architecture

The code follows a clean architecture shape:

```text
src/ojtflow/
  core/             pure contracts, enums, policies, errors
  data_tools/       rule-based parse/profile/validate/convert tools
  agents/           role-specific wrappers around rule-based services
  application/      workflow use cases and ports
  infrastructure/   Postgres, in-memory test harness, and static knowledge adapters
  interfaces/api/   FastAPI routes and request schemas
  medical/          OCR/DICOM/visual evidence extension contracts
  mcp_servers/      local MCP wrappers for allowlisted OJTFlow tools
frontend/
  src/              React product UI and API client
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
- Google OAuth sign-in through auth ports, Postgres session storage,
  Redis session cache in Postgres deployments, and HTTP-only browser session cookies.
- Rule-based CSV-to-JSON conversion after approval.
- Evidence-grounded explanation report with medical intended-use limitation.
- Healthcare-aware RAG retrieval module with real semantic embeddings and
  Postgres pgvector similarity search as the production path.
- FastAPI routes for workflows, review, assistant chat, convert, validate, retrieval, FHIR profile, OCR evidence, and health.
- OpenAI Responses planner for assistant tool selection; missing or failed LLM
  planning raises an error instead of generating a local rule/template answer.
- Persisted Assistant chat sessions/messages for Postgres storage, with frontend session history, stream replay payloads, and workflow refs.
- Local MCP server wrappers for retrieval, validation, conversion, FHIR profiling, workflow reads, review reads, and gated workflow creation.
- Authenticated runtime diagnostics for sanitized configuration, readiness checks,
  migration ledger status, and bootstrap failure classification.
- Durable owner-scoped background jobs for operational work such as retrieval
  reindexing, with a sync local runner and a queue-ready contract.
- React product console for assistant commands, workflow intake, review, schema, audit, and settings surfaces.
- React retrieval console for direct evidence search, source inventory, and corpus reindexing.

## Run Tests

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest
python scripts/evaluate-retrieval.py
```

Run the real-browser Playwright suite against the Docker stack:

```bash
cd frontend
npm run e2e
```

See `docs/testing_strategy.md` for unit, integration, real-stack, and browser E2E scope.

Release evidence is tracked in `RELEASE_CANDIDATE.md` and
`docs/release_verification_matrix.md`. Keep those documents aligned with the
release script whenever backend contracts, storage, auth, retrieval, OCR/FHIR
handoffs, frontend behavior, or deployment checks change.
The release script also runs retrieval quality checks so search changes are
checked against known healthcare evidence cases before demo freeze.

Run the full local release check against the Docker stack:

```bash
PYTHON_BIN=python scripts/release-check.sh
```

The script runs backend tests, frontend build, Docker stack rebuild, runtime
asset freshness, browser E2E, E2E cleanup, a Postgres residue assertion for
Playwright test users/workflows, and git whitespace hygiene. Set
`PYTHON_BIN` to your active virtualenv Python when needed. Use
`OJT_RELEASE_CHECK_SKIP_DOCKER_BUILD=1` only when the stack is already rebuilt,
and `OJT_RELEASE_CHECK_SKIP_E2E=1` only for a narrow local compile/test pass.

## Run With Docker

```bash
docker compose up --build
```

Use `docker-compose up --build` if your machine has Docker Compose v1.

This starts:

- `postgres` on `localhost:15432` using the pgvector-capable Postgres image
- `redis` on `localhost:16379`
- `rabbitmq` AMQP on `localhost:15673`
- RabbitMQ Management UI on `localhost:15672`
- `api` on `localhost:18000`
- `frontend` on `localhost:15173`
- OCR/RAG/embedding/ingestion/export Celery workers
- optional GPU MedSigLIP image classification service on `localhost:18103`
- optional MedSigLIP Celery worker on the `medsiglip` queue
- Flower on `localhost:15555`
- Prometheus on `localhost:19090`
- Grafana on `localhost:13000`
- Loki on `localhost:13100`

Those host ports are local defaults. Override them with
`OJT_POSTGRES_PORT`, `OJT_REDIS_PORT`, `OJT_RABBITMQ_AMQP_PORT`,
`OJT_RABBITMQ_MANAGEMENT_PORT`, `OJT_API_PORT`, `OJT_FRONTEND_PORT`,
`OJT_FLOWER_PORT`, `OJT_PROMETHEUS_PORT`, `OJT_GRAFANA_PORT`, and
`OJT_LOKI_PORT` when running beside existing services. The Compose
Postgres container also accepts `OJT_POSTGRES_DB`, `OJT_POSTGRES_USER`, and
`OJT_POSTGRES_PASSWORD`; the API container DSN is derived from those Compose
settings and points at the internal `postgres` service.

Compose health checks verify Postgres, Redis, RabbitMQ, API `/health`, and
frontend serving readiness. The frontend waits for the API health check before starting.
The Docker frontend is a built static React bundle exposed on host port `15173`
with nginx listening on container port `5173`; nginx preserves SPA routes and
proxies `/api/*` plus `/health` to the API container.

Long-running parse/OCR/RAG jobs are queue-backed in Compose. The API creates a
durable Postgres `background_jobs` record and dispatches work to RabbitMQ/Celery;
workers write status, trace output, or structured errors back to Postgres.
Scanned PDF/image OCR therefore returns a job for polling instead of blocking
the request thread. Use `/api/v1/jobs/{job_id}` for status, Flower for task
inspection, RabbitMQ Management UI for queue/consumer state, Prometheus/Grafana
for metrics, and Loki for container logs. Configure `OJT_SENTRY_DSN` to send
API and worker exceptions to Sentry without exposing secrets.

Run the GPU-backed MedSigLIP service after accepting the model terms on
Hugging Face and setting `HF_TOKEN` or `HUGGING_FACE_HUB_TOKEN`:

```bash
docker compose --profile medsiglip up --build medsiglip worker-medsiglip prometheus grafana
```

The model service loads `google/medsiglip-448` on CUDA by default and exposes
`/health`, `/classify`, and `/metrics`. The main API exposes authenticated
`/api/v1/medsiglip/status`, `/api/v1/medsiglip/classify`, and
`/api/v1/medsiglip/classification-jobs`; queued jobs are polled through the
standard `/api/v1/jobs/{job_id}` endpoint. Prometheus scrapes the MedSigLIP
service plus NVIDIA DCGM metrics, and the Grafana overview dashboard includes
MedSigLIP latency, throughput, queue depth, and GPU utilization panels.

The API applies pending Postgres migrations automatically when the Postgres
storage adapters are constructed. The explicit migration command remains useful
for CI, release checks, and inspecting pending migration output, but it is not a
separate required step for `docker compose up`.

The API image installs Python dependencies with `constraints.txt` so Docker
rebuilds of the same commit resolve to the same runtime dependency versions.
The image includes the `ojtflow[parsing]` extra by default, which enables
MarkItDown-backed PDF, DOCX, XLSX/XLS, and PPTX extraction in the local Compose
runtime. Set `OJT_PYTHON_EXTRAS=parsing,embeddings-local` before building the
API image when Docker should include local SentenceTransformers embeddings and
CrossEncoder reranking. Add `rag-framework` when Docker should include the
optional LlamaIndex retrieval adapter. Keep `pyproject.toml` ranges compatible
for local development, and refresh `constraints.txt` only after the full release
check passes.

The default backend storage is Postgres plus local file artifacts:

- `OJT_STORAGE_BACKEND=postgres`
- `OJT_PRODUCT_MODE=local_dev`
- `OJT_NO_MOCK_DATA=false`
- `OJT_DATABASE_URL=postgresql://ojtflow:ojtflow@localhost:15432/ojtflow`
- `OJT_REDIS_URL=redis://localhost:16379/0`
- `OJT_GOOGLE_CLIENT_ID=`
- `OJT_GOOGLE_CLIENT_SECRET=`
- `OJT_GOOGLE_REDIRECT_URI=http://localhost:18000/api/v1/auth/google/callback`
- `OJT_GOOGLE_FRONTEND_REDIRECT_URI=http://localhost:15173/auth/callback`
- `OJT_ALLOWED_AUTH_REDIRECT_URIS=`
- `OJT_ALLOWED_GOOGLE_HOSTED_DOMAINS=`
- `OJT_GOOGLE_OAUTH_TIMEOUT_SECONDS=10.0`
- `OJT_AUTH_SESSION_TTL_SECONDS=604800`
- `OJT_AUTH_STATE_TTL_SECONDS=600`
- `OJT_AUTH_COOKIE_NAME=ojtflow_session`
- `OJT_AUTH_COOKIE_SECURE=false`
- `OJT_AUTH_COOKIE_SAMESITE=lax`
- `OJT_AUTH_COOKIE_DOMAIN=`
- `OJT_DATA_DIR=var`
- `OJT_KNOWLEDGE_DIR=knowledge`
- `OJT_MIGRATIONS_DIR=sql/postgres/migrations`
- `OJT_MAX_UPLOAD_BYTES=26214400`
- `OJT_MAX_INLINE_DATA_BYTES=1048576`
- `OJT_UPLOAD_READ_CHUNK_BYTES=1048576`
- `OJT_ALLOWED_UPLOAD_EXTENSIONS=.pdf,.docx,.xlsx,.xls,.pptx,.png,.jpg,.jpeg,.tiff,.tif,.bmp,.gif,.webp,.html,.htm,.md,.txt,.csv,.json,.yaml,.yml`
- `OJT_EMBEDDING_PROVIDER=openai`
- `OJT_EMBEDDING_MODEL=text-embedding-3-small`
- `OJT_EMBEDDING_DIMENSIONS=384`
- `OJT_PYTHON_EXTRAS=parsing`
- `OJT_OPENAI_API_KEY=` or `OPENAI_API_KEY=`
- `OJT_OPENAI_EMBEDDING_BASE_URL=https://api.openai.com/v1`
- `OJT_OPENAI_EMBEDDING_TIMEOUT_SECONDS=20.0`
- `OJT_LLM_PROVIDER=disabled`
- `OJT_LLM_MODEL=chat-latest`
- `OJT_LLM_BASE_URL=https://api.openai.com/v1`
- `OJT_LLM_TIMEOUT_SECONDS=30.0`
- `OJT_LLM_MAX_TOOL_CALLS=4`
- `OJT_RERANK_PROVIDER=none`
- `OJT_RERANK_MODEL=BAAI/bge-reranker-base`
- `OJT_RERANK_DEVICE=auto`
- `OJT_RERANK_BATCH_SIZE=16`
- `OJT_RERANK_CANDIDATE_LIMIT=20`
- `OJT_RERANK_SCORE_WEIGHT=0.08`
- `OJT_MEDSIGLIP_ENABLED=true`
- `OJT_MEDSIGLIP_BASE_URL=http://localhost:18103`
- `OJT_MEDSIGLIP_DOCKER_BASE_URL=http://medsiglip:8000`
- `OJT_MEDSIGLIP_MODEL=google/medsiglip-448`
- `OJT_MEDSIGLIP_PORT=18103`
- `OJT_MEDSIGLIP_GPU=0`
- `OJT_MEDSIGLIP_DEVICE=cuda`
- `OJT_MEDSIGLIP_REQUIRE_GPU=true`
- `OJT_MEDSIGLIP_TIMEOUT_SECONDS=90.0`
- `OJT_MEDSIGLIP_QUEUE=medsiglip`
- `HF_TOKEN=` or `HUGGING_FACE_HUB_TOKEN=`
- `OJT_RETRIEVAL_DIVERSITY_ENABLED=true`
- `OJT_RETRIEVAL_DIVERSITY_LAMBDA=0.72`

`OJT_STORAGE_BACKEND=postgres` is the supported runtime storage configuration.
The in-memory backend is reserved for isolated in-process tests and cannot serve
production RAG.
`OJT_PRODUCT_MODE` must be `local_dev`, `demo`, `pilot`, or `production`.
Pilot and production modes require Postgres pgvector storage, real semantic
embeddings, and a real Assistant LLM provider. Missing embedding provider,
missing embedding model, missing OpenAI key for OpenAI embeddings,
`OJT_LLM_PROVIDER=disabled`, non-Postgres storage, lexical retrieval mode, and
fake/hash provider names are rejected during settings load. `OJT_NO_MOCK_DATA=true`
explicitly blocks demo/mock data paths, and it is effectively enabled in pilot
and production modes.
`OJT_DATABASE_URL` must use `postgres://` or `postgresql://` syntax with a host,
optional numeric port, and database name.
`OJT_REDIS_URL` may be blank only to mark Redis as not configured; otherwise it
must use `redis://`, `rediss://`, or `unix://` syntax with valid host/port or
socket-path components.

Numeric runtime settings for OAuth timeout, auth TTLs, upload limits, read
chunk size, and inline payload limit must be positive.
The API validates them at startup so a broken deployment fails before it starts
accepting workflow traffic.

`OJT_KNOWLEDGE_DIR` points at trusted schemas, data dictionaries, governance
rules, and retrieval seed documents. `OJT_MIGRATIONS_DIR` points at ordered
Postgres SQL migrations. Relative values resolve from the project root in local
development; container deployments set absolute `/app/...` paths so installed
Python package locations do not control runtime data discovery. The migrations
directory must exist and contain ordered `.sql` files, otherwise Postgres
startup fails before serving traffic.
Named `schema_id` values are also strict: callers must use a schema returned by
`GET /api/v1/schemas`. Set `schema_id` to `null` for explicit no-schema
validation. A missing requested schema returns a structured `not_found` error
instead of silently weakening validation.

`OJT_ALLOWED_UPLOAD_EXTENSIONS` may narrow the built-in supported upload
extensions. Values may include or omit the leading dot, are normalized to
lowercase, and must be simple supported suffixes such as `.csv` or `.pdf`.
Unsupported or unsafe values such as `.exe`, `.tar.gz`, paths, wildcards, or
extensions containing spaces are rejected during settings load.

`OJT_EMBEDDING_PROVIDER` supports real semantic providers only: `openai` and
`huggingface`. Fake, mock, rule-based, hash, lexical, keyword, random, or
test providers are rejected. OpenAI mode uses the Embeddings API with
`OJT_OPENAI_API_KEY`, falling back to `OPENAI_API_KEY` when the project-specific
variable is not set. Recommended production semantic retrieval settings are:

```text
OJT_EMBEDDING_PROVIDER=openai
OJT_EMBEDDING_MODEL=text-embedding-3-small
OJT_EMBEDDING_DIMENSIONS=384
OJT_RETRIEVAL_MODE=semantic_vector
OJT_RETRIEVAL_FRAMEWORK=custom
```

For local GPU retrieval, install the optional dependency group and use:

```bash
uv pip install -e '.[embeddings-local]'
```

For Docker GPU/local-model runs, build the API image with the same optional
dependency group included:

```bash
OJT_PYTHON_EXTRAS=parsing,embeddings-local docker compose build api
```

```text
OJT_EMBEDDING_PROVIDER=huggingface
OJT_EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
OJT_EMBEDDING_DIMENSIONS=384
OJT_HF_EMBEDDING_DEVICE=cuda
```

The Postgres semantic vector schema uses `embedding vector(384)`. Production
RAG embeds the query with the configured real provider and queries pgvector with
`embedding <=> query_vector`. If pgvector is unavailable, dimensions mismatch,
indexed vectors are missing, or index metadata belongs to a different provider
generation, the request fails with a clear unavailable error. It does not fall
back to full-text search, BM25, token matching, JSON/Python vector reranking, or
keyword retrieval. Operator-provided trusted corpus files are indexed from
`OJT_RETRIEVAL_CORPUS_DIRS` and can be refreshed through
`POST /api/v1/retrieval/reindex`.

The native retrieval adapter remains the production default:

```text
OJT_RETRIEVAL_MODE=semantic_vector
OJT_RETRIEVAL_FRAMEWORK=custom
```

See `docs/production_semantic_rag.md` for the production fail-fast policy,
provider setup, vector index requirements, reindex command, and guardrail check.

For framework-backed RAG experiments, install or build the LlamaIndex extra:

```bash
uv pip install -e '.[rag-framework]'
OJT_PYTHON_EXTRAS=parsing,rag-framework docker compose build api
```

Then opt in for non-production framework evaluation:

```text
OJT_RETRIEVAL_FRAMEWORK=llamaindex
OJT_RETRIEVAL_CANDIDATE_MULTIPLIER=4
OJT_RETRIEVAL_MIN_CANDIDATES=12
OJT_RETRIEVAL_VECTOR_WEIGHT=0.62
OJT_RETRIEVAL_BM25_WEIGHT=0.38
```

That adapter uses LlamaIndex Documents/Nodes, `SentenceSplitter`,
`VectorStoreIndex`, and `QueryFusionRetriever`. When
`llama-index-retrievers-bm25` is installed, BM25 can be a secondary signal after
semantic vector retrieval. It is not the production/default RAG path, and BM25
must not replace pgvector semantic retrieval. The API response shape stays the
same because the framework is isolated behind the existing retrieval repository
port.

Retrieval runtime controls can also be changed from the Settings page or
`PUT /api/v1/runtime/retrieval-settings`. The backend validates the requested
values, writes them to `OJT_RUNTIME_SETTINGS_PATH`, clears cached settings and
service instances, then reloads the retrieval repository with the new
framework/candidate/fusion/diversity settings.

Second-stage reranking is opt-in. The first stage retrieves a broader candidate
set with lexical, vector, and reciprocal-rank-fusion signals. When
`OJT_RERANK_PROVIDER=huggingface`, the backend applies a SentenceTransformers
CrossEncoder over the top `OJT_RERANK_CANDIDATE_LIMIT` candidates and adds a
bounded `OJT_RERANK_SCORE_WEIGHT` contribution to the transparent
`rerank_score`. Use this when local GPU is available and relevance quality is
more important than the extra model latency:

```text
OJT_RERANK_PROVIDER=huggingface
OJT_RERANK_MODEL=BAAI/bge-reranker-base
OJT_RERANK_DEVICE=cuda
OJT_RERANK_BATCH_SIZE=16
OJT_RERANK_CANDIDATE_LIMIT=20
OJT_RERANK_SCORE_WEIGHT=0.08
```

Final selection uses source-aware MMR by default to avoid returning only
near-duplicate chunks from one source. `OJT_RETRIEVAL_DIVERSITY_LAMBDA` controls
the relevance/novelty balance from `0` to `1`; the default `0.72` keeps
relevance dominant while improving selected source coverage.

The frontend container proxies `/api/*` and `/health` requests to the API
container in Docker. No API keys or ADC credential files are committed; pass
those through environment variables or mounted runtime credentials only.

## Document Upload Parsing

Upload parsing routes:

- `POST /api/v1/parse/extract`
- `POST /api/v1/parse/upload/workflow`
- `GET /api/v1/parse/extractors`
- `GET /api/v1/auth/google/url`
- `GET /api/v1/auth/google/callback`
- `GET /api/v1/auth/me`
- `GET /api/v1/auth/service-accounts`
- `POST /api/v1/auth/service-accounts`
- `POST /api/v1/auth/service-accounts/{account_id}/tokens`
- `GET /api/v1/assistant/sessions/{session_id}/stream-replays`
- `GET /api/v1/runtime/config`
- `GET /api/v1/runtime/readiness`
- `GET /api/v1/runtime/migrations`
- `GET /api/v1/runtime/storage-consistency`
- `GET /api/v1/runtime/storage-repair-plan`
- `POST /api/v1/runtime/storage-repair-markers`
- `PUT /api/v1/runtime/retrieval-settings`
- `POST /api/v1/auth/logout`

## Google OAuth Login

Create a Google OAuth client and set these callback URLs:

```text
http://localhost:18000/api/v1/auth/google/callback
http://localhost:15173/auth/callback
```

Then set:

```bash
OJT_GOOGLE_CLIENT_ID=...
OJT_GOOGLE_CLIENT_SECRET=...
OJT_GOOGLE_REDIRECT_URI=http://localhost:18000/api/v1/auth/google/callback
OJT_GOOGLE_FRONTEND_REDIRECT_URI=http://localhost:15173/auth/callback
```

Login flow:

1. The frontend calls `GET /api/v1/auth/google/url?redirect_uri=http://localhost:15173/auth/callback`.
2. Redirect the user to `data.authorization_url`.
3. Google redirects back to `/auth/callback` in the React app.
4. The backend creates/updates `ojtflow.users`, creates a hashed session in
   `ojtflow.sessions`, caches the session when a cache backend is configured,
   returns a bearer token for API clients, and sets an HTTP-only session cookie
   for the browser UI.
5. Browser calls use the session cookie automatically. API clients can still
   send `Authorization: Bearer <token>` to `GET /api/v1/auth/me`,
   `POST /api/v1/auth/logout`, and the protected workflow, parse, convert,
   validate, FHIR, and OCR routes.

Use `OJT_ALLOWED_AUTH_REDIRECT_URIS` to add deployment callback URLs beyond the
two local defaults. OAuth redirect URIs must use `http` or `https`; non-local
HTTP callbacks must use HTTPS. Redirect URIs with fragments, embedded user info,
missing hosts, or non-web schemes are rejected during settings load. Use
`OJT_ALLOWED_GOOGLE_HOSTED_DOMAINS` to restrict sign-in to one or more Google
Workspace domains. Hosted-domain allowlists and `OJT_AUTH_COOKIE_DOMAIN` must
be bare DNS domains. URLs, ports, wildcards, spaces, IP addresses, and localhost
are rejected; omit OJT_AUTH_COOKIE_DOMAIN for localhost development.

See `docs/auth_architecture.md` for the auth port/adapters, storage matrix, and
browser session transport.

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
http://localhost:15173
```

The local Vite server defaults to proxying API requests to `http://localhost:18000`. Override with:

```bash
VITE_API_PROXY_TARGET=http://127.0.0.1:18000 npm run dev
```

When using the Docker frontend, verify the running container is serving the same
hashed assets as the freshly built Docker image:

```bash
docker compose up -d --build frontend
(cd frontend && npm run runtime:assert-current)
```

If the check reports stale runtime assets, rebuild the frontend image:

```bash
docker compose up -d --build frontend
```

## Run API Locally Against Docker Postgres

Start Postgres:

```bash
docker compose up -d postgres
```

Use `docker-compose up -d postgres` if your machine has Docker Compose v1.

Optional: run migrations explicitly before starting the API or in CI:

```bash
PYTHONPATH=src python -m ojtflow.infrastructure.storage.migrate
```

Run the API:

```bash
PYTHONPATH=src python -m uvicorn ojtflow.interfaces.api.app:app --host 127.0.0.1 --port 18000
```

Use `OJT_STORAGE_BACKEND=postgres` for local and deployed API runtime. The
in-memory backend is reserved for short-lived in-process tests; invalid values,
including `sqlite`, fail during settings load.

Useful routes:

- `GET /health` raw liveness probe for Docker/load balancers
- `POST /api/v1/workflows`
- `GET /api/v1/workflows/{workflow_id}`
- `GET /api/v1/workflows/{workflow_id}/events`
- `GET /api/v1/assistant/sessions/{session_id}/stream-replays`
- `GET /api/v1/reviews`
- `GET /api/v1/schemas`
- `POST /api/v1/review/{review_id}`
- `POST /api/v1/convert`
- `POST /api/v1/validate`
- `POST /api/v1/fhir/profile`
- `POST /api/v1/ocr/evidence`
- `GET /api/v1/runtime/storage-consistency`
- `GET /api/v1/runtime/storage-repair-plan`
- `POST /api/v1/runtime/storage-repair-markers`
- `POST /api/v1/retrieval/search`
- `POST /api/v1/retrieval/reindex`
- `GET /api/v1/retrieval/sources`
- `GET /api/v1/jobs`
- `GET /api/v1/jobs/{job_id}`
- `POST /api/v1/jobs/retrieval-reindex`
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
