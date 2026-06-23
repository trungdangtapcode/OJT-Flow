# Auth Architecture

OJTFlow auth follows the same clean-architecture boundary as workflows:

- `application.auth_service.AuthService` owns the use case: OAuth state, user
  upsert, service-account creation, session creation, token lookup, and logout.
- `application.ports` defines `IdentityProvider`, `AuthRepository`, and
  `SessionCache`.
- `infrastructure.auth.google.GoogleOAuthClient` owns Google OpenID Connect
  details, validates token-response shape, and verifies ID tokens with Google's
  verifier.
- `infrastructure.storage.auth_postgres.PostgresAuthRepository` stores
  runtime users, service accounts, and sessions.
- `infrastructure.storage.auth_memory.InMemoryAuthRepository` and
  `InMemorySessionCache` are for isolated tests and ephemeral in-process runs.

## Storage Matrix

| `OJT_STORAGE_BACKEND` | User/session repository | Session cache |
| --- | --- | --- |
| `postgres` | Postgres tables under `ojtflow.users` and `ojtflow.sessions` | Redis required for ready multi-instance auth; process-local fallback is development-only and reports not-ready |
| `memory` | Process-local repository for isolated tests only | Process-local cache |

Session tokens are generated once, returned to API clients, stored as SHA-256
hashes, and never persisted as raw tokens.
Cached session payloads are validated before use; malformed cache entries are
evicted and resolved from the repository, while cached revoked or expired
sessions fail closed and are removed.
In Postgres mode, the Redis cache adapter is strict. If Redis is unavailable,
OAuth state writes/reads and session cache operations raise a structured
`dependency_unavailable` API error instead of silently using process-local
cache. This keeps local development fallback behavior out of production-like
multi-instance deployments.

Service-account tokens use the same hashed session storage with an `ojt_sa_`
raw-token prefix. Service accounts are represented by normal user rows with
`google_sub = service-account:{account_id}` and are attached to an organization
membership with an explicit RBAC role before the token is returned. See
`docs/service_accounts_v0.md`.
Valid service-account tokens can issue successor tokens for the same
`account_id` through the governed token endpoint, which allows CI rotation
without a browser login while the existing token is still active.

## Browser Session Transport

The Google callback sets an HTTP-only cookie using:

- `OJT_AUTH_COOKIE_NAME`
- `OJT_AUTH_COOKIE_SECURE`
- `OJT_AUTH_COOKIE_SAMESITE`
- `OJT_AUTH_COOKIE_DOMAIN`

`OJT_AUTH_COOKIE_NAME` must be a valid HTTP cookie token: non-empty and without
spaces, commas, semicolons, or control characters. Invalid cookie-name settings
fail at backend startup instead of producing malformed `Set-Cookie` headers.

When `OJT_AUTH_COOKIE_SAMESITE=none`, the backend emits the cookie with the
`Secure` flag even if `OJT_AUTH_COOKIE_SECURE=false`, because modern browsers
reject cross-site cookies that are not secure. Runtime config exposes both the
configured `auth.cookie_secure` value and the emitted
`auth.cookie_effective_secure` value so the operations UI can report the real
browser policy without exposing secrets.

The React app uses `credentials: "include"` and does not store bearer tokens in
`localStorage`. API clients may still use `Authorization: Bearer <token>` for
automation and Swagger-style testing.
The OAuth callback response omits the raw bearer token by default after setting
the HTTP-only cookie. API-only clients can request token material explicitly with
`include_token=true`.
OAuth URL generation, callback, current-session lookup, and logout responses are
all emitted with `Cache-Control: no-store` and `Pragma: no-cache` so browser,
proxy, and API-client caches do not retain nonce, session, or optional token
material.

Cookie-authenticated `POST`, `PUT`, `PATCH`, and `DELETE` requests must include
a trusted `Origin` header. The backend accepts origins derived from the current
API host and configured OAuth redirect URIs. Bearer-token API clients are not
subject to the cookie-origin guard.

Any frontend API response with status `401` emits a local session-expired
event. `AuthProvider` handles that event by clearing the authenticated user,
clearing React Query server-state cache, and returning the browser to the login
gate. This prevents revoked or expired sessions from leaving protected workflow
data visible from a stale client cache.

## Workflow Ownership

Authenticated workflow endpoints use the resolved backend session as the
authorization boundary. Workflow creation stores `WorkflowState.owner_user_id`
from `AuthenticatedSession.user.user_id`; workflow queues, summaries, stats,
events, output artifacts, review lists, and review decisions are filtered by
that owner. Cross-user workflow or review access returns the standard
`not_found` envelope so IDs cannot be enumerated.

## Deployment Controls

- `OJT_ALLOWED_AUTH_REDIRECT_URIS` adds deployment callback URLs beyond the
  local backend and frontend defaults.
- OAuth redirect URIs must use `http` or `https`. Non-local HTTP callbacks must
  use HTTPS; local `http://localhost`, `http://127.0.0.1`, and `http://[::1]`
  remain valid for development. Redirect URIs with fragments, embedded user
  info, missing hosts, or non-web schemes are rejected during settings load.
- `OJT_ALLOWED_GOOGLE_HOSTED_DOMAINS` restricts login to Google Workspace
  domains when set. Values must be bare DNS domains; URLs, ports, wildcards,
  spaces, IP addresses, localhost, leading dots, and trailing dots are rejected.
- `OJT_AUTH_COOKIE_DOMAIN` is optional and should be omitted for localhost/dev.
  When set for production, it must be a bare DNS domain such as `example.com` or
  `.example.com`; URLs, ports, wildcards, spaces, IP addresses, and localhost are
  rejected during settings load.
- `OJT_GOOGLE_OAUTH_TIMEOUT_SECONDS` controls outbound Google token exchange
  timeout and must be positive.
- `OJT_AUTH_SESSION_TTL_SECONDS` and `OJT_AUTH_STATE_TTL_SECONDS` control
  browser session and OAuth state lifetime. Both must be positive.
- `OJT_SERVICE_ACCOUNT_TOKEN_TTL_SECONDS` controls default automation bearer
  token lifetime.
- `OJT_SERVICE_ACCOUNT_DEFAULT_ROLE_KEY` controls the default assignable role
  used when service-account creation omits `role_key`.

## Verification

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest
```

Relevant coverage:

- missing/invalid auth returns the standard API envelope
- OAuth state is single-use
- redirect URI allow-list is enforced
- Postgres auth sessions persist across repository re-creation
- workflow and review endpoints are scoped to the authenticated owner
- browser logout and revoked-session flows clear protected UI and cached server
  state
- service-account tokens authenticate as `identity_type=service_account` and
  remain governed by workspace RBAC
- malformed or unexpected Google token responses are wrapped as expected
  `OJTFlowError` failures instead of leaking parser exceptions
