# OJTFlow API Contract v0

All `/api/v1` endpoints return the same envelope:

```json
{
  "data": {},
  "error": null
}
```

The operational liveness probe `GET /health` is intentionally outside
`/api/v1` and returns raw JSON (`{"status":"ok"}`) for Docker, load balancers,
and simple uptime checks.

All `/api/v1` workflow/data endpoints require an authenticated backend session.
Browser clients use the HTTP-only session cookie set by the Google callback.
API clients may use:

```text
Authorization: Bearer <access_token>
```

The exceptions are `GET /api/v1/auth/google/url` and
`GET /api/v1/auth/google/callback`, which are used to obtain the token.

Cookie-authenticated write requests (`POST`, `PUT`, `PATCH`, and `DELETE`) must
include a trusted `Origin` or `Referer` header. Trusted origins come from the
current API origin and configured OAuth redirect URIs. Bearer-token API clients
are not subject to this cookie-origin guard.

Workflow, review, event, output, summary, and stats endpoints are scoped to the
authenticated user. `POST /api/v1/workflows` and
`POST /api/v1/parse/upload/workflow` persist `WorkflowState.owner_user_id`
from the backend session; clients cannot set or override ownership. A workflow
owned by another user returns the standard `not_found` envelope rather than
revealing that the ID exists.

Default persistence uses Postgres plus local file-backed artifacts:

```text
OJT_STORAGE_BACKEND=postgres
OJT_DATABASE_URL=postgresql://ojtflow:ojtflow@localhost:5432/ojtflow
OJT_REDIS_URL=redis://localhost:6379/0
OJT_DATA_DIR=var
OJT_KNOWLEDGE_DIR=knowledge
OJT_MIGRATIONS_DIR=sql/postgres/migrations
OJT_AUTH_COOKIE_NAME=ojtflow_session
OJT_AUTH_COOKIE_SAMESITE=lax
OJT_MAX_UPLOAD_BYTES=26214400
OJT_MAX_INLINE_DATA_BYTES=1048576
OJT_UPLOAD_READ_CHUNK_BYTES=1048576
OJT_ALLOWED_UPLOAD_EXTENSIONS=.pdf,.docx,.xlsx,.xls,.pptx,.png,.jpg,.jpeg,.tiff,.tif,.bmp,.gif,.webp,.html,.htm,.md,.txt,.csv,.json,.yaml,.yml
OJT_EMBEDDING_PROVIDER=deterministic
OJT_EMBEDDING_MODEL=deterministic-hash-v0
OJT_EMBEDDING_DIMENSIONS=64
OJT_OPENAI_API_KEY=
OJT_OPENAI_EMBEDDING_BASE_URL=https://api.openai.com/v1
OJT_OPENAI_EMBEDDING_TIMEOUT_SECONDS=20.0
OJT_LLM_PROVIDER=disabled
OJT_LLM_MODEL=chat-latest
OJT_LLM_BASE_URL=https://api.openai.com/v1
OJT_LLM_TIMEOUT_SECONDS=30.0
OJT_LLM_MAX_TOOL_CALLS=4
OJT_HF_EMBEDDING_DEVICE=auto
OJT_HF_EMBEDDING_BATCH_SIZE=32
OJT_HF_EMBEDDING_CACHE_DIR=var/huggingface
OJT_PYTHON_EXTRAS=parsing
OJT_RERANK_PROVIDER=none
OJT_RERANK_MODEL=BAAI/bge-reranker-base
OJT_RERANK_DEVICE=auto
OJT_RERANK_BATCH_SIZE=16
OJT_RERANK_CANDIDATE_LIMIT=20
OJT_RERANK_SCORE_WEIGHT=0.08
OJT_RETRIEVAL_CORPUS_DIRS=knowledge/corpus
OJT_RETRIEVAL_CHUNK_MAX_CHARS=1200
OJT_RETRIEVAL_CHUNK_OVERLAP_CHARS=160
OJT_RETRIEVAL_DIVERSITY_ENABLED=true
OJT_RETRIEVAL_DIVERSITY_LAMBDA=0.72
OJT_RETRIEVAL_FRAMEWORK=custom
```

`OJT_STORAGE_BACKEND` must be `postgres`, `sqlite`, or `memory`. Invalid values
are rejected during settings load before API services are constructed.
`OJT_DATABASE_URL` must use `postgres://` or `postgresql://` syntax with a host,
optional numeric port, and database name. Unsupported schemes, blank values,
missing hosts, missing database names, invalid ports, and fragments are rejected
during settings load.
`OJT_REDIS_URL` may be blank only to mark Redis as not configured; otherwise it
must use `redis://`, `rediss://`, or `unix://` syntax. Unsupported schemes,
missing hosts for TCP Redis URLs, invalid ports, and fragments are rejected
during settings load.

`OJT_KNOWLEDGE_DIR` and `OJT_MIGRATIONS_DIR` control runtime discovery of
trusted healthcare knowledge files and Postgres SQL migrations. Relative values
resolve from the project root; Docker sets absolute `/app/...` paths so runtime
behavior is independent of the installed Python package location. The migration
directory must exist and contain ordered `.sql` files; a missing or empty
migration directory is a startup error for Postgres deployments.
Named `schema_id` values are strict. Use `GET /api/v1/schemas` to discover
available profiles, or send `schema_id: null` for explicit no-schema
validation. If a request names an unavailable schema, the API returns
`error.code: "not_found"` and persisted workflow starts are saved with failed
state for inspection.

`OJT_AUTH_COOKIE_NAME` must be a valid HTTP cookie token. Invalid names such as
blank values or names containing spaces, commas, or semicolons are rejected
during settings load.

OAuth redirect URI settings (`OJT_GOOGLE_REDIRECT_URI`,
`OJT_GOOGLE_FRONTEND_REDIRECT_URI`, and `OJT_ALLOWED_AUTH_REDIRECT_URIS`) must
use `http` or `https`. Non-local HTTP callbacks must use HTTPS. Local
`http://localhost`, `http://127.0.0.1`, and `http://[::1]` callbacks remain
valid for development. Redirect URIs with fragments, embedded user info, missing
hosts, or non-web schemes are rejected during settings load.

