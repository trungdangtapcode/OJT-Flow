# OJTFlow API Contract v0

All `/api/v1` endpoints return the same envelope:

```json
{
  "data": {},
  "error": null
}
```

Clients should send `X-Request-ID` on every API request. If omitted, the
backend generates one. Responses echo the ID in the `X-Request-ID` header.
Error envelopes also include `error.request_id` and
`error.details.request_id` so browser diagnostics can be matched to backend
logs and assistant stream replay events.

The operational liveness probe `GET /health` is intentionally outside
`/api/v1` and returns raw JSON (`{"status":"ok"}`) for Docker, load balancers,
and simple uptime checks.

Most `/api/v1` workflow, retrieval, artifact, assistant, governance, audit, and
runtime endpoints require an authenticated backend session. Browser clients use
the HTTP-only session cookie set by the Google callback. API clients may use:

```text
Authorization: Bearer <access_token>
```

The auth bootstrap exceptions are `GET /api/v1/auth/google/url` and
`GET /api/v1/auth/google/callback`, which are used to obtain the token.
Direct deterministic tool endpoints such as `POST /api/v1/convert`,
`POST /api/v1/validate`, `POST /api/v1/fhir/profile`, and
`POST /api/v1/ocr/evidence` are authenticated by router-level dependency in
v0 but do not yet have fine-grained RBAC scopes.

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

Workspace RBAC is enforced through
`GovernanceService.require_permission(...)`. Scope mapping is documented in
`docs/ownership_authorization_v0.md`. In short:

- workflow reads and schema inventory require `data:read`;
- workflow creation and document-to-workflow creation require `data:transform`;
- upload/extract/redaction preview actions require `data:profile`;
- raw artifact download, artifact metadata export, and workflow output export
  require `data:export`;
- review queues require `review:read`; review decisions require
  `review:write`;
- retrieval search and source inventory require `retrieval:read`;
- runtime setting writes require `settings:write`;
- operational diagnostics require `admin:read`; reindex/repair marker writes
  require `admin:write`.

PHI and sensitive-data classification is exposed as shared metadata, not as a
separate endpoint. The `phi_classification` object appears on `DataProfile`,
`ValidationReport`, `TransformationOutput`, `RedactionPreview`, persisted
`AssistantChatMessage` objects, and retrieved chunk evidence under
`Evidence.locator.phi_classification`. See `docs/phi_classification_v0.md` for
the contract, policy model, and verification commands.

`POST /api/v1/parse/redaction-preview` accepts optional `redaction_action`
values `mask`, `suppress`, `tokenize_placeholder`, or `review_gated_reveal`.
The response includes `policy_id`, `policy_version`, per-match action metadata,
`action_summary`, `requires_review`, and `reveal_required`. Public callers cannot
approve raw reveal through this endpoint; review-approved reveal is reserved for
future governed review workflows. See `docs/phi_redaction_policy_v0.md`.

Application logs are protected by a no-raw-PHI logging filter installed in the
FastAPI app factory. CI also runs `scripts/scan-no-raw-phi.py` against log
directories when present. See `docs/no_raw_phi_logging_v0.md`.

Default persistence uses Postgres plus local file-backed artifacts:

```text
OJT_STORAGE_BACKEND=postgres
OJT_PRODUCT_MODE=local_dev
OJT_NO_MOCK_DATA=false
OJT_DATABASE_URL=postgresql://ojtflow:ojtflow@localhost:5432/ojtflow
OJT_REDIS_URL=redis://localhost:6379/0
OJT_DATA_DIR=var
OJT_KNOWLEDGE_DIR=knowledge
OJT_MIGRATIONS_DIR=sql/postgres/migrations
OJT_AUTH_COOKIE_NAME=ojtflow_session
OJT_AUTH_COOKIE_SAMESITE=lax
OJT_SERVICE_ACCOUNT_TOKEN_TTL_SECONDS=7776000
OJT_SERVICE_ACCOUNT_DEFAULT_ROLE_KEY=operator
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
OJT_RETRIEVAL_EVALUATION_POLICY_PATH=
```

`OJT_PRODUCT_MODE` must be `local_dev`, `demo`, `pilot`, or `production`.
`pilot` and `production` require persistent storage and reject
`OJT_LLM_PROVIDER=disabled` during settings load. `OJT_NO_MOCK_DATA=true` blocks
demo/mock data paths explicitly; it is also effectively enabled in `pilot` and
`production`.
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
`POST /api/v1/assistant/chat`. Job creation routes accept bounded structured
arguments and store large work inputs by reference rather than accepting raw
bulk content.
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
produce a strict structured tool plan, but the backend still executes only known
allowlisted tools. `OJT_LLM_MODEL` defaults to `chat-latest` and remains the
compatibility fallback. `OJT_LLM_PLANNING_MODEL`, `OJT_LLM_SYNTHESIS_MODEL`, and
`OJT_LLM_VISION_MODEL` can pin planner, answer synthesis, and OCR/vision models
separately. `OJT_LLM_BASE_URL` must be an HTTP(S) OpenAI-compatible API base URL
and can point to a local compatible endpoint. `OJT_LLM_MAX_TOOL_CALLS` bounds
assistant tool execution per request. `OJT_LLM_PLANNING_PROGRESS_INTERVAL_SECONDS`
controls how often the streaming assistant emits planning heartbeat events while
an LLM planner call is still pending.

External provider policy settings control which data may leave the local
runtime boundary:

- `OJT_EXTERNAL_OPENAI_LLM_ENABLED`
- `OJT_EXTERNAL_OPENAI_LLM_ALLOW_PHI`
- `OJT_EXTERNAL_OPENAI_OCR_ENABLED`
- `OJT_EXTERNAL_OPENAI_OCR_ALLOW_PHI`
- `OJT_EXTERNAL_OPENAI_OCR_ALLOW_UNKNOWN`
- `OJT_EXTERNAL_OPENAI_EMBEDDINGS_ENABLED`
- `OJT_EXTERNAL_OPENAI_EMBEDDINGS_ALLOW_PHI`
- `OJT_EXTERNAL_MEDICAL_SEARCH_ENABLED`
- `OJT_EXTERNAL_MEDICAL_SEARCH_ALLOW_PHI`

Provider adapters enforce these checks before outbound calls. PHI is blocked
from OpenAI-compatible LLM, OCR, embedding, and external medical-search handoffs
by default unless policy explicitly allows it. See
`docs/external_provider_policy_v0.md`.

`OJT_MARKITDOWN_OCR_ENABLED` controls whether MarkItDown runs with OCR plugins
for OCR-sensitive uploads such as scanned PDFs, images, and image-heavy Office
files when an OpenAI-compatible API key is configured. `OJT_OPENAI_VISION_MODEL`
is still accepted as a legacy alias, but new deployments should use
`OJT_LLM_VISION_MODEL`.

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
the first-class `diversity` field and also copy the same metadata into
`handoff_context.diversity` for assistant/agent handoff compatibility.
Diversity metadata includes aggregate source counts plus `selected_hits[]` rows
with evidence ID, source ID, selected rank, original rank, relevance score,
redundancy score, selection score, and reason.

Retrieval hits expose `score_components` as the score explanation contract.
Custom/static/Postgres retrieval emits lexical RRF, vector RRF, policy boost,
and optional external reranker contribution rows. Framework adapters emit their
own framework score row while preserving the same field shape.
Retrieval packages also expose `quality_summary`, a deterministic aggregate of
`quality_signals[]` with status, 0-100 score, severity counts, blocker/warning
codes, and the top recommended action. This gives operators and assistant tools
a quick readiness signal without hiding the underlying quality signals. The
package also exposes `recommended_actions[]`, a backend-derived corrective
retrieval checklist sorted by priority. Each action includes `action_id`,
`priority`, `severity`, `action_type`, `title`, `description`, optional
`suggested_filter`, `source_signal_codes`, `evidence_ids`, and metadata. The
package also exposes `recommended_action_summary` with action count, highest
priority, highest severity, top action title, and apply-filter count for
triage surfaces. It also includes `broaden_query_count` and
`action_type_counts` so UI and assistant surfaces can distinguish filter
application, broadening, rewrite, review, source repair, and source-diversity
work without scanning every action row.
The mapping is loaded from `knowledge/retrieval/corrective_action_rules.json`
and can be overridden with `OJT_CORRECTIVE_ACTION_RULES_PATH`. Rules default to
package `quality_signal` inputs, and may declare `source = "query_diagnostic"`
to turn query-health warnings into the same ordered action contract. The same
action list and summary are copied into `handoff_context.recommended_actions`
and `handoff_context.recommended_action_summary` for assistant or future
Graph/RAG handoff.
The package also exposes `remediation_summary`, a backend-derived
plain-language next step built from corrective actions, quality summary,
warnings, or zero-hit state. The same value is copied into
`handoff_context.remediation_summary` so browser reports and assistant tools do
not need to rederive it.
The package also exposes `strategy_recommendations[]`, a backend-derived
explanation of the active retrieval technique, route, and caution/action
signals. Rules are loaded from
`knowledge/retrieval/strategy_recommendation_rules.json` and can be overridden
with `OJT_STRATEGY_RECOMMENDATION_RULES_PATH`; the same list is copied into
`handoff_context.strategy_recommendations`.
The Retrieval UI renders known `quality_signals[].metadata` structures, including
missing concepts, provenance issues, missing standards/aspects, and suggested
filters, as explicit signal details for operator review. The
readiness score/status policy is loaded from
`knowledge/retrieval/quality_gate_policy.json`; set
`OJT_RETRIEVAL_QUALITY_POLICY_PATH` to use deployment-specific severity
penalties, blocking severities, review severities, and score thresholds without
changing application code.

`OJT_RETRIEVAL_FRAMEWORK` supports `custom` and `llamaindex`. `custom` keeps the
native Postgres/static retrieval adapters. `llamaindex` uses the optional
LlamaIndex adapter behind the same retrieval port and requires
`pip install -e '.[rag-framework]'` or a Docker build with
`OJT_PYTHON_EXTRAS=parsing,rag-framework`. The response envelope and
`RetrievalPackage` schema remain unchanged. Framework-backed packages also
populate `quality_summary`, `handoff_context.quality_policy`, and per-hit
aspect/concept locator metadata when query analysis can ground those signals.

Retrieval quality gates are also policy-driven. The active
`knowledge/retrieval/quality_gate_policy.json` policy is copied into
`handoff_context.quality_policy`, including `ranking_thresholds` such as
`min_top_matched_terms`. If the top-ranked hit does not meet that exact-match
threshold, `quality_signals[]` includes `weak_top_hit_match` with the top
evidence ID, matched-term count, configured threshold, and ranking scores.
The same policy includes `provenance_requirements` for medical source classes.
When selected healthcare standards, terminology systems, or data dictionaries
lack required source version or locator metadata, `quality_signals[]` includes
`weak_evidence_provenance` with affected evidence IDs, missing fields, and the
active provenance requirement metadata.
The active policy also includes `concept_grounding_requirements`. Hits may
include `source_locator.concept_matches[]` when selected evidence supports
detected query concepts by standard system, code, display name, alias, or exact
matched term. If a detected controlled concept above the configured confidence
threshold is not represented in selected evidence, `quality_signals[]` includes
`missing_concept_grounding`.
Copied `retrieval_run_comparison` reports include `concept_grounding.added`,
`concept_grounding.removed`, and `concept_grounding.retained` so relevance
tuning can distinguish text-rank movement from loss or gain of coded medical
concept support.

