# External Provider Policy v0

F126 adds a configurable policy gate for data leaving the local OJTFlow runtime.
The goal is not to block useful AI features; the goal is to make every external
handoff explicit, auditable, and configurable before enterprise deployments send
healthcare data to OpenAI-compatible APIs or external medical search systems.

## Controlled Surfaces

The v0 policy controls these surfaces:

- `openai_llm`: Assistant planning and answer synthesis through the
  OpenAI-compatible Responses API.
- `openai_vision_ocr`: direct OpenAI-compatible vision OCR and MarkItDown OCR
  plugin usage.
- `openai_embeddings`: OpenAI-compatible embedding API calls for retrieval.
- `huggingface_embeddings`: local SentenceTransformers embeddings. This is
  represented in the policy contract even though it does not leave the runtime
  boundary.
- `external_medical_search`: generated external medical search hints, URLs, and
  query handoff metadata for sources such as PubMed, FHIR references,
  ClinicalTrials.gov, and openFDA.

## Default Behavior

Defaults are conservative for PHI:

- OpenAI-compatible LLM calls are enabled, but PHI is blocked by default.
- OpenAI-compatible OCR is enabled, but PHI is blocked by default. Unknown image
  sensitivity is allowed by default so image parsing continues to work in local
  development; set `OJT_EXTERNAL_OPENAI_OCR_ALLOW_UNKNOWN=false` to require an
  explicit local-only OCR path for unknown files.
- OpenAI-compatible embeddings are enabled, but PHI is blocked by default.
- External medical search hints are enabled, but PHI-bearing queries are blocked
  by default.
- Local Hugging Face embeddings are allowed with PHI because execution stays on
  the configured application host.

If a surface is blocked, the provider adapter raises `PolicyBlockedError` before
creating an outbound HTTP request. Retrieval keeps local corpus search working
and suppresses external search hints/tasks from handoff context when policy
blocks external medical search.

## Runtime Settings

These keys can be configured through environment variables and through
`PUT /api/v1/runtime/assistant-settings`:

```env
OJT_EXTERNAL_OPENAI_LLM_ENABLED=true
OJT_EXTERNAL_OPENAI_LLM_ALLOW_PHI=false
OJT_EXTERNAL_OPENAI_OCR_ENABLED=true
OJT_EXTERNAL_OPENAI_OCR_ALLOW_PHI=false
OJT_EXTERNAL_OPENAI_OCR_ALLOW_UNKNOWN=true
OJT_EXTERNAL_OPENAI_EMBEDDINGS_ENABLED=true
OJT_EXTERNAL_OPENAI_EMBEDDINGS_ALLOW_PHI=false
OJT_EXTERNAL_MEDICAL_SEARCH_ENABLED=true
OJT_EXTERNAL_MEDICAL_SEARCH_ALLOW_PHI=false
```

The runtime config endpoint exposes these values only as non-secret settings.
API keys, OAuth secrets, database URLs, and local paths remain non-editable
through this endpoint.

## Enforcement Points

- `OpenAIResponsesPlanner` checks `openai_llm` before planning, streaming
  planning, synthesis, and streaming synthesis.
- `OpenAIEmbeddingProvider` checks `openai_embeddings` before batch embedding
  requests.
- `extract_document(..., prefer=openai_vision)` checks `openai_vision_ocr`
  before direct vision requests.
- MarkItDown OCR plugin setup checks `openai_vision_ocr` before creating the
  plugin LLM client.
- `RetrievalService` checks `external_medical_search` before returning generated
  external search hints/tasks in plan/search handoff metadata.

## Extension Rules

- Add new outbound providers as new `ExternalProviderSurface` values and enforce
  them at the adapter boundary before network calls.
- Do not place provider policy checks inside UI components or parser/business
  logic. UI can explain policy status, but adapters own the actual boundary.
- Keep local rule-based and local model paths available when external
  providers are blocked.
- Do not treat policy allowlists as de-identification. Redaction, tokenization,
  review approval, and audit are separate controls.
- When adding live external medical search APIs later, reuse the
  `external_medical_search` surface or add a more specific surface before any
  API client sends query strings.

## Verification

Run:

```bash
OJT_STORAGE_BACKEND=memory PYTHONPATH=src pytest -q tests/test_external_provider_policy.py tests/test_config.py
```