Auth domain settings (`OJT_ALLOWED_GOOGLE_HOSTED_DOMAINS` and
`OJT_AUTH_COOKIE_DOMAIN`) must be bare DNS domains. URLs, ports, wildcards,
spaces, IP addresses, and localhost are rejected during settings load. Hosted
domain allowlists do not accept leading dots; cookie domains may use either
`example.com` or `.example.com`. For localhost development, omit
`OJT_AUTH_COOKIE_DOMAIN`.

Inline JSON/text payloads are capped by `OJT_MAX_INLINE_DATA_BYTES` for
`POST /api/v1/workflows`, `POST /api/v1/convert`,
`POST /api/v1/validate`, `POST /api/v1/fhir/profile`,
`POST /api/v1/ocr/evidence`, `POST /api/v1/retrieval/search`, and
`POST /api/v1/assistant/chat`.
Multipart uploads are capped by
`OJT_MAX_UPLOAD_BYTES`, read in `OJT_UPLOAD_READ_CHUNK_BYTES` chunks, and
filtered by `OJT_ALLOWED_UPLOAD_EXTENSIONS`. Larger inline inputs should use the
upload workflow routes so the backend can stream and preserve file artifacts.
Over-limit inline or upload requests return HTTP `413` with
`error.code = "upload_too_large"`.

`OJT_ALLOWED_UPLOAD_EXTENSIONS` can only narrow supported upload extensions.
Values may include or omit the leading dot and are normalized to lowercase.
Unsupported or unsafe values such as `.exe`, `.tar.gz`, path-like values,
wildcards, or extensions containing spaces are rejected during settings load.

`OJT_EMBEDDING_PROVIDER` supports `deterministic`, `openai`, and `huggingface`.
Deterministic mode is for offline tests and demos. OpenAI mode uses
`OJT_OPENAI_API_KEY` or, when that is blank, `OPENAI_API_KEY`. Hugging Face mode
uses SentenceTransformers and can run on GPU with `OJT_HF_EMBEDDING_DEVICE=cuda`.
The recommended semantic retrieval dimension is `384`, matching the Postgres
`embedding vector(384)` schema. Other provider names, incompatible deterministic
model IDs, invalid device values, and invalid dimension values are rejected
during settings load.

`OJT_LLM_PROVIDER` supports `disabled` and `openai`. Disabled mode keeps the
assistant deterministic and token-free. OpenAI mode uses the Responses API to
produce a structured tool plan, but the backend still executes only known
allowlisted tools. `OJT_LLM_MODEL` defaults to `chat-latest`; set it to a pinned
snapshot when release reproducibility is more important than tracking the
current model alias. `OJT_LLM_BASE_URL` must be an HTTP(S) OpenAI-compatible API
base URL. `OJT_LLM_MAX_TOOL_CALLS` bounds assistant tool execution per request.

`OJT_PYTHON_EXTRAS` is a Docker build-time setting, not a runtime secret. Keep
the default `parsing` for the standard API image, or build with
`parsing,embeddings-local` when the container should include local
SentenceTransformers embeddings and CrossEncoder reranking dependencies.

`OJT_RERANK_PROVIDER` supports `none` and `huggingface`. When enabled, retrieval
uses a SentenceTransformers CrossEncoder over the top
`OJT_RERANK_CANDIDATE_LIMIT` first-stage candidates and adds a bounded
`OJT_RERANK_SCORE_WEIGHT` contribution to each hit's `rerank_score`. Invalid
provider names, blank model identifiers, unsupported devices, non-positive
batch/candidate limits, or score weights outside `(0, 1]` are rejected during
settings load.

`OJT_RETRIEVAL_DIVERSITY_ENABLED` controls source-aware final selection after
first-stage fusion and optional reranking. When enabled, final `top_k` selection
uses an MMR-style relevance/novelty balance so repeated chunks from the same
source do not crowd out other relevant evidence. `OJT_RETRIEVAL_DIVERSITY_LAMBDA`
must be between `0` and `1`; higher values favor relevance and lower values
favor diversity. Retrieval packages expose the policy and source coverage under
`handoff_context.diversity`.

Retrieval hits expose `score_components` as the score explanation contract.
Custom/static/Postgres retrieval emits lexical RRF, vector RRF, policy boost,
and optional external reranker contribution rows. Framework adapters emit their
own framework score row while preserving the same field shape.

`OJT_RETRIEVAL_FRAMEWORK` supports `custom` and `llamaindex`. `custom` keeps the
native Postgres/static retrieval adapters. `llamaindex` uses the optional
LlamaIndex adapter behind the same retrieval port and requires
`pip install -e '.[rag-framework]'` or a Docker build with
`OJT_PYTHON_EXTRAS=parsing,rag-framework`. The response envelope and
`RetrievalPackage` schema remain unchanged.

Boundary string fields that drive tool behavior must remain non-blank after
trimming. Whitespace-only workflow instructions, workflow data, direct
conversion/validation data, FHIR payloads, OCR `name` or `source_ref` values,
and retrieval `query` values return `request_validation_error` before service
logic runs. Raw source `data` is checked for blank content without stripping so
stored dataset artifacts and hashes still represent the submitted text.
Optional identifiers and retrieval context strings are also trimmed and rejected
when blank, including `schema_id`, `workflow_id`, `fields[]`,
`detected_format`, `resource_type`, `clinical_domain`, and `standard_system`.
Path identifiers such as `/workflows/{workflow_id}` and `/review/{review_id}`
also reject encoded whitespace-only values with `request_validation_error`.

Numeric runtime settings shown above, plus OAuth timeout and auth TTLs, must be
positive. Invalid non-positive values are rejected at settings load time instead
of being silently coerced.

Schema migrations live in:

```text
sql/postgres/migrations/
```

Postgres-backed repositories apply pending migrations automatically during
service construction. For CI or release checks, the same migrator can be invoked
explicitly with:

