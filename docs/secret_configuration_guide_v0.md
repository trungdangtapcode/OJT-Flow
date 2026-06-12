# Secret Configuration Guide v0

OJTFlow runtime secret health checks report only whether a secret-like setting is
configured. They never return secret values, DSNs, tokens, prefixes, or hashes.

## Required Inputs

- `OJT_GOOGLE_CLIENT_ID`: Google OAuth web-client ID.
- `OJT_GOOGLE_CLIENT_SECRET`: Google OAuth client secret.
- `OJT_OPENAI_API_KEY` or `OPENAI_API_KEY`: OpenAI-compatible LLM, vision OCR,
  and embedding API access.
- `OJT_DATABASE_URL` or `DATABASE_URL`: Postgres connection URL.
- `OJT_REDIS_URL`: Redis session/cache URL for Postgres-backed deployments.

Pilot and production modes treat OAuth and OpenAI configuration as required
because those modes reject disabled LLM configuration and memory-only storage.

## Health Endpoint

`GET /api/v1/runtime/secrets/health` requires `admin:read`.

The response includes:

- overall `status`
- `product_mode`
- `storage_backend`
- `secret_values_exposed=false`
- per-secret `checks[]` with `name`, `status`, `configured`, `required`,
  `env_vars`, and `remediation`

Statuses:

- `ok`: configured, or not needed for the current runtime.
- `warning`: optional for this runtime but missing.
- `error`: required for this runtime and missing.

## Operational Rule

Do not paste secret values into issues, PR comments, docs, UI screenshots, or
audit records. Use the health endpoint to confirm presence and use your secret
manager or deployment environment to rotate values.
