# Remote MCP Deployment Policy v0

## Purpose

OJTFlow currently exposes MCP for trusted local/operator use. Remote MCP is
blocked by policy until the deployment implements OAuth protected-resource
metadata, resource indicators, user scoping, rate limits, and audit metadata.

The machine-readable source of truth is
`knowledge/assistant/remote_mcp_deployment_policy.json`. Operators and clients
can inspect it through:

- `GET /api/v1/assistant/mcp/remote-policy`
- MCP resource `ojtflow://assistant/mcp/remote-policy`

## Standards Baseline

The current MCP authorization specification treats a protected MCP server as an
OAuth resource server. A remote server must publish OAuth Protected Resource
Metadata so clients can discover the authorization server. Clients should use
resource indicators so a token minted for one MCP resource cannot be redeemed at
another resource.

Primary references:

- MCP Authorization:
  https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization
- OAuth 2.0 Protected Resource Metadata, RFC 9728:
  https://www.rfc-editor.org/rfc/rfc9728
- OAuth 2.0 Resource Indicators, RFC 8707:
  https://www.rfc-editor.org/rfc/rfc8707

## Required Controls

Remote MCP exposure remains disabled until all controls in the policy are
implemented and verified:

- OAuth protected-resource metadata and authorization server discovery.
- Resource indicators and exact token audience/resource validation.
- Per-user tool scoping using the same owner, role, permission, write-gate, and
  review-gate boundaries as the API Assistant.
- Rate limits and budgets by tenant, user, client, tool, and permission scope.
- Audit correlation for user, request, client, token subject, resource
  indicator, transport, workflow, workflow events, and redacted payload hashes.
- Tool manifest review for PHI sensitivity, external-network behavior,
  destructive behavior, and approval requirement.

## Implementation Shape

Remote MCP should be deployed behind the same application boundary as the API,
not as a separate tool server with independent permissions. The transport layer
should authenticate and validate tokens before a tool call reaches
`OJTFlowToolExecutor`. The executor should still enforce tool allowlists and
write gates, because transport auth only proves who is calling, not whether a
particular operation is allowed.

Every remote request should produce:

- An API request ID.
- A resolved `owner_user_id`.
- OAuth issuer, subject, client ID, audience, and resource indicator metadata.
- A rate-limit decision.
- A generic audit record with redacted input/output hashes.

Raw uploaded data, chat messages, retrieval queries, tool arguments, token
values, and tool output payloads must not be stored in generic audit metadata.

## Verification

Before enabling remote MCP, add tests that prove:

- Missing or invalid tokens return `401` with `WWW-Authenticate` and
  `resource_metadata`.
- The protected-resource metadata endpoint returns the configured authorization
  server list.
- Tokens without the configured MCP resource indicator are rejected.
- User A cannot access user B workflows, sessions, artifacts, reviews, retrieval
  judgments, or audit rows.
- Write tools still require explicit write execution and human-review gates.
- Rate-limit exhaustion returns structured retryable errors.
- Audit rows contain remote OAuth/client/resource metadata without raw payloads.