```bash
PYTHONPATH=src python -m ojtflow.infrastructure.storage.migrate
```

Local dataset and output artifact refs are stored internally as file-backed
references and are accepted by repository adapters only when they resolve under
the configured `OJT_DATA_DIR` artifact roots (`datasets/` or `outputs/`).
Unsupported schemes, non-local file authorities, missing files, directory refs,
relative `file:` URIs, direct outside paths, and symlink escapes return the
standard `not_found` envelope without echoing the local path. Public API
responses redact local filesystem refs in workflow, event, issue-location, and
handoff payloads to opaque `artifact://local/<artifact-file>` handles. Clients
cannot use those handles to read arbitrary files; generated output content is
available only through `GET /api/v1/workflows/{workflow_id}/output`. Generated
output artifacts are also verified against the
`WorkflowState.output.transformation.output_hash` value before content is
returned. A hash mismatch returns an `artifact_integrity_error` envelope and the
corrupted content is not served.

Paused workflows also verify `WorkflowState.input.input_hash` before review
approval resumes parsing and transformation. If the persisted input artifact was
changed after validation/review was prepared, approval fails with
`artifact_integrity_error`, the workflow is persisted as `failed`, and no output
artifact is generated from the tampered input.

Errors use:

```json
{
  "data": null,
  "error": {
    "code": "request_validation_error",
    "message": "Request validation failed",
    "details": {},
    "workflow_id": null
  }
}
```

Workflow-scoped domain failures populate `error.workflow_id` when returning the
identifier does not reveal another user's resource. For example, artifact
integrity failures include the workflow ID and `error.details.artifact` set to
`"input"` or `"output"`.
Required runtime dependency failures return HTTP `503` with
`error.code = "dependency_unavailable"`. For example, Postgres auth requires
Redis for multi-instance OAuth state/session cache operations; if Redis is
unavailable, auth URL, callback, session lookup, and logout operations fail
loudly instead of silently using process-local cache.

Request validation failures preserve structural diagnostics such as `loc`,
`msg`, and `type`, but submitted raw `input` values are redacted in
`error.details.errors[]`. This prevents malformed healthcare payloads from
being echoed back into browser, proxy, or observability logs.

## Workflow

`POST /api/v1/workflows`

Standard structured workflow inputs:

- CSV with a header row and one record per row.
- JSON as an array of objects.
- YAML as a list of mappings.
- FHIR-like JSON resources or Bundles. These are profiled as healthcare
  standard payloads and attached to workflow `handoff_context.fhir_profile`.

For the healthcare demo scope, `lab_result_v1` expects lab-result records with:

- `date`
- `patient_id`
- `lab_name`
- `value`
- `unit`

Request:

```json
{
  "instruction": "Clean this CSV, convert it to JSON, and explain anomalies.",
  "data": "date,patient_id,lab_name,value,unit\n2026-01-01,P001,HbA1c,7.4,%\n2026/01/02,P002,HbA1c,,\n",
  "input_format": "csv",
  "target_format": "json",
  "schema_id": "lab_result_v1",
  "require_human_review": true
}
```

Response data is a `WorkflowState`. Important fields:

- `workflow_id`
- `owner_user_id`
- `status`
- `steps`
- `input`
- `profile`
- `retrieved_context`
- `validation_report`
- `transformation_plan`
- `review`
- `output`
- `explanation`
- `handoff_context`
- `failure`
- `audit_event_refs`

If startup reaches workflow creation but fails during parsing, extraction,
retrieval, validation, policy, or transformation preparation, the backend still
persists the failed `WorkflowState` and returns a standard error envelope
instead of a `200` success response. The error includes `error.workflow_id` so
the failed run can be inspected:

```json
{
  "data": null,
  "error": {
    "code": "tool_execution_error",
    "message": "Invalid JSON: Expecting property name enclosed in double quotes",
    "details": {
      "status": "failed",
      "risk_flags": ["ToolExecutionError"],
      "error_type": "ToolExecutionError",
      "failure_code": "tool_execution_error"
    },
    "workflow_id": "wf_example"
  }
}
```

The corresponding `WorkflowState.failure` stores `code`, `message`,
`error_type`, `details`, and `failed_at`; the audit stream also includes
`workflow.failed`.

`handoff_context.retrieval_trace` records retrieval strategy, query variants,
filters, candidate count, selected evidence IDs, safety flags, and retrieval
warnings. Retrieval packages also expose
`handoff_context.query_analysis`, which records deterministic clinical query
expansion metadata: strategy, detected concepts, expanded terms, healthcare
standard cues, rule IDs, and final query variants.

`GET /api/v1/workflows`

Returns recent `WorkflowState` records for the authenticated user. This legacy
list endpoint is kept for direct API clients that need full workflow state
objects. Browser queue views should prefer `/workflows/summary`.

Query parameters:

- `status`: optional workflow status filter.
- `limit`: number of records to return. Defaults to 50 and is bounded to
  `1..100`; out-of-range values return `request_validation_error`.

`GET /api/v1/workflows/{workflow_id}` returns the current `WorkflowState`.

`GET /api/v1/workflows/{workflow_id}/events` returns append-only workflow events.

`GET /api/v1/workflows/{workflow_id}/output` returns the generated artifact
content for completed or approved workflows. The client supplies only
`workflow_id`; the backend resolves the persisted output reference from
`WorkflowState` and does not accept arbitrary file paths.

Response data:

```json
{
  "workflow_id": "wf_example",
  "output_format": "json",
  "output_hash": "sha256...",
  "byte_size": 412,
  "content": "[{\"date\":\"2026-01-01\"}]",
  "warnings": [],
  "diff_summary": {
    "format_changed": true,
    "source_format": "csv",
    "target_row_count": 3,
    "actions_applied": ["mask_sensitive_field_for_explanation"]
  }
}
```

If the workflow has not produced an artifact yet, the endpoint returns the
standard `not_found` error envelope. If the stored artifact content no longer
matches the workflow's recorded output hash, the endpoint returns HTTP `409`
with `error.code = "artifact_integrity_error"`.