Runtime retrieval tuning recommendations are data-driven. By default,
`POST /api/v1/retrieval/judgments/evaluate` loads policy rules from
`knowledge/retrieval/evaluation_policy.json`; set
`OJT_RETRIEVAL_EVALUATION_POLICY_PATH` to use a deployment-specific policy file
without changing application code.

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
- `clinical_package`
- `handoff_context`
- `failure`
- `audit_event_refs`

When the workflow input has a supported healthcare mapping, `clinical_package`
contains an `ojtflow_clinical_package` envelope with raw input identity,
FHIR-like `Bundle`, OperationOutcome-like validation issues, linked evidence,
review-gated terminology candidates, UCUM-like unit validation results,
internal Provenance-like records, review state, audit event refs, output refs,
and handoff context. For v0, `lab_result_v1` maps to FHIR-like `Patient`,
`Observation`, `DiagnosticReport`, and `DocumentReference` resources with
field-level source/derived/defaulted provenance. The package also includes
profile registry metadata and FHIR search parameter hints from
`knowledge/fhir/resource_profiles.json`. The package reports
`fhir_like_not_validated`; clients must not call it HL7 FHIR compliant or
automatically apply terminology candidates.

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
- `handoff_context.retrieval_handoff.graph_rag_lite` records graph-aware
  reranking metadata: policy version, whether graph support changed hit order,
  supported evidence count, score weights, original order, final order, and
  top graph-supported evidence refs.
- Retrieval hits may include a `graph_support` score component and
  `source_locator.graph_rag_lite` / `evidence.locator.graph_rag_lite` payloads
  with shared query targets, normalized-code targets, graph edge counts, triple
  counts, and score boost.
- Retrieval answers include `claims[].graph_guard` and
  `metadata.claim_triple_guard`; strong clinical claims without graph-triple
  support are marked `review_required` instead of silently presented as fully
  supported.
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

The endpoint is authenticated, read-only, and requires `data:read`. It does not
expose local filesystem paths beyond the repository-relative `source_ref` used
to identify the approved knowledge asset.

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

`GET /api/v1/assistant/examples`

Returns data-driven Assistant starter tasks from
`knowledge/assistant/examples.json`. These are visible starter tasks, not hidden
demo inputs. Selecting one fills the Assistant form; it does not execute until
the user submits.

Example response data:

```json
[
  {
    "example_id": "find_medical_standards",
    "label": "Find medical standards",
    "description": "Retrieve FHIR, LOINC, UCUM, policy, and schema evidence.",
    "message": "Find trusted evidence for HbA1c CSV rows with missing units.",
    "context": {
      "schema_id": "lab_result_v1",
      "fields": ["lab_name", "value", "unit"],
      "clinical_domain": "laboratory"
    }
  }
]
```

`GET /api/v1/assistant/answer-templates`

Returns governed answer templates from
`knowledge/assistant/answer_templates.json`. Use this endpoint when a UI,
MCP client, or evaluator needs the expected sections, evidence requirement, and
review conditions for a task class.

`GET /api/v1/assistant/prompt-injection-policy`

Returns the data-driven prompt-injection policy from
`knowledge/assistant/prompt_injection_policy.json`. The Assistant uses this
policy to wrap user messages, uploaded data, uploaded document metadata, manual
text snippets, selected workflow/retrieval context, retrieved chunks, tool
arguments, generated outputs, and model-visible tool metadata as untrusted
LLM-bound surfaces. Tool metadata is scanned before Assistant service
construction and cannot grant permissions or override backend policy.

Assistant LLM-generated plans and answer summaries are validated before
execution/display. Failed generated plans fall back to deterministic planning;
failed generated summaries keep the deterministic answer fallback. Streaming
answers validate cumulative output before emitting each delta. See
`docs/generated_output_validation_v0.md`.

`GET /api/v1/assistant/mcp/resources`

Returns the MCP resource catalog from `knowledge/assistant/mcp_resources.json`.
Resources are read-only operational catalogs such as assistant tools, assistant
tool progress policies, retrieval strategies, source trust policies, workflows,
reviews, schemas, and knowledge source inventory.

`GET /api/v1/assistant/mcp/prompts`

Returns the MCP prompt catalog from `knowledge/assistant/mcp_prompts.json`.
Prompts define standard operator tasks, arguments, recommended tools, evidence
requirements, and write-action policy. They do not grant execution authority.

`GET /api/v1/assistant/mcp/remote-policy`

Returns the remote MCP deployment readiness policy from
`knowledge/assistant/remote_mcp_deployment_policy.json`. The policy is
data-driven and currently sets `remote_exposure_allowed=false` until OAuth
protected-resource metadata, resource indicators, per-user scoping, rate
limits, audit correlation, and tool manifest review controls are implemented
and verified.

`GET /api/v1/assistant/memory-policy`

Returns the data-driven allowlist from `knowledge/assistant/memory_policy.json`.
Only keys in this policy can be persisted as Assistant memory.

`GET /api/v1/assistant/memory`

Returns the authenticated user's safe operational preference snapshot:

```json
{
  "policy_version": "assistant_memory.v1",
  "preferences": [
    {
      "key": "evidence_detail_level",
      "value": "detailed",
      "category": "evidence",
      "source": "user"
    }
  ],
  "context": {
    "evidence_detail_level": "detailed"
  }
}
```

`PUT /api/v1/assistant/memory/{key}`

Sets one policy-allowlisted operational preference:

```json
{
  "value": "detailed",
  "source": "user"
}
```

The backend rejects unknown keys, denied key terms such as patient identifiers,
and value patterns that look like PHI, uploaded content, clinical facts, or raw
data. The route is for preferences such as explanation style, evidence detail,
and default retrieval strategy only.

`DELETE /api/v1/assistant/memory/{key}`

Deletes one stored preference for the authenticated user.

`GET /api/v1/assistant/sessions`

Lists persisted Assistant chat sessions for the authenticated user. Query
parameters:

- `include_archived`: include archived sessions when `true`; default `false`.
- `limit`: maximum sessions to return; default `100`.
- `q`: optional search text. Searches session titles and persisted message
  content for the authenticated user.

`POST /api/v1/assistant/sessions`

Creates a persisted Assistant chat session:

```json
{
  "title": "New chat"
}
```

When the title is omitted or set to `New chat`, the backend generates the
session title from the first appended user message. Generated titles are
intent-level summaries and avoid copying raw uploaded content or obvious
patient identifiers into the chat list. `PATCH` remains available for explicit
user renaming.

`GET /api/v1/assistant/sessions/{session_id}`

Returns the user-owned session summary and ordered messages.

`GET /api/v1/assistant/sessions/{session_id}/stream-replays`

Returns persisted SSE replay artifacts for a user-owned session. Replay
artifacts are stored separately from chat messages so support staff can inspect
stream order, tool progress, planner deltas, errors, and final response without
polluting the normal chat transcript or inflating message counts. Replay
`status` is one of `completed`, `failed`, or `cancelled`; `cancelled` means the
client disconnected or explicitly stopped the active stream before a final
assistant response was produced.

`PATCH /api/v1/assistant/sessions/{session_id}`

Renames a user-owned session:

```json
{
  "title": "Reviewed lab CSV"
}
```

`POST /api/v1/assistant/sessions/{session_id}/archive`

Archives a user-owned session. Archived sessions are hidden from the default
session list but can be returned with `include_archived=true`.

`DELETE /api/v1/assistant/sessions/{session_id}`

Deletes a user-owned session and its persisted messages.

`POST /api/v1/assistant/sessions/{session_id}/messages`

Appends a persisted message or tool artifact:

```json
{
  "role": "user",
  "content": "Validate this lab CSV and explain the issues with trusted evidence.",
  "workflow_refs": [],
  "payload": {
    "context": {
      "schema_id": "lab_result_v1",
      "input_format": "csv"
    }
  }
}
```

Session and message records are stored through the configured backend: memory
for tests, SQLite for local development, and Postgres for production-like
deployments. Session access is owner-scoped by authenticated user ID. Messages
include `workflow_refs` so the UI can deep-link chat turns to workflow runs.
If `workflow_refs` is omitted, the backend extracts common workflow reference
fields such as `workflow_id`, `workflow_ids`, `workflow_ref`, and
`workflow_refs` from the structured payload.

`POST /api/v1/assistant/chat`

`POST /api/v1/assistant/chat/stream`

Streams the same assistant operation over server-sent events for the browser
chat UI. The stream emits `planning_started`, `planning_step`, optional
`planning_delta`, optional fallback `planning_progress`, `plan_ready`,
`tool_started`, zero or more `tool_progress`, `tool_completed`, optional
`warning`, `synthesis_started`, zero or more `answer_delta`, optional
`cancelled`, optional `error`, and `final` events. Tool progress stages are loaded from
`knowledge/assistant/tool_progress_policies.json`, so labels and progress copy
are data-driven instead of hardcoded in the browser. When OpenAI is configured,
planning and answer synthesis use the OpenAI Responses streaming API. Planner
text/tool-plan deltas are forwarded as `planning_delta` before any backend tool
executes, so users can see the model is building a plan instead of watching a
black-box spinner. If a configured planner cannot stream, the backend still
emits `planning_progress` heartbeat events between `planning_started` and
`plan_ready`, including `elapsed_seconds`. If execution fails after response
headers have been sent, the backend emits a structured `error` event because
the HTTP status can no longer be changed. If the browser aborts the stream, the
backend records a `cancelled` replay status and appends a cancellation event to
the replay when possible.

Before planning, the API injects the authenticated user's safe Assistant memory
under `context.assistant_memory`. Caller-provided `assistant_memory` context is
removed first so clients cannot spoof stored preferences. Memory contains only
backend-validated operational preferences, never raw uploaded content, patient
identifiers, or clinical facts.

