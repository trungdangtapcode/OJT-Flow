# Frontend Architecture

The frontend is an operations console for B2B healthcare data workflow users:
implementation analysts, integration engineers, clinical reviewers, and
compliance reviewers.

Unauthenticated users should land on a focused access boundary, not a marketing
landing page. The login surface keeps one primary Google OAuth action, identifies
the API/session/scope context, and explains the trust boundary with compact facts
that do not claim runtime state unavailable to the auth gate.

## Stack

- Vite and React render the SPA.
- TanStack Router owns URL state and deep links such as `/workflows/{workflow_id}`.
- TanStack Query owns server state, caching, invalidation, and mutation refresh.
- TanStack Table renders operational queues.
- Tailwind CSS v4 plus small local shadcn-style primitives provide the design system.
- Playwright verifies real browser behavior against the Docker stack.

## Boundaries

- `src/app` contains cross-cutting providers and auth/session orchestration.
- `src/components/layout` contains reusable app chrome.
- `src/components/ui` contains reusable low-level UI primitives.
- `src/components/domain` contains reusable domain presentation components such
  as workflow status and validation severity badges.
- `src/features/*` contains product workflows: assistant, workbench, workflows,
  retrieval, reviews, schemas, audit, and settings.
- `src/api.ts` is the frontend API boundary. Feature components call query hooks,
  not raw fetch logic. It parses response bodies through text-first JSON parsing
  so malformed upstream JSON becomes a structured `ApiRequestError` instead of a
  raw browser `SyntaxError`, and it rejects valid JSON that does not match the
  project response envelope before feature code can consume partial data. It
  also wraps browser transport failures as `network_error` so offline API,
  proxy, or container failures show a consistent operator-facing error.
- `src/lib/server-state.ts` contains TanStack Query keys, server-state hooks,
  mutation invalidation, and API error formatting shared across features.
- `src/types.ts` mirrors public backend response contracts.

## Runtime Delivery

The Docker frontend image is a production static asset image, not a Vite dev
server. The build stage runs the Vite production build and the runtime stage
serves `/usr/share/nginx/html` through NGINX. NGINX owns SPA fallback, immutable
asset caching, no-store HTML caching, security headers, and same-origin proxying
for `/api/` and `/health`.

The frontend Docker build context should contain only files required by the
Dockerfile: package manifests, Vite/TypeScript config, `index.html`, `src`, and
`nginx.conf`. Local Playwright tests, screenshots, auth state, generated build
output, and helper scripts stay outside the image context through
`frontend/.dockerignore`. Runtime freshness is verified by comparing the
container-served asset references with the freshly built Docker image.

## UX Model

The primary route is `/workflows`, an operations command center. It uses summary
and stats endpoints for queue rendering, then loads full workflow state only for
the selected workflow. This keeps the UI scalable as persisted workflow states
grow with evidence, audit events, output references, and handoff context.
Queue screens use server-backed sorting and pagination rather than client-only
table state. Desktop workflow details are allowed to scroll inside the detail
pane; mobile views must keep the document width equal to the viewport and render
validation issues as readable cards instead of forcing wide clinical tables.
Operational pages use the shared `SummaryStrip` primitive for top-level status
facts, then keep list/detail regions in one work area with compact rows,
table primitives, and explicit selected-record context. Summary strips render
as compact mobile grids: three facts stay three-up, while four or five facts use
two-column mobile grids and wider desktop grids so status facts do not dominate
the viewport. Use cards for bounded tools, selected detail panels, and repeated
mobile records; avoid stacking decorative metric cards where a summary strip or
divider list provides the same information with less scan cost.
The authenticated app shell owns global navigation, session identity, refresh,
and sign-out. Desktop navigation may be dense, but mobile shell controls must
stay at least 44px in each tap dimension, keep one active `aria-current="page"`
navigation item, and preserve icon-only labels with explicit accessible names.
Workflow detail follows the same pattern: identity first, workflow facts second,
then tabbed groups for steps, validation issues, retrieval evidence, review,
output, and audit. Evidence uses structured rows on desktop and compact cards
on mobile so source, claim, trust, and confidence stay comparable without
forcing horizontal overflow. Retrieval trace safety flags must be visible in
the Evidence tab so operators can distinguish trusted evidence from
safety-sensitive query context. Graph handoff summary must also be visible in
the Evidence tab whenever the backend emits `graph_context`, because evidence
without entity/triple visibility is too weak for regulated review.
The workflow detail implementation keeps this split visible in code:
`workflow-detail.tsx` is the query and tab-routing shell,
`workflow-detail-chrome.tsx` owns loading/failure/fact-strip chrome,
`workflow-detail-review.tsx` owns review-gate decisions, and
`workflow-detail-sections.tsx` owns the tab sections. Do not fold those
responsibilities back into the shell; add another sibling section component when
a new workflow-detail surface needs meaningful logic.