Review approval uses the same integrity rule for stored input. An input hash
mismatch during `POST /api/v1/review/{review_id}` returns HTTP `409`, records a
`workflow.failed` audit event, and leaves `output` unset. If the input still
passes integrity checks but a deterministic resume tool fails, for example the
stored content cannot be parsed with the workflow's declared format, the review
route returns the same persisted-failure error envelope with
`error.workflow_id` and `WorkflowState.failure`.

FHIR-like workflow behavior:

- JSON input with root `resourceType` or `Bundle.entry[].resource.resourceType`
  triggers lightweight FHIR profiling during orchestration.
- `handoff_context.fhir_profile` records resource type counts, minimal shape
  issues, and evidence IDs.
- `handoff_context.fhir_handoff` records Graph-NER/RAG handoff terms.
- `handoff_context.retrieval_handoff.graph_context` records extracted evidence
  graph nodes, edges, and triples for retrieval-grounded explanation.
- The retrieval query receives `resource_type`, so standard evidence such as
  FHIR Observation guidance can be ranked with the workflow context.

`GET /api/v1/workflows/summary`

Returns a paged operational projection for queue/table views without requiring
the browser to download full workflow states.

Query parameters:

- `status`: optional workflow status filter.
- `q`: optional search across workflow ID, instruction, schema ID, and review ID.
- `page`: 1-based page number.
- `page_size`: capped at 100.
- `sort`: one of `updated_at`, `created_at`, `status`, `workflow_id`, `issue_count`, `evidence_count`.
- `direction`: `asc` or `desc`.

Response data:

```json
{
  "items": [
    {
      "workflow_id": "wf_example",
      "owner_user_id": "usr_example",
      "status": "needs_human_review",
      "instruction": "Clean this CSV, convert it to JSON, and explain anomalies.",
      "schema_id": "lab_result_v1",
      "target_format": "json",
      "issue_count": 8,
      "review_id": "rev_example",
      "review_status": "pending",
      "evidence_count": 5,
      "created_at": "2026-05-31T00:00:00+00:00",
      "updated_at": "2026-05-31T00:01:00+00:00"
    }
  ],
  "page": 1,
  "page_size": 25,
  "total": 1
}
```

`GET /api/v1/workflows/stats`

Returns aggregate operational counts for the authenticated user's workflows:

- `total`
- `by_status`
- `pending_reviews`
- `failed`
- `completed`
- `review_gated`
- `average_issue_count`

## Review

`POST /api/v1/review/{review_id}`

```json
{
  "decision": "approve",
  "payload": {}
}
```

The API records `review.decided_by` and the `review.decided` audit-event actor
from the authenticated backend session. Clients must not send or spoof reviewer
identity in the request body.

Review decisions are also owner-scoped. A user cannot approve, reject, list, or
inspect another user's pending review by guessing `review_id`.

Allowed decisions:

- `approve`
- `approve_with_edits`
- `reject`
- `clarify`
- `cancel`

`approve_with_edits` is available for structured API clients only when the
request includes explicit deterministic edit actions:

```json
{
  "decision": "approve_with_edits",
  "payload": {
    "actions": [
      {
        "action": "mask_sensitive_field_for_explanation",
        "field": "patient_id",
        "reason": "Keep patient identifiers masked in generated output.",
        "requires_review": true
      }
    ]
  }
}
```

The backend replaces the pending transformation-plan actions with the supplied
validated actions before execution. Empty edit payloads, unsupported action
names, or target-format changes return `policy_blocked` and leave the review
pending with no output artifact. The browser UI intentionally hides
`approve_with_edits` until a real edit form exists, so users cannot accidentally
approve the original plan under an edited decision label.

The service enforces the `HumanReview.allowed_decisions` contract before
mutating workflow state. Terminal review decisions are single-use: after a
review leaves `pending`, another decision for the same `review_id` returns
`policy_blocked` with `error.workflow_id` and
`error.details.review_status`. `clarify` is non-terminal in v0. It appends to
`review.clarification_requests`, records an audit event, leaves the review
`pending`, and allows a later approve/reject/cancel decision.

Approval is also failure-observable. If approval is accepted but the resumed
parser/converter/explanation path fails, the failed workflow is persisted and
the review endpoint returns a non-`200` error envelope instead of silently
returning a failed workflow as success.

`GET /api/v1/reviews/summary`

Returns the same `WorkflowSummaryPage` projection as workflow summaries, but
limited to workflows with review gates. `status=pending` filters by review
status, not workflow status. Use `status=all` to disable the review-status
filter.

`GET /api/v1/reviews`

Returns recent full workflow states that have attached review gates. This
legacy endpoint is intended for direct API clients; browser review tables should
prefer `/reviews/summary`.

Query parameters:

- `status`: optional review status filter. Defaults to `pending`.
- `limit`: number of records to return. Defaults to 50 and is bounded to
  `1..100`; out-of-range values return `request_validation_error`.

Summary list endpoints validate `sort`, `direction`, and `page_size`; legacy
list endpoints validate `limit`. Invalid values return the standard
`request_validation_error` envelope.

## Schema Registry

`GET /api/v1/schemas`

Returns approved schema profiles loaded by the workflow service knowledge
repository. The operations UI uses this registry to show validation-ready
healthcare data formats before users start workflows.

Response data is a list of schema entries. Each entry includes:

- `schema_id`
- `version`
- `title`
- `required`
- `field_count`
- `fields`
- `source_ref`

The endpoint is authenticated and read-only. It does not expose local filesystem
paths beyond the repository-relative `source_ref` used to identify the approved
knowledge asset.

## Direct Conversion

`POST /api/v1/convert`

```json
{
  "data": "a,b\n1,2\n",
  "input_format": "csv",
  "target_format": "json"
}
```

Response data includes:

- `detected_format`
- `output_format`
- `output`
- `metadata.output_hash`
- `metadata.source_format`
- `metadata.target_format`
- `metadata.source_row_count`
- `metadata.target_row_count`
- `metadata.lossy`
- `metadata.actions_applied`
- `metadata.diff_summary`
- `metadata.warnings`

