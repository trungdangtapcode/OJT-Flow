# Rate Limiting v0

OJTFlow enforces API rate limits through FastAPI middleware before request
handlers execute. Limits are data-driven from:

```text
knowledge/security/rate_limit_policy.json
```

Config:

```env
OJT_RATE_LIMIT_ENABLED=true
OJT_RATE_LIMIT_BACKEND=auto
OJT_RATE_LIMIT_POLICY_PATH=knowledge/security/rate_limit_policy.json
OJT_RATE_LIMIT_REDIS_PREFIX=ojtflow:rate_limit
```

Backends:

- `auto`: uses Redis for Postgres deployments when available; otherwise falls
  back to process-local memory.
- `redis`: requires Redis.
- `memory`: process-local fixed-window counters for tests and local development.

## Policy Shape

Each rule has:

- `key`
- `description`
- `methods`
- `path_prefixes`
- `limit`
- `window_seconds`
- `scope`: `ip` or `session_or_ip`
- `enabled`

Every matching rule is enforced. This allows a route such as Assistant chat to
count against both `assistant_chat` and `external_connectors`.

## F134 Coverage

The default policy covers:

- OAuth auth URL/callback and auth mutations.
- Assistant chat, stream, and session-message routes.
- File upload, clipboard image parsing, extraction, and upload workflow routes.
- Retrieval plan/search.
- Retrieval reindex and background reindex jobs.
- External-provider-capable routes that may trigger OpenAI-compatible LLM/OCR,
  embedding, or external medical search work.

## Response

When a limit is exceeded the API returns status `429` with the standard envelope:

```json
{
  "data": null,
  "error": {
    "code": "rate_limited",
    "message": "Rate limit exceeded.",
    "details": {
      "rule_key": "assistant_chat",
      "limit": 40,
      "remaining": 0,
      "retry_after_seconds": 42,
      "window_seconds": 60,
      "scope": "session_or_ip"
    },
    "workflow_id": null,
    "request_id": "req_123"
  }
}
```

The response also includes `Retry-After`, `X-RateLimit-Limit`,
`X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers.
