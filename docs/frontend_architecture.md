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
  proxy, or container failures show a consistent operator-facing error. The API
  boundary generates `X-Request-ID` when one is not supplied and emits a global
  API error browser event containing status, code, endpoint, workflow ID,
  request ID, and sanitized details.
- `src/lib/server-state.ts` contains TanStack Query keys, server-state hooks,
  mutation invalidation, and API error formatting shared across features.
- `src/app/api-error-panel.tsx` listens for global API error events and renders
  the compact copyable diagnostic panel. Feature pages should keep using shared
  hooks/helpers rather than dispatching their own global diagnostics.
- `src/data/page-guides.json` is the data source for primary-page operator
  guides. `src/components/layout/page-guide.tsx` renders it from the app shell
  based on the active route, so guide copy can change without editing page
  components.
- `src/types.ts` mirrors public backend response contracts.

## Runtime Delivery

The Docker frontend image is a production static asset image, not a Vite dev
server. The build stage runs the Vite production build and the runtime stage
serves `/usr/share/nginx/html` through NGINX. NGINX owns SPA fallback, immutable
asset caching, no-store HTML caching, security headers, and same-origin proxying
for `/api/` and `/health`.

Feature routes are lazy-loaded at the TanStack Router boundary. The app shell,
auth gate, and providers stay eager, but assistant, retrieval, workflows,
workbench, reviews, schemas, audit, settings, and help pages must be imported
with `React.lazy`/`Suspense` so the initial operations route does not download
heavy search or assistant UI code until the user visits those routes.
Primary app-shell navigation uses TanStack Router `preload="intent"` so lazy
route chunks start loading on hover/focus, preserving fast navigation without
returning to eager feature imports.

The frontend Docker build context should contain only files required by the
Dockerfile: package manifests, Vite/TypeScript config, `index.html`, `src`, and
`nginx.conf`. Local Playwright tests, screenshots, auth state, generated build
output, and helper scripts stay outside the image context through
`frontend/.dockerignore`. Runtime freshness is verified by comparing the
container-served asset references with the freshly built Docker image.

## UX Model

