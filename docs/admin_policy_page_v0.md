# Admin Policy Page v0

The Settings page now includes an Admin policy controls panel for operators.
It is backed by `/api/v1/runtime/config` and the existing Assistant runtime
settings update endpoint.

## Covered Controls

- Review thresholds: default human review and OCR low-confidence review threshold.
- PHI handling: whether external provider surfaces allow PHI.
- External providers: OpenAI LLM, vision OCR, embeddings, and external medical search.
- Retention: artifact retention rule count and whether a retention override exists.
- Tool gates: registered tool count and tools requiring explicit approval.
- Audit: whether hash-chain fields are written and required for the deployment.

## Editable Policy

External-provider policy switches are edited through the Assistant runtime
settings form. Saving uses `PUT /api/v1/runtime/assistant-settings`, then the
backend clears service caches so policy changes apply to subsequent tool calls,
retrieval, OCR, and LLM planning.

The UI does not store its own policy state outside the backend runtime settings
response. If the backend does not return a policy field, the page displays a
loading/unavailable state instead of inventing a value.

## Extension Points

F132 should add setting history and rollback. After that, this page can show who
changed each policy, the previous value, the reason, and rollback actions.