The workbench remains the intake route for starting deterministic parse,
validation, retrieval, conversion, and review-gated workflows. It supports both
pasted structured data and multipart file upload. Structured file uploads such
as CSV/JSON/YAML use deterministic parsing directly; document-like uploads use
the backend extraction hook when optional extractor packages are installed.
Workbench should expose the active intake mode, source format, target format,
schema/profile, and review-gate state before the form so users understand the
contract before submitting data. Keep the intake form explicit rather than
wizard-heavy: clear labels, native file input behavior, visible source payload
stats, schema-aligned examples, and one primary start action per mode. The
human-review gate should be rendered as a bounded control with its current
approval/audit state near the submit action because it changes workflow
semantics.
Review and audit screens are narrower operational views over the same contracts.
Workbench standard examples must keep source format, target format, schema, and
sample payload aligned so users can start from CSV rows, JSON records, or YAML
records without manually reconciling the contract. FHIR-like JSON examples use
the same workflow path with no lab schema selected; the backend profiles the
resource and emits FHIR handoff context during orchestration.
The workbench implementation keeps orchestration and reusable rendering
separate: `workbench-page.tsx` owns state, mutation submission, and navigation;
`workbench-examples.ts` owns standard payload examples; `workbench-controls.tsx`
owns repeated intake controls and operational side panels; and
`workbench-utils.ts` owns pure formatting and upload-file validation helpers.
Keep backend calls in the page through server-state hooks and keep pure file
validation reusable so upload guard behavior remains testable without UI state.
The retrieval route is the operator surface for direct search. It owns query
builder state, calls `/retrieval/search` through typed server-state hooks,
lists trusted sources, refreshes the retrieval index, and renders rank signals,
trace warnings, safety flags, and Graph-NER handoff context. It should stay an
inspection console, not a separate workflow executor: workflow creation remains
in Workbench and workflow-scoped evidence remains in Workflow Detail. The route
must surface embedding and rerank provider metadata from runtime config and
retrieval handoff context so operators can distinguish first-stage hybrid
searches from searches refined by second-stage reranking. It must also surface
source coverage from retrieval diversity metadata so redundant single-source
results are visible during evidence review. Query-analysis filter suggestions
should be actionable from the trace view only through explicit operator apply
controls; the UI must not silently apply suggested filters before users can see
the reason, confidence, and existing applied state. Result facets should also be
actionable refinements: applying a visible facet bucket must update the query
builder filter state and rerun the typed retrieval search instead of mutating
results locally. Selected refinements should remain visible as removable chips
with a clear-all action so operators can audit and undo the active search
constraints. If the query builder changes after a search, the results panel
must show that ranked evidence has pending changes until the current request
state is submitted again. The ranked-results panel should also render the last
submitted request summary and use that submitted payload to mark result facets
as applied, so displayed evidence remains auditable even while the builder is
being edited. When displayed evidence is stale, operators must be able to
restore the query builder to the submitted request without changing the result
package or issuing another search.
The assistant route is the operator shortcut over those same backend contracts.
It calls `/assistant/chat` through a typed mutation, renders model/tool mode,
write-gate state, executed tool calls, and compact evidence/output previews.
It should also show the server allowlisted assistant/MCP tools from
`/assistant/tools` before a command is run, so users can see what the assistant
can do without reading backend docs or waiting for a transcript.
It must not duplicate workflow detail, retrieval console, or review-decision
logic; it should route users into the underlying workflow/retrieval artifacts
once a command has produced durable state or evidence.
Settings is an operator readiness surface, not a prose documentation page. It
should show status facts first, then group runtime configuration into compact
sections, summarize readiness/security/inventory counts before detailed rows,
and render operational policy as structured rows. Configuration values must come
from runtime endpoints and auth state rather than hardcoded deployment claims.
Assistant runtime controls belong here: the page should expose reloadable
planner mode, model, timeout, and tool-call limits while keeping API keys and
other secrets backend-only.
Embedding and rerank provider state should be visible here because model choice,
device, and second-stage reranking materially affect retrieval latency and
evidence quality.

## Extension Rules

- Add backend-visible fields to `src/types.ts` first, then expose them through
  `src/api.ts` and a feature query hook.
- Keep feature-specific state inside `src/features/*`.
- Do not import from one feature directory into another. Promote shared server
  state, layout, or domain rendering into `src/lib` or `src/components`.
- Keep rendering components free of persistence, fetch, storage, and auth logic.
- Use summary endpoints for list screens; use full workflow endpoints for detail
  screens.
- Add Playwright coverage for user-visible workflow changes that span auth,
  API, and rendering.
- Keep direct `fetch` calls inside `src/api.ts`; feature pages should reach the
  backend through `src/lib/server-state.ts` query/mutation hooks. The Python
  frontend architecture tests enforce this boundary.
- Do not store auth or workflow state in `localStorage`, `sessionStorage`, or
  `document.cookie`; browser sessions are handled through HTTP-only cookies and
  backend session state.