Direct conversion uses the workflow service parser and transformation agent, but
does not create a workflow, dataset, output artifact, or audit event. CSV output
from nested JSON/YAML sets `metadata.lossy=true` and includes a warning.

## Direct Validation

`POST /api/v1/validate`

```json
{
  "data": "date,patient_id,lab_name,value,unit\n2026/01/02,P002,HbA1c,,\n",
  "input_format": "csv",
  "schema_id": "lab_result_v1"
}
```

Response data includes:

- `profile`
- `validation_report.valid`
- `validation_report.issues`
- `validation_report.requires_review`

Direct validation uses the same parser, profiler, schema repository, and
validation agent service graph as persisted workflows. It does not create a
workflow, dataset, output artifact, or audit event.
If `schema_id` names a profile that is not available in the configured
knowledge directory, direct validation returns `not_found`; `schema_id: null`
is the explicit mode for validation without a schema profile.

## Assistant Chat

`GET /api/v1/assistant/tools`

Returns the server-owned assistant/MCP tool catalog. This is a read-only
operator discovery endpoint; it exposes tool names, descriptions, permission
scope, approval requirement, and JSON input schema, but no secrets or executable
client code.

Example response data:

```json
[
  {
    "name": "validate_with_evidence",
    "description": "Validate submitted healthcare data and retrieve trusted evidence that explains schema, unit, date, PHI, and interoperability issues.",
    "permission_scope": "data:validate",
    "requires_approval": false,
    "input_schema": {
      "type": "object",
      "required": ["data"]
    }
  }
]
```

`POST /api/v1/assistant/chat`

```json
{
  "message": "Validate this lab CSV and explain the issues with trusted evidence.",
  "context": {
    "data": "date,patient_id,lab_name,value,unit\n2026/01/02,P002,HbA1c,,\n",
    "input_format": "csv",
    "schema_id": "lab_result_v1",
    "fields": ["date", "patient_id", "lab_name", "value", "unit"],
    "clinical_domain": "laboratory"
  },
  "execute_write_actions": false
}
```

The assistant is an operator convenience layer over existing backend tools. It
does not replace workflow state, retrieval trace, validation reports, or human
review. Response data includes:

- `message`
- `mode`
- `model`
- `findings[].title`
- `findings[].detail`
- `findings[].severity`
- `findings[].source_tool`
- `findings[].source_ids`
- `evidence_summary[].source_id`
- `evidence_summary[].claim`
- `evidence_summary[].trust_level`
- `evidence_summary[].confidence`
- `tool_calls[].tool_name`
- `tool_calls[].status`
- `tool_calls[].arguments`
- `tool_calls[].output`
- `tool_calls[].summary`
- `tool_calls[].requires_approval`
- `suggestions`
- `warnings`

The assistant can call:

- `retrieval_search`
- `validate_data`
- `validate_with_evidence`
- `convert_data`
- `fhir_profile`
- `list_workflows`
- `list_reviews`
- `get_workflow`
- `workflow_summary`
- `start_workflow`

`validate_with_evidence` is the preferred assistant path for healthcare data
quality questions because it validates the payload and retrieves standards
evidence in one response. `workflow_summary` is the preferred assistant path
for chat-based workflow inspection.

`start_workflow` is a write action. It returns `status="requires_approval"`
unless the request explicitly sets `execute_write_actions=true`. The assistant
does not expose review approval, rejection, cancellation, or destructive
artifact actions in v0.

## FHIR-Like Profile

`POST /api/v1/fhir/profile`

```json
{
  "data": "{\"resourceType\":\"Observation\",\"status\":\"final\"}"
}
```

This endpoint performs lightweight FHIR-like profiling only. It does not perform full HL7 FHIR validation.
FHIR profiling is owned by the medical evidence application service so the API
route remains transport-only and the same hook can later call a full validator.
The `data` field is trimmed and must be non-blank.

Response data includes:

- `profile.is_fhir_like`
- `profile.resource_type`
- `profile.resource_counts`
- `profile.handoff_context`
- `evidence`

## OCR Evidence Stub

`POST /api/v1/ocr/evidence`

```json
{
  "fields": [
    {
      "page": 1,
      "name": "patient_id",
      "value": "P001",
      "bbox": [0, 0, 10, 10],
      "confidence": 0.72,
      "source_ref": "storage://doc/demo"
    }
  ]
}
```

Response data includes normalized OCR fields and `Evidence(source_type="ocr_box")`.
Fields with confidence below `0.8` require review.
OCR evidence normalization is owned by the medical evidence application service.
The endpoint does not perform OCR extraction and does not persist workflow
artifacts.

Request validation:

- `fields` must contain at least one OCR field.
- `page` is 1-based and must be greater than or equal to `1`.
- `bbox` must contain exactly four non-negative numbers: `[x, y, width, height]`.
- `confidence` must be between `0.0` and `1.0`.
- `name` and `source_ref` are trimmed and must be non-blank.

## Runtime Configuration

`GET /api/v1/runtime/config`

Returns sanitized runtime facts for the authenticated operations UI. This route
must never expose DSNs, OAuth client secrets, ADC material, session tokens, or
local filesystem paths.

Response data includes:

- `status`
- `storage_backend`
- `persistent_storage`
- `postgres_configured`
- `redis_configured`
- `auth.google_oauth_configured`
- `auth.cookie_secure`
- `auth.cookie_effective_secure`
- `auth.cookie_samesite`
- `embedding.provider`
- `embedding.model`
- `embedding.dimensions`
- `embedding.openai_configured`
- `embedding.openai_base_url_configured`
- `embedding.hf_device`
- `embedding.hf_batch_size`
- `embedding.hf_cache_dir_configured`
- `llm.provider`
- `llm.model`
- `llm.openai_configured`
- `llm.timeout_seconds`
- `llm.max_tool_calls`
- `llm.runtime_settings_configured`
- `llm.runtime_settings`
- `retrieval.framework`
- `retrieval.corpus_dir_count`
- `retrieval.chunk_max_chars`
- `retrieval.chunk_overlap_chars`
- `retrieval.candidate_multiplier`
- `retrieval.min_candidates`
- `retrieval.vector_weight`
- `retrieval.bm25_weight`
- `retrieval.diversity_enabled`
- `retrieval.diversity_lambda`
- `retrieval.hnsw_ef_search`
- `retrieval.runtime_settings_configured`
- `retrieval.runtime_settings`
- `upload.max_upload_bytes`
- `upload.max_inline_data_bytes`
- `upload.allowed_extensions`

