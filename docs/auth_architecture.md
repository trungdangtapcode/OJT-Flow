# Auth Architecture

OJTFlow auth follows the same clean-architecture boundary as workflows:

- `application.auth_service.AuthService` owns the use case: OAuth state, user
  upsert, session creation, token lookup, and logout.
- `application.ports` defines `IdentityProvider`, `AuthRepository`, and
  `SessionCache`.
- `infrastructure.auth.google.GoogleOAuthClient` owns Google OpenID Connect
  details and verifies ID tokens with Google's verifier.
- `infrastructure.storage.auth_postgres.PostgresAuthRepository` stores
  production users and sessions.
- `infrastructure.storage.auth_sqlite.SQLiteAuthRepository` keeps local
  fallback sessions restart-safe.
- `infrastructure.storage.auth_memory.InMemoryAuthRepository` and
  `InMemorySessionCache` are for tests and ephemeral runs.

## Storage Matrix

| `OJT_STORAGE_BACKEND` | User/session repository | Session cache |
| --- | --- | --- |
| `postgres` | Postgres tables under `ojtflow.users` and `ojtflow.sessions` | Redis with process-local fallback |
| `sqlite` | SQLite `users` and `sessions` tables in `OJT_DATABASE_PATH` | Process-local cache |
| `memory` | Process-local repository | Process-local cache |

Session tokens are generated once, returned to API clients, stored as SHA-256
hashes, and never persisted as raw tokens.

## Browser Session Transport

The Google callback sets an HTTP-only cookie using:

- `OJT_AUTH_COOKIE_NAME`
- `OJT_AUTH_COOKIE_SECURE`
- `OJT_AUTH_COOKIE_SAMESITE`
- `OJT_AUTH_COOKIE_DOMAIN`

The React app uses `credentials: "include"` and does not store bearer tokens in
`localStorage`. API clients may still use `Authorization: Bearer <token>` for
automation and Swagger-style testing.

## Deployment Controls

- `OJT_ALLOWED_AUTH_REDIRECT_URIS` adds deployment callback URLs beyond the
  local backend and frontend defaults.
- `OJT_ALLOWED_GOOGLE_HOSTED_DOMAINS` restricts login to Google Workspace
  domains when set.
- `OJT_GOOGLE_OAUTH_TIMEOUT_SECONDS` controls outbound Google token exchange
  timeout.

## Verification

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/tcuong1000/.ostwin/.venv/bin/python -m pytest
```

Relevant coverage:

- missing/invalid auth returns the standard API envelope
- OAuth state is single-use
- redirect URI allow-list is enforced
- SQLite auth sessions persist across repository re-creation