```json
{
  "message": "Validate this lab CSV and explain the issues with trusted evidence.",
  "session_id": "chat_abc123",
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

Failed tool recovery is explicit, not prompt-only. To retry a failed tool call,
send the original tool name and arguments in `context.assistant_recovery`; the
backend bypasses the LLM planner and executes that exact allowlisted tool plan:

```json
{
  "message": "Retry failed tool call retrieval_search.",
  "context": {
    "assistant_recovery": {
      "action": "retry_tool",
      "tool_name": "retrieval_search",
      "arguments": {
        "query": "HbA1c missing unit",
        "top_k": 3
      },
      "failed_status": "failed",
      "failed_summary": "Prior retrieval failed."
    }
  }
}
```

To continue without re-running failed tools, use `continue_after_failure`. This
produces a deterministic continuation response with no backend tool execution
and keeps the failed step unresolved for review:

```json
{
  "message": "Continue without retrying the failed tool call.",
  "context": {
    "assistant_recovery": {
      "action": "continue_after_failure",
      "failed_tool_calls": [
        {
          "tool_name": "retrieval_search",
          "status": "failed",
          "summary": "Prior retrieval failed."
        }
      ]
    }
  }
}
```

When `session_id` is supplied, each SSE event is stamped with `stream_id`,
`session_id`, `sequence`, and `created_at`. After the stream finishes or emits a
structured error, the backend persists one replay artifact for that stream.

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
- retrieval corrective actions appear as `findings[]` titled
  `Recommended search action` and as `suggestions[]` when a retrieval tool
  returns `recommended_actions[]`
- retrieval remediation appears as a `Retrieval remediation` finding and
  `Next retrieval step` suggestion when a retrieval package returns
  `remediation_summary`; direct retrieval-only deterministic answers also use
  that remediation as the top-level `message`, while validation-first answers
  continue to lead with validation findings
- `evidence_summary[].source_id`
- `evidence_summary[].claim`
- `evidence_summary[].trust_level`
- `evidence_summary[].confidence`
- `evidence_summary[].match_explanation`
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
- `generate_mapping_draft`
- `create_review_task`

`validate_with_evidence` is the preferred assistant path for healthcare data
quality questions because it validates the payload and retrieves standards
evidence in one response. `retrieval_search` and `validate_with_evidence`
support governed source scope through `clinical_domain`, `standard_system`,
`source_type`, exact `source_id`, and `trust_level`. `workflow_summary` is the
preferred assistant path for chat-based workflow inspection.

`start_workflow`, `generate_mapping_draft`, and `create_review_task` are write
actions. They return `status="requires_approval"` unless the request explicitly
sets `execute_write_actions=true`. `generate_mapping_draft` parses, validates,
retrieves evidence, and creates a transformation plan in `needs_human_review`
status without writing transformed output; approval or approve-with-edits can
execute later through the review workflow. `create_review_task` creates a
durable workflow in `needs_human_review` status with a pending human review and
audit event, so unresolved data quality, terminology, or evidence decisions can
leave the chat surface and enter the governed review queue. The assistant does
not expose review approval, rejection, cancellation, or destructive artifact
actions in v0.

The browser UI adds an additional operator confirmation before sending
`execute_write_actions=true`: it lists tools from the backend catalog where
`requires_approval=true`, shows risk and approval reason metadata, and blocks
the send action until the operator confirms the next write-enabled command.
The API remains the final enforcement boundary; unconfirmed or malicious clients
cannot bypass backend tool permission checks without explicitly setting
`execute_write_actions=true`.

`GET /api/v1/audit/records`

Lists generic append-only audit records visible to the authenticated user.
Query parameters:

- `action`: optional exact action filter such as
  `assistant.tool.validate_with_evidence` or `mcp.tool.start_workflow`.
- `workflow_id`: optional workflow correlation filter.
- `assistant_session_id`: optional Assistant chat session correlation filter.
- `limit`: maximum records to return; default `100`, maximum `500`.

Assistant tool execution and local MCP tool execution both write audit records
through the configured storage backend. Records include owner, action, actor,
status, request ID, Assistant session ID, workflow ID, workflow event refs,
input hash, output hash, and sanitized metadata. Raw tool arguments and raw
tool output are not stored in the generic audit record. Payload-like strings
such as `data`, `message`, `query`, and nested context strings are hashed before
hashing the audit input fingerprint.

Every generic audit record also includes v0 hash-chain fields written by the
repository append path: `chain_scope`, `chain_sequence`,
`previous_record_hash`, `record_hash`, `hash_algorithm`, and `chain_status`.
The chain is scoped per owner user. Existing pre-F130 records may not have these
fields; new records are linked going forward.

Example response data:

```json
[
  {
    "audit_id": "aud_abc123",
    "owner_user_id": "usr_123",
    "workflow_id": "wf_456",
    "workflow_event_refs": ["evt_parser", "evt_validation"],
    "assistant_session_id": "chat_789",
    "request_id": "req_20260611",
    "timestamp": "2026-06-11T00:00:00+00:00",
    "action": "assistant.tool.validate_with_evidence",
    "actor_id": "usr_123",
    "actor_type": "assistant",
    "status": "completed",
    "input_hash": "9f86d081884c7d659a2feaa0c55ad015...",
    "output_hash": "e3b0c44298fc1c149afbf4c8996fb924...",
    "chain_scope": "owner_user:usr_123",
    "chain_sequence": 12,
    "previous_record_hash": "bbf6f78c21058d6b...",
    "record_hash": "2165bf0330f7f3a2...",
    "hash_algorithm": "sha256",
    "chain_status": "linked",
    "metadata": {
      "tool_name": "validate_with_evidence",
      "argument_keys": ["data", "execute_write_actions", "schema_id"],
      "workflow_ids": ["wf_456"],
      "requires_approval": false,
      "data_char_count": 72
    }
  }
]
```

`GET /api/v1/audit/export`

Builds an owner-scoped JSON audit export package for compliance review.
Query parameters:

- `action`: optional exact action filter.
- `workflow_id`: optional workflow correlation filter.
- `assistant_session_id`: optional Assistant chat session correlation filter.
- `include_workflow_events`: includes append-only workflow events when
  `workflow_id` is supplied; default `true`.
- `limit`: maximum generic audit records to return; default `100`, maximum `500`.

The export package combines sanitized generic audit records with workflow events
when available. It also includes explicit coverage metadata for workflows,
reviews, Assistant/MCP tool calls, auth events, runtime setting changes, and
source ingestion. Scopes without current audit producers are reported as
`not_available` instead of being silently omitted.

Example response data:

```json
{
  "export_id": "audexp_abc123",
  "generated_at": "2026-06-11T00:00:00+00:00",
  "owner_user_id": "usr_123",
  "export_format": "json",
  "filters": {
    "workflow_id": "wf_456",
    "action": null,
    "assistant_session_id": null,
    "limit": 100,
    "include_workflow_events": true
  },
  "summary": {
    "record_count": 1,
    "workflow_event_count": 2,
    "covered_scope_count": 1,
    "partial_scope_count": 2,
    "unavailable_scope_count": 3,
    "includes_raw_payloads": false
  },
  "coverage": [
    {
      "scope": "assistant_tool_calls",
      "status": "covered",
      "record_count": 1,
      "event_count": 0,
      "description": "Assistant and local MCP tool calls write sanitized generic audit records with input/output hashes and correlation metadata.",
      "limitations": ["Raw tool arguments and raw tool output are intentionally excluded."]
    }
  ],
  "records": [],
  "workflow_events": []
}
```

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
- `profile.profile_registry_version`
- `profile.profiled_resource_types`
- `profile.profile_issues`
- `profile.search_parameters`
- `profile.profile_evidence`
- `profile.handoff_context`
- `evidence`

## Interoperability

`GET /api/v1/interoperability/analytics/omop/mapping-profile`

Returns the data-driven OMOP preview mapping profile. Response data includes
`profile_id`, `target_cdm`, supported target tables, row rules, field mappings,
review policy, standard refs, and warnings.

`POST /api/v1/interoperability/analytics/omop/preview`

Previews how a `ClinicalPackage` maps into OMOP target tables. Request:

```json
{
  "package": {
    "package_type": "ojtflow_clinical_package",
    "schema_version": "clinical_package.v0",
    "workflow_id": "wf_demo",
    "raw_input": {
      "dataset_ref": "storage://datasets/demo",
      "input_hash": "sha256:demo",
      "declared_format": "csv",
      "detected_format": "csv"
    },
    "clinical_bundle": {
      "resourceType": "Bundle",
      "type": "collection",
      "entry": [],
      "resources": []
    },
    "operation_outcome": {"resourceType": "OperationOutcome", "issue": []}
  }
}
```

Response data includes `table_previews[]`, `total_rows`,
`vocabulary_candidates[]`, concept coverage, unmapped fields, data-quality
warnings, and `review_required`.

`GET /api/v1/interoperability/analytics/omop/dqd-compatibility`

Returns OHDSI Data Quality Dashboard compatibility notes and future integration
path. OJTFlow preview data is not a replacement for running DQD against a real
OMOP database.

`GET /api/v1/interoperability/analytics/cohort-research-workflow`

Returns the cohort/research workflow concept, intended use, prohibited uses,
required approvals, output artifacts, and controls that keep analytics separate
from clinical decision support.

`GET /api/v1/interoperability/external/connectors`

Returns the governed external source connector registry for PubMed,
ClinicalTrials.gov, openFDA, LOINC, UCUM, RxNav, and FHIR docs. Each connector
declares auth requirements, rate-limit policy, license notes, update cadence,
allowed use, prohibited use, cache policy, and ingestion approval requirements.

`GET /api/v1/interoperability/external/cache-policy`

Returns external API cache key fields, required metadata fields, default TTL,
stale-while-revalidate window, invalidation triggers, privacy controls, and
warnings.

`POST /api/v1/interoperability/external/cache/metadata`

Builds deterministic cache metadata for an external API response without
persisting the response. Request:

```json
{
  "connector_id": "pubmed",
  "endpoint_url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
  "query": "HbA1c LOINC Observation",
  "source_release_version": "fetched:2026-06-11",
  "response_text": "{\"count\":\"2\"}",
  "metadata": {"workspace_id": "default"}
}
```

Response data includes a cache key, hashed endpoint/query metadata,
source release version, fetch/expiry timestamps, response hash, and explicit
`searchable_after_approval=false`.

`GET /api/v1/interoperability/external/ingestion-approval-policy`

Returns the source ingestion approval policy. Newly fetched external documents
are candidates and are not searchable until the approval decision reaches
`approved_searchable`.

`POST /api/v1/interoperability/external/ingestion/approval-preview`

Previews whether an external source candidate may become searchable. Request:

```json
{
  "connector_id": "pubmed",
  "document_id": "pubmed-123",
  "source_url": "https://pubmed.ncbi.nlm.nih.gov/123/",
  "source_release_version": "fetched:2026-06-11",
  "license_accepted": true,
  "reviewer_approved": false,
  "contains_phi": false
}
```

Response data includes `state`, `searchable`, `required_actions[]`, and
warnings.

`GET /api/v1/interoperability/external/link-launchers`

Returns transparent external link launchers for official healthcare sources.
Launchers build visible URLs only; they do not fetch, cache, ingest, or index
external content.

`POST /api/v1/interoperability/external/link-launch`

Builds one transparent external URL. Request:

```json
{
  "launcher_id": "pubmed",
  "query": "HbA1c unit standard"
}
```

Response data includes the URL, the encoded query, connector/source metadata,
and warnings that PHI should not be sent to external sites.

`POST /api/v1/interoperability/export/etl-package`

Builds a provenance-preserving ETL manifest for analytics teams. Request:

```json
{
  "package": {
    "package_type": "ojtflow_clinical_package",
    "schema_version": "clinical_package.v0",
    "workflow_id": "wf_demo",
    "raw_input": {
      "dataset_ref": "storage://datasets/demo",
      "input_hash": "sha256:demo",
      "declared_format": "csv",
      "detected_format": "csv"
    },
    "clinical_bundle": {
      "resourceType": "Bundle",
      "type": "collection",
      "entry": [],
      "resources": []
    },
    "operation_outcome": {"resourceType": "OperationOutcome", "issue": []}
  },
  "include_resources": false
}
```

Response data includes `clinical_package_hash`, OMOP preview, resource manifest,
provenance record count, audit refs, output refs, and warnings.

`POST /api/v1/interoperability/fhir/bulk/import`

Parses FHIR Bulk Data-style NDJSON resources with lightweight validation.
Request:

```json
{
  "data": "{\"resourceType\":\"Patient\",\"id\":\"P001\"}\n{\"resourceType\":\"Observation\",\"id\":\"O001\",\"status\":\"final\"}\n",
  "source_ref": "bulk-fhir://demo/patient-observation.ndjson",
  "allowed_resource_types": ["Patient", "Observation"]
}
```

Response data includes `resource_count`, `resource_counts`, `resources[]`,
`rejected_line_count`, and `warnings[]`. Each resource includes line number,
resource type, optional ID, raw resource JSON, and warnings.

`POST /api/v1/interoperability/fhir/bulk/export-package`

Exports a `ClinicalPackage` as grouped FHIR-like NDJSON files. Request:

```json
{
  "package": {
    "package_type": "ojtflow_clinical_package",
    "schema_version": "clinical_package.v0",
    "workflow_id": "wf_demo",
    "raw_input": {
      "dataset_ref": "storage://datasets/demo",
      "input_hash": "sha256:demo",
      "declared_format": "csv",
      "detected_format": "csv"
    },
    "clinical_bundle": {
      "resourceType": "Bundle",
      "type": "collection",
      "entry": [],
      "resources": []
    },
    "operation_outcome": {"resourceType": "OperationOutcome", "issue": []}
  },
  "require_approval": true
}
```

Response data includes `package_id`, `workflow_id`, `approved_for_export`,
`files[]`, `resource_count`, and `warnings[]`. Each file includes resource type,
filename, NDJSON text, resource count, and output hash.

`POST /api/v1/interoperability/hl7v2/observations`

Parses a starter HL7 v2 ORU-style lab message and maps OBX segments into
FHIR-like Observation records with segment provenance. Request:

```json
{
  "data": "MSH|^~\\&|LAB|HOSP|OJT|OJT|202606111200||ORU^R01|MSG1|P|2.5\rPID|1||P001^^^MRN||DOE^JANE\rOBX|1|NM|4548-4^HbA1c^LN||7.4|%^percent|||||F|||20260611\r",
  "source_ref": "hl7v2://demo/oru-r01"
}
```

Response data includes parsed message segments, segment counts, patient ID,
Observation resources, field provenance, and warnings.

`POST /api/v1/interoperability/dicom/metadata`

Profiles DICOM metadata without reading pixel data and returns an
ImagingStudy-like mapping. Request:

```json
{
  "metadata": {
    "StudyInstanceUID": "1.2.3",
    "SeriesInstanceUID": "1.2.3.4",
    "SOPInstanceUID": "1.2.3.4.5",
    "Modality": "MR",
    "AccessionNumber": "ACC-001",
    "PatientIdentityRemoved": "YES"
  },
  "source_ref": "dicom://study/1.2.3"
}
```

Response data includes `profile` and `imaging_study`. PixelData is intentionally
excluded from the metadata profile.

`POST /api/v1/interoperability/document-reference`

Builds a DocumentReference-like resource for uploaded PDFs, images, notes, and
extracted reports. Request:

```json
{
  "document_id": "artifact_123",
  "filename": "lab-report.pdf",
  "content_type": "application/pdf",
  "source_ref": "storage://uploads/lab-report.pdf",
  "description": "Uploaded lab report"
}
```

Response data includes a `ClinicalResourceRecord` for the DocumentReference-like
resource plus warnings.

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
- `product_mode`
- `storage_backend`
- `persistent_storage`
- `postgres_configured`
- `redis_configured`
- `audit.hash_chain_written`
- `audit.hash_chain_required`
- `audit.hash_chain_required_configured`
- `review_policy.default_human_review_required`
- `review_policy.ocr_low_confidence_threshold`
- `retention.artifact_rule_count`
- `retention.artifact_policy_configured`
- `tools.registered_count`
- `tools.approval_required_count`
- `tools.write_gates_enabled`
- `rate_limit.enabled`
- `rate_limit.backend`
- `rate_limit.policy_configured`
- `rate_limit.redis_prefix_configured`
- `cost_controls.policy_configured`
- `cost_controls.llm_max_request_chars`
- `cost_controls.ocr_max_openai_vision_bytes`
- `cost_controls.embedding_max_request_inputs`
- `cost_controls.embedding_max_request_chars`
- `cost_controls.batch_max_total_bytes`
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
- `llm.runtime_settings.external_*` provider-policy switches
- `policy.no_mock_data`
- `policy.effective_no_mock_data`
- `policy.requires_real_llm`
- `policy.requires_persistent_storage`
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
- `retrieval.rule_packs[]` with sanitized `name`, `status`, `source`,
  `env_var`, `configured`, `rule_count`, `version`, and `content_hash`
- `upload.max_upload_bytes`
- `upload.max_inline_data_bytes`
- `upload.allowed_extensions`

Retrieval rule-pack entries may reference controlling environment variables
such as `OJT_QUERY_EXPANSION_RULES_PATH`, `OJT_FILTER_SUGGESTION_RULES_PATH`,
`OJT_QUERY_DIAGNOSTIC_RULES_PATH`, `OJT_QUERY_PROFILE_RULES_PATH`,
`OJT_RANKING_BOOST_RULES_PATH`,
`OJT_RETRIEVAL_EVALUATION_POLICY_PATH`, `OJT_CORRECTIVE_ACTION_RULES_PATH`,
`OJT_STRATEGY_RECOMMENDATION_RULES_PATH`,
`OJT_STANDARD_SEARCH_PLAYBOOK_RULES_PATH`, `OJT_EVIDENCE_BUCKET_RULES_PATH`,
`OJT_SEARCH_HINT_TARGETS_PATH`, and `OJT_FHIR_SEARCH_PARAMETERS_PATH`.
The response exposes the env var name, loaded status, rule-pack version, and
SHA-256 content hash, but not local paths.

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
      "planning_model": "chat-latest",
      "synthesis_model": "chat-latest",
      "vision_model": "gpt-4.1-mini",
      "openai_configured": true,
      "base_url": "https://api.openai.com/v1",
      "base_url_configured": true,
      "timeout_seconds": 30.0,
      "max_tool_calls": 4,
      "planning_progress_interval_seconds": 2.0,
      "runtime_settings_configured": true,
      "runtime_settings": {
        "llm_provider": "openai",
        "llm_model": "chat-latest",
        "llm_planning_model": "chat-latest",
        "llm_synthesis_model": "chat-latest",
        "llm_vision_model": "gpt-4.1-mini",
        "llm_base_url": "https://api.openai.com/v1",
        "llm_timeout_seconds": 30.0,
        "llm_max_tool_calls": 4,
        "llm_planning_progress_interval_seconds": 2.0,
        "external_openai_llm_enabled": true,
        "external_openai_llm_allow_phi": false,
        "external_openai_ocr_enabled": true,
        "external_openai_ocr_allow_phi": false,
        "external_openai_ocr_allow_unknown": true,
        "external_openai_embeddings_enabled": true,
        "external_openai_embeddings_allow_phi": false,
        "external_medical_search_enabled": true,
        "external_medical_search_allow_phi": false
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
        "embedding_provider": "openai",
        "embedding_model": "text-embedding-3-small",
        "embedding_dimensions": 384,
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
decisions are not editable through this endpoint. Requires `settings:write`.

Request:

```json
{
  "llm_provider": "openai",
  "llm_model": "gpt-4.1-mini",
  "llm_planning_model": "gpt-4.1-mini",
  "llm_synthesis_model": "gpt-4.1",
  "llm_vision_model": "gpt-4.1-mini",
  "llm_base_url": "https://api.openai.com/v1",
  "llm_timeout_seconds": 30.0,
  "llm_max_tool_calls": 4,
  "llm_planning_progress_interval_seconds": 2.0,
  "external_openai_llm_enabled": true,
  "external_openai_llm_allow_phi": false,
  "external_openai_ocr_enabled": true,
  "external_openai_ocr_allow_phi": false,
  "external_openai_ocr_allow_unknown": true,
  "external_openai_embeddings_enabled": true,
  "external_openai_embeddings_allow_phi": false,
  "external_medical_search_enabled": true,
  "external_medical_search_allow_phi": false
}
```

Response:

```json
{
  "data": {
    "settings": {
      "llm_provider": "openai",
      "llm_model": "gpt-4.1-mini",
      "llm_planning_model": "gpt-4.1-mini",
      "llm_synthesis_model": "gpt-4.1",
      "llm_vision_model": "gpt-4.1-mini",
      "llm_base_url": "https://api.openai.com/v1",
      "llm_timeout_seconds": 30.0,
      "llm_max_tool_calls": 4,
      "llm_planning_progress_interval_seconds": 2.0,
      "external_openai_llm_enabled": true,
      "external_openai_llm_allow_phi": false,
      "external_openai_ocr_enabled": true,
      "external_openai_ocr_allow_phi": false,
      "external_openai_ocr_allow_unknown": true,
      "external_openai_embeddings_enabled": true,
      "external_openai_embeddings_allow_phi": false,
      "external_medical_search_enabled": true,
      "external_medical_search_allow_phi": false
    },
    "reloaded": true
  },
  "error": null
}
```

`PUT /api/v1/runtime/retrieval-settings`

Persists editable retrieval runtime settings and reloads cached backend service
instances after validation. It accepts retrieval-scoped ranking controls and
embedding provider/model/dimension controls. Changing embeddings requires
running retrieval reindex before vector search is fully aligned. Secrets,
database URLs, OAuth settings, file paths, and model API keys are not editable
through this endpoint. Requires `settings:write`.

Request:

```json
{
  "embedding_provider": "openai",
  "embedding_model": "text-embedding-3-small",
  "embedding_dimensions": 384,
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
      "embedding_provider": "openai",
      "embedding_model": "text-embedding-3-small",
      "embedding_dimensions": 384,
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

`GET /api/v1/runtime/settings-history`

Returns append-only runtime settings history entries. Query parameters:

- `limit`: maximum entries to return; default `100`, maximum `500`.

Each entry includes `change_id`, `changed_at`, `surface`, `actor_id`,
`actor_email`, `reason`, `rollback_of`, and `changes[]` with old/new value
presence and value fields.

`POST /api/v1/runtime/settings-history/rollback`

Rolls back one runtime settings history entry and appends a rollback history
entry. Request:

```json
{
  "change_id": "rsh_abc123",
  "reason": "Rollback after pilot validation."
}
```

Response data includes:

- `settings.assistant`
- `settings.retrieval`
- `reloaded`
- `history_entry`

`GET /api/v1/runtime/secrets/health`

Returns sanitized secret/config readiness for admins. The response never
includes secret values, DSNs, token prefixes, or hashes.

Response data includes:

- `status`
- `product_mode`
- `storage_backend`
- `secret_values_exposed`
- `checks[].name`
- `checks[].status`
- `checks[].configured`
- `checks[].required`
- `checks[].env_vars`
- `checks[].remediation`

`GET /api/v1/runtime/ai-risk-register`

Returns the data-driven AI risk register for admins. Requires `admin:read`.
The register is aligned to NIST AI RMF-style governance and is used as an
operator-visible control map, not as a legal compliance certification.

Response data includes:

- `version`
- `standard_refs[]`
- `intended_system_use`
- `prohibited_uses[]`
- `risks[].risk_id`
- `risks[].title`
- `risks[].intended_use`
- `risks[].limitation`
- `risks[].nist_ai_rmf_functions[]`
- `risks[].genai_profile_risk_areas[]`
- `risks[].severity`
- `risks[].likelihood`
- `risks[].residual_risk`
- `risks[].owner_role`
- `risks[].monitoring_signals[]`
- `risks[].human_oversight`
- `risks[].controls[]`
- `risks[].evidence_refs[]`

Example:

```json
{
  "data": {
    "version": "ai_risk_register.v1",
    "standard_refs": [
      "NIST AI RMF 1.0: GOVERN, MAP, MEASURE, MANAGE"
    ],
    "intended_system_use": "Governed healthcare data operations assistant for parsing, validating, retrieving trusted evidence, explaining data quality issues, and preparing human-reviewed workflow outputs.",
    "prohibited_uses": [
      "Diagnosis, treatment, triage, or patient-specific medical advice."
    ],
    "risks": [
      {
        "risk_id": "AIR-001",
        "title": "Clinical misuse or diagnostic overreach",
        "intended_use": "Data operations support only.",
        "limitation": "The assistant may retrieve medical standards but must not provide diagnosis, treatment, or triage.",
        "nist_ai_rmf_functions": ["GOVERN", "MAP", "MANAGE"],
        "genai_profile_risk_areas": ["human-AI configuration", "information integrity"],
        "severity": "critical",
        "likelihood": "medium",
        "residual_risk": "medium",
        "owner_role": "clinical safety owner",
        "monitoring_signals": [
          "clinical_advice_prompt",
          "blocked_output_validation",
          "human_review_override_request"
        ],
        "human_oversight": "Clinical or data-steward review is required before workflow output is used operationally.",
        "controls": [
          {
            "control_id": "AIR-001-C1",
            "title": "Assistant policy blocks diagnosis/treatment claims",
            "implementation_ref": "src/ojtflow/infrastructure/llm/openai.py",
            "status": "implemented"
          }
        ],
        "evidence_refs": ["docs/generated_output_validation_v0.md"]
      }
    ]
  },
  "error": null
}
```

`GET /api/v1/runtime/disclaimers`

Returns user-facing product boundary disclaimers for authenticated users. This
route is intentionally available to normal users because the non-diagnostic,
non-treatment, human-reviewed intended-use boundary must be visible during
ordinary operation.

Response data includes:

- `version`
- `intended_use`
- `non_diagnostic_statement`
- `human_review_requirement`
- `prohibited_uses[]`
- `surfaces[].surface_id`
- `surfaces[].title`
- `surfaces[].message`
- `surfaces[].severity`
- `surfaces[].review_required`
- `surfaces[].prohibited_uses[]`
- `surfaces[].human_review_text`
- `surfaces[].evidence_text`

Example:

```json
{
  "data": {
    "version": "disclaimer_policy.v1",
    "intended_use": "OJTFlow supports healthcare data operations: parsing, validation, evidence retrieval, workflow review, and governed export preparation.",
    "non_diagnostic_statement": "OJTFlow is not a diagnostic, treatment, triage, or patient-specific medical advice system.",
    "human_review_requirement": "Meaning-changing transformations, sensitive-field decisions, weak evidence, terminology choices, and workflow outputs require qualified human review before operational use.",
    "prohibited_uses": [
      "Do not use OJTFlow to diagnose, treat, triage, or recommend patient care."
    ],
    "surfaces": [
      {
        "surface_id": "assistant",
        "title": "Assistant Boundary",
        "message": "The Assistant can explain data quality issues, find trusted evidence, and run governed tools. It must not diagnose, recommend treatment, or approve clinical actions.",
        "severity": "caution",
        "review_required": true,
        "prohibited_uses": ["Clinical advice"],
        "human_review_text": "Write actions and meaning-changing outputs stay review-gated.",
        "evidence_text": "Assistant answers should cite evidence or clearly state missing evidence."
      }
    ]
  },
  "error": null
}
```

`GET /api/v1/runtime/owasp-llm-threat-model`

Returns the data-driven OWASP LLM Top 10 threat model for admins. Requires
`admin:read`. The model maps OWASP LLM risk categories to OJTFlow surfaces,
monitoring signals, concrete mitigation code, and focused tests.

Response data includes:

- `version`
- `standard_ref`
- `source_url`
- `categories[].category_id`
- `categories[].category_name`
- `categories[].owasp_ref`
- `categories[].risk_statement`
- `categories[].applicable_surfaces[]`
- `categories[].mitigations[]`
- `categories[].monitoring_signals[]`
- `categories[].residual_risk`
- `categories[].residual_risk_note`
- `categories[].roadmap_refs[]`
- `categories[].evidence_refs[]`

Each mitigation includes:

- `mitigation_id`
- `title`
- `status`
- `owner_role`
- `implementation_refs[]`
- `test_refs[]`
- `notes`

Example:

```json
{
  "data": {
    "version": "owasp_llm_threat_model.v1",
    "standard_ref": "OWASP Top 10 for LLM Applications 2025",
    "source_url": "https://genai.owasp.org/llm-top-10/",
    "categories": [
      {
        "category_id": "LLM01",
        "category_name": "Prompt Injection",
        "owasp_ref": "https://genai.owasp.org/llmrisk/llm01-prompt-injection/",
        "risk_statement": "Uploaded data, retrieved chunks, user messages, or tool metadata can try to override system instructions or trigger unauthorized tool use.",
        "applicable_surfaces": [
          "assistant_planner",
          "assistant_synthesis",
          "retrieval_chunks"
        ],
        "mitigations": [
          {
            "mitigation_id": "LLM01-M1",
            "title": "Wrap untrusted content and scan prompt-injection patterns before LLM-bound use",
            "status": "implemented",
            "owner_role": "security owner",
            "implementation_refs": [
              "src/ojtflow/core/policy/prompt_injection_policy.py"
            ],
            "test_refs": ["tests/test_assistant_safety.py"],
            "notes": "User data and retrieved evidence are marked as untrusted content."
          }
        ],
        "monitoring_signals": ["prompt_injection_assessment"],
        "residual_risk": "medium",
        "residual_risk_note": "Instruction separation reduces but cannot eliminate adversarial text risk.",
        "roadmap_refs": ["F118", "F127"],
        "evidence_refs": ["docs/assistant_safety_cases_v0.md"]
      }
    ]
  },
  "error": null
}
```

`GET /api/v1/runtime/readiness`

Returns sanitized readiness diagnostics for authenticated operators with
`admin:read`. This is
separate from the public raw `GET /health` liveness probe: `/health` should stay
cheap enough for Docker/load balancer checks, while readiness verifies that the
backend can reach the runtime spine: storage, migrations, auth/session cache,
model provider configuration, MCP tool metadata, workflow repository, schemas,
retrieval assets, background jobs, and sampled artifact references.
The response must not expose DSNs, OAuth secrets, Redis URLs, ADC material,
session tokens, or local filesystem paths.

Response data includes:

- `status`: `ready`, `degraded`, or `not_ready`.
- `checks[]`: named checks with `status`, `summary`, and sanitized `details`.

Current checks:

- `settings`
- `postgres_migrations`
- `artifact_directory`
- `auth_configuration`
- `session_cache`
- `embedding_configuration`
- `llm_configuration`
- `mcp_tool_registry`
- `retrieval_rule_packs`: data-driven retrieval policy/rule-pack availability.
- `workflow_repository`
- `background_job_repository`: owner-scoped job repository probe, runner mode,
  queue-backed support flag, and supported job type inventory.
- `schema_inventory`
- `retrieval_inventory`: source inventory plus a bounded retrieval search probe.
- `storage_consistency`: sampled workflow input/output artifact refs and hashes.

`postgres_migrations` validates the source migration manifest for all backends.
In Postgres mode it also compares the manifest with `ojtflow.schema_migrations`
and reports pending versions, unknown applied versions, and checksum mismatches
without exposing the DSN.
The same data is available in the Settings page and through
`GET /api/v1/runtime/migrations` for admin drill-down.
In Postgres mode, `session_cache` verifies that Redis can be reached with a
short ping. If Redis is missing or unavailable, readiness returns
`status = "not_ready"` because process-local OAuth/session fallback is not
multi-instance safe for Postgres deployments.
`auth_configuration` reports whether Google OAuth is fully configured and
whether hosted-domain restrictions and cookie settings are active. Partial OAuth
configuration is an error because the login path cannot work with only one of
client ID or client secret.
`embedding_configuration` and `llm_configuration` verify that selected providers
are internally consistent. Selecting OpenAI mode without an API key is an error;
deterministic embeddings or disabled LLM mode are valid for local/dev mode and
are reported explicitly.
`mcp_tool_registry` checks that tool metadata has unique names and scoped
allowed-agent metadata before those tools are exposed to MCP clients.
For file artifacts, `artifact_directory` performs safe create/delete probes in
the data, dataset, and output directories and returns only booleans and error
types, never local filesystem paths.
For schemas, `schema_inventory` must load at least one trusted profile. If the
configured knowledge directory yields zero schemas, readiness returns
`status = "not_ready"` because default schema-backed workflows cannot run.
For retrieval rule packs, `retrieval_rule_packs` verifies that data-driven
query expansion, filter suggestion, query diagnostic, ranking boost, evaluation
policy, corrective-action, evidence-bucket, and search-hint target files are
loadable. If any pack is missing or malformed, readiness returns
`status = "not_ready"` and exposes only sanitized pack metadata such as name,
status, source, env var, rule count, version, and content hash.
For retrieval, `retrieval_inventory` runs a small approved-source query through
the same workflow retrieval service path and reports only operational metadata:
`source_count`, `probe_hit_count`, `probe_strategy`, `probe_candidates_seen`, and
`probe_warning_count`.
If no trusted retrieval sources are loaded, readiness returns
`status = "not_ready"` because evidence-backed workflows cannot run. If sources
exist but the bounded probe returns no evidence, readiness returns
`status = "degraded"` so operators can investigate retrieval quality without
blocking all startup.
For persistent storage, `storage_consistency` samples the authenticated user's
visible workflows and checks local artifact references from workflow input,
extracted dataset handoff context, step output refs, and transformation output
refs. It also samples persisted dataset metadata rows and checks that dataset
rows point to existing files, that workflow artifact refs have backing dataset
rows, and that dataset/file hashes agree. When hashes are present it streams
files and compares SHA-256 digests. The check returns counts and sanitized
examples with workflow ID, dataset ID, label, and error type, never file paths
or storage refs. Memory storage skips this check.
If a readiness check fails, the check is marked `error` and exposes only a
sanitized `error_type`; exception messages, DSNs, Redis URLs, and local paths are
not returned.

`GET /api/v1/runtime/performance-budgets`

Returns the data-driven performance budget catalog for authenticated operators
with `admin:read`. Response data includes catalog ID, version, environment,
metrics, p95/ratio/count budgets, blocking flags, measurement commands, notes,
and warnings. These are CI/local smoke budgets, not production SLOs.

`GET /api/v1/runtime/load-smoke-plan`

Returns bounded load-smoke scenarios for workflow creation, retrieval search,
assistant stream, upload parsing, reindexing, and runtime readiness. Response
data includes method, path, repetitions, warmup requests, expected status, p95
budget, error-ratio budget, description, notes, and warnings.

`GET /api/v1/runtime/observability-dashboard`

Returns the observability dashboard signal contract for authenticated operators
with `admin:read`. Response data includes dashboard panels for API health,
workflow throughput, assistant streaming, retrieval quality, background jobs,
governance/security, and LLM/OCR cost. The endpoint exposes the dashboard spec,
not a hosted metrics backend.

`GET /api/v1/runtime/release-gates`

Returns CI, release, and manual deployment gate definitions. Response data
includes gate ID, category, required/recommended/manual status, command,
evidence, owner, blocking flag, notes, and warnings.

`GET /api/v1/runtime/deployment-smoke-plan`

Returns deployment smoke targets and expected checks. Response data includes
frontend/API targets, URL env vars, default URLs, required and optional paths,
expected statuses, required env variables, and warnings. The runnable smoke
command is `PYTHONPATH=src python scripts/deployment-smoke.py`.

`GET /api/v1/runtime/migrations`

Returns sanitized migration diagnostics for authenticated operators. For
non-Postgres storage backends this validates the source manifest and returns
`status = "not_required"`. For Postgres it compares the manifest with
`ojtflow.schema_migrations`.

Response data includes:

- `status`: `ok`, `warning`, `error`, or `not_required`.
- `required`: whether Postgres migration state is required for the active
  storage backend.
- `bootstrap_code`: one of the operator-facing classifications such as `ok`,
  `not_required`, `pending_migrations`, `migration_history_conflict`,
  `dependency_unavailable`, `missing_dsn`, `bad_dsn`, `auth_failed`,
  `dns_failed`, `network_refused`, `network_timeout`, `missing_extension`, or
  `duplicate_migration`.
- `bootstrap_summary`: sanitized operator summary without DSNs or raw database
  error text.
- `manifest_count`, `applied_count`, `pending_count`,
  `unknown_applied_count`, and `checksum_mismatch_count`.
- `latest_available_version` and `latest_applied_version`.
- `migrations[]`: version, name, checksum, status, `applied_at`,
  nullable `duration_ms`, and nullable `failure_reason`.

`duration_ms` is populated for migrations applied by the updated runner. Older
rows may show `null` and should render as "not recorded". Failed migration
attempts are reported as bootstrap diagnostics rather than inserted into the
applied migration ledger.

`GET /api/v1/runtime/storage-consistency`

Returns a direct sanitized storage consistency report for authenticated
operators. This is the drill-down view behind the `storage_consistency`
readiness check.

Query parameters:

- `limit`: number of visible workflows to sample for the authenticated user,
  from `1` to `500`; default is `100`.

Response data includes:

- `status`: `consistent` or `inconsistent`.
- `report.required`: whether persistent file-backed storage is active.
- `report.sampled_workflow_count`: number of workflow states inspected.
- `report.artifact_ref_count`: number of workflow artifact refs extracted.
- `report.dataset_record_count`: number of dataset metadata rows inspected.
- `report.checked_hash_count`: number of refs with SHA-256 hashes checked.
- `report.checked_dataset_file_count`: number of dataset row files hashed.
- `report.missing_count`: missing, unsupported, or out-of-root artifact refs.
- `report.missing_dataset_file_count`: dataset rows whose file ref is missing,
  unsupported, or outside the configured artifact roots.
- `report.missing_dataset_record_count`: workflow artifact refs without a
  sampled dataset metadata row.
- `report.hash_mismatch_count`: artifacts whose content hash differs from
  workflow state.
- `report.dataset_hash_mismatch_count`: dataset row files whose content hash
  differs from the dataset metadata row.
- `report.unreferenced_dataset_record_count`: dataset metadata rows not
  referenced by the sampled workflows. This is an orphan candidate count, not an
  automatic delete instruction.
- `report.examples[]`: sanitized workflow ID, dataset ID, label, and error type
  only.

The endpoint does not return file paths, storage refs, DSNs, secrets, or raw
artifact content. Memory storage returns `required = false`.

`GET /api/v1/runtime/storage-repair-plan`

Returns a sanitized, non-destructive repair plan derived from the same workflow
and dataset sample as the storage consistency report.

Query parameters:

- `limit`: number of visible workflows to sample, from `1` to `500`; default
  is `100`.
- `max_candidates`: number of repair candidates to return, from `1` to `500`;
  default is `100`.

Response data includes:

- `status`: `not_required`, `no_action_needed`, or `review_required`.
- `plan.required`: whether file-backed persistent storage is active.
- `plan.dry_run`: always `true`; the plan endpoint does not mutate anything.
- `plan.mutation_applied`: always `false`.
- `plan.scanned_file_count`: number of files scanned in configured dataset and
  output artifact directories.
- `plan.total_candidate_count` and `plan.returned_candidate_count`.
- `plan.candidates[]`: sanitized candidate ID, kind, severity, recommended
  action, workflow ID, dataset ID, artifact-ref hash, and bounded evidence.

Candidate kinds include `missing_artifact_ref`, `missing_dataset_record`,
`missing_dataset_file`, `hash_mismatch`, `dataset_hash_mismatch`,
`orphaned_dataset_record`, and `orphaned_file_artifact`.

`POST /api/v1/runtime/storage-repair-markers`

Builds the current repair plan and writes a sanitized marker artifact under the
runtime data directory when candidates exist. This is the first repair command:
it marks orphaned rows/files for operator review without deleting files or
mutating workflow/dataset rows. Requires `admin:write`.

Response `status` is `not_required`, `no_action_needed`, or `marked`. When
marked, response data includes a `marker` with `marker_id`, `marked_at`,
`candidate_count`, `candidate_ids`, `marker_ref_hash`, and `destructive=false`.
The response still does not expose local paths or raw storage refs.

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

Returns the active identity, user, session metadata, and `service_account`
metadata when the bearer token belongs to an automation identity.

`GET /api/v1/auth/service-accounts`

Requires `users:read`. Returns service accounts in the current organization by
default. `organization_id` can be supplied only when the caller is also a
member of that organization.

`POST /api/v1/auth/service-accounts`

Requires `users:write`. Creates a service-account user, attaches it to the
organization with an assignable RBAC `role_key`, and returns the first bearer
token once. The raw token is not persisted; only the SHA-256 hash is stored in
the existing session table.

Request:

```json
{
  "slug": "nightly-ingestion",
  "display_name": "Nightly Ingestion",
  "role_key": "operator",
  "token_ttl_seconds": 3600
}
```

Response data includes:

- `service_account`
- `token_type`
- `access_token`
- `expires_at`

Service-account bearer tokens use the same API header:

```text
Authorization: Bearer ojt_sa_...
```

After authentication, service accounts are governed by the same ownership and
RBAC checks as human users.

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

## Organization Workspaces

`GET /api/v1/organizations/current`

Returns the authenticated user's current organization workspace. If the user has
no active organization membership yet, the backend creates a default workspace
from `knowledge/governance/workspace_defaults.json`.

Response data includes:

- `organization.organization_id`
- `organization.slug`
- `membership.user_id`
- `membership.role_key`
- `groups`
- `group_memberships`
- `settings.settings`
- `settings.version`

`GET /api/v1/organizations`

Lists organization workspaces visible to the authenticated user. The v0 backend
bootstraps a default workspace when none exists.

`GET /api/v1/governance/rbac-policy`

Returns the active data-driven role and permission catalog from
`knowledge/governance/rbac_roles.json`.

Response data includes:

- `version`
- `permissions[].permission_scope`
- `permissions[].risk_level`
- `roles[].role_key`
- `roles[].permission_scopes`
- `roles[].assignable`
- `roles[].system_role`

`PATCH /api/v1/organizations/{organization_id}/settings`

Deep-merges workspace-level settings and increments the settings version.

Example request:

```json
{
  "settings": {
    "review_policy": {
      "low_confidence_threshold": 0.75
    },
    "assistant": {
      "write_actions_require_confirmation": true
    }
  }
}
```

`POST /api/v1/organizations/{organization_id}/groups`

Creates a group in the organization workspace for future RBAC and assignment
workflows.

Example request:

```json
{
  "slug": "data-stewards",
  "display_name": "Data Stewards",
  "description": "Users responsible for data quality review.",
  "role_keys": ["data-steward"]
}
```

F119 stores role keys and groups but does not enforce full RBAC. F120 defines
role-to-permission policy, and F121 applies ownership checks across workflows,
reviews, chat sessions, artifacts, source inventory, runtime settings, and
exports.

## Retrieval Plan

`POST /api/v1/retrieval/plan`

Uses the same request shape as retrieval search, but returns a plan-only retrieval response:
query planning only. It does not rank evidence, touch the vector index, or generate graph
handoff context. Use it to preview route/profile, query aspects, rewrites,
executable retrieval tasks, filter suggestions, and external medical search
hints before running a full search.

```json
{
  "query": "HbA1c lab CSV missing units FHIR Observation",
  "top_k": 5,
  "schema_id": "lab_result_v1",
  "fields": ["date", "patient_id", "lab_name", "value", "unit"],
  "clinical_domain": "laboratory",
  "trust_level": "approved"
}
```

Response data is a `RetrievalPlan`:

- `query`: normalized `RetrievalQuery`
- `query_analysis`: the same deterministic analysis later used by retrieval,
  including `query_profile`, `query_aspects`, `query_variant_details`,
  `retrieval_tasks`, `filter_suggestions`, `diagnostics`, and `search_hints`
- `coverage_summary`: backend-owned pre-search readiness summary for local
  task coverage, external follow-ups, inferred standards, filters, warnings, and
  a human-readable summary sentence plus `next_action`
- `task_summary`: backend-owned execution summary with task counts for runnable
  local searches, required local searches, external open/copy follow-ups,
  blocked tasks, a `primary_action`, and a human-readable summary
- `risk_signals[]`: prioritized backend pre-search risks, each with `code`,
  `severity`, `message`, `suggested_action`, `source`, and `metadata`
- `search_signature`: stable signature for the normalized request
- `summary`: short human-readable plan summary

`query_analysis.retrieval_tasks[]` is the ordered execution plan. Each task
includes `task_id`, `target` (`local_corpus` or `external_medical_index`),
`action_type` (`run_local_search`, `open_external_url`, or `copy_query`),
`query`, `rationale`, `priority`, `required`, optional `aspect_id` or
`search_hint_target`, `query_variants`, `standards`, `suggested_filters`, and
`warnings`. This is the user-facing bridge between query planning and the
backend tools that will run or launch the search.

When external-provider policy blocks `external_medical_search`, retrieval keeps
local corpus tasks but suppresses external search hints and external
`retrieval_tasks` before returning plan/search handoff metadata. The response
adds an `external_medical_search_policy_blocked` diagnostic or trace safety flag
with the policy reason, rather than exposing PHI-bearing external query strings.

Example response envelope:

```json
{
  "data": {
    "query": {
      "query": "HbA1c lab CSV missing units FHIR Observation",
      "workflow_id": null,
      "fields": ["date", "patient_id", "lab_name", "value", "unit"],
      "schema_id": "lab_result_v1",
      "detected_format": null,
      "resource_type": null,
      "top_k": 5,
      "filters": {
        "clinical_domain": "laboratory",
        "trust_level": "approved"
      }
    },
    "query_analysis": {
      "strategy": "postgres_fts_vector_rrf",
      "query_profile": {
        "intent": "schema_validation",
        "clinical_domain": "laboratory",
        "risk_level": "moderate"
      },
      "query_aspects": [
        {
          "aspect_id": "schema_fields",
          "label": "Required lab-result fields",
          "query": "lab result required fields date patient_id value unit",
          "priority": 1,
          "required": true
        }
      ],
      "query_variant_details": [],
      "retrieval_tasks": [
        {
          "task_id": "local_schema_fields",
          "label": "Search trusted local corpus for required lab fields",
          "target": "local_corpus",
          "action_type": "run_local_search",
          "query": "lab result required fields date patient_id value unit",
          "rationale": "Ground validation against approved local schemas before showing evidence.",
          "priority": 1,
          "required": true,
          "aspect_id": "schema_fields",
          "search_hint_target": null,
          "query_variants": ["lab result required fields date patient_id value unit"],
          "standards": ["FHIR", "UCUM"],
          "suggested_filters": {
            "schema_id": "lab_result_v1",
            "source_type": "schema"
          },
          "warnings": [],
          "metadata": {}
        },
        {
          "task_id": "external_fhir_observation",
          "label": "Review FHIR Observation reference externally",
          "target": "external_medical_index",
          "action_type": "open_external_url",
          "query": "FHIR Observation laboratory result units",
          "rationale": "Use external standards pages as manual follow-up; do not treat them as executed local evidence.",
          "priority": 4,
          "required": false,
          "aspect_id": null,
          "search_hint_target": "FHIR Observation",
          "query_variants": ["FHIR Observation laboratory result units"],
          "standards": ["FHIR"],
          "suggested_filters": {},
          "warnings": ["External follow-up is not automatically ingested."],
          "metadata": {
            "url": "https://hl7.org/fhir/observation.html"
          }
        }
      ],
      "filter_suggestions": [],
      "diagnostics": [],
      "search_hints": []
    },
    "coverage_summary": {
      "ready": true,
      "local_task_count": 1,
      "required_local_task_count": 1,
      "external_task_count": 1,
      "standard_count": 2,
      "filter_count": 2,
      "standards": ["FHIR", "UCUM"],
      "warnings": [],
      "next_action": "Run required local search tasks first, then review external follow-ups.",
      "summary": "Plan is ready for local evidence search with 1 required local task and 1 external follow-up."
    },
    "task_summary": {
      "total_task_count": 2,
      "runnable_local_count": 1,
      "required_runnable_local_count": 1,
      "external_open_count": 1,
      "external_copy_count": 0,
      "manual_followup_count": 1,
      "blocked_task_count": 0,
      "primary_action": "Run required local search tasks first, then review external follow-ups.",
      "summary": "1 local runnable task(s), 1 external/manual follow-up(s), and 0 blocked task(s)."
    },
    "risk_signals": [],
    "search_signature": "sha256:example",
    "summary": "Prepared 2 retrieval task(s) for review-grade healthcare evidence search."
  },
  "error": null
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
    "source_type": "terminology_system",
    "source_id": "terminology:ucum"
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
- `quality_signals[]` with `code`, `severity`, `message`,
  `suggested_action`, `evidence_ids`, and `metadata`
- `recommended_actions[]` with ordered corrective retrieval actions and
  optional `suggested_filter`
- `recommended_action_summary` with corrective-action triage counts
- `remediation_summary` with the backend-derived operator next step
- `interpretation` with backend-derived package status, plain-language summary,
  top evidence/source IDs, score driver, support status, matched terms,
  concept/aspect labels, required bucket coverage, warnings, and next action
- `strategy_recommendations[]` with backend-owned retrieval technique and route
  explanations
- `standard_search_plan` with backend-owned healthcare-standard follow-up search
  steps, including route type, standard system, suggested query, governance
  notes, supported filters, and data-driven match metadata
- `diversity` with source-aware final-selection state, selected/candidate source
  counts, duplicate selected-source count, optional lambda value, and
  `selected_hits[]` rationale rows
- `trace.strategy`
- `trace.query_variants`
- `trace.query_variant_details[]` with `variant`, `source`, `reason`, and
  `metadata`
- `handoff_context.query_analysis.search_hints[]` with `target`, `query`,
  optional launch `url`, `rationale`, `warnings`, and optional metadata. FHIR
  hints can include `metadata.parameter_examples`,
  `metadata.lineage_followup`, `metadata.registry_version`, and
  `metadata.capability_warning`. LOINC and UCUM terminology hints can include
  authenticated endpoint scope, parameter examples, selected terminology
  terms, selected unit candidates, validation-operation metadata, and
  `metadata.launchable`. UCUM hints expose `url` only when the selected unit
  candidate is concrete.
- `trace.fusion_diagnostics` with hybrid/fusion observability such as method,
  diagnostic scope, lexical/vector overlap when available, selected-hit rank
  delta when available, dominant signal balance, and interpretation
- `trace.filters_applied`
- `trace.candidates_seen`
- `trace.final_hit_ids`
- `trace.safety_flags`
- `trace.warnings`
- `answer`: evidence-only retrieval answer with status, citations, claims,
  unsupported claims, missing-evidence gaps, source freshness warnings, and
  graph-path summary
- `handoff_context`
- `handoff_context.answer` mirrors the top-level answer for Assistant and MCP
  clients
- `handoff_context.graph_context`
- `handoff_context.query_analysis`
- `handoff_context.query_route` with selected route ID, strategy ID,
  retrieval mode, rationale, matched criteria, suggested filters, and risk
  controls from the data-driven query router
- `handoff_context.diversity` mirrors top-level `diversity` for assistant and
  agent handoff compatibility
- `handoff_context.quality_policy`
- `handoff_context.retrieval_rule_packs`
- `handoff_context.standard_search_plan`
- `handoff_context.search_request`
- `handoff_context.search_signature`
- `handoff_context.graph_record` when graph persistence is enabled

`trace.safety_flags` marks retrieval query context that should remain data-only
for downstream agents. Current values include
`prompt_injection_pattern_in_query` and `sensitive_field_context`.
`handoff_context.graph_context` uses contract `graph_ner_handoff.v0`. It is a
deterministic GraphRAG-lite handoff with query/evidence/standard/field/concept
nodes, `supports`, `mentions_entity`, `requests_resource`,
`has_search_parameter`, `uses_standard`, and `normalizes_to` edges, plus
summary counts. Entity rules come from
`knowledge/terminologies/graph_ner_rules.json`; medical concept-code
normalization comes from `knowledge/terminologies/medical_concepts.json`; FHIR
search-parameter expansion comes from
`knowledge/terminologies/fhir_search_parameters.json`. This is retrieval
grounding and audit metadata, not an autonomous clinical coding decision.
When graph persistence is enabled, the backend stores this graph context after
the search and returns `handoff_context.graph_record` with `graph_id`, workflow
and search metadata, node/edge/triple counts, and creation time. Graph records
are owner-scoped for direct API access.
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
`suggested_action`; each diagnostic also includes structured `metadata` such as
query token count, active metadata filters, applied standard, suggested
standards, detected concepts, and schema/format/resource context when relevant.
Warning diagnostics are copied into `trace.warnings`.
`query_analysis.query_route` is selected from
`knowledge/retrieval/query_route_rules.json` using query profile, input format,
resource type, active filters, diagnostics, concepts, standards, and tokens.
It is copied to `handoff_context.query_route` and mirrored to
`trace.fusion_diagnostics.query_route` for observability. This is an auditable
route-selection contract; v0 does not silently switch storage adapters or
bypass evidence-quality/review checks based on the route alone.
Diagnostics can flag low-specificity searches, missing healthcare concepts,
conflicting standard filters, and over-constrained metadata filters when the
query scope is narrow but clinical/schema context is weak. It
can include `query_profile`, a data-driven route hint with `profile_id`,
`label`, `route`, `complexity`, `retrieval_mode`, `description`,
`suggested_filters`, and contributing `rule_ids`; this is operator-visible
guidance for adaptive retrieval, not a hidden automatic route change. It can
include `query_aspects`, deterministic query-decomposition rows with
`aspect_id`, `label`, review `question`, `rationale`, `priority`, contributing
`rule_id`, `suggested_terms`, and `suggested_filters`; these rows help users
verify which medical evidence aspects the search should cover without silently
running hidden independent searches or producing clinical recommendations.
Matched aspects also contribute auditable `trace.query_variant_details[]` rows
with `source="query_aspect_rule"` so first-stage ranking uses the decomposition
plan transparently. Ranked hits may include
`source_locator.query_aspect_matches[]` with aspect ID, label, rule ID,
priority, matched filters, matched terms, and reason, allowing clients to show
which evidence supports which decomposed search aspect. It
also includes `search_hints`, deterministic external medical search syntax
scaffolds with `target`, `query`, optional `url`, `rationale`, and `warnings`
for workflows such as PubMed/MeSH literature search, FHIR resource search
templates, ClinicalTrials.gov API v2 study search, and openFDA drug
label/adverse-event search. Current targets include `pubmed`, `fhir`,
`clinicaltrials_gov`, `openfda_drug_label`, and `openfda_drug_event`.
If active external-provider policy blocks `external_medical_search`, these hints
are omitted from `handoff_context.query_analysis.search_hints` and corresponding
external tasks are omitted from `handoff_context.query_analysis.retrieval_tasks`.
`handoff_context.retrieval_rule_packs` records sanitized active retrieval
rule-pack fingerprints with pack name, status, source, env var, rule count,
version, and content hash. This lets copied evaluation reports and downstream
audit records identify the exact query-expansion, diagnostic, ranking,
query-profile, query-aspect, quality-gate, evaluation, and search-hint rule
data used for the search. `handoff_context.quality_policy` records the active
retrieval readiness policy version and severity scoring rules used to produce
`quality_summary`. `handoff_context.search_request` records the normalized
server-side retrieval request, and `handoff_context.search_signature` is a
stable `sha256:<digest>` fingerprint of that request for judgment, report, and
audit correlation.
The standard-search playbook rule pack is included in the same fingerprinted
inventory and drives `standard_search_plan`, including FHIR, terminology,
privacy, and external medical-search route guidance. A playbook rule can match
query profiles, detected standards, concepts, decomposed query aspects, dataset
field names, query tokens, resource type, quality signals, safety flags, and
required filters. This keeps route selection in backend rule data rather than
React copy or LLM-only reasoning.
`hits[].snippet` is an extractive preview with `text`, `start_char`, `end_char`,
`matched_terms`, and `extraction_strategy`. The full source claim remains in
`hits[].evidence.claim`.
`coverage` reports whether standards inferred from query analysis, such as
`FHIR`, `LOINC`, and `UCUM`, are represented in the final selected evidence.
Each `coverage.standard_system[]` item includes `suggested_action` and
`suggested_filter` so clients can present explicit remediation controls for
missing expected standards. Missing expected standards are returned as
`coverage.warnings` and copied into `trace.warnings`. `coverage.query_aspects[]`
uses the same coverage item shape for query-aspect plans that include supported
suggested filters. These items report whether selected evidence covers each
aspect's metadata criteria and expose the same explicit remediation filter
contract when coverage is missing.
`facets` summarizes the final selected hits into buckets for `source_type`,
`clinical_domain`, `standard_system`, and `trust_level`.
`quality_signals` is a deterministic retrieval-quality checklist for operator
review. It summarizes whether the package has hits, whether expected standard
coverage is complete, whether query-context safety flags were detected, and
whether selected evidence is source-diverse. These signals are observability and
review guidance, not clinical decision support.

Copyable `retrieval_run_comparison` reports include active/baseline
`query_aspects` deltas with added, removed, and retained aspect summaries. This
lets relevance tuning notes distinguish decomposition coverage changes from
rank, quality-signal, facet, rule-pack, and evidence changes. The same report
includes `coverage` deltas with improved, regressed, added, removed, and
retained standard/aspect coverage diagnostics. Copyable `retrieval_cockpit`
and `retrieval_run_comparison` reports also include `remediation_summary`
fields derived from the same quality/action summaries shown in recent-run
history, so copied audit notes retain the operator-visible next step.

Retrieval endpoints require an authenticated session. Searches without
`workflow_id` run over the approved knowledge inventory. Searches with
`workflow_id` are owner-scoped; users cannot attach direct retrieval context to
another user's workflow by guessing an ID.
The `query` field and optional context fields are trimmed and must be non-blank
when supplied.
`filters` is a typed metadata filter object, not an arbitrary JSON bag. Current
supported keys are `trust_level`, `clinical_domain`, `standard_system`,
`source_type`, and exact `source_id`. Unsupported filter keys or invalid enum values return
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

`GET /api/v1/retrieval/source-policies` returns source trust policy catalog
data from `knowledge/source_catalog/source_trust_policies.json`, including
domain, standard system, intended use, prohibited use, refresh cadence, license
constraints, evidence tier, and reviewer policy.

`GET /api/v1/retrieval/strategies` returns data-driven retrieval strategy
presets from `knowledge/retrieval/strategy_catalog.json`, including lexical,
vector, hybrid, metadata-filtered, high-recall, and exact-source modes.

`GET /api/v1/retrieval/graph/contexts` returns persisted Graph-NER context
records owned by the authenticated user. Query parameters:

- `workflow_id`: optional workflow scope.
- `limit`: `1..1000`, default `100`.

`GET /api/v1/retrieval/graph/export` returns a `GraphExport` envelope for the
same owner/workflow scope. Query parameters:

- `workflow_id`: optional workflow scope.
- `limit`: `1..1000`, default `100`.
- `format`: `jsonl` for nodes/edges/triples or `rdf_jsonl` for
  subject/predicate/object triples only.

The export payload includes `content_type = application/x-ndjson`, aggregate
graph/node/edge/triple counts, `generated_at`, and `content` containing newline
delimited JSON. This is an operational export for downstream graph/RAG tools,
not a clinical decision-support artifact.

`GET /api/v1/retrieval/graph/neighborhood` returns a bounded
`GraphNeighborhood` from persisted Graph-NER records owned by the authenticated
user. Query parameters:

- `workflow_id`: optional workflow scope.
- `q`: optional text search over node labels, node metadata, triples, and
  source retrieval query text.
- `node_id`: optional exact Graph-NER node ID.
- `evidence_id`: optional evidence node/triple scope.
- `source_id`: optional evidence source ID.
- `normalized_code`: optional canonical code such as `LOINC:4548-4`.
- `resource_type`: optional FHIR-like resource type.
- `field`: optional data-field node label.
- `relation`: optional edge relation or triple predicate.
- `limit`: graph records scanned, `1..1000`, default `100`.
- `max_depth`: graph expansion depth, `0..2`, default `1`.

The response includes matching source graph IDs, aggregate node/edge/triple
counts, matched node/evidence IDs, bounded `nodes`, `edges`, `triples`, and
warnings when no persisted graph or criteria match exists. This endpoint is for
GraphRAG/evidence exploration and audit, not clinical decision support.

`GET /api/v1/retrieval/corpus/adapters` returns available corpus source adapter
definitions, including adapter ID, source family, ingestion mode, license notes,
and operational requirements.

`GET /api/v1/retrieval/corpus/manifest` returns the reviewed corpus source
manifest used by ingestion and readiness checks.

`GET /api/v1/retrieval/corpus/chunking-profiles` returns data-driven chunking
profiles for standards pages, terminology pages, structured records, PDFs, and
internal policies.

`GET /api/v1/retrieval/judgments` returns durable relevance judgments for the
authenticated user. Optional query parameters:

- `query`: exact query text; the backend hashes it for lookup.
- `run_id`: browser/search run identifier.
- `evidence_id`: evidence item identifier.
- `limit`: default `500`, maximum `1000`.

`GET /api/v1/retrieval/judgments/summary` returns aggregate label inventory for
the authenticated user, optionally filtered by `query`. Response data includes
`total_count`, `query_count`, `evidence_count`, `source_count`, per-value counts,
`average_rating`, `latest_updated_at`, and `sample_limit`.

`POST /api/v1/retrieval/judgments/evaluate` evaluates one ranked retrieval
result list against the authenticated user's stored judgments for the submitted
query:

```json
{
  "query": "FHIR Observation HbA1c unit",
  "ranked_evidence_ids": ["ev_schema_lab_result_v1", "ev_ucum_unit_policy"],
  "cutoff": 2
}
```

Response data includes `coverage_at_k`, `hit_rate_at_k`, `precision_at_k`,
`judged_precision`, `average_precision_at_k`, `mrr_at_k`, `ndcg_at_k`,
per-value counts, unjudged evidence IDs, the judgment IDs that contributed to
the score, `evaluation_readiness` with label confidence thresholds, and policy-driven
`recommendations[]` with severity, metric, message, suggested action, evidence
IDs, and rule metadata. This endpoint is intended for operator-facing
evaluation of the current ranked result list; it does not mutate judgments or
workflow state.

`PUT /api/v1/retrieval/judgments` upserts one user-scoped query/evidence
judgment:

```json
{
  "query": "FHIR Observation HbA1c unit",
  "evidence_id": "ev_schema_lab_result_v1",
  "source_id": "schema:lab_result_v1",
  "source_type": "schema",
  "value": "relevant",
  "rating": 3,
  "run_id": "browser-run-1",
  "search_signature": "{\"query\":\"FHIR Observation HbA1c unit\"}",
  "metadata": {
    "review_surface": "retrieval_console"
  }
}
```

The durable key is `(owner_user_id, query_hash, evidence_id)`. `run_id` and
`search_signature` are stored as trace metadata but are not the durable identity,
so rerunning the same query can reload prior labels for matching evidence.
`value` is one of `relevant`, `partial`, or `not_relevant`; `rating` is a graded
0-3 relevance score used by retrieval evaluation. If the UI omits `rating`, the
backend derives it from `value`.

`DELETE /api/v1/retrieval/judgments/{judgment_id}` removes one judgment owned by
the authenticated user.

`GET /api/v1/retrieval/sources` returns available trusted retrieval sources,
including source type, version, trust level, clinical domain, standard system,
and chunk count. The seeded source inventory includes local schema/governance
knowledge plus curated healthcare-standard assets under `knowledge/`, including
the official source catalog, medical concept seed registry, FHIR R4 search
parameter seed, clinical data standards map, medical search playbook, and public
dataset ingestion plan. Requires `retrieval:read`.

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
Requires `admin:read`.

`GET /api/v1/retrieval/freshness` returns a `RetrievalFreshnessReport` for the
governed retrieval source catalog. It combines corpus adapters, source trust
policies, the local corpus manifest, and currently indexed source inventory.

Response data includes `status`, `score`, source counts by readiness state,
`stale_count`, `unindexed_count`, `missing_policy_count`, catalog versions, and
`sources[]`. Each source includes lifecycle/reviewer state, refresh cadence,
indexed chunk count, last observed snapshot time, freshness window, issues, and
recommended actions. This endpoint is intended for RAG operations and medical
source governance; it does not perform live external fetching.
Requires `admin:read`.

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
authenticated session, `admin:write`, and does not accept arbitrary document text; corpus
files must be placed in configured trusted knowledge directories first.
Large official datasets such as MeSH RDF/XML, RxNorm/RxNav cache exports,
LOINC downloads, MedlinePlus XML, openFDA downloads, and ClinicalTrials.gov API
snapshots should be ingested into ignored runtime/object storage and then
distilled into reviewed knowledge chunks. They should not be committed directly
to source control. Corpus content comes from trusted runtime directories
configured by operators.

## Job Operations

Background jobs are durable, owner-scoped operational records for work that may
be moved to a queue-backed worker later. v0 includes a sync local runner so the
same job contract is available before worker execution is introduced.

`GET /api/v1/jobs`

Optional query parameters:

- `status`: `queued`, `running`, `succeeded`, `failed`, or `cancelled`.
- `job_type`: `retrieval_reindex`, `file_parse`, `ocr_extract`,
  `embedding_reindex`, `external_ingest`, or `export_package`.
- `limit`: `1` to `500`, default `100`.

Response data is an owner-scoped list of `BackgroundJob` objects with
`job_id`, `job_type`, `status`, `input`, `output`, structured `error`,
`progress`, attempts, and timestamps.

`GET /api/v1/jobs/{job_id}`

Returns one owner-scoped `BackgroundJob` or a structured not-found error.

`POST /api/v1/jobs/{job_id}/cancel`

Cancels a queued or running owner-scoped background job. Terminal jobs
(`succeeded`, `failed`, or `cancelled`) are returned unchanged. Cancelled jobs
store `status="cancelled"`, a structured `error.code="job_cancelled"`, a
progress message, and `completed_at`.

`POST /api/v1/jobs/retrieval-reindex`

Creates a durable retrieval reindex job. The default `execute_now=true` runs the
job through the sync local runner and records the output or structured failure
on the job row. The job `input` includes the originating `request_id` from the
API middleware so operations staff can connect the job record to frontend
diagnostics and backend logs.

```json
{
  "include_seeded": true,
  "include_corpus": true,
  "execute_now": true
}
```

Example response:

```json
{
  "data": {
    "job_id": "job_abc123",
    "owner_user_id": "user_123",
    "job_type": "retrieval_reindex",
    "status": "succeeded",
    "input": {
      "include_seeded": true,
      "include_corpus": true,
      "request_id": "web_123"
    },
    "output": {"repository": "postgres_fts_vector_rrf", "chunks_indexed": 42},
    "error": null,
    "progress": {"current": 1, "total": 1, "message": "Completed"},
    "attempts": 1,
    "max_attempts": 1,
    "created_at": "2026-06-11T00:00:00+00:00",
    "updated_at": "2026-06-11T00:00:01+00:00",
    "started_at": "2026-06-11T00:00:00+00:00",
    "completed_at": "2026-06-11T00:00:01+00:00"
  },
  "error": null
}
```

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
When OCR is configured, `auto` uses MarkItDown OCR plugins for OCR-sensitive
documents and direct OpenAI vision fallback for raw image files that still
produce empty text.

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
server-recognized upload extensions. `openai_vision` appears when an
OpenAI-compatible OCR key is available; MarkItDown OCR plugin support is part
of the `markitdown` extractor path.

`POST /api/v1/parse/upload/jobs`

Accepts a multipart file upload and creates a durable `file_parse` background
job. In local sync mode the job may complete before the response returns; in
queue-backed mode it remains queued for a worker. The uploaded bytes are stored
as an owner-scoped `UploadedArtifact` with hash, MIME type, byte size, source,
retention policy, and extraction trace metadata.

`POST /api/v1/parse/upload/batch/jobs`

Accepts multiple multipart files and creates one parse job per file with shared
batch metadata such as `batch_id`, `case_id`, and `project_id`. Each file still
gets its own artifact, dedupe check, job, and trace path.

`POST /api/v1/parse/clipboard/images/jobs`

Accepts pasted image bytes and creates the same artifact/job/trace path as a
file upload. The Assistant paste UX uses this route before injecting extracted
document context into chat.

`POST /api/v1/parse/redaction-preview`

Returns a deterministic PHI-like redaction preview for submitted text,
including structured CSV sensitive-column masking and span-level findings for
patterns such as SSNs, emails, and phone numbers. This route is intended to run
before external OCR/LLM handoff.

`GET /api/v1/parse/artifacts`

Lists uploaded artifacts owned by the authenticated user. Response data includes
artifact ID, filename, MIME type, extension, byte size, hash, source,
duplicate-of link, retention policy, metadata, and timestamps.

`GET /api/v1/parse/artifacts/{artifact_id}`

Returns one owner-scoped artifact metadata record.

`GET /api/v1/parse/artifacts/{artifact_id}/download`

Downloads the owner-scoped artifact bytes and records an artifact access event.

`GET /api/v1/parse/artifacts/{artifact_id}/export`

Exports owner-scoped artifact metadata as JSON and records an artifact access
event.

`GET /api/v1/parse/artifacts/{artifact_id}/traces`

Lists extraction traces for an owner-scoped artifact, including extractor
choice, fallback path, warnings, confidence, quality score, and output refs.

`GET /api/v1/parse/artifacts/{artifact_id}/access-events`

Lists owner-scoped artifact access events such as download, metadata export,
and metadata view.