Example:

```json
{
  "data": {
    "storage_backend": "postgres",
    "persistent_storage": true,
    "postgres_configured": true,
    "redis_configured": true,
    "data_dir_configured": true,
    "auth": {
      "google_oauth_configured": true,
      "hosted_domain_restricted": false,
      "cookie_secure": false,
      "cookie_effective_secure": false,
      "cookie_samesite": "lax",
      "session_ttl_seconds": 604800,
      "state_ttl_seconds": 600
    },
    "embedding": {
      "provider": "openai",
      "model": "text-embedding-3-small",
      "dimensions": 384,
      "openai_configured": true,
      "openai_base_url_configured": true,
      "hf_device": "auto",
      "hf_batch_size": 32,
      "hf_cache_dir_configured": true
    },
    "llm": {
      "provider": "openai",
      "model": "chat-latest",
      "openai_configured": true,
      "base_url_configured": true,
      "timeout_seconds": 30.0,
      "max_tool_calls": 4,
      "runtime_settings_configured": true,
      "runtime_settings": {
        "llm_provider": "openai",
        "llm_model": "chat-latest",
        "llm_timeout_seconds": 30.0,
        "llm_max_tool_calls": 4
      }
    },
    "retrieval": {
      "framework": "llamaindex",
      "corpus_dir_count": 1,
      "chunk_max_chars": 1200,
      "chunk_overlap_chars": 160,
      "candidate_multiplier": 4,
      "min_candidates": 12,
      "vector_weight": 0.62,
      "bm25_weight": 0.38,
      "diversity_enabled": true,
      "diversity_lambda": 0.72,
      "hnsw_ef_search": 100,
      "runtime_settings_configured": true,
      "runtime_settings": {
        "retrieval_framework": "llamaindex",
        "retrieval_candidate_multiplier": 4,
        "retrieval_min_candidates": 12,
        "retrieval_vector_weight": 0.62,
        "retrieval_bm25_weight": 0.38,
        "retrieval_diversity_enabled": true,
        "retrieval_diversity_lambda": 0.72,
        "retrieval_hnsw_ef_search": 100
      }
    },
    "upload": {
      "max_upload_bytes": 26214400,
      "max_inline_data_bytes": 1048576,
      "read_chunk_bytes": 1048576,
      "allowed_extensions": [".csv", ".json", ".yaml"]
    }
  },
  "error": null
}
```

`retrieval.hnsw_ef_search` is the Postgres pgvector HNSW query-depth setting
applied transaction-locally for vector candidate retrieval. Higher values
increase recall and latency; lower values reduce latency and can miss more
approximate-nearest-neighbor candidates.

`PUT /api/v1/runtime/assistant-settings`

Persists editable Assistant/LLM runtime settings and reloads cached backend
service instances after validation. It accepts only planner/runtime control
fields; API keys, OAuth secrets, database URLs, file paths, and approval
decisions are not editable through this endpoint.

Request:

```json
{
  "llm_provider": "openai",
  "llm_model": "gpt-4.1-mini",
  "llm_timeout_seconds": 30.0,
  "llm_max_tool_calls": 4
}
```

Response:

```json
{
  "data": {
    "settings": {
      "llm_provider": "openai",
      "llm_model": "gpt-4.1-mini",
      "llm_timeout_seconds": 30.0,
      "llm_max_tool_calls": 4
    },
    "reloaded": true
  },
  "error": null
}
```

`PUT /api/v1/runtime/retrieval-settings`

Persists editable retrieval runtime settings and reloads cached backend service
instances after validation. It accepts only retrieval-scoped keys; secrets,
database URLs, OAuth settings, file paths, and model API keys are not editable
through this endpoint.

Request:

```json
{
  "retrieval_framework": "llamaindex",
  "retrieval_candidate_multiplier": 4,
  "retrieval_min_candidates": 12,
  "retrieval_vector_weight": 0.62,
  "retrieval_bm25_weight": 0.38,
  "retrieval_diversity_enabled": true,
  "retrieval_diversity_lambda": 0.72,
  "retrieval_hnsw_ef_search": 100
}
```

Response:

```json
{
  "data": {
    "settings": {
      "retrieval_framework": "llamaindex",
      "retrieval_candidate_multiplier": 4,
      "retrieval_min_candidates": 12,
      "retrieval_vector_weight": 0.62,
      "retrieval_bm25_weight": 0.38,
      "retrieval_diversity_enabled": true,
      "retrieval_diversity_lambda": 0.72,
      "retrieval_hnsw_ef_search": 100
    },
    "reloaded": true
  },
  "error": null
}
```

`GET /api/v1/runtime/readiness`

Returns sanitized readiness diagnostics for authenticated operators. This is
separate from the public raw `GET /health` liveness probe: `/health` should stay
cheap enough for Docker/load balancer checks, while readiness verifies that the
backend can reach the workflow repository and load governance/retrieval assets.
The response must not expose DSNs, OAuth secrets, Redis URLs, ADC material,
session tokens, or local filesystem paths.

Response data includes:

- `status`: `ready`, `degraded`, or `not_ready`.
- `checks[]`: named checks with `status`, `summary`, and sanitized `details`.

Current checks:

- `settings`
- `artifact_directory`
- `session_cache`
- `workflow_repository`
- `schema_inventory`
- `retrieval_inventory`: source inventory plus a bounded retrieval search probe.