The primary authenticated route is `/assistant`, a governed natural-language
workspace for end users who should not need to understand every backend
operation before starting. It exposes starter tasks, persistent chat sessions,
file and clipboard intake, tool-call streaming, and review-gated write controls.
OAuth callbacks should return users to this route. `/workflows` remains the
operations command center for queue inspection: it uses summary and stats
endpoints for queue rendering, then loads full workflow state only for the
selected workflow. This keeps the UI scalable as persisted workflow states
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
The app must also expose operator guidance as first-class routes and contextual
control help. `/help` owns role-based onboarding and task routing, `/help/tutorials`
owns step-by-step walkthroughs, and `/help/manual` owns input format guidance,
glossary, output interpretation, issue/warning interpretation, a retrieval search manual,
and safety rules. Dense surfaces such as Assistant,
Workbench, Workflow Operations, Reviews, Schemas, and Retrieval should use the
shared guide panel for page-level orientation and compact keyboard-focusable tooltips
for high-risk controls. Tooltips explain meaning and operator risk, not
implementation trivia. Page-level guides should answer: what this page is for,
what the user should inspect first, which decision is safe, and when to send a
workflow to human review.
Workflow detail follows the same pattern: identity first, workflow facts second,
then tabbed groups for steps, validation issues, retrieval evidence, review,
output, and audit. Evidence uses structured rows on desktop and compact cards
on mobile so source, claim, trust, and confidence stay comparable without
forcing horizontal overflow. Retrieval trace safety flags must be visible in
the Evidence tab so operators can distinguish trusted evidence from
safety-sensitive query context. Graph handoff summary must also be visible in
the Evidence tab whenever the backend emits `graph_context`, because evidence
without entity/triple visibility is too weak for regulated review.
Retrieval runtime status rendering should stay outside the page shell:
`frontend/src/features/retrieval/components/retrieval-runtime-status.tsx` is
only the public runtime-status export surface. `runtime-status-strip.tsx` owns
the compact runtime status strip composition and rerank/diversity badges.
`runtime-status-fact.tsx` owns individual runtime fact cards, and
`runtime-graph-status.ts` owns graph supporting-copy formatting.
`graph-handoff-panel.tsx` owns graph context rendering.
`integrity-panel.tsx` owns only the index-integrity card shell and report
presence branch. `integrity-panel-header.tsx` owns title/status actions,
`integrity-summary-metrics.tsx` owns report metric composition,
`integrity-warnings.tsx` owns warning tokens, `integrity-source-checks.tsx` owns
source-check section layout, `integrity-source-check-row.tsx` owns per-source
check rows, and `integrity-loading-notice.tsx` owns the loading copy.
`retrieval-runtime-status-model.ts` owns the runtime status view contract used
by model and presentation code. The status strip should show
retrieval mode, reranker state, graph handoff readiness, and index integrity
before detailed trace panels so non-expert operators can orient themselves
without reading raw trace JSON. `retrieval-summary-model.ts` owns
`retrievalRuntimeStatusStripView` so the page does not assemble runtime status
objects inline. Runtime stack models own package/ranking/diversity derivation.
`retrieval-integrity-model.ts` owns prioritized integrity check
selection, integrity badge tones, and short hash formatting.
`frontend/src/features/retrieval/hooks/use-retrieval-integrity-session.ts` owns
the integrity query, corpus-integrity toggle, reindex mutation, and
operator-facing integrity/reindex notices. The retrieval page composes the hook
and passes the resulting state/callbacks into runtime panels.
Retrieval trace rendering should stay outside the page shell:
`frontend/src/features/retrieval/components/retrieval-trace-panel.tsx` owns only
the trace card shell and unavailable-state branch.
`retrieval-trace-panel-types.ts` owns the trace view and callback contracts.
`retrieval-trace-header.tsx` owns the title, help tooltip, and description.
`retrieval-trace-content.tsx` owns trace facts, query-analysis block
composition, corrective actions, coverage diagnostics, query rewrites, safety
flags, and warnings. `query-analysis-block.tsx` owns query-analysis section
ordering. `query-analysis-header.tsx` owns the query-analysis heading, strategy
badge, and metric row; `query-analysis-counter.tsx` owns each metric counter.
`query-analysis-token-sections.tsx` owns repeated detected-concept,
standard-cue, and expanded-term token-list sections.
`retrieval-trace-unavailable.tsx` owns the empty trace message. The
`frontend/src/features/retrieval/model/retrieval-trace-view-model.ts` owns
conversion from `RetrievalPackage` into trace view data, including query-analysis
display blocks, trace facts, formatted runtime stack labels, query variants,
and safety/warning lists. The retrieval page owns only filter support rules,
current search state, and action callbacks.
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
must guide first-time users before a search runs: the ranked evidence empty
state should explain what Retrieval is for, how to start from presets, how
schema/format/source context changes scope, and why readiness should be read
before individual hits. The route should also explain source inventory filters
because exact source scope can over-constrain evidence. Exact source scope
controls must explain that the search is constrained to one source, show when a
source is applied, and tell operators to clear it before judging corpus-wide
coverage.
Query-builder rendering should stay outside the page shell:
`frontend/src/features/retrieval/components/query-builder-panel.tsx` owns the
query-builder card shell, header placement, and form submit container.
`query-builder-form-content.tsx` owns form child ordering, including notices,
preset strip placement, query/context/scope fields, source-scope picker,
active-filter adapter placement, and submit button placement.
`query-builder-panel-types.ts` owns the typed value/options/status/action
contracts shared by the shell and field modules. `query-builder-header.tsx` owns
the query-builder title/description, and `query-builder-submit-button.tsx` owns
pending/search button rendering.
`query-builder-fields.tsx` is only the compatibility export surface.
`query-builder-text-fields.tsx` owns the query and field textareas,
`query-builder-context-fields.tsx` owns only the context-control grid
composition, and `query-builder-context-controls.tsx` is only the compatibility
export surface for context controls. `query-builder-schema-control.tsx`,
`query-builder-top-k-control.tsx`, `query-builder-format-control.tsx`, and
`query-builder-resource-control.tsx` own their individual labels, help text,
options, and value wiring.
`query-builder-scope-fields.tsx` owns domain, standard, trust, and source-type
control configuration. `query-builder-scope-select.tsx` owns the shared scope
label/help/select rendering. `query-builder-notices.tsx` owns form, search,
options, stale-search, and plan-control notices.
`query-builder-active-filter-bar.tsx` owns active-filter entry derivation and
the `ActiveFilterBar` adapter for query-builder callbacks.
`frontend/src/features/retrieval/hooks/use-retrieval-form-session.ts` owns the
query-builder session shell, preset application, plan-control notices, and
submitted-payload restoration. `use-retrieval-form-payload-actions.ts` owns
preset and submitted-payload mapping into form fields.
`use-retrieval-form-field-state.ts` owns raw query-builder field state.
`use-retrieval-form-state.ts` composes raw field state, setter objects, and
derived form state. `retrieval-form-state-builders.ts` owns pure form value and
setter object assembly for that hook.
`retrieval-form-derived-state.ts` owns payload, active-filter, and current
search-signature derivation from those values. `retrieval-form-defaults.ts` owns
the default query-builder values so initial search policy does not live inside
React state calls.
`use-retrieval-filter-controls.ts` owns supported-filter state mutation and
payload override generation. `use-query-builder-draft-actions.ts` owns
draft-control callbacks that mark custom searches. The retrieval page owns
backend search execution, option loading, and callback composition. Query
builder child components should not import retrieval service hooks or execute
backend searches directly.
The retrieval page column layout should also stay outside the orchestration
shell. `retrieval-query-column.tsx` composes the query builder, plan preview,
and run history. `retrieval-results-column.tsx` composes runtime status, search
results, trace, Graph-NER handoff, integrity, and source inventory. The page
owns data/session wiring and passes display-ready component props into these
columns; it should not import those child panels directly.
Exact source scope selection should stay outside the page shell:
`frontend/src/features/retrieval/components/source-scope-picker.tsx` owns the
source picker shell. `use-source-scope-picker-state.ts` owns local source-search
input state and visible-source derivation. `source-scope-picker-format.ts`
owns source search matching and count formatting. `source-scope-option-row.tsx`
owns selectable source row rendering, `source-scope-selected-summary.tsx` owns
the applied-source summary, `source-scope-status-notice.tsx` owns exact-source
risk/status copy, `source-metadata-badges.tsx` owns repeated source badges, and
`source-scope-empty-state.tsx` owns empty-result copy. The page owns only the
selected source ID state and search rerun behavior.
Trusted source inventory should also stay outside the page shell:
`frontend/src/features/retrieval/components/source-inventory-panel.tsx` owns the
inventory card shell. `use-source-inventory-panel-state.ts` owns local filter
state, filtered-source derivation, filter option derivation, filter-presence
checks, reset behavior, and readiness derivation.
`source-inventory-header.tsx` owns trusted-source title, help, counts, and
clear-filter action display. `source-inventory-source-list.tsx` owns source-card
mapping and empty/loading source-list copy.
`source-inventory-filter-controls.tsx` owns inventory filter control
composition and search input wiring. `source-inventory-filter-header.tsx` owns
filter title/help/count display. `source-filter-chip-group.tsx` owns reusable
chip filter groups, and `source-filter-chip-class.ts` owns chip state styling.
`source-inventory-readiness-panel.tsx` owns source-readiness presentation,
`source-card.tsx` owns the Use source action surface, and
`retrieval-source-inventory-model.ts` is only the public source-inventory model
export surface. `retrieval-source-inventory-filters.ts` owns filter matching and
filter option derivation. `retrieval-source-inventory-readiness.ts` owns
readiness policy, readiness badge variants, and operator-facing readiness
messages. `retrieval-source-inventory-types.ts` owns the typed filter/readiness
contracts, and `retrieval-source-inventory-values.ts` owns shared option-value
normalization. The retrieval page should pass loaded sources and the exact-source
callback only; it should not own inventory filtering details.
Active search constraints should also stay outside the page shell:
`frontend/src/features/retrieval/components/active-filter-bar.tsx` owns the
selected metadata filter chips and clear actions.
`frontend/src/features/retrieval/model/retrieval-filter-model.ts` is only the
public filter-model export surface. `retrieval-filter-types.ts` owns supported
filter fields and typed filter contracts. `retrieval-filter-active.ts` owns
active-filter derivation and submitted-search filter selection.
`retrieval-filter-format.ts` owns filter labels and display values.
`retrieval-filter-suggestions.ts` owns suggested-filter coercion,
coverage/bucket suggested actions, query profile/aspect filter entries, and
applied-filter matching. The form-session hook owns current filter state; the
page owns rerun behavior and passes typed callbacks.
Submitted-search display should stay outside the result shell:
`frontend/src/features/retrieval/components/submitted-search-summary.tsx` owns
only the submitted request card composition. `submitted-search-summary-header.tsx`
owns current/stale status and restore control rendering,
`submitted-search-metadata-chips.tsx` owns submitted payload metadata chips, and
`submitted-search-filter-chips.tsx` owns applied-filter chip rendering. The
page/result shell passes the submitted payload plus already-derived filter chips
so filter derivation remains centralized.
The first-run empty-state guide is a standalone presentation concern:
`frontend/src/features/retrieval/components/first-run-guide.tsx` owns the guide
content and the page shell should only compose `RetrievalFirstRunGuide`.
Ranked evidence result composition should stay outside the page shell:
`frontend/src/features/retrieval/components/search-results-panel.tsx` owns the
ranked evidence result shell only. It should derive `searchResultsViewModel`,
render the header, and compose `search-results-content.tsx`.
`search-results-panel-types.ts` owns the public SearchResults prop contract.
`search-results-content-props.ts` owns mapping panel props and the view model
into overview/judgment/evidence/hit-list section props.
`search-results-content.tsx` owns package-level panel order and composes the
overview, judgment, evidence, and hit-list sections without importing individual
cockpit, judgment, evidence-readiness, facet, or recommended-action panels
directly.
`search-results-overview-section.tsx` owns triage, cockpit, answer, review path,
interpretation, submitted-search restore, and recommended actions.
`search-results-judgment-section.tsx` owns relevance judgment summary and copied
evaluation-report JSON. `search-results-evidence-section.tsx` owns evidence
readiness, evidence buckets, support matrix, and result facets.
`search-results-section-types.ts` owns shared section prop contracts.
`frontend/src/features/retrieval/model/search-results-view-model.ts` owns
package-level derived view data for that shell: submitted result filters,
judgment metrics, required-bucket coverage, cockpit report JSON, and support
matrix rows.
`search-results-header.tsx` owns the ranked-evidence header, runtime badges, and
first-run empty state. `search-results-hit-list.tsx` owns result-vs-empty
composition and zero-hit adapter placement. `search-results-hit-card-list.tsx`
owns ranked hit card mapping, diversity selection lookup, and relevance judgment
wiring. The result shell composes submitted request
summary, cockpit, evidence readiness, facets, support matrix, answer summary,
triage, relevance summary, review path, and recommended actions. The retrieval
page is a route shell only: it imports `use-retrieval-page-controller.ts`,
renders the chrome, and places the query/results columns. Hook composition and
mutable session wiring live in `use-retrieval-page-workspace.ts`; page-level
server query composition lives in `use-retrieval-page-controller.ts`.
`retrieval-page-props.ts` is the stable presenter entrypoint, while
`retrieval-page-chrome-props.ts`, `retrieval-page-query-column-props.ts`, and
`retrieval-page-results-column-props.ts` map controller/workspace state into
display-ready props for each page region. `retrieval-page-query-column-props.ts`
only composes the query-column prop sections; `retrieval-page-query-builder-props.ts`
owns QueryBuilderPanel prop shaping and `retrieval-page-search-plan-preview-props.ts`
owns SearchPlanPreviewPanel prop shaping.
`retrieval-page-search-run-history-props.ts` owns SearchRunHistoryPanel prop
mapping, run restore/baseline callbacks, relevance judgment wiring, and history
report formatting for the query column. `retrieval-page-search-results-props.ts`
owns the SearchResults prop mapping and relevance-judgment callback binding for
the results column. `retrieval-page-trace-props.ts` owns RetrievalTracePanel
prop mapping, trace formatter wiring, trace action callbacks, and active trace
filter display derivation.
Retrieval page chrome should stay outside the orchestration shell:
`frontend/src/features/retrieval/components/retrieval-page-chrome.tsx` owns the
page header, reindex button display, summary strip composition, orientation
guide placement, and top-level retrieval notices. The retrieval page computes
summary/error values and passes display-ready props; it should not render header
or notice markup inline.
The always-visible retrieval orientation guide is also standalone:
`frontend/src/features/retrieval/components/retrieval-inline-guide.tsx` owns
the compact "how to read Retrieval" walkthrough and manual link. It must stay
presentation-only and should not import retrieval service hooks or derive search
state.
The top-level retrieval summary strip is presentation-only:
`frontend/src/features/retrieval/components/retrieval-summary-strip.tsx` owns
the five summary facts layout. `retrieval-summary-model.ts` computes the
runtime/search/readiness view model from backend contracts and
`retrieval-page-chrome-props.ts` passes display-ready values into the strip.
Retrieval presets should also stay outside the page shell:
`frontend/src/features/retrieval/components/search-preset-strip.tsx` owns preset
loading/empty states and composition. `use-search-preset-strip-state.ts` owns
local preset search/category state and filtered-preset derivation. `search-preset-filter.ts`
owns data-driven preset matching and category extraction.
`search-preset-header.tsx` owns preset title/help/count rendering.
`search-preset-category-filter.tsx` owns category buttons and active styling.
`search-preset-card.tsx` owns per-preset row rendering, source chips, launch-hint
chips, and the top-k badge. The page owns only loading presets from the server
and applying a selected preset to the query builder state.
Small retrieval trace and graph facts should also stay outside the page shell:
`frontend/src/features/retrieval/components/trace-fact.tsx` owns trace label/value
rows and `frontend/src/features/retrieval/components/graph-counter.tsx` owns the
Graph-NER handoff count tiles. These are leaf display primitives; they should
not import retrieval hooks, mutate query state, or derive backend policy.
Reusable metric/fact tiles should use
`frontend/src/features/retrieval/components/metric-primitives.tsx`. Integrity
counts, integrity facts, and source-readiness counts are shared visual primitives;
the page and panels remain responsible for backend data, filtering, and policy
decisions.
Retrieval cockpit presentation should stay outside the page shell:
`frontend/src/features/retrieval/components/retrieval-search-cockpit.tsx` owns
the cockpit container and composes the header plus section stack.
`search-cockpit-section-stack.tsx` owns cockpit section order, including
query-health, readiness, metrics, strategy recommendations, standards plan,
source diversity, query transformation, and next-best-action placement.
`search-cockpit-header.tsx` owns the cockpit title, route badges, and
header action/status composition.
`search-cockpit-copy-action.tsx` owns the cockpit report copy button and JSON
report help, while `copy-feedback.ts` owns copied-state timing.
`search-cockpit-status-badges.tsx` owns status badge rendering, and
`search-cockpit-status-badge-view.ts` owns required-bucket and coverage-gap
badge policy.
`search-cockpit-insights.tsx` is only the public insight export surface.
`search-cockpit-metric-grid.tsx` owns metric composition.
`search-cockpit-query-transformation.tsx` owns query transformation summary.
`search-cockpit-next-best-action.tsx` owns next-action text and control
composition. `search-cockpit-apply-action.tsx` owns the top filter apply button,
and `search-cockpit-broaden-controls.tsx` owns source-scope/all-filter
broadening controls. Strategy/search-plan panels and source-diversity panel
placement remain composed by the section stack.
`frontend/src/features/retrieval/model/retrieval-cockpit-view-model.ts` owns
pure cockpit view-model assembly. `retrieval-cockpit-view-types.ts` owns the
view and active-filter contracts shared by cockpit components.
`retrieval-cockpit-view-derivations.ts` owns small pure derivations used by the
view assembler, including required evidence-bucket coverage and route labels.
`retrieval-cockpit-quality-summary.ts` owns quality-summary display mapping and
badge policy. `frontend/src/features/retrieval/model/retrieval-cockpit-runtime.ts`
is only the public cockpit-runtime export surface. `retrieval-cockpit-ranking-runtime.ts`
owns ranking and fusion facts. `retrieval-cockpit-query-runtime.ts` owns
query-analysis parsing. `retrieval-cockpit-diversity-runtime.ts` owns
source-diversity facts. `retrieval-cockpit-evidence-counts.ts` owns coverage
gap and concept-grounding counters. `frontend/src/features/retrieval/model/retrieval-cockpit-signals.ts`
is only the public signal export surface. `retrieval-cockpit-filter-signals.ts`
owns active-filter shaping and re-exports recommended filter-action helpers.
`retrieval-cockpit-recommended-action-filter.ts` owns recommended-action
filter extraction.
`retrieval-cockpit-query-health.ts` owns query-health checklist assembly.
`retrieval-cockpit-query-health-signals.ts` owns extraction of payload/package
signals used by those rules. `retrieval-cockpit-query-health-items.ts` owns
base query-health checklist ordering. `retrieval-cockpit-query-health-item-builders.ts`
owns item object assembly and stable labels.
`retrieval-cockpit-query-health-item-policy.ts` is only the compatibility export
surface for item policy helpers. `retrieval-cockpit-query-health-item-status.ts`
owns status rules, while `retrieval-cockpit-query-health-item-descriptions.ts`
owns static query-health operator text and formatting.
`retrieval-cockpit-query-health-diagnostics.ts` owns query-diagnostic mapping,
and `retrieval-cockpit-query-health-types.ts` owns the query-health item
contract. `retrieval-cockpit-readiness.ts` owns
readiness checklist derivation from query health, evidence buckets, source
diversity, and governance actions. `frontend/src/features/retrieval/components/search-cockpit-panels.tsx`
is only the cockpit panel compatibility export surface. `query-health-panel.tsx`
owns query-health section shell, overall badge, help copy, and row composition.
`query-health-item-card.tsx` owns per-item status, description, and
filter-broadening actions. `search-readiness-checklist.tsx`
owns readiness checklist cards. `cockpit-metric-card.tsx` owns cockpit metric
cells. `query-health-status.ts` owns shared health badge and overall-status
mapping, while `search-cockpit-panel-types.ts` owns shared panel item types.
`frontend/src/features/retrieval/model/retrieval-report-model.ts` is only a
public report-builder barrel. `retrieval-report-cockpit.ts` owns only copied
cockpit report JSON orchestration. `retrieval-report-cockpit-retrieval.ts`
owns retrieval trace fields, `retrieval-report-cockpit-query-analysis.ts` owns
query-analysis report fields, `retrieval-report-cockpit-ranking.ts` owns
ranking-stack report fields, `retrieval-report-cockpit-readiness.ts` owns
evidence-readiness report fields, `retrieval-report-cockpit-rule-packs.ts` owns
rule-pack report rows, and `retrieval-report-cockpit-strategy.ts` owns strategy
recommendation rows. `retrieval-report-evidence-hits.ts` owns evidence-hit
report rows, `retrieval-report-diversity.ts` owns source-diversity report
payloads, and `retrieval-report-medical-hints.ts` owns medical-search-hint route
details. The page derives the cockpit view model,
calls report builders, and passes filter callbacks; cockpit components should
not import retrieval hooks or construct backend reports.
Source-diversity presentation should stay outside the page shell:
`frontend/src/features/retrieval/components/source-diversity-panel.tsx` owns the
source diversity shell and stable compatibility export surface.
`source-diversity-panel-view.ts` owns enabled/disabled explanation text,
state/duplicate badge policy, mode labels, balance-weight labels, and visible
selection derivation.
`source-diversity-metric-card.tsx` owns source-diversity metric cells,
`source-diversity-rationale.tsx` owns selected-hit rationale rows,
`source-list-delta.tsx` owns source-id delta chips, and
`run-comparison-source-diversity.tsx` owns active-vs-baseline
source-diversity comparison. The page derives the diversity stack and comparison
stack from backend trace metadata and uses the exported view-model types where
needed.
Strategy and standards-aware search-plan presentation should stay outside the
page shell. `frontend/src/features/retrieval/components/strategy-standard-panels.tsx`
is only the compatibility export surface. `standard-search-plan-panel.tsx` owns
the healthcare search-plan shell only. `standard-search-plan-header.tsx` owns
the summary, route badges, and help copy. `standard-search-step-card.tsx` owns
per-step layout and filter apply controls. `standard-search-match-reasons.tsx`
owns match-reason chips. `standard-search-governance-notes.tsx` owns per-step
and plan-level governance notes.
`strategy-recommendations-panel.tsx` owns the strategy recommendation section
shell, count badge, help copy, and card list composition.
`strategy-recommendation-card.tsx` owns per-recommendation row rendering,
source-signal chips, and supported filter-action buttons.
`strategy-standard-format.ts` owns route badges, count labels, and
metadata-to-chip interpretation. The page passes the backend plan,
recommendations, and supported-filter action callback without duplicating row
rendering.
Evidence-readiness presentation should stay outside the page shell:
`frontend/src/features/retrieval/components/evidence-readiness-panel.tsx` owns
readiness card composition only. `evidence-readiness-shell-class.ts` owns shell
state styling. `evidence-readiness-header.tsx` owns the readiness title,
coverage summary, and quality summary badge placement.
`evidence-readiness-interpretation-card.tsx` owns readiness interpretation copy
and quality blocker/warning chips.
`evidence-readiness-missing-buckets.tsx` owns missing required-bucket rows and
their supported-filter action buttons. `evidence-readiness-model.ts` is only
the public readiness export surface. `evidence-readiness-view.ts` owns
required-bucket derivation and bucket-signal extraction.
`evidence-readiness-interpretation.ts` owns readiness interpretation and quality
badge variants. `evidence-readiness-types.ts` owns the typed view/filter
contracts, and `evidence-readiness-format.ts` owns count formatting. The page
passes backend package data plus supported filter helpers so the component does
not parse metadata or own retrieval policy.
Result facet refinement should stay outside the page shell:
`frontend/src/features/retrieval/components/result-facets.tsx` owns only the
facet panel shell and section composition. `result-facet-sections.ts` owns
data-driven facet-section derivation, `result-facet-bucket-button.tsx` owns
bucket button presentation and applied/loading states, and
`result-facet-types.ts` owns the shared filter/section contracts. The page owns
active filter state and rerun behavior.
Corrective-action presentation should stay outside the page shell:
`frontend/src/features/retrieval/components/recommended-actions-panel.tsx` owns
recommended-action section composition and empty state only.
`recommended-actions-header.tsx` owns action counts and header badges.
`recommended-action-card.tsx` owns per-action card composition and apply-filter
button placement. `recommended-action-card-header.tsx` owns per-action badges,
source labels, title, and action description layout.
`recommended-action-filter-summary.tsx` owns selected filter display.
`recommended-action-broaden-controls.tsx` owns clear-source-scope and
broaden-search buttons for `broaden_query` actions. `recommended-actions-types.ts`
owns the public filter contract, and `recommended-actions-panel-model.ts` owns
display-only action type counts. The page keeps the backend-derived
action-to-filter helpers and passes them as explicit callbacks so retrieval
policy does not drift into component rendering.
Judgment evaluation presentation should stay outside the page shell:
`frontend/src/features/retrieval/components/judgment-evaluation-panels.tsx` owns
the relevance judgment summary shell and copy-report hook bridge.
`judgment-evaluation-detail-stack.tsx` owns child panel ordering.
`judgment-evaluation-header.tsx` owns heading/header composition only.
`judgment-evaluation-badges.tsx` owns local, stored-label, server-evaluation,
and sync-status badges. `judgment-evaluation-copy-action.tsx` owns copy button
presentation and report-help copy. `use-judgment-evaluation-report-copy.ts`
bridges evaluation-report JSON into shared `copy-feedback.ts` copied-state
timing. `judgment-evaluation-help.tsx` owns judgment metric
operator guidance copy. `judgment-evaluation-outcome-badges.tsx` owns local outcome badges.
`judgment-evaluation-readiness.tsx` owns readiness-status rendering and readiness
badge policy. `judgment-evaluation-metrics.tsx` owns local and server metric
grids. `judgment-evaluation-recommendations.tsx` owns server evaluation
recommendation rows. `judgment-metric-card.tsx` owns the shared metric-card
primitive.
`frontend/src/features/retrieval/hooks/use-retrieval-judgment-session.ts` owns
local relevance judgment state and syncing indicators only.
`use-retrieval-judgment-queries.ts` owns persisted judgment, summary, and server
evaluation query loading. `use-retrieval-judgment-hydration.ts` owns pruning
judgments for removed runs and hydrating persisted rows into local run state.
`use-retrieval-judgment-actions.ts` owns upsert/delete mutation wiring and
mutation side-effect orchestration only. `retrieval-judgment-action-state.ts`
owns local judgment state transitions for toggle removal, optimistic updates,
and persisted-mutation reconciliation. The page only passes active run context
and renders returned state, while
`frontend/src/features/retrieval/model/retrieval-judgment-model.ts` is only the
public judgment export surface. `retrieval-judgment-types.ts` owns shared
contracts. `retrieval-judgment-actions.ts` owns pure optimistic judgment state,
toggle/removal helpers, and index updates. `retrieval-judgment-payload.ts` owns
backend upsert payload construction.
`retrieval-judgment-metrics.ts` owns local metric calculation and nDCG/DCG math.
`retrieval-judgment-report.ts` owns evaluation report JSON assembly.
`retrieval-judgment-mapping.ts` owns persisted-judgment normalization, run-hit
lookup, comparison judgment selection, and judgment keys.
Relevance judgment controls should stay outside the page shell:
`frontend/src/features/retrieval/components/relevance-judgment-control.tsx` owns
the option buttons and operator help text. The judgment-session hook owns
persisted judgment state and mutation hooks; judgment labels, badge policy, and
ratings stay in `retrieval-judgment-labels.ts` so policy remains explicit and
testable.
After a search, the left rail should show a compact search-plan preview before
run history. It should be derived from `RetrievalPackage` and the submitted
search payload, not from local heuristics. The preview should show the backend
route/profile, query aspects, query rewrites, external medical search hints, and
execution tasks plus filter suggestions so non-expert users can understand what
the system searched for before reading ranked evidence or trace internals.
Search-plan preview rendering should stay outside the page shell:
`frontend/src/features/retrieval/components/search-plan-preview-panel.tsx` owns
plan-preview orchestration and suggested-filter/task callback wiring.
`use-search-plan-preview-panel-view.ts` owns panel-level view and copy callback
construction. `search-plan-preview-panel-view.ts` owns plan-preview view-model
assembly from package/plan data. `search-plan-preview-report.ts` owns copied
report payload text assembly. `frontend/src/features/retrieval/components/search-plan-preview.tsx`
owns the pure preview shell and copy feedback bridge. `search-plan-preview-header.tsx`
owns the title and help tooltip. `search-plan-copy-action.tsx` owns the
copy-plan button. `search-plan-preview-empty.tsx`
owns the no-plan/plan-error empty state. `search-plan-preview-content.tsx` owns
summary-stack, detail-stack, and search-running notice composition.
`search-plan-preview-summary-stack.tsx` owns route decision, planning/error
notice, coverage summary, and task-summary composition.
`search-plan-preview-detail-stack.tsx` owns risk-signal, task-preview, aspect,
rewrite, hint, and suggested-filter ordering. `search-plan-preview-notices.tsx` owns
planning, unavailable-plan, and search-running notices.
`search-plan-route-decision-panel.tsx` owns route decision presentation.
`search-plan-suggested-filters-panel.tsx` owns suggested-filter rendering and
filter-apply rows. Component callback contracts live in
`frontend/src/features/retrieval/components/search-plan-preview-types.ts`, while
`frontend/src/features/retrieval/model/search-plan-preview-types.ts` owns preview
view contracts shared by model and presentation code. Retrieval query-analysis
and report models own derivation/export objects.
`frontend/src/features/retrieval/hooks/use-retrieval-plan-session.ts`
owns debounced plan payload state, plan-query loading/error state,
current-plan freshness checks, and stale-result preview package selection; the
page owns only run/filter callbacks.
Execution-task rows should be actionable with target-aware behavior: local
corpus tasks run through the normal retrieval mutation/history path and update
visible query/filter controls. external medical-index tasks open their backend-provided follow-up URL
when available instead of pretending to be local retrieval. Every task row must
also expose a copy-query action so syntax-only external tasks remain usable.
Search-plan task rendering should stay outside the page shell:
`frontend/src/features/retrieval/components/search-plan-task-preview.tsx` owns
the execution-task container and target grouping. `search-plan-task-group.tsx`
owns the group shell and empty-state branch. `search-plan-task-group-view.ts`
owns task ordering, visible-row window, remaining-task selection, and
required/optional counts.
`search-plan-task-group-toolbar.tsx` owns group-level copy-query controls and
count badge rendering. `search-plan-task-group-count-view.ts` owns
required/optional count labels, badge variants, and guidance copy.
`search-plan-task-remaining.tsx` owns the
collapsed remaining-task disclosure. `search-plan-task-row.tsx` owns only the
per-task row composition. `search-plan-task-badges.tsx` owns task priority,
target, required/optional, and label badge rendering. `search-plan-task-badge-view.ts`
owns target and required/optional badge policy. `search-plan-task-action-summary.tsx`
owns the What happens explanation. `search-plan-task-filter-chips.tsx` owns
suggested-filter chips, and `search-plan-task-actions.tsx` owns copy-query
controls, local task execution buttons, and external follow-up links.
`frontend/src/features/retrieval/model/search-plan-tasks.ts` owns deterministic
task ordering, clipboard text, action labels, action descriptions, and external
URL extraction. `frontend/src/features/retrieval/hooks/use-retrieval-search-actions.ts`
is only the public retrieval search-action composition surface.
`use-retrieval-filter-search-actions.ts` is only the public filter/source-scope
search-action composition surface.
`use-retrieval-metadata-filter-search-actions.ts` owns supported-filter
application, clear-filter actions, and filter-suggestion validation.
`use-retrieval-source-scope-search-actions.ts` owns exact source-scope apply and
clear actions. `use-retrieval-plan-filter-action.ts`
owns plan-preview filter suggestion behavior and plan-only confirmation notices.
`retrieval-filter-search-action-policy.ts` owns conditional rerun
policy and source-scope override construction. `use-retrieval-planned-task-action.ts`
owns local task execution from search-plan tasks.
`retrieval-search-task-controls.ts` owns planned-task control synchronization,
`retrieval-search-plan-notice.ts` owns plan-only confirmation notice wording,
and `retrieval-search-action-types.ts` owns shared action contracts. The retrieval page
should pass callbacks and should not duplicate task row presentation or search
action orchestration logic.
Search-plan summary panel rendering should also stay outside the page shell:
`frontend/src/features/retrieval/components/search-plan-summary-panels.tsx` is
only the public summary-panel export surface.
`search-plan-coverage-summary-panel.tsx` owns plan coverage presentation.
`search-plan-task-summary-panel.tsx` owns the execution-summary shell and metric
cards. `search-plan-run-order.tsx` owns run-order guidance.
`search-plan-task-summary-actions.tsx` owns first-action and external-follow-up
buttons, while `search-plan-task-summary-actions.ts` owns deterministic task
selection for those actions. `search-plan-risk-signals-panel.tsx` owns risk
signal rows and severity badges. `search-plan-summary-types.ts` owns shared
summary view contracts used by model and presentation code. The retrieval plan
preview panel derives coverage/task/risk view models from backend contracts,
then passes display-ready values into those panels.
Search-plan detail panel rendering should stay in
`frontend/src/features/retrieval/components/search-plan-detail-panels.tsx` as a
compatibility export surface only. `search-plan-aspect-preview.tsx` owns aspect
rows, `search-plan-rewrite-preview.tsx` owns query rewrite rows,
`search-plan-hint-preview.tsx` owns medical search hints, and
`search-plan-filter-suggestion-preview.tsx` owns filter suggestion rows.
`search-plan-detail-types.ts` owns shared plan-detail view contracts, while
`search-plan-detail-format.ts` owns shared display formatting. The page remains
responsible for backend plan loading and passing search-action callbacks, while
`retrieval-filter-model.ts` derives query-profile/query-aspect filter entries
from normalized query-analysis data.
Supported filter suggestions in the same preview should also be actionable
before full search. Applying one must reuse the normal filter/query-builder path:
plan-only previews update visible controls without immediately running search,
while fresh completed-package previews may refresh ranked evidence with the new
filter. The action should disable itself while the suggestion is already applied
or search is pending. Plan-only filter application should show an inline confirmation near the active filter controls
telling the operator to run search to refresh evidence.
The same preview must include a plan coverage summary before task details:
required local tasks, optional external follow-ups, inferred standards, filter
count, and any plan warnings. This is a pre-search readiness view over backend
plan fields, not a second frontend retrieval policy. Prefer
`RetrievalPlan.coverage_summary`; a frontend-derived summary is only a
compatibility fallback for completed packages or older plan payloads. The
coverage card should show `coverage_summary.next_action` as the primary operator
instruction before task details.
The preview should also show `RetrievalPlan.task_summary` as the execution
summary before individual task rows. This summary is the backend source of truth
for runnable local tasks, required first actions, manual external follow-ups,
blocked tasks, and the operator-facing `primary_action`; the frontend may derive
the same shape only as a compatibility fallback. The summary panel should expose
guided actions for running the first required local task and copying external
medical follow-up queries so the plan can be acted on without scanning all task
rows.
The same summary panel must include a plain-language run order for non-expert
operators: run required local corpus tasks first, apply supported filters when
needed, then review external medical-index follow-ups as manual context. Each
task row should also include a compact "What happens" explanation derived from
`target` and `action_type` so users can distinguish governed OJTFlow evidence searches
from external links or copied manual queries before clicking an action.
Task rows should be grouped by target: local OJTFlow searches first, then
external follow-ups. This prevents a long list of manual medical-index links
from hiding the actions that can actually refresh governed evidence inside the
app, and it makes empty states explicit when one class of task is absent. Each
group should keep the first tasks visible and expose overflow through an inline
"Show remaining" disclosure so no backend-generated task is lost behind a copy
JSON escape hatch. Each group should also show required and optional task counts
using the backend `required` flag so non-expert operators can prioritize before
opening individual task rows. Within each group, required tasks should render
before optional tasks, then by backend priority and label; the backend task plan
remains unchanged, but the grouped UI reflects the operator priority model.
Each group should provide a copy action for all queries in that group
so operators can export only local OJTFlow searches or only external follow-ups
without copying the full search-plan JSON. Task clipboard exports should use one
shared formatter and include required/optional status, priority, target, action,
query text, and URL when an external follow-up has one.
The preview should also show `RetrievalPlan.risk_signals[]` as a compact
pre-search risk panel. Frontend fallback signals may only adapt existing
diagnostics/coverage for compatibility; new risk policy belongs in the backend.
When a completed search returns zero ranked hits, the result panel must render
operator remediation instead of a generic empty state: candidate count, active
submitted filters, missing required evidence buckets, source-inventory guidance,
direct controls to clear exact source scope or all active metadata filters, and
any supported backend corrective filter.
Zero-hit remediation presentation should stay outside the page shell:
`frontend/src/features/retrieval/components/no-result-remediation-panel.tsx` is
only the shell for zero-hit remediation. `no-result-remediation-header.tsx` owns
the no-evidence title and summary badges. `no-result-loosen-scope-card.tsx` owns
active-filter chips plus clear-source and clear-all controls.
`no-result-quality-card.tsx` owns source-inventory and quality-gap guidance.
`no-result-suggestion-card.tsx` owns supported backend corrective-filter apply
controls. `search-results-no-result-remediation.tsx` owns submitted-filter
derivation, missing-bucket counts, candidate counts, and backend corrective-action
selection from the retrieval package. The page and hit list only decide whether
zero-hit remediation should be rendered.
The route
loads search presets from `/retrieval/presets` so healthcare examples and
default query-builder state are managed as trusted knowledge data rather than
hardcoded React constants. The preset selector should apply query, fields,
schema, format, resource, and metadata constraints without executing a search;
operators still submit explicitly. Preset category filters and preset text
search are derived from preset data so the selector remains usable as the
registry grows. Query-builder controls must explain what each scope parameter
does, especially query text, fields, schema, Top K, source format, resource,
domain, standard, trust, and source type, because these parameters directly
change evidence recall and governance risk. Format and top-K controls come from
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
Query rewrite rendering should stay outside the page shell:
`frontend/src/features/retrieval/components/query-variant-list.tsx` owns the
rewrite empty state, explanatory copy, and copy-feedback state.
`query-variant-row.tsx` owns source badges, copy-query button UI, reason text,
and variant card layout. Query rewrites should be actionable: operators must be
able to copy backend-generated rewrites to rerun manually, compare them with
the submitted query, or use them during external medical search follow-up. The
retrieval trace/query-analysis models own variant derivation and fallback compatibility.
per-hit ranking boost signals from `source_locator.ranking_boosts`, including
the applied rule ID, reason, and weight, with
`source_locator.ranking_boost_rules` kept as the compatibility fallback for
older payloads. It must also surface source coverage from retrieval
diversity metadata so redundant single-source results are visible during
evidence review. Result cards must render per-hit diversity selection details
from first-class `diversity.selected_hits`, falling back to
`handoff_context.diversity.selected_hits` for older responses. Details must
include original rank, normalized relevance, redundancy, MMR score, and
selection reason.
Result cards must also render `source_locator.query_aspect_matches[]` as
per-hit aspect support, including aspect label, priority, matched filters,
matched terms, and reason.
Result cards must also render `source_locator.concept_matches[]` as per-hit
concept grounding, including standard system, optional code, display name,
confidence, matched fields, aliases, and reason.
Per-hit explanation rendering should stay outside the page shell:
`frontend/src/features/retrieval/components/hit-card.tsx` is only the ranked
hit shell. It assembles the per-hit view model, keeps the card section order,
and wires the header, relevance control, score section, evidence section, and
locator disclosure. `hit-card-types.ts` owns the public hit-card prop contract
and relevance-judgment aliases. `hit-card-evidence-section.tsx` owns
snippet/claim display, evidence summary panels, interpretation guidance, match
explanation, and provenance. `hit-card-score-section.tsx` owns score meters,
score explanation, source-diversity rationale, concept/aspect support, ranking
signals, and matched terms. `use-hit-card-copy-report.ts` owns the copy-to-JSON
workflow.
`hit-card-header.tsx` owns rank/source identity badges and the copy-to-JSON
action surface.
`frontend/src/features/retrieval/model/hit-card-view-model.ts` owns per-hit
view derivation: evidence signals, support summary, match explanation,
usability summary, provenance entries, and copy key. `hit-card-report.ts` owns
copyable evidence report serialization from the hit-card view.
`hit-ranking-signals.tsx` owns ranking boost rows.
`hit-matched-terms.tsx` owns exact matched-term chips. `hit-locator-details.tsx`
owns the locator/evidence-id disclosure. The retrieval page maps backend hits to
`HitCard` props and owns filters, judgments, and search orchestration.
`frontend/src/features/retrieval/components/hit-explanation-panels.tsx` is only
the stable explanation barrel. `hit-score-explanation.tsx` owns score meters and
score-component rows; `hit-diversity-selection.tsx` owns diversity-selection
details; `hit-concept-grounding.tsx` owns concept grounding cards; and
`hit-query-aspect-support.tsx` owns query-aspect support cards. Evidence logic is split under
`frontend/src/features/retrieval/model/`: `retrieval-evidence-signals.ts` is
only the public evidence-signal export surface. `retrieval-evidence-score-components.ts`
owns hit-derived score components. `retrieval-evidence-signal-extraction.ts`
owns concept matches, query-aspect matches, and ranking boost signals.
`retrieval-evidence-hit-signals.ts` owns the combined hit-signal view.
`retrieval-evidence-match-explanation.ts` owns match-explanation assembly.
`retrieval-evidence-match-explanation-fallback.ts` owns signal-derived fallback
values when backend match-explanation fields are absent.
`retrieval-evidence-match-explanation-merge.ts` owns backend/fallback merge
policy and support-status fallback.
`retrieval-evidence-match-explanation-values.ts` owns matched bucket lookup and
top-score fallback value derivation.
`retrieval-evidence-match-explanation-backend.ts` owns raw
backend `match_explanation` field extraction and coercion. `retrieval-evidence-provenance.ts` owns
locator/provenance summaries and source links; `retrieval-evidence-support.ts`
is only the support-model barrel; `retrieval-evidence-support-summary.ts` owns
support summaries, support status, and support-status badge policy;
`retrieval-evidence-support-hit.ts` adapts hit data into support summaries;
`retrieval-evidence-support-matrix.ts` owns support matrix rows and bucket-label
lookups; `retrieval-evidence-use-guidance.ts` is only the compatibility export
surface for evidence-use guidance; `retrieval-evidence-use-guidance-action.ts`
owns operator action guidance, `retrieval-evidence-use-guidance-reasons.ts`
owns reason extraction, and `retrieval-evidence-usability-summary.ts` owns
usability summary wording;
`retrieval-evidence-report.ts` owns copied evidence JSON reports.
`retrieval-evidence-corrective-actions-report.ts` owns corrective-action report
context shaping for copied evidence reports.
`retrieval-evidence-types.ts` is only the public evidence-type export surface.
`retrieval-evidence-provenance-types.ts`, `retrieval-evidence-support-types.ts`,
`retrieval-evidence-matrix-types.ts`, `retrieval-evidence-signal-types.ts`, and
`retrieval-evidence-match-types.ts` own provenance, support, matrix, signal, and
match-explanation contracts. `retrieval-evidence-model.ts`
is only the stable barrel export. The page owns diversity selection lookup and
passes model-derived values into presentation components.
Result cards must render a compact evidence support summary above the detailed
sections, using data-derived counts for matched terms, provenance fields,
grounded concepts, supported aspects, and ranking signals.
Ranked evidence triage should stay outside the page shell:
`frontend/src/features/retrieval/components/ranked-evidence-triage.tsx` owns
the section shell, guidance icon placement, and decision-state badge.
`ranked-evidence-triage-guidance.ts` owns triage policy and readiness tone
selection. `ranked-evidence-triage-facts.tsx` owns compact facts for hits,
required evidence buckets, judgments, and readiness, while
`ranked-evidence-triage-fact.tsx` owns the repeated fact primitive.
`ranked-evidence-triage-types.ts` owns the view contract. The page derives the
triage view from backend package state and relevance metrics. The triage must
warn before use when results are stale, no hits were returned, required buckets
are missing, or no relevance labels exist.
Evidence support matrix rendering should stay outside the page shell:
`frontend/src/features/retrieval/components/evidence-support-matrix.tsx` owns
the matrix section shell and help copy; `evidence-support-matrix-card.tsx` owns
mobile card composition, `evidence-support-matrix-card-header.tsx` owns mobile
card rank/source/status/score header rendering, `evidence-support-mobile-field.tsx`
owns repeated mobile field wrappers, and `evidence-support-signal-badges.tsx`
owns reusable support signal badges for both mobile cards and the desktop table.
`evidence-support-matrix-table.tsx` owns the desktop table shell;
`evidence-support-matrix-table-row.tsx` owns desktop per-evidence row cells;
`evidence-support-matrix-types.ts` owns shared row and formatter contracts. The
retrieval page owns judgment lookup and passes package state into `retrieval-evidence-model`;
`retrieval-evidence-support-matrix.ts` owns `evidenceSupportMatrixRows` and
bucket-label lookup, while `retrieval-evidence-support-summary.ts` owns
support-status derivation so evidence policy remains centralized.
Corrective-action type chips should stay outside the page shell:
`frontend/src/features/retrieval/components/corrective-action-type-count-chips.tsx`
owns the compact count chip rendering, while
`frontend/src/features/retrieval/model/corrective-actions.ts` owns deterministic
action-type count sorting shared by search-run summaries and chip display.
Section help copy should use the local primitive
`frontend/src/features/retrieval/components/section-help-text.tsx` instead of
inline paragraph classes. This keeps explanatory copy visually consistent while
larger panels continue to own their data and actions.
Token-list empty states and warning chips should use
`frontend/src/features/retrieval/components/token-list.tsx`. This keeps the
common "none"/warning chip treatment consistent across quality, coverage,
integrity, and query-analysis panels without moving those panels' data logic.
Retrieval quality-signal rendering should stay split by responsibility:
`quality-signal-list.tsx` owns the section shell and empty state;
`quality-signal-list-item.tsx` owns the individual signal card and evidence-id
chips; `quality-signal-metadata-details.tsx` owns metadata detail display;
`quality-signal-metadata.ts` owns metadata detail assembly,
`quality-signal-metadata-sections.ts` owns deterministic concept/provenance/filter
metadata extraction, `quality-signal-metadata-values.ts` owns primitive metadata
coercion, and
`quality-signal-variants.ts` owns severity badge policy reused by other panels.
Signal policy still comes from backend contracts.
Result cards must also render a compact `Why this matched` explanation using
existing retrieval package data: top score driver, evidence-pack bucket
membership, exact matched terms, concept/aspect grounding, provenance count,
and ranking-signal count. The same `match_explanation` object used by copied
reports must include stable bucket IDs, concept IDs, query-aspect IDs,
provenance field labels, ranking-signal rule IDs, and the top score component
object, not only display labels. This explanation should sit near the claim so
users do not need to inspect raw score components or locator JSON to understand
why a source appeared.
Each result card must also translate support signals into operator action
guidance: strong evidence can be used with provenance check, partial evidence
needs review before relying on it, and weak evidence should trigger query/source
adjustment or a not-relevant judgment. This guidance must be derived from
matched terms, provenance, concept/aspect grounding, ranking signals, evidence
buckets, and persisted relevance judgment state. It must not create new medical
claims or hide the raw evidence details.
Per-hit interpretation guidance should stay outside the page shell:
`frontend/src/features/retrieval/components/evidence-interpretation-guidance.tsx`
is only the public interpretation-guidance export surface.
`evidence-usability-summary-panel.tsx` owns the usability summary layout.
`evidence-use-guidance-panel.tsx` owns evidence-use guidance presentation.
`hit-match-explanation-panel.tsx` owns the `Why this matched` section shell,
status badge, and grounding badges. `hit-match-explanation-metric.tsx` owns each
metric card.
`evidence-support-status.ts` owns shared support-status badge mapping, and
`evidence-interpretation-guidance-types.ts` owns shared presentation contracts.
Evidence-support model helpers own
support-summary, support-status, hit-adapter, and use-guidance derivation from
hits/provenance/signals; the retrieval page should pass those helpers into
result composition and keep only current package, judgment, and callback state.
Result cards must render a compact evidence provenance summary with source
version and key locator fields such as standard, URL, path, PMID, DOI, API,
resource, table, document, and chunk identifiers before the raw JSON details.
URL/API values, PubMed IDs, and DOIs must render as external links when they can
be safely normalized.
Evidence provenance and snippet rendering should stay outside the page shell:
`frontend/src/features/retrieval/components/evidence-provenance-snippet.tsx` is
only the public provenance/snippet export surface.
`evidence-provenance-summary.tsx` owns provenance field badges and external-link
rendering. `snippet-block.tsx` owns snippet range display and matched-term chips.
`highlighted-text.tsx` owns inline highlight rendering, while
`evidence-highlight-utils.ts` owns term normalization, highlight splitting, and
matched-term count labels. Snippets must expose backend-provided matched terms
as visible chips so operators can see why a passage ranked without opening raw
JSON. The retrieval page owns provenance entry derivation, locator
normalization, copied evidence reports, and claim formatting.
Each ranked evidence card must also offer a copyable `retrieval_evidence_hit`
report containing evidence identity, support-summary counts, `match_explanation`,
ranking scores/components, concept/aspect grounding, provenance summary,
locators, and snippet context.
The retrieval cockpit must expose package-level source-diversity selection.
First-class `diversity.selected_hits` should render as selected-hit rationale
with source ID, selected rank, original rank, redundancy score, selection score,
and the backend-provided reason. The same selection details should be included
in copied answer and cockpit reports so source balance remains auditable
outside the browser.
Run comparison must also compare source-diversity deltas between active and
baseline runs: selected-source count, candidate-source count, duplicate selected
source count, selected-source overlap, added/removed/retained source IDs,
selection mode, and lambda. This prevents relevance tuning from accidentally
improving score order while narrowing evidence to one source family.
Copy actions for evidence, comparison, evaluation, and search-hint reports must
show transient success feedback so operators can tell the clipboard action
completed without opening developer tools or raw browser state. Report copy
buttons should identify that they export JSON and explain the report's intended
offline use, such as cockpit audit context, single-hit evidence support,
run-comparison tuning, or judgment-evaluation metrics. Retrieval components
should use `frontend/src/features/retrieval/components/copy-feedback.ts` for
clipboard fallback behavior and copied-state timers instead of duplicating local
DOM clipboard helpers.
The ranked-result panel must render the package-level clinical evidence pack
from `evidence_buckets[]`, including required schema/policy gaps, bucket hit
counts, source IDs, and warnings. This gives operators a fast readiness scan
across evidence classes before reading individual cards.
The ranked-result panel must also render an evidence support matrix before the
long card list. Each row should summarize rank, source, standard system,
package evidence buckets, matched-term count, provenance count, concept
grounding count, query-aspect count, persisted judgment state, final score, and
a deterministic support status. The matrix must derive from `RetrievalPackage`
hits, `evidence_buckets[]`, `source_locator` metadata, and persisted judgments;
it must not create hidden clinical claims or browser-only relevance scores. The
matrix must explain how to interpret weak rows, missing provenance, and missing
concept/aspect support before users inspect long evidence cards.
Per-hit evidence support chips should stay outside the page shell:
`frontend/src/features/retrieval/components/hit-evidence-audit-strip.tsx`
owns the compact matched-term, provenance, concept, aspect, and ranking-signal
badges. Evidence-support models own support-summary derivation from hits,
provenance, match explanation, and ranking metadata; the page should not carry
local support-status helper functions.
Per-hit relevance judgment controls should also stay outside the page shell:
`frontend/src/features/retrieval/components/relevance-judgment-control.tsx`
owns the judgment control shell, help copy, and option-button rendering. The
retrieval page owns loaded judgment state and mutation calls; judgment model
modules own option definitions, labels, badge policy, metric calculations, and
persisted-judgment normalization.
Each ranked evidence card must also render a compact usability summary derived
from the same support status, match explanation, provenance, bucket membership,
and persisted judgment state. It should state whether the hit is strong,
partial, or weak support, give the next operator recommendation, name the
primary limitation, and export the same data as `usability_summary` in copied
`retrieval_evidence_hit` JSON.
On mobile, the evidence support matrix must render card rows instead of forcing
the wide table as the primary view. The desktop table can remain horizontally
scrollable for comparison, but the mobile-first view should show each evidence
row as rank/source, standard, buckets, support badges, judgment, and score.
The same ranked-result panel must render an evidence-readiness summary above
the bucket grid. It should translate the backend
`missing_required_evidence_buckets` quality signal into required-gap badges,
show the current `quality_summary` status/score, and display the backend
suggested action so operators know the next remediation step without opening
trace metadata. When a missing bucket provides a supported `suggested_filter`,
the panel should expose an explicit Apply action that reruns search through the
same typed filter path used by facets and coverage diagnostics.
The readiness summary must also provide an operator interpretation of the
quality status: ready means inspect provenance before use, review means require
human review, blocked means do not use downstream, and missing scores are
treated as unreviewed.
The ranked-result and trace panels must render backend
`recommended_actions[]` as a corrective-action checklist. Each action should
show priority, action type, source quality signal, description, and an Apply
button only when the backend provides a supported `suggested_filter`. The UI
must not invent hidden corrective actions in the browser; the mapping comes
from the active backend `corrective_actions` retrieval rule pack.
The corrective-action checklist and recent-run summaries should show backend
action-type counts from `recommended_action_summary.action_type_counts`,
including broaden-query and apply-filter counts, so users can understand the
kind of remediation requested before reading detailed action rows.
Recent-run rows render those values as compact action-type chips beside the
total action count, sorted by count, so repeated searches can be compared
without opening the trace.
Each recent-run row should also render a plain-language `Run remediation`
summary derived from backend quality/action summaries: top corrective action
when available, quality top action when no corrective action exists, warning
inspection when only warnings exist, or broadening/source-inventory guidance for
zero-hit runs. The same derived summary should be included in copied cockpit and
comparison JSON reports as `remediation_summary` so audit notes match what the
operator saw in the run history. New packages should use backend
`RetrievalPackage.remediation_summary`; local derivation is only a compatibility
fallback for older payloads.
Recent-run evidence scope display should stay outside the page shell:
`frontend/src/features/retrieval/components/search-run-evidence-summary.tsx`
owns the compact Run scope and Run remediation card, while
`search-run-evidence-summary-view.ts` owns coverage-gap, grounded-concept, and
search-aspect badge labels and variants.
`frontend/src/features/retrieval/model/search-run-presentation.ts` is only the
public run-presentation export surface. `search-run-labels.ts` owns scope labels
and corrective-action source labels. `search-run-quality.ts` owns quality badge,
tone, delta badge, signed-delta, and readiness-glance derivation.
`search-run-remediation.ts` owns plain-language remediation fallback text.
`search-run-history-model.ts` owns local run construction and comparison
baseline selection. The
`frontend/src/features/retrieval/hooks/use-retrieval-run-session.ts` owns
run-session behavior composition. `use-retrieval-run-session-state.ts` owns
local active run ID, submitted payload, signature, recent-run list, and
comparison baseline state. `retrieval-run-session-record.ts` owns
pure run-record construction from submitted payloads and backend packages.
`retrieval-run-session-transitions.ts` owns pure completed-search, restore, and
clear transition payloads for run-session state. `retrieval-run-session-validation.ts` owns
run-session payload validation messages.
`retrieval-run-session-completion.ts` owns committing completed search runs into
session state, including recent-run history upsert, active run selection,
submitted payload, and last search signature updates.
`use-retrieval-run-session-actions.ts` is only the public run-session action
composition surface. `use-retrieval-run-search-action.ts` owns React callback
memoization and form-submit event handling.
`retrieval-run-search-executor.ts` owns the search execution sequence: form
payload creation, payload validation, backend search call, run record creation,
and completed-run commit. `use-retrieval-run-history-actions.ts` owns
submitted-search restore, run restore, and clear-run callbacks.
`use-active-retrieval-run-state.ts` owns active run/package selection for the
session hook.
`retrieval-run-session-history.ts` owns pure recent-run history policy,
including signature-based upsert, history-limit pruning, and stale comparison
baseline detection, plus active run/package selection. `use-retrieval-run-session-types.ts` owns the hook input
contract. The
retrieval page should compose the hook and panels; it should not duplicate run
presentation, local run creation, or comparison selection logic inline.
Recent-run history rendering should stay outside the page shell:
`frontend/src/features/retrieval/components/search-run-history.tsx` owns run
history card composition, clear behavior, and row list placement.
`search-run-history-row.tsx` owns the clickable row shell and restore behavior.
`search-run-history-row-summary.tsx` owns only the row title/status summary
composition. `search-run-history-row-badges.tsx` owns per-run profile,
warning/action, signature, and corrective-action badges.
`search-run-history-row-details.tsx` owns top source/profile/action detail
lines. `search-run-history-row-actions.tsx` owns the comparison baseline button.
Embedded run-scope summaries stay in `search-run-evidence-summary.tsx`.
`search-run-history-format.ts` owns small run-history formatting and status-variant helpers, and
`search-run-history-types.ts` owns the local component contract.
`frontend/src/features/retrieval/components/search-run-history-panel.tsx` owns
recent-run composition and comparison node placement.
`search-run-comparison-active.ts` owns active-vs-baseline comparison selection
and facet config construction. `use-search-run-comparison-view.ts` owns
comparison judgment selection, recommended-action/report assembly, operator
summary derivation, and rule-pack view mapping.
`search-run-comparison-node.tsx` owns mapping that derived comparison view into
`SearchRunComparisonPanel` props. `search-run-history-panel-types.ts` owns the
panel contract. The run-session hook owns run list state, restore behavior,
selected active run ID, and selected baseline run ID; the page passes callbacks
only.
Search-run comparison container rendering should stay outside the page shell:
`frontend/src/features/retrieval/components/search-run-comparison-panel.tsx`
owns the comparison card shell, header placement, summary/detail section
placement, and footer placement. `search-run-comparison-help.tsx` owns comparison
guidance copy, and `search-run-comparison-top-source.tsx` owns top-source footer
rendering. `search-run-comparison-summary-section.tsx`
owns operator summary, baseline query, at-a-glance metrics, diagnosis,
recommended actions, comparison metrics, source-diversity summary, and the
compact delta metric grid. `search-run-comparison-detail-section.tsx` owns
query-profile, concept-grounding, query-aspect, coverage, quality-signal, facet,
rule-pack, rank-movement, and evidence-change detail panels.
`search-run-comparison-types.ts` owns shared comparison panel contracts.
`search-run-comparison-header.tsx` owns header layout and comparison-report copy
UI, `search-run-comparison-status-badges.tsx` owns status badge policy, and
`copy-feedback.ts` owns copied-state timing.
`search-run-comparison-baseline.tsx` owns the baseline
query row; `search-run-comparison-metric-grid.tsx` owns the compact delta metric
grid. The page should not calculate rank movement, evidence churn,
quality-signal deltas, coverage changes, source-diversity deltas, rule-pack
diffs, or copied comparison reports inline.
`frontend/src/features/retrieval/model/retrieval-run-comparison.ts` is only the
public comparison export surface. `retrieval-run-comparison-builder.ts` owns
run-to-run comparison orchestration and diagnosis attachment.
`retrieval-run-comparison-dimension-values.ts` owns dimension fan-out for
evidence churn, rank movement, coverage, facets, quality signals, concept
grounding, query aspects, rule packs, and source diversity.
`retrieval-run-comparison-core-values.ts` owns scalar delta and top-source flag
calculation. `retrieval-run-comparison-run-values.ts` owns active/baseline run
identity and payload mapping. `retrieval-run-comparison-metric-input.ts` owns
aggregate metric input assembly from evidence churn and rank movement. Shared contracts live in
`retrieval-run-comparison-types.ts`, which is only the public
comparison-type export surface. `retrieval-run-comparison-core-types.ts` owns
the aggregate comparison contract, `retrieval-run-comparison-change-types.ts`
owns query aspect, concept grounding, coverage, and quality-signal change-set
contracts, `retrieval-run-comparison-facet-types.ts` owns facet comparison
contracts, `retrieval-run-comparison-metric-types.ts` owns aggregate metric
contracts, `retrieval-run-comparison-rank-types.ts` owns rank movement
contracts, and `retrieval-run-comparison-rule-pack-types.ts` owns rule-pack
change contracts.
`retrieval-run-comparison-metrics.ts` is
only the public metrics export surface. `retrieval-run-comparison-aggregate-metrics.ts`
owns evidence-overlap/churn metrics, `retrieval-run-comparison-evidence.ts`
owns added/removed/retained evidence-id set deltas,
`retrieval-run-comparison-rank-changes.ts` owns rank movement,
`retrieval-run-comparison-source-diversity.ts` owns source-diversity deltas,
`retrieval-run-comparison-quality-summary.ts` owns readiness fingerprint and
quality-score deltas, and `retrieval-run-comparison-rule-packs.ts` owns
rule-pack diffs and rule-pack view mapping. `retrieval-run-comparison-dimensions.ts`
is only the public dimension-comparison export surface.
`retrieval-run-comparison-coverage.ts` owns coverage status changes,
`retrieval-run-comparison-facets.ts` owns facet value deltas,
`retrieval-run-comparison-quality-signals.ts` owns quality-signal deltas,
`retrieval-run-comparison-profiles.ts` owns query-profile change checks, and
`retrieval-run-comparison-concepts.ts` owns query-aspect and concept-grounding
comparisons. The page should not duplicate any of that derivation inline.
`frontend/src/features/retrieval/model/retrieval-comparison-diagnosis.ts`
is only a compatibility barrel. `retrieval-comparison-diagnosis-rules.ts` owns
only public diagnosis composition. Profile, grounding, and rule-pack warnings
live in `retrieval-comparison-diagnosis-profile-rules.ts`; coverage, quality
signals, and readiness changes live in
`retrieval-comparison-diagnosis-quality-rules.ts`; facet, top-source,
source-diversity, rank, and evidence-set changes live in
`retrieval-comparison-diagnosis-source-rules.ts`; and the stable fallback lives
in `retrieval-comparison-diagnosis-stability.ts`.
`retrieval-comparison-actions.ts` is only the compatibility export surface.
`retrieval-comparison-recommended-actions.ts` is only the recommended-action
export surface. `retrieval-comparison-recommended-action-policy.ts` owns
recommended-action policy composition only.
`retrieval-comparison-recommended-action-quality.ts` owns quality-summary,
coverage, and quality-signal actions;
`retrieval-comparison-recommended-action-configuration.ts` owns query-profile
and rule-pack actions; `retrieval-comparison-recommended-action-evidence.ts`
owns evidence-churn and source-diversity actions;
`retrieval-comparison-recommended-action-judgments.ts` owns missing-judgment
actions; `retrieval-comparison-recommended-action-stable.ts` owns the stable
fallback action; and
`retrieval-comparison-recommended-action-summary.ts` owns recommended-action
summary derivation.
`retrieval-comparison-operator-summary.ts` owns operator-summary derivation.
`retrieval-comparison-action-format.ts` owns small formatting helpers shared by
comparison action summaries. `retrieval-comparison-report.ts` owns only the
public copied comparison report assembler.
`retrieval-comparison-report-summary.ts` owns report summary derivation, and
`retrieval-comparison-report-sections.ts` is only the public report-section
export surface. `retrieval-comparison-report-run-sections.ts` owns
active/baseline run sections and remediation. `retrieval-comparison-report-deltas.ts`
owns deltas, dimensions, and facet change reports. `retrieval-comparison-report-evidence.ts`
owns judgments, evidence IDs/rank changes, and rule-pack report sections.
`retrieval-comparison-report-source-diversity.ts` owns source-diversity report
sections. `retrieval-comparison-types.ts` is only the public
comparison-contract export surface. `retrieval-comparison-diagnosis-types.ts`
owns diagnosis contracts and diagnostic input shape.
`retrieval-comparison-recommendation-types.ts` owns recommended-action contracts
and recommendation input shape. `retrieval-comparison-summary-types.ts` owns
operator-summary contracts. `retrieval-comparison-report-types.ts` owns copied
report input contracts. `retrieval-comparison-judgment-types.ts` owns
comparison judgment input contracts.
`frontend/src/features/retrieval/model/retrieval-search-payload.ts` owns
retrieval form serialization, field parsing, and search signature construction.
`retrieval-planned-task-payload.ts` owns planned-task search override and
supported-filter mapping policy. The form-session hook and retrieval page should
import those helpers and keep React state/effects, not duplicate request payload
policy.
`frontend/src/features/retrieval/model/retrieval-search-options-model.ts` owns
query-builder option view derivation from backend search options, trusted
sources, presets, and current form state. It also owns search-option merging,
selected-source lookup, metadata option lists, and numeric option normalization.
The page owns current control state, but not option-list construction rules.
`frontend/src/features/retrieval/model/retrieval-query-analysis.ts` owns only
public query-analysis orchestration and exports. `retrieval-query-analysis-stack.ts`
owns record-to-stack assembly from backend query-analysis records. Shared query-analysis contracts
live in `retrieval-query-analysis-types.ts`. `retrieval-query-analysis-values.ts`
is only a public value-parser export surface. Primitive backend coercion and
shared uniqueness helpers live in `retrieval-query-analysis-coercion.ts`.
`retrieval-query-analysis-profile-values.ts` is only the profile/aspect/concept/
filter/diagnostic/hint value-parser export surface. Profile records live in
`retrieval-query-analysis-profile-value.ts`, query aspects in
`retrieval-query-analysis-aspect-values.ts`, concept candidates in
`retrieval-query-analysis-concept-values.ts`, filter suggestions in
`retrieval-query-analysis-filter-values.ts`, diagnostics in
`retrieval-query-analysis-diagnostic-values.ts`, and search hints in
`retrieval-query-analysis-hint-values.ts`.
Retrieval task parsing and action-type fallback policy live in
`retrieval-query-analysis-task-values.ts`.
`retrieval-query-analysis-plan.ts` is only the public plan export surface.
`retrieval-query-analysis-plan-summary.ts` is only the plan-summary export
surface. `retrieval-query-analysis-plan-coverage-summary.ts` owns plan coverage
fallback derivation and next-action policy.
`retrieval-query-analysis-plan-task-summary.ts` owns task-summary fallback
derivation and primary-action policy. `retrieval-query-analysis-plan-risk.ts` owns risk-signal
fallback derivation. `retrieval-query-analysis-plan-values.ts` owns backend
plan summary and risk-signal value coercion. Query rewrite conversion lives in
`retrieval-query-analysis-variants.ts`. The page may map normalized objects
into display-specific filter labels, but should not parse backend
query-analysis payloads directly.
`frontend/src/features/retrieval/model/retrieval-runtime-stack.ts` is the public
runtime-stack export surface. `retrieval-runtime-ranking-stack.ts` is only the
public ranking-stack export surface. `retrieval-runtime-ranking-types.ts` owns
ranking/fusion contracts. `retrieval-runtime-ranking-extraction.ts` owns
ranking-framework, embedding, and reranker normalization from backend payloads.
`retrieval-runtime-ranking-labels.ts` owns hybrid, framework, embedding, and
reranker display labels. `retrieval-runtime-fusion-diagnostics.ts` owns fusion
diagnostic normalization and display tone.
`retrieval-runtime-diversity-stack.ts` owns source-diversity normalization and
diversity-selection lookup helpers. `retrieval-runtime-quality-policy.ts` owns
quality-policy normalization and trace labels. Shared source-diversity contracts
live in `retrieval-source-diversity-types.ts`; model code must not import those
contracts from the presentation component. The page should consume those model
helpers for trace facts, cockpit reports, and run summaries instead of parsing
`handoff_context` runtime metadata inline.
`frontend/src/features/retrieval/model/retrieval-run-summary.ts` owns only run
summary orchestration and stable public exports. Shared run-summary contracts
live in `retrieval-run-summary-types.ts`; low-level value coercion lives in
`retrieval-run-summary-values.ts`. Quality warning counts and quality-summary
fingerprints live in `retrieval-run-quality-summary.ts`. Rule-pack normalization
and fingerprints live in `retrieval-run-rule-packs.ts`. `retrieval-run-dimensions.ts` is only the
public dimension export surface. Coverage summaries live in
`retrieval-run-coverage.ts`, query-profile summaries live in
`retrieval-run-query-profile.ts`, query-aspect summaries live in
`retrieval-run-query-aspects.ts`, and concept-grounding summaries live in
`retrieval-run-concept-grounding.ts`.
Corrective-action summaries live in `retrieval-run-actions.ts`. The page may
compare summaries and compose reports, but it should not rebuild package-level
run summaries inline.
Copied retrieval report JSON builders should stay outside React components.
`retrieval-report-plan.ts` owns search-plan preview report composition.
`retrieval-report-standard-plan.ts` owns standard-search-plan report
serialization. `retrieval-report-interpretation.ts` owns fallback interpretation
reports. `retrieval-report-cockpit.ts` owns only the cockpit report assembler;
`retrieval-report-cockpit-*.ts` files own retrieval, query-analysis, ranking,
readiness, rule-pack, and strategy subreports.
`retrieval-report-diversity.ts`, `retrieval-report-evidence-hits.ts`, and
`retrieval-report-medical-hints.ts` own the source-diversity, evidence-hit, and
medical-search-hint subreports used by that assembler. Shared report value
coercion lives in `retrieval-report-values.ts`. Components may pass current
package/plan state into these builders, but should not assemble those report
schemas inline.
`frontend/src/features/retrieval/model/retrieval-format.ts` owns shared
deterministic formatting helpers for claims, confidence, scores, counts,
percentages, nullable metrics, and search signatures. The page and components
may pass those helpers into child components, but should not redefine local
copies.
The ranked-result panel should also render a compact package-level `Search
answer` section before detailed readiness, facets, matrices, and hit cards.
This section must derive from the backend retrieval package and show the
operator-visible status, readiness score, remediation summary, top evidence
source, required-support coverage, warnings, and backend action count. It should
state that the summary supports workflow evidence review and is not clinical
advice. Its copy action should export a `retrieval_search_answer` JSON report
including backend `interpretation` so operators can share the plain-language
result without copying raw trace state. That report should also include bounded
`medical_search_hints` with route details for FHIR, LOINC, UCUM, and external
medical search targets plus the source-diversity report when present.
`Search answer` should stay outside the page shell:
`frontend/src/features/retrieval/components/search-answer-card.tsx` owns only
the card shell and section composition. `use-search-answer-card-state.ts` owns
view-model invocation, copyable-report serialization, and copy-feedback state.
`search-answer-header.tsx`
owns the title/status/readiness/hit-count/copy action row. `search-answer-metrics.tsx`
owns answer metric rows, `search-answer-warning-panel.tsx` owns bounded warning
display, and `search-answer-format.ts` owns small answer display formatting.
`frontend/src/features/retrieval/model/search-answer.ts` is only the public
model export surface. `search-answer-view-model.ts` owns deterministic summary
assembly and metric rows. `search-answer-status.ts` owns status and remediation
fallback policy. `search-answer-report.ts` owns only the copyable
`retrieval_search_answer` JSON report assembly. `search-answer-interpretation.ts`
owns fallback interpretation when the backend does not provide one, and
`search-answer-hints.ts` owns bounded medical search hint extraction.
`search-answer-warnings.ts` owns warning extraction. The page shell should only
compose `SearchAnswerCard` into the ranked-result panel.
Evidence-pack bucket rendering should stay outside the page shell:
`frontend/src/features/retrieval/components/evidence-pack-buckets.tsx` owns the
bucket cards, required-gap badge, source chips, and warning chips. The page
passes backend `evidence_buckets[]` without deriving additional bucket policy.
Immediately after `Search answer`, the ranked-result panel should render a
guided `Review path` section. It should be a plain-language checklist derived
from backend `quality_summary`, `interpretation`, `recommended_actions[]`,
`evidence_buckets[]`, package warnings, candidate counts, and the top ranked
hit. The section must tell non-expert operators whether the package is ready,
needs review, or is blocked, then show the next operator action without making
new clinical claims. It must use the same package data as downstream panels so
there is no browser-only decision model hidden from audit.
The implementation should keep this concern outside the page shell:
`frontend/src/features/retrieval/components/retrieval-review-path.tsx` owns
the panel composition and help copy, while the check grid and next-action card
stay in `retrieval-review-path-check-list.tsx`,
`retrieval-review-path-check-card.tsx`, and
`retrieval-review-path-action-card.tsx`. Shared review-path display formatting
belongs in `retrieval-review-path-format.ts`; the panel shell should not carry
icon maps, count formatting, or card-level status styling. The model barrel
`frontend/src/features/retrieval/model/retrieval-review-path.ts` is only the
public review-path export surface. `retrieval-review-path-builder.ts` owns path
assembly, `retrieval-review-checklist.ts` owns deterministic checklist policy,
`retrieval-review-guidance.ts` owns ready/review/blocked operator guidance,
`retrieval-review-warnings.ts` owns warning extraction/count labels, and
`retrieval-review-actions.ts` owns primary-action selection. The page shell
should only compose `RetrievalReviewPathPanel` into the result column.
Immediately after `Review path`, the ranked-result panel should render an
`Evidence interpretation` section that translates the same package into
operational review language: why the top result matched, required bucket
coverage, warnings, and the next backend-recommended action. This panel must be
derived from `hits[]`, `evidence_buckets[]`, `recommended_actions[]`,
`coverage`, and `trace` data. It must not hardcode medical conclusions or
clinical advice; it explains retrieval support quality for the operator before
they inspect individual evidence cards.
Like the other top result summaries, the implementation should stay outside the
page shell: `frontend/src/features/retrieval/components/evidence-interpretation-panel.tsx`
owns the section shell, status badges, help tooltip, and card grid composition.
`evidence-interpretation-card.tsx` owns repeated interpretation-card rendering.
`frontend/src/features/retrieval/model/evidence-interpretation.ts`
is only the public model export surface. `evidence-interpretation-view-model.ts`
owns package-level status, summary, support-status, and card-context assembly.
`evidence-interpretation-cards.ts` is the deterministic interpretation card
orchestrator. `evidence-interpretation-top-match-card.ts`,
`evidence-interpretation-coverage-card.ts`, and
`evidence-interpretation-next-action-card.ts` own top-match, required-bucket
coverage, and next-action card policy from backend interpretation and fallback
signals.
`evidence-interpretation-status.ts` owns support badge and fallback status/summary
policy. `evidence-interpretation-values.ts` owns backend value coercion, warning
extraction, primary-action selection, and count formatting.
When the backend action is `broaden_query`, the ranked-result panel should
expose explicit broadening controls using the same submitted-search filter
handlers as Query Health: clear exact source scope when active, or clear all
metadata filters and rerun retrieval. The UI should show whether the action was
derived from a package `quality_signal` or a `query_diagnostic` so users can
distinguish retrieval-readiness failures from query-health warnings.
The retrieval cockpit must also render backend `strategy_recommendations[]`.
When a recommendation provides a supported `suggested_filters` entry, the UI
may expose an Apply action through the same typed filter path used by facets,
coverage gaps, and corrective actions. Unsupported recommendation filters must
remain display-only.
The trace and recent-run list must show the backend
`handoff_context.search_signature` in compact form, and copied run-comparison
reports must include active/baseline server search signatures for offline audit
correlation.
The “Search settings changed” warning must compare the current query-builder
payload against the last submitted payload, not against the backend
`search_signature`. Server signatures include backend/rule-pack context for
audit correlation and can differ from the browser form signature immediately
after a valid search.
The trace panel must render `quality_signals` as a compact retrieval-quality
checklist with severity, message, suggested action, and evidence references so
operators can review package readiness without opening raw JSON. Known metadata
payloads such as missing concepts, provenance issues, missing standards/aspects,
and suggested filters must render as explicit signal details.
Trace sections must also explain their operational meaning: quality signals
explain readiness, coverage diagnostics explain missing standards/aspects,
query rewrites are backend-generated variants, diagnostics explain parser and
expansion issues, and safety flags mark untrusted or sensitive query context.
It must also show `handoff_context.quality_policy` so the readiness score can
be traced to the active data-driven gate policy, including top-hit match
thresholds and provenance requirement scope.
The top retrieval summary strip should also surface `quality_summary` as a
readiness score, so operators can tell whether the active package is ready,
needs review, or is blocked before reading detailed traces.
The ranked-result panel must start with a compact retrieval cockpit before the
long evidence list. The cockpit summarizes the active query profile, retrieval
route, hybrid stack, reranker state, candidate/hit counts, required evidence
bucket coverage, quality readiness, concept grounding, query-aspect plan, and
backend recommended next action. It must derive every value from the visible
`RetrievalPackage` and submitted search payload; the browser must not invent
hidden actions, routes, or medical standards.
The cockpit must also render a query-health checklist derived from the submitted
payload and retrieval package: query specificity, clinical context, search
scope, result coverage, readiness, and safety signals. This checklist should
tell users when a search is too short, missing schema/format/field context,
over-constrained by exact source scope or many filters, returning sparse hits,
blocked by readiness, or carrying safety warnings. The same `query_health[]`
data must be exported in the cockpit JSON report.
The cockpit must also render a top-level search-readiness checklist before
deeper metrics. It should consolidate query health, required evidence classes,
source spread/diversity, and governance action/readiness into four scan-friendly
checks. The same checklist must be exported as
`evidence_readiness.readiness_checklist` in copied `retrieval_cockpit` JSON.
Backend `query_analysis.diagnostics[]` warnings must also appear as query-health
rows, including `overconstrained_metadata_filters`, so data-driven rule-pack
diagnostics are visible before users open the detailed trace panel.
The trace query-diagnostics list should render structured diagnostic metadata
as compact chips, including query token count, active filter count,
active metadata filter names, applied standard, and suggested standards when
present.
When that over-constraint diagnostic is present, query health should expose
explicit broadening actions: clear exact source scope when active, or clear all metadata filters
and rerun search. The UI must not silently clear filters.
The cockpit must expose a copyable `retrieval_cockpit` JSON report containing
the submitted payload, search signature, query-analysis profile/aspects,
ranking stack, package `interpretation`, quality readiness, evidence buckets,
compact `evidence_hits` with per-hit `match_explanation`, recommended actions,
facets, graph context, and active retrieval rule-pack fingerprints.
The query-analysis panel should render `query_profile` when present, including
profile label, route, complexity, recommended retrieval mode, suggested
filters, and contributing rule IDs. This makes adaptive retrieval guidance
visible before it becomes a backend route switch. Supported profile-suggested
filters should use the same explicit operator apply controls as query-analysis
filter suggestions; unsupported profile fields should remain visible but not
actionable. Profile filter controls must compare against the submitted
`trace.filters_applied` payload, not the live query-builder draft, so displayed
applied state remains tied to the visible result package.
Query-analysis composition should stay outside the page shell:
`frontend/src/features/retrieval/components/query-analysis-block.tsx` owns the
query-analysis card layout, counters, and child panel ordering.
`query-analysis-block-types.ts` owns the query-analysis block view contract.
`retrieval-trace-view-model.ts` owns `queryAnalysisBlockView`, while
`retrieval-filter-active.ts` owns submitted-filter applied-state derivation. The
page owns supported-field policy and callback wiring.
Query profile rendering should stay outside the page shell:
`frontend/src/features/retrieval/components/query-profile-card.tsx` owns the
profile card layout and composes profile subviews. `query-profile-card-types.ts`
owns the card/filter-entry view contracts. `query-profile-filter-actions.tsx`
owns unsupported-field messaging and explicit apply buttons.
`query-profile-rule-list.tsx` owns rule ID rendering.
`retrieval-filter-suggestions.ts` owns query-profile suggestion extraction and
`queryProfileFilterEntries` orchestration. `retrieval-filter-entry-suggestions.ts`
owns suggested-filter entry display shaping and applied-filter matching.
`retrieval-filter-active.ts` owns submitted-filter applied-state derivation; the
page owns the apply callback.
The same query-analysis panel should render `query_aspects` as a compact search
aspect plan, including aspect label, review question, rationale, priority,
suggested terms, suggested filters, and contributing rule ID. These aspects are
operator-visible decomposition guidance and must not silently run hidden
subqueries or mutate filters. Supported aspect-suggested filters should use the
same explicit apply path and submitted-filter applied-state checks as profile
and query-analysis filter suggestions.
Query aspect rendering should stay outside the page shell:
`frontend/src/features/retrieval/components/query-aspect-plan.tsx` owns only the
aspect-plan shell, empty state, header, and card list.
`query-aspect-plan-card.tsx` owns aspect card layout, suggested-term chips, and
rule display. `query-aspect-filter-controls.tsx` owns only the filter-control
row wrapper and compatibility exports. `query-aspect-filter-badges.tsx` owns
passive filter badges, and `query-aspect-filter-action.tsx` owns
unsupported-field messaging and explicit apply buttons.
`query-aspect-plan-types.ts` owns shared presentation contracts.
`retrieval-filter-suggestions.ts` owns `queryAspectFilterEntries` orchestration,
`retrieval-filter-entry-suggestions.ts` owns suggested-filter entry display
shaping and applied-filter matching, `retrieval-filter-active.ts` owns
submitted-filter applied-state derivation, and `retrieval-filter-format.ts` owns
supported-field coercion; the page owns supported-field policy and the apply
callback.
Concept candidate rendering should stay outside the page shell:
`frontend/src/features/retrieval/components/concept-candidate-list.tsx` owns the
candidate card layout, clinical-domain chip, confidence chip, and matched-alias
chips. The retrieval query-analysis model owns concept candidate normalization
from backend contracts; the page owns only callback wiring and display
composition.
Query diagnostic rendering should stay outside the page shell:
`frontend/src/features/retrieval/components/query-diagnostic-list.tsx` owns the
diagnostic section shell and empty-state copy. `query-diagnostic-row.tsx` owns
per-diagnostic card rendering and severity badge policy.
`query-diagnostic-metadata.ts` owns display metadata chip shaping, and
`query-diagnostic-types.ts` owns the shared diagnostic presentation contract.
Retrieval query-analysis value helpers and cockpit-signal models own backend
diagnostic normalization and query-health derivation.
Query-analysis filter suggestions
should be actionable from the trace view only through explicit operator apply
controls; the UI must not silently apply suggested filters before users can see
the reason, confidence, and existing applied state. Result facets should also be
Filter suggestion rendering should stay outside the page shell:
`frontend/src/features/retrieval/components/filter-suggestion-list.tsx` owns
suggestion chips, confidence display, applied state, and the visible Apply
button. `retrieval-filter-format.ts` owns supported-field coercion, and
`retrieval-filter-suggestions.ts` owns applied state;
`use-retrieval-search-actions.ts` owns the apply callback, so unsupported fields
remain data-driven and explicit.
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
Coverage diagnostics rendering should stay outside the page shell:
`frontend/src/features/retrieval/components/coverage-diagnostics-panel.tsx`
owns coverage diagnostics section composition and keeps the public export stable.
`coverage-diagnostics-types.ts` owns the filter/action contracts.
`coverage-diagnostics-header.tsx` owns the heading, warning badge, and help copy.
`coverage-diagnostics-empty-state.tsx` owns the no-gap fallback.
`coverage-diagnostics-item-list.tsx` owns standard/aspect list mapping, and
`coverage-diagnostics-item-row.tsx` owns each missing-coverage row and apply
button. The retrieval page owns the supported-filter checks, suggested action
derivation, field labels, and value formatting so backend-driven remediation
policy stays explicit.
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
schema/format/resource/domain/standard/source/trust/field filters. The row must
show `quality_summary.top_action` and the backend corrective-action count/top
action when present so operators see the next readiness action without opening
raw JSON.
The retrieval query builder must expose exact source ID scoping from
`/retrieval/sources` and submit it through the typed `filters.source_id`
contract. Active filter chips, submitted-search restoration, run history, and
search signatures must preserve that exact source scope rather than filtering
only visible cards on the client.
Comparison output should include a copyable JSON report with the active payload,
baseline payload, summaries, deltas, metrics, evidence changes, and rank
movement so tuning notes can be reproduced outside the browser. Search-run
summaries and copied comparison reports should include the active query-profile
route/mode context so relevance tuning can distinguish query changes from
adaptive-routing changes. They should also include `quality_summary` status,
score, top action, blocker codes, and warning codes for active and baseline
runs, plus a quality-score delta. Copied comparison reports should include a
top-level summary with stable/changed status, top diagnosis, quality before/after
state, evidence churn counts, retrieval deltas, changed dimensions, and judgment
count so review notes can be scanned before the detailed sections. The summary
should also include top-source before/after stability. They should
also include `recommended_actions[]` derived from quality top action, coverage
diagnostics, profile/rule-pack changes, quality-signal changes, evidence churn,
and missing judgments so copied reports lead directly to review decisions. Each
recommended action should include priority, severity, source, action, and reason
and must be sorted by priority before rendering or copying. Reports and UI
headers should also expose an action summary with action count, highest
priority, highest severity, source count, and sources so reviewers can scan
urgency without reading every action. The UI should render the source list as
compact chips with per-source action counts above the detailed action rows. The
comparison panel should first render an at-a-glance row for readiness status
movement with score delta, highest action priority, evidence overlap, result
churn, top-source stability, and source-spread delta. It should then render a compact
operator summary with a plain-language headline, scan-friendly bullets, and
review-focus chips before the detailed comparison sections. It should then render a compact
comparison diagnosis that names the likely change drivers before the detailed
sections, then render the same recommended actions as a visible review checklist
before metrics and detailed deltas. The copyable JSON report should include the
same `operator_summary`, diagnosis, and actions for offline tuning notes.
Run-comparison summary rendering should stay outside the page shell:
`frontend/src/features/retrieval/components/run-comparison-summary-panels.tsx`
is only a compatibility barrel. `run-comparison-summary-metrics.tsx` is only the
summary metrics export surface. `run-comparison-at-a-glance.tsx` owns the
at-a-glance row, `run-comparison-metrics.tsx` owns detailed comparison metrics,
and `run-comparison-delta-metric.tsx` owns signed delta metric rows.
`run-comparison-summary-narrative.tsx` is only the compatibility export surface
for narrative cards. `run-comparison-operator-summary.tsx` owns operator-summary
rendering, `run-comparison-diagnosis.tsx` owns comparison-diagnosis rendering,
and `run-comparison-recommended-actions.tsx` owns recommended-action checklist
rendering. `run-comparison-metric-card.tsx` owns the reusable comparison metric
card, and `run-comparison-summary-types.ts` owns shared view contracts.
`use-retrieval-page-workspace.ts` owns retrieval session composition only:
form, run, judgment, plan, workspace search-action adapter, and derived-view
hook composition.
`use-retrieval-page-workspace-types.ts` owns the workspace argument and search
mutation contracts, so API-facing mutation shape does not live inline in the
composition hook. `use-retrieval-workspace-search-submit.ts` owns the mutation
submit adapter that clears form/plan notices before backend search execution.
`use-retrieval-workspace-search-actions.ts` owns workspace-specific search-action
policy adaptation, including supported-filter policy injection into the generic
search-action hook.
`use-retrieval-workspace-clear-actions.ts` owns coordinated clearing across run
history and relevance judgments. `use-retrieval-workspace-view.ts` owns
memoized trace-panel view derivation from the active retrieval package.
Comparison selection and baseline/active run state stay in
`use-retrieval-run-session.ts`. Comparison policy rules should stay in
`retrieval-comparison-diagnosis-*-rules.ts` plus the diagnosis orchestrator,
recommended-action policy in `retrieval-comparison-recommended-action-policy.ts`,
recommended-action rollups in
`retrieval-comparison-recommended-action-summary.ts`, and copied-report content
in `retrieval-comparison-report.ts`.
Run-comparison detail rendering should also stay outside the page shell:
`frontend/src/features/retrieval/components/run-comparison-detail-panels.tsx`
is only a compatibility barrel. `run-comparison-query-detail-panels.tsx` is
only the query-detail export surface. `run-comparison-query-profile.tsx` owns
query-profile detail cards, `run-comparison-concept-grounding.tsx` owns concept
grounding change cards, and `run-comparison-query-aspects.tsx` owns query-aspect
detail cards.
`run-comparison-quality-detail-panels.tsx` is only the quality-detail export
surface. `run-comparison-coverage-panel.tsx` owns the coverage diagnostics
shell, `run-comparison-coverage-status-list.tsx` owns improved/regressed status
changes, `run-comparison-coverage-summary-list.tsx` owns added/removed/retained
summary chips, and `run-comparison-coverage-key.ts` owns stable coverage row
keys.
`run-comparison-quality-signals-panel.tsx` owns quality signal changes.
`run-comparison-facet-coverage-panel.tsx` owns facet coverage deltas.
`run-comparison-rank-rule-panels.tsx` is only the rank/rule export surface.
`run-comparison-rank-changes.tsx` owns rank-movement detail cards,
`run-comparison-evidence-change.tsx` owns evidence-ID change chips, and
`run-comparison-rule-packs.tsx` owns rule-pack change detail cards. Shared view
contracts live in `run-comparison-detail-types.ts`. The retrieval page owns the
comparison models and passes formatting helpers where the presentation needs
human-readable count labels. Deterministic comparison labels and delta badges
belong in `search-run-quality.ts`. The comparison panel should render the
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
It should compare source-diversity policy and outcome across active and
baseline packages, including selected-source coverage, duplicate selected-source
delta, overlap, and source IDs added/removed/retained. Recommended actions
should flag duplicate-source regressions and policy changes so reviewers know
whether a tuning run is still evidence-diverse enough for healthcare workflows.
The comparison panel must also explain how to read the comparison before showing
long deltas: baseline is the older selected run, active is the currently
displayed package, warning deltas and quality changes are tuning signals, and
rank movement is not clinical evidence. Overlap, churn, shared-evidence, and
mean-rank-delta metrics must include operator-facing interpretation so users can
distinguish broad result replacement from rank-order instability.
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
Judgment controls and metric summaries must explain that labels are for the
submitted query-document pair, that coverage is the share of hits judged, and
that Precision@k/nDCG@k are only meaningful after enough explicit judgments.
The persisted judgment evaluation panel must render `evaluation_readiness`
before server metrics so operators can see whether the current label set is
unlabeled, low confidence, usable with gaps, or ready for tuning.
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
The source inventory panel must also show source readiness before filters and
source rows: visible/total source count, indexed chunk count, domain coverage,
standard coverage, source-type coverage, empty-source warnings, and whether the
inventory is filtered. This prevents operators from confusing a filtered source
view with corpus-wide evidence coverage, and makes reindexing problems visible
before a source-scoped search is run.
Medical search hints in the trace should be copyable and launchable when the
backend provides a vetted URL, so PubMed, ClinicalTrials.gov, and openFDA
workflows remain backend-owned and data-driven instead of hardcoded in React.
Medical search hint rendering should stay outside the page shell:
`frontend/src/features/retrieval/components/search-hint-list.tsx` owns the
list shell and copy feedback state; `search-hint-card.tsx` owns per-hint
copy/open actions and warnings; `search-hint-metadata-details.tsx` owns only
the route-detail disclosure wrapper; `search-hint-metadata-summary.tsx` owns
summary badges; `search-hint-metadata-section-list.tsx` owns section ordering.
`search-hint-endpoint-scope-section.tsx`,
`search-hint-selected-candidates-section.tsx`,
`search-hint-parameter-examples-section.tsx`,
`search-hint-capability-warning.tsx`, and
`search-hint-lineage-followup-section.tsx` own endpoint, candidate, parameter,
warning, and lineage section presentation; and
`search-hint-metadata.ts` owns route metadata view construction for endpoint
scope, parameter examples, selected terminology or unit candidates, capability
warnings, and lineage follow-up. `search-hint-metadata-values.ts` owns
deterministic metadata value coercion for arrays, optional strings, parameter
examples, and lineage follow-up.
The retrieval page composes current package/plan state from the run-session and
plan-session hooks; preview and hint components pass that state into
query-analysis and report-model helpers.
The assistant route is the operator shortcut over those same backend contracts.
`frontend/src/features/assistant/assistant-page.tsx` is the route composition
root. It owns server-state query/mutation wiring, active form state, stream
abort wiring, and page layout only. Session state helpers live in
`assistant-session.ts`; attachment/context parsing and clipboard/file
validation live in `assistant-attachments.ts`; reusable display formatting lives
in `assistant-format.ts`; the chat-session rail lives in
`assistant-session-sidebar.tsx`; attachment and advanced-context controls live
in `assistant-input-panels.tsx`; the starter-task empty state lives in
`assistant-empty-state.tsx`; the compact assistant guide lives in
`assistant-inline-guide.tsx`; the backend tool allowlist disclosure lives in
`assistant-tool-catalog-panel.tsx`; chronological stream rendering lives in
`assistant-live-timeline.tsx`; planner-stream parsing, planner argument
summaries, planning-start copy, and completed-tool lookup live in
`assistant-live-timeline-model.ts`; final assistant response rendering lives in
`assistant-response-details.tsx`; and response/tool-output interpretation,
badge policy, evidence extraction, standards-plan coercion, search-hint
coercion, and source-diversity coercion live in `assistant-response-model.ts`.
New assistant behavior should be added to the smallest matching module first,
not directly to the route file.
The chat UI should call `/assistant/chat/stream` through the server-state
boundary, render planning and tool-call events as they arrive, and stream OpenAI
answer deltas into the current assistant bubble instead of waiting for a single
final response. It must still support the non-streaming `/assistant/chat`
contract for API clients, but the product UI should prefer the stream path.
The page should expose ChatGPT-style chat sessions so users can separate
investigations, switch between prior transcripts, and start a clean thread
without losing the current composer context. Sessions and messages are
backend-owned through `/assistant/sessions`; the browser may keep optimistic
drafts while a stream is running, but persisted history must come from the API
instead of browser storage or hidden mock data. The browser should create new
threads as `New chat` and let the backend generate the durable title from the
first user message, so PHI-safe title rules stay centralized.
The Assistant composer is the default intake surface for end users: it must
support starter prompts, typed commands, clipboard image paste, file attachment,
and drag-and-drop file selection. The browser only validates configured upload
limits and sends the file through the existing extraction hooks; parsing,
OCR/vision fallback, artifact persistence, and assistant context generation
stay behind the API boundary.
The assistant workspace should keep desktop scrolling contained: session list,
message timeline, and composer live inside a contained app-viewport chat
surface so the LLM stream and tool timeline stay visible instead of fighting
the surrounding page scroll. The message timeline should auto-follow the active
stream inside that panel rather than moving the whole browser page.
The stream request must be abortable from the composer, preserving any partial
transcript and showing a cancellation state rather than leaving a stuck spinner.
Long LLM planning must not look frozen: the UI should render backend
`planning_step` events and streamed `planning_delta` planner text before
`plan_ready`, so users can see what the model is doing before tools execute.
If the configured planner cannot stream, the UI should still render fallback
`planning_progress` heartbeat events between `planning_started` and
`plan_ready`, including elapsed seconds, so users can tell the assistant is
still waiting for a tool plan.
Assistant stream UI must render events chronologically in one timeline:
connection, planning, planner text, validated plan, tool calls, answer
synthesis, streamed LLM text, warnings, and errors. It must not place the LLM
answer in a separate section above a long tool panel, because users lose sight
of streamed model output while tools expand below it. Tool rows should stay
compact by default and expose detailed arguments/results only inside expandable
sections.
Backend `tool_progress` events should render inline between `tool_started` and
`tool_completed`, with labels and progress percentages coming from the
data-driven Assistant progress policy catalog rather than browser hardcoding.
This gives long validation, retrieval, OCR-adjacent extraction, workflow, and
review operations observable intermediate state without inventing a separate
tool console.
The timeline should also render the validated `plan_ready` payload before
tool execution: plan mode, selected tool sequence, rationale, and bounded
argument JSON. The UI must not imply that partial planning text is executable;
backend tools run only after the structured plan validates.
If the backend emits an `error` stream event, the UI should render it in the
live tool timeline and stop waiting for a final response.
The transcript renders model/tool mode, answer synthesis mode, write-gate
state, executed tool calls, and compact evidence/output previews.
Assistant evidence summary cards must render compact retrieval
`match_explanation` fields when present: support status, top score driver,
evidence buckets, concept/aspect labels, provenance count, and ranking-signal
count. This keeps chat evidence explainable without requiring users to open raw
tool output.
Assistant retrieval tool cards should also surface source-diversity summaries
from the first-class `diversity` field, falling back to
`handoff_context.diversity` for older responses. Chat users should see selected
versus candidate source counts, duplicate selected-source count, and compact
selected-hit reasons without opening raw JSON.
Assistant and Retrieval standards-plan cards should also show compact
backend-provided match reasons such as matched dataset fields, query aspects,
standards, concepts, and quality signals. The UI must read those reasons from
tool/package metadata instead of re-deriving healthcare logic in React.
Retrieval medical-search hint cards should render backend metadata as structured
route details: parameter examples, endpoint scope, selected terminology terms,
selected unit candidates, lineage follow-up, and capability warnings. This
keeps LOINC, UCUM, FHIR, and external-search guidance understandable without
requiring users to inspect raw JSON.
Assistant tool cards should surface the same medical-search hints compactly
when retrieval tools return `query_analysis.search_hints`, so chat users can
see launchable or copyable follow-up routes without leaving the conversation.
When a hint includes a backend-provided `url`, the Assistant card should expose
an external Open action with standard `noopener noreferrer` safeguards.
All hint cards should also expose Copy for the generated query syntax, including
syntax-only hints that require a configured terminology or literature system.
Its primary form should be understandable to an end user: show outcome-oriented
starter tasks from `/assistant/examples`, ask what operation the user wants
done, and reserve JSON for optional data/filter context. Starter task data must
come from `knowledge/assistant/examples.json`; the form should not preload
hidden sample data.
The assistant composer should also accept one attached file or pasted
clipboard image. Attachments are extracted through `/parse/extract` before the
chat stream starts, and the extracted text plus filename, source format,
extractor, size/count metadata, and warnings are inserted into assistant
context. The UI should show the attached source as a removable chip and render
the parsed source summary in the transcript so users know which file/image was
used.
For image/scanned-document uploads, the transcript must preserve extractor
warnings so operators can see whether base MarkItDown conversion, MarkItDown
OCR plugin support, or direct OpenAI vision fallback produced the usable text.
It should also show the server allowlisted assistant/MCP tools from
`/assistant/tools` before a command is run, so users can see what the assistant
can do without reading backend docs or waiting for a transcript.
Unsupported chat should display the backend no-action warning instead of
looking like a successful retrieval or workflow operation.
When OpenAI mode is enabled, the transcript should make clear that the model
planned tool use and streamed the final answer after backend execution; raw
tool output remains secondary audit detail.
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
Retrieval source-diversity controls should explain the lambda tradeoff directly
in the form: lower values favor source novelty, higher values favor raw
relevance, and the default should keep relevance primary while reducing
repeated-source evidence. The lambda input should remain visible but disabled
when source diversity is disabled so the inactive setting is still inspectable.
Retrieval runtime controls should show the active retrieval rule-pack inventory
from `/runtime/config`, including sanitized pack name, status, rule count,
version, short content hash, default-vs-override source, and controlling
environment variable. The UI must not expose local filesystem paths for those
packs.
The readiness panel should render the `retrieval_rule_packs` check as a nested
pack list, not only generic detail chips, so missing or malformed query
expansion, diagnostic, ranking, corrective-action, evidence-bucket, evaluation,
or search-hint rules and their fingerprints are visible to operators before
they run searches.

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
