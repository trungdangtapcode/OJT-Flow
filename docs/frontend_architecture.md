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
When a completed search returns zero ranked hits, the result panel must render
operator remediation instead of a generic empty state: candidate count, active
submitted filters, missing required evidence buckets, source-inventory guidance,
direct controls to clear exact source scope or all active metadata filters, and
any supported backend corrective filter.
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
Result cards must render a compact evidence support summary above the detailed
sections, using data-derived counts for matched terms, provenance fields,
grounded concepts, supported aspects, and ranking signals.
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
Result cards must render a compact evidence provenance summary with source
version and key locator fields such as standard, URL, path, PMID, DOI, API,
resource, table, document, and chunk identifiers before the raw JSON details.
URL/API values, PubMed IDs, and DOIs must render as external links when they can
be safely normalized.
Each ranked evidence card must also offer a copyable `retrieval_evidence_hit`
report containing evidence identity, support-summary counts, `match_explanation`,
ranking scores/components, concept/aspect grounding, provenance summary,
locators, and snippet context.
Copy actions for evidence, comparison, evaluation, and search-hint reports must
show transient success feedback so operators can tell the clipboard action
completed without opening developer tools or raw browser state. Report copy
buttons should identify that they export JSON and explain the report's intended
offline use, such as cockpit audit context, single-hit evidence support,
run-comparison tuning, or judgment-evaluation metrics.
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
The ranked-result panel should also render a compact package-level `Search
answer` section before detailed readiness, facets, matrices, and hit cards.
This section must derive from the backend retrieval package and show the
operator-visible status, readiness score, remediation summary, top evidence
source, required-support coverage, warnings, and backend action count. It should
state that the summary supports workflow evidence review and is not clinical
advice. Its copy action should export a `retrieval_search_answer` JSON report
including backend `interpretation` so operators can share the plain-language
result without copying raw trace state.
Immediately after `Search answer`, the ranked-result panel should render an
`Evidence interpretation` section that translates the same package into
operational review language: why the top result matched, required bucket
coverage, warnings, and the next backend-recommended action. This panel must be
derived from `hits[]`, `evidence_buckets[]`, `recommended_actions[]`,
`coverage`, and `trace` data. It must not hardcode medical conclusions or
clinical advice; it explains retrieval support quality for the operator before
they inspect individual evidence cards.
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
churn, and top-source stability. It should then render a compact
comparison diagnosis that names the likely change drivers before the detailed
sections, then render the same recommended actions as a visible review checklist
before metrics and detailed deltas. The copyable JSON report should include the
same diagnosis and actions for offline tuning notes. The comparison panel should render the
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
The assistant route is the operator shortcut over those same backend contracts.
The chat UI should call `/assistant/chat/stream` through the server-state
boundary, render planning and tool-call events as they arrive, and stream OpenAI
answer deltas into the current assistant bubble instead of waiting for a single
final response. It must still support the non-streaming `/assistant/chat`
contract for API clients, but the product UI should prefer the stream path.
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