In Postgres mode, `session_cache` verifies that Redis can be reached with a
short ping. If Redis is missing or unavailable, readiness returns
`status = "not_ready"` because process-local OAuth/session fallback is not
multi-instance safe for Postgres deployments.
For file artifacts, `artifact_directory` performs safe create/delete probes in
the data, dataset, and output directories and returns only booleans and error
types, never local filesystem paths.
For schemas, `schema_inventory` must load at least one trusted profile. If the
configured knowledge directory yields zero schemas, readiness returns
`status = "not_ready"` because default schema-backed workflows cannot run.
For retrieval, `retrieval_inventory` runs a small approved-source query through
the same workflow retrieval service path and reports only operational metadata:
`source_count`, `probe_hit_count`, `probe_strategy`, `probe_candidates_seen`, and
`probe_warning_count`.
If no trusted retrieval sources are loaded, readiness returns
`status = "not_ready"` because evidence-backed workflows cannot run. If sources
exist but the bounded probe returns no evidence, readiness returns
`status = "degraded"` so operators can investigate retrieval quality without
blocking all startup.
If a readiness check fails, the check is marked `error` and exposes only a
sanitized `error_type`; exception messages, DSNs, Redis URLs, and local paths are
not returned.

Example:

```json
{
  "data": {
    "status": "ready",
    "checks": [
      {
        "name": "workflow_repository",
        "status": "ok",
        "summary": "Workflow repository is reachable.",
        "details": {
          "visible_workflows": 0
        }
      },
      {
        "name": "retrieval_inventory",
        "status": "ok",
        "summary": "Retrieval source inventory and search probe are available.",
        "details": {
          "source_count": 5,
          "probe_hit_count": 3,
          "probe_strategy": "postgres_fts_vector_rrf",
          "probe_candidates_seen": 5,
          "probe_warning_count": 0
        }
      }
    ]
  },
  "error": null
}
```

## Google OAuth Auth

All auth/session responses return `Cache-Control: no-store` and
`Pragma: no-cache`. This includes OAuth URL generation, OAuth callback, current
session lookup, and logout. The callback may set cookies and can optionally
return bearer token material, so clients and intermediaries must not cache these
responses.

`GET /api/v1/auth/google/url`

Returns:

- `authorization_url`: Google OAuth URL for redirecting the user.
- `state`: nonce cached by the backend and verified during callback.

The frontend passes:

```text
redirect_uri=http://localhost:5173/auth/callback
```

Swagger/API-only testing can omit `redirect_uri`, which uses the backend
callback:

```text
http://localhost:8000/api/v1/auth/google/callback
```

`GET /api/v1/auth/google/callback?code=...&state=...`

Exchanges the Google authorization code, verifies the identity token with
Google's verifier, creates or updates the user, creates a backend session, sets
an HTTP-only session cookie for browser clients, and returns:

- `expires_at`
- `user`

The browser callback response does not include the raw bearer token by default.
API-only clients that need the bearer token may pass `include_token=true`; that
adds `token_type` and `access_token` to the response body.

`GET /api/v1/auth/me`

Requires either the session cookie or:

```text
Authorization: Bearer <access_token>
```

Returns the active user and session metadata.

`POST /api/v1/auth/logout`

Requires a valid active session cookie or bearer token, revokes the persisted
session, clears the cache entry when present, and expires the browser cookie.
Invalid or expired tokens return the standard `unauthorized` envelope instead of
being reported as successful logout.
When authenticated by cookie, logout also requires the trusted-origin write
guard described above.

Structured unauthorized response:

```json
{
  "data": null,
  "error": {
    "code": "unauthorized",
    "message": "Missing authenticated session.",
    "details": {},
    "workflow_id": null
  }
}
```

## Retrieval Search

`POST /api/v1/retrieval/search`

```json
{
  "query": "HbA1c lab CSV missing units FHIR Observation",
  "top_k": 5,
  "schema_id": "lab_result_v1",
  "fields": ["date", "patient_id", "lab_name", "value", "unit"],
  "clinical_domain": "laboratory",
  "trust_level": "approved",
  "filters": {
    "standard_system": "UCUM",
    "source_type": "terminology_system"
  }
}
```

Response data is a `RetrievalPackage`:

- `hits[].evidence`
- `hits[].score`
- `hits[].lexical_score`
- `hits[].vector_score`
- `hits[].rerank_score`
- `hits[].score_components[]` with `component`, `label`, `value`, optional
  `rank`, `description`, and `metadata`
- `hits[].matched_terms`
- `hits[].snippet`
- `evidence`
- `coverage`
- `facets`
- `trace.strategy`
- `trace.query_variants`
- `trace.query_variant_details[]` with `variant`, `source`, `reason`, and
  `metadata`
- `trace.filters_applied`
- `trace.candidates_seen`
- `trace.final_hit_ids`
- `trace.safety_flags`
- `trace.warnings`
- `handoff_context`
- `handoff_context.graph_context`
- `handoff_context.query_analysis`

`trace.safety_flags` marks retrieval query context that should remain data-only
for downstream agents. Current values include
`prompt_injection_pattern_in_query` and `sensitive_field_context`.
`handoff_context.query_analysis` is auditable query-understanding metadata.
It can include standard cues such as `FHIR`, `LOINC`, and `UCUM`; concept IDs
such as `hba1c_laboratory_test` and `unit_normalization`; and the rule IDs that
produced expanded query variants. It includes `concept_candidates`, a list of
controlled-vocabulary candidates with `concept_id`, `display_name`,
`standard_system`, `code`, `clinical_domain`, `matched_aliases`, `confidence`,
`source`, and `metadata`. It also includes `filter_suggestions`, a list of
deterministic metadata filter recommendations with `field`, `value`, `reason`,
`rule_id`, `confidence`, and `applied`. It also includes `diagnostics`, a list
of deterministic query-quality checks with `code`, `severity`, `message`, and
`suggested_action`; warning diagnostics are copied into `trace.warnings`. It
also includes `search_hints`, deterministic external medical search syntax
scaffolds with `target`, `query`, optional `url`, `rationale`, and `warnings`
for workflows such as PubMed/MeSH literature search, FHIR resource search
templates, ClinicalTrials.gov API v2 study search, and openFDA drug
label/adverse-event search. Current targets include `pubmed`, `fhir`,
`clinicaltrials_gov`, `openfda_drug_label`, and `openfda_drug_event`.
`hits[].snippet` is an extractive preview with `text`, `start_char`, `end_char`,
`matched_terms`, and `extraction_strategy`. The full source claim remains in
`hits[].evidence.claim`.
`coverage` reports whether standards inferred from query analysis, such as
`FHIR`, `LOINC`, and `UCUM`, are represented in the final selected evidence.
Missing expected standards are returned as `coverage.warnings` and copied into
`trace.warnings`.
`facets` summarizes the final selected hits into buckets for `source_type`,
`clinical_domain`, `standard_system`, and `trust_level`.

