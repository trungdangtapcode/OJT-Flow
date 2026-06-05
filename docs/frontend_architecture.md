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
loads search presets from `/retrieval/presets` so healthcare examples and
default query-builder state are managed as trusted knowledge data rather than
hardcoded React constants. The preset selector should apply query, fields,
schema, format, resource, and metadata constraints without executing a search;
operators still submit explicitly. Preset category filters and preset text
search are derived from preset data so the selector remains usable as the
registry grows. Format and top-K controls come from
`/retrieval/search-options` so Markdown, FHIR-like, and future search profiles
can be added through trusted registry data. The route
must surface embedding and rerank provider metadata from runtime config and
retrieval handoff context so operators can distinguish first-stage hybrid
searches from searches refined by second-stage reranking. It must render
`hits[].score_components` as a compact score explanation so operators can see
the final score contributions without opening raw JSON. The trace must render
`trace.query_variant_details` as query rewrite cards with source and reason,
including `query_aspect_rule` variants from the deterministic aspect plan, and
falling back to `trace.query_variants` for older payloads. It must also surface
per-hit ranking boost signals from `source_locator.ranking_boosts`, including
the applied rule ID, reason, and weight, with
`source_locator.ranking_boost_rules` kept as the compatibility fallback for
older payloads. It must also surface source coverage from retrieval
diversity metadata so redundant single-source results are visible during
evidence review. Result cards must render per-hit diversity selection details
from `handoff_context.diversity.selected_hits` when present, including original
rank, normalized relevance, redundancy, MMR score, and selection reason.
Result cards must also render `source_locator.query_aspect_matches[]` as
per-hit aspect support, including aspect label, priority, matched filters,
matched terms, and reason.
Result cards must also render `source_locator.concept_matches[]` as per-hit
concept grounding, including standard system, optional code, display name,
confidence, matched fields, aliases, and reason.
Result cards must render a compact evidence provenance summary with source
version and key locator fields such as standard, URL, path, PMID, DOI, API,
resource, table, document, and chunk identifiers before the raw JSON details.
URL/API values, PubMed IDs, and DOIs must render as external links when they can
be safely normalized.
Each ranked evidence card must also offer a copyable `retrieval_evidence_hit`
report containing evidence identity, ranking scores/components, concept/aspect
grounding, provenance summary, locators, and snippet context.
Copy actions for evidence, comparison, evaluation, and search-hint reports must
show transient success feedback so operators can tell the clipboard action
completed without opening developer tools or raw browser state.
The trace and recent-run list must show the backend
`handoff_context.search_signature` in compact form, and copied run-comparison
reports must include active/baseline server search signatures for offline audit
correlation.
The trace panel must render `quality_signals` as a compact retrieval-quality
checklist with severity, message, suggested action, and evidence references so
operators can review package readiness without opening raw JSON. Known metadata
payloads such as missing concepts, provenance issues, missing standards/aspects,
and suggested filters must render as explicit signal details.
It must also show `handoff_context.quality_policy` so the readiness score can
be traced to the active data-driven gate policy, including top-hit match
thresholds and provenance requirement scope.
The top retrieval summary strip should also surface `quality_summary` as a
readiness score, so operators can tell whether the active package is ready,
needs review, or is blocked before reading detailed traces.
The query-analysis panel should render `query_profile` when present, including
profile label, route, complexity, recommended retrieval mode, suggested
filters, and contributing rule IDs. This makes adaptive retrieval guidance
visible before it becomes a backend route switch. Supported profile-suggested
filters should use the same explicit operator apply controls as query-analysis
filter suggestions; unsupported profile fields should remain visible but not
actionable. Profile filter controls must compare against the submitted
`trace.filters_applied` payload, not the live query-builder draft, so displayed
applied state remains tied to the visible result package.
The same query-analysis panel should render `query_aspects` as a compact search
aspect plan, including aspect label, review question, rationale, priority,
suggested terms, suggested filters, and contributing rule ID. These aspects are
operator-visible decomposition guidance and must not silently run hidden
subqueries or mutate filters. Supported aspect-suggested filters should use the
same explicit apply path and submitted-filter applied-state checks as profile
and query-analysis filter suggestions.
Query-analysis filter suggestions
should be actionable from the trace view only through explicit operator apply
controls; the UI must not silently apply suggested filters before users can see
the reason, confidence, and existing applied state. Result facets should also be
actionable refinements: applying a visible facet bucket must update the query
builder filter state and rerun the typed retrieval search instead of mutating
results locally. Standard coverage gaps should use
`coverage.standard_system[].suggested_filter` to render explicit remediation
buttons for supported fields, keeping the backend responsible for what action is
appropriate and the UI responsible for operator confirmation. Query-aspect
coverage gaps should render `coverage.query_aspects[]` in the same diagnostics
surface so operators can see whether selected evidence covers the search aspect
plan and explicitly apply supported remediation filters. Selected
refinements should remain visible as removable chips with a clear-all action so
operators can audit and undo the active search constraints. If the query builder
changes after a search, the results panel
must show that ranked evidence has pending changes until the current request
state is submitted again. The ranked-results panel should also render the last
submitted request summary and use that submitted payload to mark result facets
as applied, so displayed evidence remains auditable even while the builder is
being edited. When displayed evidence is stale, operators must be able to
restore the query builder to the submitted request without changing the result
package or issuing another search. The Retrieval console should keep a compact
in-session history of recent unique search runs with hit count, candidate count,
warnings, quality issue count, and top source so operators can compare recent search packages
and restore recent result packages without rerunning every query. Operators
should be able to select a baseline run for pairwise comparison instead of only
using the previous run. The active run comparison should show deltas,
overlap and churn metrics, evidence IDs that were added, removed, or retained,
and rank movement for retained evidence so relevance tuning remains inspectable.
Each recent-run row should also render a compact data-derived run scope from the
submitted payload and returned package, including quality status/score,
coverage-gap count, grounded concept count, search-aspect count, and active
schema/format/resource/domain/standard/source/trust/field filters.
Comparison output should include a copyable JSON report with the active payload,
baseline payload, summaries, deltas, metrics, evidence changes, and rank
movement so tuning notes can be reproduced outside the browser. Search-run
summaries and copied comparison reports should include the active query-profile
route/mode context so relevance tuning can distinguish query changes from
adaptive-routing changes. The comparison panel should render a compact
comparison diagnosis that names the likely change drivers before the detailed
sections, and the copyable JSON report should include the same diagnosis for
offline tuning notes. The comparison panel should render the
active-vs-baseline query-profile comparison directly, including profile label,
route, retrieval mode, complexity, and stable/changed status. It should compare
query-aspect plans across active and baseline runs, including added, removed,
and retained aspects, so operators can see whether decomposition coverage
changed before interpreting rank movement. It should compare controlled medical
concept grounding across active and baseline runs, including added, removed,
and retained LOINC/RxNorm/MeSH/FHIR-style concepts. It should compare standard and
query-aspect coverage diagnostics across active and baseline runs, including
improved, regressed, added, removed, and retained coverage items. It should compare
quality signal codes across active and baseline runs, including added, removed,
and retained signals, so readiness regressions are visible without opening raw
JSON. It should compare selected-hit facets across active and baseline runs for
source type, clinical domain, standard system, and trust level, including
added, removed, and retained values. It should also compare sanitized retrieval
rule-pack fingerprints from the active
and baseline packages. This lets operators separate relevance changes caused by
query/filter edits from changes caused by rule-pack data, and the copyable
comparison report must include the same rule-pack delta.
Result cards
should collect explicit relevance judgments for the query-document pair and
persist those judgments through `/retrieval/judgments` so rerun queries can
hydrate prior labels for matching evidence. Comparison reports should include
the available judgments as imported-judgment scaffolding.
The results panel should summarize judgment-aware metrics from current
in-session judgments, including coverage, Precision@k, judged precision, and
nDCG@k. It should also surface the persisted judgment summary from
`/retrieval/judgments/summary`, including stored label count and sync state, so
operators can distinguish transient local labels from durable evaluation data.
For the active ranked result list, the panel should also call
`/retrieval/judgments/evaluate` and show server-computed Coverage@k,
HitRate@k, MAP@k, MRR@k, nDCG@k, unjudged-hit count, and policy-driven
recommendations. This keeps rank-aware evaluation tied to the durable judgment
store rather than browser-local state, and turns poor coverage or ordering into
explicit next actions for the operator.
The same panel should provide a copyable `retrieval_judgment_evaluation` JSON
report containing server metrics, local in-session metrics, stored-label
summary, recommendations, relevant evidence IDs, active query-profile context,
and active retrieval rule-pack fingerprints for offline relevance tuning notes.
The trusted source inventory should be searchable and filterable by
data-derived source type, clinical domain, and standard system so large corpora
remain inspectable.
Medical search hints in the trace should be copyable and launchable when the
backend provides a vetted URL, so PubMed, ClinicalTrials.gov, and openFDA
workflows remain backend-owned and data-driven instead of hardcoded in React.
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
Retrieval runtime controls should show the active retrieval rule-pack inventory
from `/runtime/config`, including sanitized pack name, status, rule count,
version, short content hash, default-vs-override source, and controlling
environment variable. The UI must not expose local filesystem paths for those
packs.
The readiness panel should render the `retrieval_rule_packs` check as a nested
pack list, not only generic detail chips, so missing or malformed query
expansion, diagnostic, ranking, evaluation, or search-hint rules and their
fingerprints are visible to operators before they run searches.

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
