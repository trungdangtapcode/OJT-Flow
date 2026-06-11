# Abuse And Cost Controls v0

OJTFlow blocks unusually expensive operations before external providers or
batch ingestion work starts. The policy is data-driven:

```text
knowledge/security/abuse_cost_policy.json
```

Config:

```env
OJT_ABUSE_COST_POLICY_PATH=knowledge/security/abuse_cost_policy.json
```

## Enforced Surfaces

- OpenAI-compatible LLM planning and synthesis: maximum serialized request
  character count.
- OpenAI embeddings: maximum inputs per request, total character count, and
  maximum single text length.
- OpenAI vision OCR: maximum image bytes before direct vision OCR.
- MarkItDown OCR plugin: disabled for files above the configured OCR plugin
  byte ceiling.
- Batch ingestion: maximum total bytes across all files before artifacts/jobs
  are created.

## Failure Shape

Exceeded limits raise `policy_blocked` with structured details:

```json
{
  "surface": "openai_embeddings",
  "metric": "single_text_chars",
  "value": 20001,
  "limit": 20000,
  "policy": "abuse_cost_policy.v1"
}
```

## Runtime Visibility

`GET /api/v1/runtime/config` exposes sanitized cost-control facts:

- `cost_controls.policy_configured`
- `cost_controls.llm_max_request_chars`
- `cost_controls.ocr_max_openai_vision_bytes`
- `cost_controls.embedding_max_request_inputs`
- `cost_controls.embedding_max_request_chars`
- `cost_controls.batch_max_total_bytes`

The response does not expose local policy file paths.