Retrieval endpoints require an authenticated session. Searches without
`workflow_id` run over the approved knowledge inventory. Searches with
`workflow_id` are owner-scoped; users cannot attach direct retrieval context to
another user's workflow by guessing an ID.
The `query` field and optional context fields are trimmed and must be non-blank
when supplied.
`filters` is a typed metadata filter object, not an arbitrary JSON bag. Current
supported keys are `trust_level`, `clinical_domain`, `standard_system`, and
`source_type`. Unsupported filter keys or invalid enum values return
`request_validation_error` before the retrieval repository runs, so the API does
not silently accept filters that the ranking layer cannot enforce.

`GET /api/v1/retrieval/presets` returns data-driven operator query presets
loaded from `knowledge/retrieval/search_presets.json`. Each preset includes
`preset_id`, `label`, `description`, optional `category`, `query`, `top_k`,
`fields`, optional schema, format, resource, clinical-domain, standard, trust,
source-type constraints, target source labels, and launch-hint target names. The
frontend uses these presets to seed the query builder instead of hardcoding
healthcare search examples in React.

`GET /api/v1/retrieval/search-options` returns data-driven query-builder
controls loaded from `knowledge/retrieval/search_options.json`. The response
includes `version`, `detected_formats[]` with `value`, `label`, and optional
`description`, plus `top_k_values[]`. The Retrieval UI uses this endpoint for
format and top-K controls so Markdown, FHIR-like, and future intake/search
profiles can be added through trusted data.

`GET /api/v1/retrieval/sources` returns available trusted retrieval sources,
including source type, version, trust level, clinical domain, standard system,
and chunk count. The seeded source inventory includes local schema/governance
knowledge plus curated healthcare-standard assets under `knowledge/`, including
the official source catalog, medical concept seed registry, FHIR R4 search
parameter seed, clinical data standards map, medical search playbook, and public
dataset ingestion plan.

`GET /api/v1/retrieval/integrity` returns a `RetrievalIntegrityReport` for the
current retrieval index. Query parameters:

- `include_seeded`: default `true`.
- `include_corpus`: default `false`.

Response data includes `repository`, `status`, `checked_scope`,
`expected_source_count`, `indexed_source_count`, `ok_count`, `stale_count`,
`missing_count`, `extra_count`, per-source `checks`, and `warnings`. Each check
contains `source_id`, `status`, expected/indexed chunk counts, expected/indexed
hashes, and a message. This endpoint is intended for operational consistency
checks after deployment, reindexing, or source file changes.

`POST /api/v1/retrieval/reindex` refreshes the trusted retrieval index from
seeded knowledge and configured local corpus directories:

```json
{
  "include_seeded": true,
  "include_corpus": true
}
```

Response data includes repository type, indexed chunk count, embedding provider
metadata, and local corpus indexing stats. The endpoint requires an
authenticated session and does not accept arbitrary document text; corpus
files must be placed in configured trusted knowledge directories first.
Large official datasets such as MeSH RDF/XML, RxNorm/RxNav cache exports,
LOINC downloads, MedlinePlus XML, openFDA downloads, and ClinicalTrials.gov API
snapshots should be ingested into ignored runtime/object storage and then
distilled into reviewed knowledge chunks. They should not be committed directly
to source control. Corpus content comes from trusted runtime directories
configured by operators.

## Upload Workflow

`POST /api/v1/parse/upload/workflow`

Accepts multipart uploads and returns the same `WorkflowState` as
`POST /api/v1/workflows`.

Form fields:

- `file`: upload file.
- `instruction`: required natural-language workflow instruction. The backend
  trims surrounding whitespace and rejects blank or omitted values with
  `error.code = "request_validation_error"`.
- `target_format`: `json`, `yaml`, or `csv`.
- `schema_id`: optional validation schema. Blank multipart values are treated as
  omitted, which keeps unstructured document upload usable.
- `require_human_review`: boolean review gate.
- `extractor`: `auto`, `markitdown`, or `mineru`. Values are trimmed and
  normalized before validation.

Structured text uploads (`.csv`, `.json`, `.yaml`, `.md`, `.txt`) do not require
optional document extraction packages. They are decoded as UTF-8, stored as
derived text artifacts, and parsed with the deterministic parser for the
detected file type.

`POST /api/v1/parse/extract`

Extracts text from an uploaded file without creating a workflow, dataset row,
review gate, output artifact, or audit event. This is intended for upload
preview and extractor diagnostics before a user commits to a governed workflow.

Form fields:

- `file`: upload file.
- `extractor`: `auto`, `markitdown`, or `mineru`.

Response data includes:

- `filename`: sanitized upload filename.
- `source_format`: detected source extension/type.
- `extractor_used`: selected extraction engine.
- `page_count`: page count when the extractor reports one.
- `char_count`
- `word_count`
- `text`: extracted markdown/plain text.
- `warnings`: non-fatal extraction warnings.

The same upload filename, extension, size, chunking, and empty-file validation
rules used by `/parse/upload/workflow` apply here. Over-limit uploads return
`upload_too_large`; unsupported extensions or unavailable extractor choices
return `unsupported_upload`.

`GET /api/v1/parse/extractors` returns installed extractor inventory and the
server-recognized upload extensions.
