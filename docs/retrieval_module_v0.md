# Retrieval Module v0

OJTFlow retrieval v0 turns the old static evidence fixture into a replaceable,
healthcare-aware retrieval subsystem. It supports the workflow explanation and
review path; it does not generate clinical advice.

## Architecture

The application layer depends on a `RetrievalRepository` port. Workflow code
builds a `RetrievalQuery` from the user instruction, parsed field profile,
schema ID, and detected format, then stores returned evidence in
`WorkflowState.retrieved_context`.

Production Docker uses Postgres with:

- `ojtflow.knowledge_documents`
- `ojtflow.knowledge_chunks`
- generated `tsvector` search
- optional pgvector `vector(384)` and HNSW index when the extension is available
- JSON embeddings as a portable fallback

Memory and SQLite modes use the static retrieval repository so tests and local
demos do not require database state. The static adapter still accepts configured
embedding providers for parity with Postgres mode.

`OJT_RETRIEVAL_FRAMEWORK=custom` is the default and uses the native Postgres or
static adapters above. `OJT_RETRIEVAL_FRAMEWORK=llamaindex` opts into the
framework adapter behind the same `RetrievalRepository` port. That adapter uses
LlamaIndex `Document`/`Node` objects, `SentenceSplitter`, `VectorStoreIndex`,
and `QueryFusionRetriever`; when `llama-index-retrievers-bm25` is installed, it
adds BM25 to vector retrieval with reciprocal-rank fusion. The API response
contract remains `RetrievalPackage`, so workflow state, UI rendering, assistant
tools, and audit/explanation paths do not depend on LlamaIndex types.
Framework retrieval also populates package readiness metadata and per-hit
aspect/concept locator signals through the same OJTFlow retrieval contracts.
It emits the same `standard_search_plan` contract as the native retrieval
engine, so UI, assistant, and future MCP tool behavior do not diverge by
retrieval framework.
The LlamaIndex adapter builds a reusable in-process index for the current
trusted chunk generation and invalidates it on `reindex()`. Retrieval still
applies OJTFlow metadata filters before returning evidence. For framework
retrieval, those filters are also passed into LlamaIndex vector/BM25 retrievers
before ranking so healthcare metadata constraints such as `standard_system`,
`clinical_domain`, `source_type`, exact `source_id`, and `trust_level` shape
the candidate pool instead of being only a post-hoc UI filter. The trace reports
`handoff_context.framework_components` with full node count, filtered node
count, metadata filter count, candidate pool size, BM25 availability, and index
generation.
Candidate-pool sizing and fusion weights are configuration-backed through
`OJT_RETRIEVAL_CANDIDATE_MULTIPLIER`, `OJT_RETRIEVAL_MIN_CANDIDATES`,
`OJT_RETRIEVAL_VECTOR_WEIGHT`, and `OJT_RETRIEVAL_BM25_WEIGHT`. They can be
changed from the Settings page or `PUT /api/v1/runtime/retrieval-settings`,
which validates the effective settings, writes `OJT_RUNTIME_SETTINGS_PATH`
atomically, clears cached settings/services, and reloads the retrieval adapter.

## Ranking

The retrieval pipeline is auditable in v0:

1. Analyze the query and build variants from instruction, fields, schema,
   format, resource type, and deterministic clinical-standard expansion rules.
2. Candidate chunks are filtered by trust level, clinical domain, standard system,
   source type, or exact source ID.
3. Postgres mode retrieves separate lexical and vector candidate pools before
   fusion so exact-term evidence and semantic-neighbor evidence cannot starve
   each other inside a single bounded SQL result set.
4. LlamaIndex mode applies equivalent metadata filters to framework retrievers
   before fusion, then keeps a post-filter safety check before evidence is
   emitted.
5. Lexical score uses token overlap and Postgres full-text search in Postgres mode.
6. Vector score uses the configured embedding provider:
   deterministic hash embeddings for offline tests, OpenAI semantic embeddings
   for CPU-safe production-like retrieval, or Hugging Face/SentenceTransformers
   embeddings for local GPU retrieval.
7. Reciprocal Rank Fusion combines lexical and vector rankings.
8. Data-driven ranking boost rules favor schema matches, field matches,
   approved sources, and relevant healthcare standards.
9. Each ranked hit gets a deterministic extractive snippet: the most
   query-relevant sentence/window from the source chunk, with matched terms and
   normalized source offsets.
10. Final selected hits use source-aware diversity selection before packaging,
   so repeated high-scoring chunks from one source do not hide independent
   standard, policy, or terminology evidence. The trace exposes selected-hit
   rationale under the first-class `diversity.selected_hits` contract and also
   mirrors it to `handoff_context.diversity.selected_hits` for agent handoff.
11. Final selected hits are summarized into result facets by source type,
   clinical domain, standard system, and trust level.
12. Trace safety flags mark prompt-injection-like query text and sensitive field
   context without blocking retrieval.

The retrieval package now includes a `graph_context` handoff that extracts
entities and evidence triples from the retrieved claims. This is a
GraphRAG-lite context for validation/explanation workflows, not diagnosis,
treatment, triage, or medication advice.
When the backend has a graph repository configured, every retrieval package
with a graph handoff also stores an owner-scoped `GraphContextRecord`. The
package returns `handoff_context.graph_record` with the persisted graph ID,
workflow/search metadata, counts, and creation time. Operators can list these
records through `GET /api/v1/retrieval/graph/contexts` and export the graph
neighborhood as newline-delimited JSON through
`GET /api/v1/retrieval/graph/export?format=jsonl` or RDF-like triples through
`format=rdf_jsonl`. The export is operational graph/RAG metadata only; it is
not a clinical decision-support artifact.
Operators can also call `GET /api/v1/retrieval/graph/neighborhood` to expand a
bounded subgraph by text, node ID, evidence ID, source ID, normalized code,
FHIR-like resource type, data field, relation, owner, and workflow scope.
The Retrieval page exposes the same capability in the `Graph query` panel:
operators can query persisted graph neighborhoods by text, node, evidence,
source, normalized code, workflow, or relation; seed the query from the current
run's top evidence/node/source; inspect recent persisted graph records; and
review bounded node, edge, and triple results without leaving the retrieval
workspace.

GraphRAG-lite reranking is configured by
`knowledge/retrieval/graph_rag_policy.json` and included in the sanitized
retrieval rule-pack fingerprint list. After Graph-NER builds the package graph,
the backend computes a bounded `graph_support` score component for evidence that
shares query graph targets, evidence triples, or normalized-code paths. The
score is additive and auditable:

- `hits[].score_components[]` may include `component="graph_support"`.
- `hits[].source_locator.graph_rag_lite` and
  `hits[].evidence.locator.graph_rag_lite` show shared query targets, graph
  edge counts, triple counts, normalized-code targets, and score boost.
- `handoff_context.graph_rag_lite` and
  `trace.fusion_diagnostics.graph_rag_lite` show whether graph support changed
  the final hit order and which evidence had graph support.
- `support_matrix.rows[].metadata.graph_rag_lite` carries the same support data
  into answer synthesis and assistant/MCP handoff.

Graph support can promote a weak support row to partial or a partial support row
to strong only when the configured policy threshold is met. It cannot override
source trust, freshness, PHI, policy, or human-review gates.

The package also includes a guarded `answer` object. This is deterministic
retrieval synthesis, not open-ended clinical generation. It is built only from
the `support_matrix`, ranked evidence, source metadata, and Graph-NER handoff:

- `answer.status` is `supported`, `partial`, `review_required`, or `refused`.
- `answer.answer_text` summarizes only retrieved evidence claims and cites
  evidence IDs.
- `answer.claims[]` links each answer claim to evidence IDs, citation IDs, and
  graph path refs when Graph-NER produced matching evidence triples.
- `answer.claims[].graph_guard` records the claim-to-triple guard status:
  `supported`, `review_required`, or `not_required`.
- `answer.unsupported_claims[]` carries weak or unsupported support rows
  instead of allowing them into confident answer text.
- `answer.missing_evidence_gaps[]` explains why a package cannot support a
  complete answer.
- `answer.freshness_warnings[]` flags stale, deprecated, blocked,
  review-needed, unapproved, or version-mismatched sources.
- `answer.metadata.claim_triple_guard` summarizes how many clinical claims were
  graph-supported versus review-required.

If no row reaches strong or partial evidence support, the answer is refused and
the trace receives `retrieval_answer_refused_unsupported`. This keeps Assistant,
MCP, UI, and export consumers from inventing conclusions outside the retrieved
evidence package. If a strong clinical claim lacks graph-triple support, the
answer is marked review-required instead of silently presenting it as fully
supported.

The package also includes a `standard_search_plan`. This is a typed,
healthcare-standard playbook selected from
`knowledge/retrieval/standard_search_playbook_rules.json`. It tells operators
which governed search route should be run next, such as FHIR resource search
with Provenance/AuditEvent follow-up, LOINC terminology lookup, UCUM unit
validation, RxNorm medication normalization, PHI review, or literature/trial
search hints. The plan is returned as first-class API data instead of hidden UI
copy, so the assistant, retrieval console, exports, and future MCP tools can
all use the same route guidance.

The governed external medical-source scope now includes LOINC, UCUM, RxNav,
SNOMED CT placeholder/lookup boundaries, ICD-10-CM, OMOP CDM, MeSH,
PubMed/NCBI E-utilities, ClinicalTrials.gov API v2, and openFDA. These sources
are declared as adapters and trust policies first. Live fetch jobs must preserve
endpoint, query, source release or fetch timestamp, cache hash, and approval
state before fetched records become searchable.

Corpus search is partitioned by tenant-aware policy from
`knowledge/source_catalog/corpus_partitions.json`. `GET
/api/v1/retrieval/corpus/partitions` exposes the active catalog. The default
partitions are:

- `global_standards`: shared approved standards, terminology metadata, schemas,
  and curated public guidance. Visibility is global and external-provider use is
  allowed when the broader PHI/external-provider policy also allows it.
- `tenant_policies`: organization-scoped policies, implementation guides, and
  tenant data dictionaries. Visibility requires the active workspace
  `organization_id`; external-provider use is blocked by default.
- `private_documents`: user or workspace uploaded private artifacts. Visibility
  requires the active organization scope, PHI is allowed only under private
  retention policy, and external-provider use is blocked by default.

Corpus manifest items, indexed chunks, retrieval source inventory rows, and
Postgres/static/LlamaIndex retrieval filters all carry the same partition
metadata: `corpus_partition_id`, `corpus_partition_label`,
`corpus_partition_purpose`, `corpus_visibility`, `organization_id`,
`external_provider_allowed`, `phi_allowed`, and `retention_policy_id`.
Authenticated retrieval routes add the caller's active workspace organization to
search filters and overwrite any caller-supplied `organization_id`. Global
chunks remain visible to every workspace; tenant and private chunks are returned
only for matching organization scope. Operators can narrow search explicitly
with `filters.corpus_partition` and `filters.corpus_visibility`. The Retrieval
source inventory surfaces these fields as badges and filter chips so users can
see whether a result came from global standards, tenant policy, or private
documents before using it.

Private corpus ingestion is available through `POST
/api/v1/retrieval/private-corpus/ingest`. It accepts inline text or the latest
extracted trace for an uploaded artifact. The ingestion path is deliberately
PHI-safe:

- redaction preview runs before indexing;
- only redacted text is written into retrieval chunks;
- chunks are stamped into `private_documents` with the active workspace
  organization ID;
- `external_provider_allowed=false` is stored on every source/chunk;
- uploaded artifact retention policy is preserved, while inline text receives a
  private-corpus retention policy requiring review;
- source inventory and search filters hide private chunks outside the matching
  organization scope.

This is private retrieval grounding, not external semantic enrichment. If an
embedding provider is external, the indexed text is already redacted and the
source metadata still tells downstream tools not to send private corpus content
to external providers.

External medical search transparency is exposed on each `RetrievalPackage` as
`external_query_transparency`. These records are generated for PubMed,
ClinicalTrials.gov, and openFDA search hints. They show the exact external query
or URL that would be used, parsed request parameters, retrieval filters, result
IDs when a future connector supplies them, cache key metadata, cache state,
source release placeholder, rate-limit/auth policy, and execution status.

The current backend does not execute those external searches automatically.
Records use `cache_state=not_executed` and either `execution_status=not_executed`
or `blocked_by_route_budget` depending on the selected route budget. This keeps
operators from seeing a black-box "external RAG" claim: every possible external
handoff is visible, reproducible, and policy-gated before source ingestion.

Source freshness is now a first-class readiness gate. `GET
/api/v1/retrieval/freshness` compares the governed corpus adapter catalog,
source trust policy catalog, generated local corpus manifest, and active source
inventory. Each source receives a deterministic status:

- `ready`: approved, policy-covered, indexed when expected, and within its
  freshness window.
- `watch`: usable but operationally weak, such as configured-but-unindexed
  local snapshots, missing governed external snapshots, or stale local files.
- `needs_review`: source lifecycle, reviewer state, or trust policy coverage
  blocks production confidence.
- `blocked`: disabled, blocked, or failed sources should not be used for
  retrieval evidence.

The Retrieval page renders the same report as the `Source freshness gate`
panel. Operators can use it before tuning RAG or judging answers, because a
high-ranking chunk from stale or unreviewed medical evidence is still unsafe to
treat as trusted grounding.

Ranked packages now also carry package-time source governance. Every selected
hit is matched against `knowledge/source_catalog/source_trust_policies.json`
and `knowledge/source_catalog/corpus_adapters.json` by source ID, canonical
source ID, adapter policy mapping, or standard/domain. The resulting
`source_governance` payload is copied into:

- `hits[].source_locator.source_governance`
- `hits[].evidence.locator.source_governance`
- `hits[].match_explanation.source_governance`
- `handoff_context.source_governance`

The same decisions emit `source_governance_ok`,
`source_governance_review_required`, or `source_governance_blocked` quality
signals. This keeps corrective RAG honest: a highly ranked chunk can still be
review-gated when its source policy requires reviewer approval, its adapter is
candidate/deprecated, or its governed healthcare source has no trust policy.

Playbook rules are data-driven and can trigger from query profile, detected
standards, detected concepts, decomposed query-aspect IDs, uploaded dataset
field names, query tokens, FHIR resource type, quality signals, safety flags,
or required metadata filters. This lets a CSV field such as `unit` select a
UCUM validation route even when the user never names UCUM explicitly.

## Query Transformations

Query transformations live in
`knowledge/retrieval/query_transformation_rules.json` and are included in the
sanitized `handoff_context.retrieval_rule_packs` fingerprint list. The current
registry emits deterministic `query_transformation_rule` variants for:

- `rewrite`: makes clinical standard, schema, resource, and field context
  explicit.
- `step_back_query`: asks the broader healthcare-standard requirements
  question before evidence lookup.
- `multi_query_expansion`: combines decomposed query aspects, suggested terms,
  detected concepts, and standards for high-recall search.
- `hyde`: optional deterministic HyDE-style hypothetical evidence text for
  recall experiments. This rule is disabled unless
  `OJT_RETRIEVAL_ENABLE_HYDE=true`.

The transformations are data-driven and rendered as first-class
`query_variant_details[]` rows with rule ID, strategy, priority, and reason.
They do not call an LLM and do not bypass source filters, evidence support
checks, or human review gates.

## Query Router

The selected query route lives in `query_analysis.query_route` and is copied to
`handoff_context.query_route`; the same object is also mirrored into
`trace.fusion_diagnostics.query_route` for package-level observability.
Routes are loaded from `knowledge/retrieval/query_route_rules.json` and are
included in the sanitized `handoff_context.retrieval_rule_packs` fingerprint
list.

The router selects a strategy recommendation from trusted rule data using:

- query profile ID, profile route, and retrieval mode
- detected input format and FHIR-like resource type
- active metadata filter keys and values
- query diagnostic codes and safety-sensitive concepts
- detected concepts, standards, tokens, and whether fields are present

Current route outputs include `exact_source_lookup`, `metadata_filtered`,
`hybrid_rrf`, and `high_recall_review` strategy IDs. The route object includes
the selected rule ID, route ID, strategy ID, retrieval mode, rationale,
confidence, matched criteria, suggested filters, risk controls, and an optional
`budget`. Built-in routes include budgets for max candidates, max returned
hits, reranker candidate limit, source-diversity behavior, external-network
permission, and latency target. `rank_chunks` enforces the candidate, returned
hit, reranker, and diversity parts of that budget, then writes the selected
budget and effective runtime budget to `handoff_context` and
`trace.fusion_diagnostics`. External-network permission is advisory in v0
because the local search path does not execute live external queries; if a route
does not allow external network use, external search hints remain review-only.
The router is an auditable selection contract; it does not silently switch
storage adapters or bypass the existing evidence-quality, source-filter,
review, and support-matrix checks.

## Citation Locator Normalization

Retrieval preserves raw source locator dictionaries, but ranked hits, evidence,
support-matrix rows, and answer citations can now include
`normalized_citation_locator`. The normalizer is driven by
`knowledge/retrieval/citation_locator_rules.json`, so new locator families can
be added without changing ranking code.

The normalized locator shape includes:

- `locator_kind`: for example `fhir_page`, `pubmed_record`,
  `clinicaltrials_study`, `openfda_endpoint`, `ucum_unit`, `rxnorm_concept`,
  `pdf_page`, or `internal_section`
- `display` and `canonical_url` when a canonical URL can be built safely
- source ID/type/version, standard system, identifier, path, page, section,
  raw locator keys, warnings, and rule metadata

The current rule set covers FHIR R4 resource pages, PubMed PMID records and
search context, ClinicalTrials.gov study/API context, openFDA endpoint context,
UCUM units, RxNorm concepts/source context, PDF pages, and internal policy or
knowledge sections. If required template fields are missing, the normalizer
falls through to lower-priority rules instead of inventing a misleading URL.

## Search Presets

Operator-facing retrieval examples live in
`knowledge/retrieval/search_presets.json` and are served through
`GET /api/v1/retrieval/presets`. This keeps query-builder defaults, healthcare
example searches, and metadata constraints in trusted data instead of React
source. A preset can specify `query`, `fields`, `schema_id`, `detected_format`,
`resource_type`, `clinical_domain`, `standard_system`, `trust_level`,
`source_type`, `top_k`, `category`, `target_sources`, and
`launch_hint_targets`. Query-builder controls that are not source inventory,
such as detected format labels and top-K choices, live in
`knowledge/retrieval/search_options.json` and are served through
`GET /api/v1/retrieval/search-options`. These files are read on request, so
operators can update trusted retrieval registry data without editing frontend
code or restarting the API. The Retrieval console applies a preset to the query
builder only; operators still submit the search explicitly so preset changes
remain reviewable and stale-result state remains accurate.

## Healthcare Sources

Seeded v0 sources include:

- OJTFlow lab schema and data dictionary
- human-review governance triggers
- CSV lab-to-JSON transformation pattern
- FHIR Observation R4 direction
- curated FHIR R4 search parameter seeds for Observation, DiagnosticReport,
  MedicationRequest, and Condition
- LOINC laboratory terminology direction
- UCUM unit terminology direction
- RxNorm medication terminology direction
- OMOP CDM analytics export direction
- MeSH/PubMed biomedical literature-search direction
- query expansion rule registry for deterministic healthcare retrieval variants
- filter suggestion rule registry for deterministic self-query metadata suggestions
- query aspect rule registry for deterministic decomposition of healthcare
  search intent into reviewable evidence aspects
- ranking boost rule registry for deterministic domain-aware first-stage ranking policy
- medical search hint target registry for external target rationale and warnings
- an official healthcare source catalog covering MeSH, RxNorm/RxNav, LOINC,
  FHIR R4, UCUM, MedlinePlus, openFDA, and ClinicalTrials.gov
- a public dataset ingestion plan that keeps large third-party corpora out of
  git and routes them through explicit ingestion adapters

The implementation preserves original user data and records terminology evidence
without silently normalizing clinical concepts.

## Knowledge Expansion

The source-controlled `knowledge/` tree is intentionally a curated seed layer,
not a bulk data dump. It now contains:

- `knowledge/source_catalog/official_healthcare_sources.json`: authoritative
  source inventory, access URLs, intended use, and ingestion mode.
- `knowledge/terminologies/medical_concepts.json`: small controlled-vocabulary
  seed registry used by deterministic query analysis.
- `knowledge/retrieval/query_expansion_rules.json`: deterministic query
  expansion rules used by the analyzer before first-stage retrieval.
- `knowledge/retrieval/filter_suggestion_rules.json`: deterministic metadata
  filter suggestion rules for fields such as `clinical_domain` and
  `standard_system`.
- `knowledge/retrieval/query_diagnostic_rules.json`: deterministic
  query-quality diagnostic rules for low-specificity queries, missing
  healthcare concept matches, conflicting standard filters, and
  over-constrained metadata filters with too little clinical query context.
- `knowledge/retrieval/query_profile_rules.json`: deterministic query-profile
  rules that map concepts, standards, tokens, and candidate metadata to
  operator-visible adaptive retrieval route guidance.
- `knowledge/retrieval/query_aspect_rules.json`: deterministic query-aspect
  rules that decompose medical search intent into operator-visible evidence
  aspects with questions, rationale, suggested terms, and suggested filters.
- `knowledge/retrieval/ranking_boost_rules.json`: deterministic ranking boost
  rules for schema, field, trust-level, source-type, concept, and healthcare
  standard matches.
- `knowledge/retrieval/evidence_bucket_rules.json`: deterministic evidence
  bucket registry that maps selected hits into schema, policy, terminology,
  FHIR, source-locator, prior-decision, and fallback evidence-pack groups.
- `knowledge/retrieval/corrective_action_rules.json`: deterministic corrective
  action registry that maps retrieval quality signals to prioritized operator
  actions such as applying filters, broadening queries, requiring review, or
  reindexing sources.
- `knowledge/retrieval/evaluation_policy.json`: runtime retrieval evaluation
  policy that converts durable judgment metrics into operator-facing tuning
  recommendations.
- `knowledge/retrieval/quality_gate_policy.json`: retrieval package readiness
  policy that maps quality signal severities to score penalties, blocking
  severities, review severities, and the score threshold below which a package
  requires review.
- `knowledge/retrieval/search_hint_targets.json`: target metadata for
  external and terminology search hints, including operator rationale and
  warnings for PubMed, FHIR, LOINC, UCUM, ClinicalTrials.gov, and openFDA.
- `knowledge/retrieval/standard_search_playbook_rules.json`: deterministic
  healthcare-standard search playbook rules that turn query profiles,
  standards, query aspects, dataset fields, query tokens, resource types,
  safety flags, and quality signals into operator-facing FHIR, terminology,
  privacy, and external-search route steps.
- `knowledge/terminologies/fhir_search_parameters.json`: FHIR R4 search
  parameter templates for resource-level search hints. FHIR search hints expose
  `metadata.parameter_examples`, `metadata.lineage_followup`, and a capability
  warning so the UI can show concrete `code`, `patient`, `date`, and
  `value-quantity` syntax plus Provenance/AuditEvent follow-up without
  hardcoding FHIR in React.
  LOINC hints expose the authenticated Search API scope endpoints and
  query/rows/offset parameter examples. UCUM hints expose the NLM FHIR
  CodeSystem `$validate-code` operation parameters and selected candidate unit
  strings. UCUM hints are launchable only when the analyzer has a concrete unit
  candidate; placeholder unit-code hints remain copy-only to avoid sending
  meaningless requests.
Assistant synthesis receives compact `medical_search_hints` and `diversity`
from retrieval tool results, so the model can mention governed FHIR, LOINC,
UCUM, PubMed, ClinicalTrials.gov, openFDA follow-up routes, and selected-source
spread without inspecting raw retrieval JSON.
- `knowledge/corpus/clinical_data_standards_map.md`: project-scope map from
  workflow use cases to FHIR, LOINC, UCUM, RxNorm, MeSH/PubMed,
  ClinicalTrials.gov, openFDA, and OMOP.
- `knowledge/corpus/medical_search_playbook.md`: retrieval design notes based
  on advanced RAG patterns such as query transformation, hybrid retrieval,
  reranking, source-aware diversity, and coverage diagnostics.
- `knowledge/corpus/public_dataset_ingestion_plan.md`: priority ingestion plan
  for official public healthcare sources.

Bulk data belongs in runtime storage, not in the repo. The next ingestion layer
should fetch official datasets or API snapshots into ignored local/object
storage, normalize them into `KnowledgeDocument` and `KnowledgeChunk` records,
record source release metadata, and expose only reviewed distilled chunks to
the retrieval index. This keeps licenses, update cadence, provenance, and
storage size manageable for an enterprise deployment.

## Query Analysis

Retrieval now includes deterministic clinical query analysis before first-stage
ranking. This follows the query-transformation direction used in practical RAG
systems, but keeps the healthcare v0 behavior auditable: no LLM rewrites are
used, and every expansion is tied to a rule ID.

Current rules detect:

- laboratory observation identity cues and expand toward LOINC terminology.
- HbA1c/A1c synonyms and expand toward LOINC/FHIR lab-observation evidence.
- missing or ambiguous units and expand toward UCUM/FHIR `valueQuantity`.
- FHIR Observation profile cues.
- CSV/tabular quality cues.
- sensitive patient identifier context for human-review governance.
- medication normalization cues and expand toward RxNorm terminology.
- observational analytics/export cues and expand toward OMOP CDM evidence.
- biomedical literature-search cues and expand toward MeSH/PubMed search.
- clinical-trial cues and expand toward ClinicalTrials.gov API v2 search.
- drug regulatory/safety cues and expand toward openFDA label and adverse-event search.

The public retrieval package exposes this under
`handoff_context.query_analysis`:

```json
{
  "strategy": "deterministic_clinical_expansion_v0",
  "detected_concepts": ["hba1c_laboratory_test", "unit_normalization"],
  "concept_candidates": [
    {
      "concept_id": "glucose_serum_plasma",
      "display_name": "Glucose in serum or plasma",
      "standard_system": "LOINC",
      "code": "2345-7",
      "clinical_domain": "laboratory",
      "matched_aliases": ["glucose"],
      "confidence": 0.8,
      "source": "https://loinc.org/2345-7",
      "metadata": {
        "preferred_units": ["mg/dL", "mmol/L"]
      }
    }
  ],
  "expanded_terms": ["HbA1c", "UCUM computable unit"],
  "standards": ["LOINC", "FHIR", "UCUM"],
  "rule_ids": ["hba1c_lab_test", "unit_normalization"],
  "query_profile": {
    "profile_id": "laboratory_standardization",
    "label": "Laboratory standardization",
    "route": "clinical_data_normalization",
    "complexity": "moderate",
    "retrieval_mode": "hybrid_with_standard_coverage",
    "description": "Use when the query is about lab values, LOINC identifiers, UCUM units, or FHIR Observation normalization.",
    "suggested_filters": {
      "clinical_domain": "laboratory",
      "trust_level": "approved"
    },
    "rule_ids": ["profile_laboratory_standardization"]
  },
  "query_variants": ["..."],
  "filter_suggestions": [
    {
      "field": "standard_system",
      "value": "UCUM",
      "reason": "Detected UCUM standard context.",
      "rule_id": "suggest_standard_ucum",
      "confidence": 0.86,
      "applied": false
    }
  ],
  "diagnostics": [],
  "search_hints": [
    {
      "target": "fhir",
      "query": "Observation?code=<loinc-code>&subject=Patient/<id>&date=ge<yyyy-mm-dd>",
      "rationale": "Use FHIR resource-specific search parameters first and fall back to text search only when structured fields are unavailable.",
      "warnings": [
        "This is a template only; replace placeholders with validated identifiers, codes, and dates."
      ]
    }
  ]
}
```

`diagnostics[]` can include `overconstrained_metadata_filters` when the request
combines several metadata filters such as `clinical_domain`, `standard_system`,
`source_type`, `source_id`, or `trust_level` with a sparse query and no schema,
field, resource, or format context. This warns operators not to treat a narrow
source-scoped result as proof that the broader corpus lacks evidence.
Diagnostics include structured `metadata` for audit and UI rendering, including
`query_token_count`, `active_metadata_filters`,
`active_metadata_filter_count`, `applied_standard`, `suggested_standards`,
`detected_concepts`, and `detected_standards` when those values are available.

## Readiness Policy

Retrieval readiness is data-driven through
`knowledge/retrieval/quality_gate_policy.json` or
`OJT_RETRIEVAL_QUALITY_POLICY_PATH`. The engine still emits deterministic
`quality_signals[]`, but `quality_summary.score`, `quality_summary.status`, and
the top review action now use the active policy instead of embedded severity
penalties. The active policy metadata is copied into
`handoff_context.quality_policy` so workflow explanations, assistant tools, and
operators can see which scoring policy produced the readiness state.
The same policy can also declare `ranking_thresholds`, currently including
`min_top_matched_terms`, to require a minimum exact query-term overlap on the
top-ranked hit. When the top hit fails that gate, retrieval emits
`weak_top_hit_match` with the top evidence ID, matched-term count, threshold,
and score components needed for operator review.
The policy can also declare `provenance_requirements` for medical source
classes. The default gate checks healthcare standards, terminology systems, and
data dictionaries for a source version plus at least one auditable locator key
such as `path`, `url`, `standard`, `pmid`, `doi`, `api`, `resource`, `table`,
or `document_id`. Missing provenance emits `weak_evidence_provenance` with the
affected evidence IDs, missing fields, and active requirement metadata. This
keeps clinical search packages aligned with FHIR-style provenance expectations
and PubMed/NLM-style citation metadata instead of treating anonymous text as
equivalent to a traceable medical source.
The policy also declares `concept_grounding_requirements`. When enabled, the
retriever compares detected controlled-vocabulary concepts against selected-hit
metadata, codes, display names, aliases, and matched terms. Supporting hits
expose `source_locator.concept_matches[]` with concept ID, display name,
standard system, optional code, confidence, matched fields, aliases, and a
reason. If a detected concept above the configured confidence threshold is not
represented by selected evidence, retrieval emits `missing_concept_grounding`.
This keeps the package aligned with coded medical search practice such as FHIR
`Coding`/`CodeableConcept`, LOINC code/display search, and RxNorm concept
grounding.
The policy also declares `evidence_bucket_requirements`. The default requires
`schema` and `policy` evidence buckets in selected results because downstream
validation/explanation needs both data-contract evidence and governance/safety
evidence. Missing required buckets emit
`missing_required_evidence_buckets`, reduce `quality_summary.score`, and keep
the package in review until the operator broadens the search, changes filters,
or adds the missing trusted source class. Deployments can override this with
`{"required_bucket_ids": []}` only when a retrieval surface does not need
governed workflow readiness.
The Retrieval console carries the same concept grounding into run comparison:
active-vs-baseline comparisons list added, removed, and retained grounded
concepts, and copied `retrieval_run_comparison` reports include a
`concept_grounding` section for offline relevance-tuning notes.
The Retrieval trace renders structured quality signal metadata directly for
operator review, including missing concepts, provenance issues, missing
standards/aspects, and suggested filters, so readiness diagnostics are usable
without opening raw response JSON.
Ranked evidence cards show a compact support summary before the detailed
sections, with data-derived counts for matched terms, provenance fields,
grounded concepts, supported aspects, and ranking signals. This gives reviewers
a fast scan of why a hit is useful before reading the full explanations.
Ranked evidence cards also show a compact provenance summary with source
version and key locator metadata before the expandable raw locator JSON, making
the provenance quality gate inspectable during normal evidence review. URL/API
locators, PubMed IDs, and DOIs render as external links when they can be safely
normalized.
Each ranked evidence card can copy a `retrieval_evidence_hit` report containing
evidence identity, support-summary counts, score components, ranking boosts,
concept/aspect grounding, provenance summary, raw locators, and snippet context
for audit notes or assistant handoff. The copied evidence report also includes
`corrective_actions.related_to_evidence` and
`corrective_actions.package_top_actions` so offline notes preserve both
evidence-specific and package-level remediation context. Copyable evidence,
comparison, evaluation, and search-hint actions show transient success feedback
in the UI so operators know the
clipboard action completed.

Retrieval packages also expose `evidence_buckets[]`, a clinical evidence pack
summary derived from the selected hits. Bucket definitions are loaded from
`knowledge/retrieval/evidence_bucket_rules.json`; deployments can point
`OJT_EVIDENCE_BUCKET_RULES_PATH` to an approved replacement registry. The
default buckets group evidence into `schema`, `policy`, `terminology`,
`fhir_mapping`, `source_locator`, `prior_decision`, and `other` so reviewers
can see whether a search result is grounded by the right classes of healthcare
evidence before using it in a workflow. `schema` and `policy` buckets are
required by the default readiness policy for governed workflow use; when either
bucket has no selected hits, the package marks it `missing` and emits
deterministic bucket warnings such as `missing_schema_evidence`. Readiness
turns those bucket gaps into the package-level
`missing_required_evidence_buckets` quality signal. Bucket membership is
data-driven from source type, source ID, standard system, and locator metadata.
Each bucket can also expose a `suggested_filter` such as
`{"source_type": "schema"}` or `{"standard_system": "ojtflow_policy"}` so the
UI can offer explicit remediation searches for missing evidence classes without
hardcoding bucket behavior in React. The original `hits[]` and `evidence[]`
arrays remain unchanged; buckets are an operator and assistant audit view over
the selected evidence, not a second ranking pass.

The Retrieval console renders a package-level search cockpit above the detailed
ranked evidence. The cockpit is a scan-first view over the same package fields:
`handoff_context.query_analysis.query_profile`, query-aspect decomposition,
expanded terms, ranking stack, reranker state, diversity/source spread,
`quality_summary`, `evidence_buckets[]`, coverage gaps, concept grounding, and
`recommended_actions[]`. It is intentionally presentation-only; remediation
buttons are shown only when the backend provides a supported `suggested_filter`.
The left rail also renders a compact search-plan preview before and after full
retrieval. Before search, the UI calls `POST /api/v1/retrieval/plan`, which
returns a `RetrievalPlan` from the same adapter-owned query analysis used by
ranked retrieval. After search, the preview switches to the completed
`RetrievalPackage`. In both states it shows the selected route, matched query
profile, decomposed search aspects, query rewrites, external medical-search
hints, execution tasks, and filter suggestions before an operator opens the full
trace. `query_analysis.retrieval_tasks[]` is the ordered task plan that bridges
planning to tool execution: local corpus searches are required coverage tasks,
while external medical-index tasks remain optional follow-ups with explicit
target/action/rationale/warnings. Operators can run local corpus tasks directly
from the preview when `action_type="run_local_search"`; the UI applies supported
task filters to the query builder and uses the same retrieval mutation/history
path as a normal evidence search. External medical-index tasks open
backend-provided follow-up URLs when `action_type="open_external_url"` and fall
back to copying syntax when `action_type="copy_query"`. Every task row can copy
its exact planned query so syntax-only follow-ups remain usable outside the app. The preview also
lets operators apply supported query-analysis filter suggestions before full
search through the same typed filter path used by trace remediation. In
plan-only mode this updates the query builder without running retrieval; after a
completed package it can refresh ranked evidence with the new filter. Plan-only
filter application shows an inline confirmation so the operator knows the query
builder changed and search still needs to run. The preview
also shows plan coverage before task details: required local tasks, optional external
follow-ups, inferred standards, suggested filter count, and plan warnings. Its
source of truth is backend `RetrievalPlan.coverage_summary`; the frontend may
derive the same shape only as a compatibility fallback for older plan payloads.
`coverage_summary.next_action` is the backend-owned operator instruction for the
next search step.
`task_summary` is the backend-owned execution summary that separates local
OJTFlow-runnable search tasks from external medical index follow-ups. The UI
uses it to show which work can run immediately, which tasks are required first,
and which follow-ups require opening or copying external search syntax. The
summary panel should expose direct actions for the first runnable local task and
for copying external follow-up syntax so operators do not need to hunt through
every task row before starting.
The summary panel also presents a stable run order for end users: execute
required local corpus tasks first, apply supported filters when the plan narrows
source/standard/trust scope, then review external medical-index follow-ups as
manual context. Each execution-task row includes a "What happens" explanation
derived from the backend task `target` and `action_type`: local tasks refresh
the governed OJTFlow evidence package, external URL tasks open a source outside
the app, and copy-query tasks prepare syntax for manual review. This keeps the
planning UI usable for operators who do not already know the retrieval
architecture.
The backend also returns `RetrievalPlan.risk_signals[]` so the preview can show
prioritized pre-search risks before task execution; these signals are derived
from backend coverage and query diagnostics, not from frontend heuristics.
Its copy action exports a
`retrieval_search_plan_preview` report so review notes and demos can preserve
the exact plan that produced the ranked evidence.

This is separate from `evaluation_policy.json`: quality gates assess the current
retrieval package before downstream use, while evaluation policy turns durable
human relevance judgments into tuning recommendations.

`query_profile` is loaded from
`knowledge/retrieval/query_profile_rules.json`, with deployment override
support through `OJT_QUERY_PROFILE_RULES_PATH`. It is a deterministic routing
hint for adaptive retrieval and operator review, not an automatic hidden
retriever switch. Current profile rules cover laboratory standardization,
medication safety, biomedical literature evidence, and observational analytics.
The Retrieval console renders profile-suggested filters as explicit operator
actions when they map to supported metadata filters, and displays unsupported
profile fields without applying them. Applied-state badges are based on the
submitted `trace.filters_applied` values for the displayed retrieval package,
so draft query-builder edits do not change the apparent provenance of the
current results.

Filter suggestions are a deterministic self-query feature: they recommend
metadata filters such as `clinical_domain=laboratory`,
`standard_system=UCUM`, or exact `source_id=terminology:ucum`, but do not apply them silently. The analyzer loads those
rules from `knowledge/retrieval/filter_suggestion_rules.json`; each rule
declares a `rule_id`, filter field, filter value, reason, confidence, and match
criteria over detected concepts, standards, query-expansion rule IDs, and
controlled-vocabulary candidate metadata. Code still allowlists supported
filter fields (`clinical_domain`, `standard_system`, `source_type`,
`trust_level`, and `source_id`) before accepting registry rules.
`OJT_FILTER_SUGGESTION_RULES_PATH` can point the runtime to a
deployment-specific rule pack.

The Retrieval console shows confidence and whether each suggestion is already
applied. Supported suggestions can be applied explicitly from the trace panel,
which updates the query-builder filter state and reruns the search through the
same typed `/retrieval/search` request path.

`query_aspects` is a deterministic query-decomposition scaffold loaded from
`knowledge/retrieval/query_aspect_rules.json`, with deployment override support
through `OJT_QUERY_ASPECT_RULES_PATH`. Aspect rules match the same auditable
inputs as query profiles: detected concepts, standards, query-expansion rule
IDs, tokens, and controlled-vocabulary candidate metadata. Each matched aspect
emits an `aspect_id`, label, review question, rationale, priority,
contributing rule ID, suggested terms, and suggested filters. Current rules
cover laboratory identity/standardization, unit and value quality, sensitive
data review, medication terminology/safety, literature/external evidence, and
observational schema context. This is a search-planning and review aid; it does
not run hidden independent searches or make clinical recommendations. Each
matched aspect contributes a transparent `query_variant_details[]` row with
`source="query_aspect_rule"`, so first-stage retrieval can use the
data-driven decomposition plan while preserving full provenance. Each ranked
hit can also include `source_locator.query_aspect_matches[]`, recording the
aspect ID, label, rule ID, priority, matched metadata filters, matched suggested
terms, and deterministic reason for the hit-aspect support. The Retrieval
console shows those rows as per-hit "Aspect support" evidence, shows
aspect-suggested filters with applied-state badges based on the submitted
retrieval trace, and lets operators explicitly apply supported metadata filters
through the same typed search path used by other filter suggestions. The
retrieval package also reports `coverage.query_aspects[]` for aspects with
supported suggested filters, counting selected evidence that matches the aspect
criteria and raising `missing_query_aspect_coverage` when the selected evidence
does not cover the aspect plan.

Every retrieval package includes `handoff_context.search_request` and
`handoff_context.search_signature`. The request is the normalized server-side
query/filter/top-k contract used by the retrieval service. The signature is a
stable `sha256:<digest>` fingerprint of that normalized request, so browser
history entries, copied comparison reports, durable judgments, assistant tools,
and audit notes can reference the same backend search contract.

Deterministic query expansion rules are loaded from
`knowledge/retrieval/query_expansion_rules.json`, not hardcoded into the query
analyzer. Each rule defines `rule_id`, `concept`, trigger terms, expanded
terms, standards, and an auditable query variant. The analyzer reads the
registry on request, so trusted rule updates can be made as data changes without
editing source code. `OJT_QUERY_EXPANSION_RULES_PATH` can point the runtime to a
different registry for local evaluation or deployment-specific rule packs.

Concept candidates are loaded from `knowledge/terminologies/medical_concepts.json`,
also not hardcoded into the query analyzer. The seed registry currently covers a
small set of common examples across LOINC, RxNorm, and MeSH, such as HbA1c
`4548-4`, glucose `2345-7`, creatinine `2160-0`, sodium `2951-2`, potassium
`2823-3`, total cholesterol `2093-3`, metformin RxCUI `6809`, Diabetes Mellitus
MeSH `D003920`, Hypertension MeSH `D006973`, and chronic kidney failure MeSH
`D007676`. Rules and candidates improve query variants, filter suggestions, and
operator transparency. They are scaffold data, not a substitute for a full
licensed terminology service or final clinical code assignment.

Diagnostics are deterministic query-quality checks. They flag low-specificity
queries, missing healthcare concept matches, and standard filters that conflict
with the standards inferred from query content. They also flag sparse queries
that combine several narrowing metadata filters, because such searches can make
coverage look weaker than it is. Diagnostic codes, severities, messages, and
suggested actions are loaded from
`knowledge/retrieval/query_diagnostic_rules.json`; the code only owns the
allowlisted condition mechanics. `OJT_QUERY_DIAGNOSTIC_RULES_PATH` can point
the runtime to a deployment-specific rule pack for local evaluation or
enterprise policy wording. Warning diagnostics are copied into
`RetrievalTrace.warnings` for audit and UI visibility.

Ranking boost rules are loaded from `knowledge/retrieval/ranking_boost_rules.json`,
not hardcoded into the ranking engine. Each rule defines `rule_id`, `weight`,
`reason`, a required `match` condition, and optional `any_of` alternatives.
Supported match operators are intentionally narrow: schema ID in source ID,
requested fields in matched terms, detected format presence, applied
clinical-domain filter match, chunk trust level, source type, standard system,
matched query terms, detected concepts, and query-expansion rule IDs.
`OJT_RANKING_BOOST_RULES_PATH` can point the runtime to a deployment-specific
ranking policy. The default policy intentionally gives stronger boosts to
direct schema-source matches, HbA1c/LOINC concept grounding, and FHIR
Observation profile grounding so broad unit evidence does not crowd out the
canonical schema, terminology, or profile source for those query intents.
Applied boosts are copied into each hit's
`source_locator.ranking_boosts` as rule ID, weight, and reason objects so
ranking influence is visible in API payloads and the Retrieval console. The
legacy `source_locator.ranking_boost_rules` ID list is preserved for compact
audit views and older clients.

Each hit also carries `score_components`, the auditable score explanation for
the final hit score. The deterministic adapters emit lexical RRF, vector RRF,
policy boost, and optional external reranker contribution rows. Each row carries
the component key, operator label, numeric contribution, optional rank,
description, and metadata such as raw score, RRF `k`, or ranking-rule IDs. This
keeps the final score inspectable without requiring clients to reconstruct
ranking math from separate fields.

The trace also carries `fusion_diagnostics`, a package-level RRF observability
summary. It reports lexical/vector top overlap, mean selected-hit rank delta,
dominant signal balance across selected hits, and a compact interpretation such
as `lexical_vector_agree`, `mixed_fusion_signals`, or
`lexical_vector_diverge`. This helps reviewers tell whether keyword and vector
signals support the same ordering before trusting rank position.
When the LlamaIndex adapter owns fusion internally, the same field is still
present but uses `diagnostic_scope=framework_managed_fusion`; overlap and rank
delta are `null` because the framework does not expose separate lexical/vector
rank lists through the public adapter boundary.

Query analysis also emits `query_variant_details` alongside the legacy
`query_variants` list. Each detail records the variant text, source, reason,
and metadata such as matched rule IDs, schema ID, detected format, or controlled
vocabulary concept. The trace copies those details to
`trace.query_variant_details` so operator review can inspect query rewrites
without guessing why a variant was used.

`RetrievalPackage.diversity` contains source-aware diversity metadata,
including `selected_hits`, one row per final hit.
Each row records evidence ID, source ID, selected rank, original rank,
normalized relevance, redundancy penalty, final MMR selection score, and a short
reason. This makes source diversity auditable per result card instead of only
showing aggregate selected-source counts.

Search hints are syntax scaffolds for medical search workflows outside the
local retrieval index. PubMed hints prefer a conservative combination of
title/abstract text words and MeSH-review warnings; FHIR hints produce resource
search templates such as `Observation?code=...&subject=...&date=...`;
ClinicalTrials.gov hints produce API v2 study searches by condition,
intervention, and recruitment status; openFDA hints produce public drug-label
and adverse-event endpoint queries. These hints are never executed
automatically and are not clinical recommendations. Each hint carries the
search syntax in `query` and may include a launchable `url` when the target has
a stable public endpoint. The React trace renders those hints with copy/open
actions from backend data instead of hardcoding external search URLs in the UI.
Target rationale and warnings are loaded from
`knowledge/retrieval/search_hint_targets.json`, while provider-specific query
syntax, URL encoding, and template construction remain deterministic analyzer
logic. The analyzer reads the registry on request so trusted target metadata can
change without a code edit. `OJT_SEARCH_HINT_TARGETS_PATH` can point the runtime
to a deployment-specific target registry.
For example, `PubMed systematic review HbA1c units` produces a `pubmed` hint
that combines HbA1c title/abstract terms, unit terms, and publication-type
terms, plus a PubMed URL using the same encoded search statement, while warning
operators to confirm preferred MeSH headings before using the query as a final
literature strategy.

For example, `ClinicalTrials.gov diabetes metformin recruiting eligibility`
produces a `clinicaltrials_gov` hint shaped like
`https://clinicaltrials.gov/api/v2/studies?query.cond=Diabetes+Mellitus&query.intr=Metformin...`.
`openFDA metformin adverse event boxed warning drug label` produces
`openfda_drug_label` and `openfda_drug_event` hints shaped around the drug
label and FAERS adverse-event endpoints. Both routes include warnings to verify
timestamps, product identity, limitations, and source provenance.

Research basis:

- RAG query transformation patterns:
  `https://github.com/NirDiamant/RAG_Techniques`
- LlamaIndex documents/nodes and node parsing:
  `https://docs.llamaindex.ai/en/v0.10.34/module_guides/loading/documents_and_nodes/`
- LlamaIndex vector retriever:
  `https://docs.llamaindex.ai/en/stable/api_reference/retrievers/vector/`
- LlamaIndex reciprocal rerank fusion retriever:
  `https://docs.llamaindex.ai/en/v0.10.22/examples/retrievers/reciprocal_rerank_fusion/`
- Metadata-aware self-query retrieval:
  `https://api.python.langchain.com/en/latest/langchain/retrievers/langchain.retrievers.self_query.base.SelfQueryRetriever.html`
- Elasticsearch query rules for contextual search control:
  `https://www.elastic.co/docs/reference/elasticsearch/rest-apis/retrievers/rule-retriever`
- PubMed search, Automatic Term Mapping, field tags, and MeSH behavior:
  `https://pubmed.ncbi.nlm.nih.gov/help/`
- NLM MeSH retrieval usage:
  `https://www.nlm.nih.gov/mesh/intro_retrieval.html`
- HL7 FHIR R4 search semantics:
  `https://hl7.org/fhir/R4/search.html`
- FHIR Observation R4: `https://hl7.org/fhir/r4/observation.html`
- NLM MeSH data: `https://www.nlm.nih.gov/databases/download/mesh.html`
- RxNorm/RxNav APIs: `https://lhncbc.nlm.nih.gov/RxNav/APIs/RxNormAPIs.html`
- LOINC examples: `https://loinc.org/2345-7` and `https://loinc.org/4548-4`
- UCUM units: `https://ucum.nlm.nih.gov/`
- MedlinePlus XML: `https://medlineplus.gov/xml.html`
- openFDA APIs: `https://open.fda.gov/apis/`
- openFDA query syntax: `https://open.fda.gov/apis/query-syntax/`
- ClinicalTrials.gov API v2: `https://clinicaltrials.gov/data-api/api`
- ClinicalTrials.gov search areas:
  `https://clinicaltrials.gov/data-about-studies/search-areas`

## Snippets And Context Compression

Every `RetrievalHit` includes `snippet`, a deterministic extractive preview of
the source claim. Snippets select the highest-overlap sentence/window after
retrieval and before UI/explanation rendering:

```json
{
  "text": "Missing units require human review before downstream clinical analytics use.",
  "start_char": 44,
  "end_char": 114,
  "matched_terms": ["missing", "units", "human", "review"],
  "extraction_strategy": "deterministic_sentence_window_v0"
}
```

This is a conservative form of contextual compression: it reduces review noise
and makes evidence easier to inspect without asking a model to rewrite clinical
content. The full evidence `claim` remains available for audit and downstream
handoff.

Every `RetrievalHit` also includes a backend-owned `match_explanation` object.
It is generated after evidence-bucket classification so UI cards, copied
evidence reports, and copied cockpit reports all use the same source of truth:

```json
{
  "version": 1,
  "support_status": "strong",
  "top_score_driver": "Lexical score +0.420",
  "top_score_component": {
    "component": "lexical_score",
    "label": "Lexical score",
    "rank": null,
    "value": 0.42
  },
  "matched_terms": ["hba1c", "unit"],
  "bucket_ids": ["schema", "source_locator"],
  "concept_ids": ["hba1c_lab_test"],
  "aspect_ids": ["unit_and_value_quality"],
  "provenance_fields": ["Standard", "Chunk"],
  "ranking_signal_rule_ids": ["boost_schema_match"]
}
```

The object is deterministic and data-derived. It does not create new clinical
claims; it exposes stable IDs and score drivers already present in the
retrieval package.

Research basis:

- RAG contextual compression / relevant segment extraction:
  `https://github.com/NirDiamant/RAG_Techniques/blob/main/all_rag_techniques/contextual_compression.ipynb`
- Search-result highlighting/snippets:
  `https://www.elastic.co/docs/reference/elasticsearch/rest-apis/highlighting`

## Result Facets

`RetrievalPackage.facets` summarizes final selected hits:

```json
{
  "source_type": [{"value": "terminology_system", "count": 2}],
  "clinical_domain": [{"value": "laboratory", "count": 4}],
  "standard_system": [{"value": "UCUM", "count": 1}],
  "trust_level": [{"value": "approved", "count": 5}]
}
```

This follows standard search UI practice: result sets expose bucket counts so
operators can understand coverage and refine filters. The Retrieval console
renders supported facet buckets as explicit refinement controls. Selecting a
bucket updates the query-builder filter state and reruns the same typed
`/retrieval/search` request instead of filtering visible cards on the client.
Applied refinements are shown as active chips next to the query builder; each
chip can be removed independently, and operators can clear all metadata
refinements before rerunning the typed search.
The console also tracks a deterministic signature of the submitted request. If
operators change the query builder after a result package is displayed, the
results header is marked with pending changes until the current request shape is
submitted again. Ranked evidence also shows a submitted-search summary with the
query, target size, schema, format, resource, fields, and metadata constraints
that produced the displayed result set. Result facet applied states are based on
that submitted request, not unsaved edits in the query builder. When the query
builder has drifted, the summary exposes a restore action that syncs the builder
back to the submitted request without mutating displayed evidence or rerunning
retrieval.
In v0 these facets are computed over selected hits, not the full indexed corpus,
so the counts match the evidence cards visible in the Retrieval console.

Research basis:

- Solr faceting: `https://solr.apache.org/guide/solr/latest/query-guide/faceting.html`
- Elasticsearch bucket aggregations:
  `https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations-bucket.html`

## Standard Coverage Diagnostics

`RetrievalPackage.coverage` compares standards inferred by query analysis with
the standards represented in final selected evidence:

```json
{
  "standard_system": [
    {
      "field": "standard_system",
      "value": "UCUM",
      "selected_count": 1,
      "status": "covered",
      "severity": "info",
      "reason": "Selected evidence includes UCUM grounding.",
      "suggested_action": "Keep the current retrieval scope; selected evidence already includes UCUM grounding.",
      "suggested_filter": {}
    },
    {
      "field": "standard_system",
      "value": "FHIR",
      "selected_count": 0,
      "status": "missing",
      "severity": "warning",
      "reason": "Query analysis expected FHIR grounding, but no selected evidence used that standard.",
      "suggested_action": "Apply standard_system=FHIR or broaden the query to retrieve FHIR-grounded evidence.",
      "suggested_filter": {
        "standard_system": "FHIR"
      }
    }
  ],
  "warnings": [
    "Query analysis expected FHIR grounding, but no selected evidence used that standard."
  ]
}
```

The diagnostic is deterministic and metadata-based. It does not claim clinical
adequacy; it tells operators when the selected retrieval package is missing a
standard cue that the query analysis expected. Missing coverage warnings are
also copied into `RetrievalTrace.warnings` so existing audit views continue to
surface them. Missing diagnostics also include `suggested_action` and
`suggested_filter` so the Retrieval console can offer an explicit
operator-controlled refinement, such as applying `standard_system=FHIR`, instead
of silently mutating the query.

Research basis:

- Azure AI Search faceted navigation and filters:
  `https://learn.microsoft.com/en-us/azure/search/search-filters`
- Algolia faceting and filtering:
  `https://www.algolia.com/doc/guides/managing-results/refine-results/faceting`
- RAGAS context recall/precision as a retrieval evaluation lens:
  `https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/context_precision/`
- RAGAS context recall:
  `https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/context_recall/`

## Retrieval Quality Signals

`RetrievalPackage.quality_signals` is the package-level checklist that turns
trace metadata into operator-facing quality gates:

```json
[
  {
    "code": "hits_available",
    "severity": "success",
    "message": "Retrieved 5 evidence item(s) from 12 candidate(s).",
    "suggested_action": "Review the ranked evidence and score explanations before using it downstream.",
    "evidence_ids": ["ev_123"],
    "metadata": {
      "hit_count": 5,
      "candidate_count": 12
    }
  },
  {
    "code": "missing_standard_coverage",
    "severity": "warning",
    "message": "Selected evidence is missing expected standard grounding for UCUM.",
    "suggested_action": "Apply the suggested standard filters or broaden the query.",
    "evidence_ids": [],
    "metadata": {
      "missing_standards": ["UCUM"],
      "suggested_filters": [{"standard_system": "UCUM"}]
    }
  }
]
```

Current signals are deterministic and derived from selected hits, coverage
diagnostics, query safety flags, and source-diversity metadata. They are meant
to make retrieval review faster and more auditable: a reviewer can see whether
the result set is empty, under-covered, safety-sensitive, or source-redundant
without reading raw trace JSON first. They do not score clinical correctness or
replace a human review.

`RetrievalPackage.quality_summary` rolls the same signals into a quick
operator-readiness summary with `status`, 0-100 `score`, severity counts,
blocker/warning codes, and `top_action`. The summary is also copied into
`handoff_context.quality_summary` so assistant and future Graph/RAG handoff
layers can use the same readiness signal without parsing UI state. The summary
does not hide the underlying signals; it only provides a first-glance answer to
whether the package is ready, needs review, or is blocked.

`RetrievalPackage.recommended_actions` turns warning/destructive signals into a
deterministic corrective retrieval checklist. The mapping is loaded from
`knowledge/retrieval/corrective_action_rules.json`; deployments can point
`OJT_CORRECTIVE_ACTION_RULES_PATH` to an approved replacement registry. This
follows the corrective-RAG pattern: evaluate initial retrieval quality, then
propose concrete recovery steps instead of leaving the operator to interpret raw
diagnostics. Current actions include `apply_filter`, `broaden_query`,
`rewrite_query`, `reindex_source`, `add_source`, `require_review`, and
`diversify_sources`. Actions are sorted by backend priority and include source
signal codes, evidence IDs, optional supported `suggested_filter`, and metadata
such as the missing evidence bucket or concept. The package also exposes
`recommended_action_summary` with action count, highest priority, highest
severity, top action title, apply-filter count, broaden-query count, and
per-action-type counts. The same action list and summary are copied into
`handoff_context.recommended_actions` and
`handoff_context.recommended_action_summary` so the Assistant can explain or
execute governed remediation without re-deriving policy in the browser.
`RetrievalPackage.remediation_summary` is the backend-owned plain-language next
step derived from the same action/quality/warning state. It is copied into
`handoff_context.remediation_summary`, and clients should prefer it over local
fallback text so UI, assistant, and copied reports stay consistent.
`RetrievalPackage.interpretation` is the backend-owned package-level evidence
interpretation used by the browser, assistant, and future MCP tools. It exposes
status, summary, top evidence/source IDs, top score driver, support status,
matched terms, concept/aspect labels, required bucket coverage, warning count,
and next action title/detail. It is also copied into
`handoff_context.interpretation`. Clients may keep compatibility fallbacks for
older payloads, but new UI should prefer this field so search meaning is
consistent across surfaces.

Corrective-action rules are source-scoped. Rules default to
`source = "quality_signal"` for package readiness signals, and can opt into
`source = "query_diagnostic"` for pre-retrieval query-health diagnostics. For
example, the `overconstrained_metadata_filters` diagnostic produces a
`broaden_query` action before an operator treats low coverage from a narrowly
filtered request as evidence that the broader corpus lacks support.

`RetrievalPackage.strategy_recommendations` explains the active retrieval route
and practical RAG technique in operator language. Rules are loaded from
`knowledge/retrieval/strategy_recommendation_rules.json`; deployments can point
`OJT_STRATEGY_RECOMMENDATION_RULES_PATH` to an approved replacement registry.
Current rule predicates can match query profile, retrieval mode, quality signal
codes, safety flags, missing required evidence buckets, and reranker state. The
same list is copied into `handoff_context.strategy_recommendations`, so the
Assistant and future Graph/RAG layer see the same route explanation as the
Retrieval UI.

Research basis:

- Corrective/self-improving RAG pattern: evaluate retrieved evidence and adapt
  with correction or additional retrieval before generation.
  `https://github.com/NirDiamant/RAG_Techniques`
- LlamaIndex retrieval evaluation overview:
  `https://docs.llamaindex.ai/en/stable/module_guides/evaluating/index.html`
- LlamaIndex observability overview:
  `https://docs.llamaindex.ai/en/stable/module_guides/observability/`
- RAGAS available retrieval metrics:
  `https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/`

## API

The React operations console exposes these contracts through `/retrieval`.
Operators can run direct evidence searches, inspect rank components, verify
query variants and filters, see safety warnings, inspect the graph handoff, list
trusted sources, and trigger explicit reindexing. Workflow-scoped evidence is
still rendered inside the Workflow Detail Evidence tab.

Search:

```http
POST /api/v1/retrieval/search
```

```json
{
  "query": "HbA1c lab CSV missing units FHIR Observation",
  "top_k": 5,
  "schema_id": "lab_result_v1",
  "fields": ["date", "patient_id", "lab_name", "value", "unit"],
  "clinical_domain": "laboratory",
  "trust_level": "approved"
}
```

List sources:

```http
GET /api/v1/retrieval/sources
```

Refresh indexed retrieval sources:

```http
POST /api/v1/retrieval/reindex
```

```json
{
  "include_seeded": true,
  "include_corpus": true
}
```

Check retrieval index consistency:

```http
GET /api/v1/retrieval/integrity?include_seeded=true&include_corpus=false
```

The integrity report compares trusted source chunks with the currently indexed
chunks and returns source-level status values:

- `ok`: indexed source hash matches trusted source hash.
- `missing`: trusted source is absent from the index.
- `stale`: indexed source exists but content or metadata differs.
- `extra`: indexed source is outside the selected check scope.

By default the check verifies seeded project knowledge. Operators can include
configured local corpus directories with `include_corpus=true`.

Direct retrieval requires an authenticated session. Requests without
`workflow_id` search the approved knowledge inventory. Requests with
`workflow_id` are scoped to the authenticated workflow owner and return
`not_found` for other users' workflow IDs.

Workflow output includes:

- `retrieved_context`
- `handoff_context.retrieval_trace`
- `handoff_context.retrieval_handoff`
- `handoff_context.retrieval_handoff.graph_context`

`graph_context` uses contract `graph_ner_handoff.v0` and includes:

- `nodes`: query, evidence, healthcare standard, clinical concept, standard
  code, data-field, FHIR resource, and FHIR search-parameter nodes.
  Standards, data fields, and fallback clinical concepts are recognized from
  `knowledge/terminologies/graph_ner_rules.json`, overridable with
  `OJT_GRAPH_NER_RULES_PATH`. Nodes include deterministic `confidence` and
  `rule_source` metadata when available. Every node also carries `provenance`
  with the extractor name/version, extraction source, confidence when known,
  review state, and source evidence/chunk metadata when the node came from a
  retrieved claim. Reused nodes can carry `additional_provenance` entries when
  the same concept appears in both query text and retrieved evidence.
- `clinical_concept` nodes whose label matches an alias in
  `knowledge/terminologies/medical_concepts.json` (the same seed registry
  deterministic query analysis uses, overridable with
  `OJT_MEDICAL_CONCEPT_REGISTRY_PATH`) carry dictionary normalization:
  `normalized_code` (e.g. `LOINC:4548-4`), `normalized_system`,
  `normalized_display`, `clinical_domain`, and `concept_registry_id`. The
  matching `standard_code` node carries `standard_system` and `display_name`.
- FHIR resource nodes expand into search-parameter nodes from
  `knowledge/terminologies/fhir_search_parameters.json`, overridable with
  `OJT_FHIR_SEARCH_PARAMETERS_PATH`. These nodes expose `target_field`,
  `search_type`, and example query syntax for downstream retrieval/MCP tools.
- `edges`: auditable relationships such as `supports`, `mentions_field`,
  `mentions_entity`, `requests_resource`, `has_search_parameter`,
  `uses_standard`, and `normalizes_to` (clinical concept to its canonical
  standard code). Edges carry the same `provenance` envelope; `normalizes_to`
  edges use `review_state="candidate_requires_review"` because deterministic
  code candidates are reviewable evidence, not an automatic clinical coding
  decision.
- `triples`: source/evidence triples, including `normalizes_to` triples that
  pair a recognized concept label with its canonical code (for example
  `HbA1c / normalizes_to / LOINC:4548-4`), for downstream Graph-NER/RAG
  handoff. Triples include provenance with the source evidence ID and chunk
  locator when available.
- `summary`: extractor version, node, edge, triple, provenance, candidate
  review, Graph-NER rule, and concept-registry counts so UIs and operators can
  tell whether a graph package is thin, review-heavy, or well grounded.

Concept normalization is deterministic dictionary lookup against seed
registries, not a clinical coding decision; unmapped terms keep their plain
`clinical_concept` node without a `normalizes_to` edge.

`handoff_context.graph_conflict_report` uses contract
`graph_conflict_report.v1`. It is produced after Graph-NER and before answer
synthesis so final answers can be review-gated when evidence disagrees. The
policy is loaded from `knowledge/retrieval/graph_conflict_rules.json`,
overridable with `OJT_GRAPH_CONFLICT_RULES_PATH`. The report currently detects:

- `contradictory_source_claim`: evidence claims that match opposing
  data-driven guidance patterns, such as required versus not-required fields.
- `deprecated_terminology_mapping`: normalized terminology evidence from a
  deprecated, blocked, failed, or review-required source/version.
- `conflicting_units`: the same normalized concept linked to multiple UCUM unit
  candidates across retrieved evidence.
- `version_mismatched_standard_guidance`: retrieved guidance for the same
  standard/resource/domain spanning multiple source versions.

Each conflict includes `conflict_id`, `kind`, `severity`, `rule_id`,
`message`, `suggested_action`, evidence refs, graph node/edge refs when
available, normalized-code candidates when relevant, and metadata such as unit
codes, preferred units, source lifecycle state, or version groups. Any
review-required conflict is copied into retrieval trace warnings and forces the
guarded retrieval answer to `review_required` when it would otherwise be fully
supported.

Persisted graph records are stored in the backend spine:

- Memory mode keeps graph records for tests and local demos only.
- SQLite mode stores `graph_contexts` beside workflow, event, dataset,
  retrieval, assistant, and audit tables.
- Postgres mode stores `ojtflow.graph_contexts` through migration
  `019_graph_contexts.sql`.
- `GET /api/v1/retrieval/graph/contexts` lists authenticated-owner records,
  optionally filtered by `workflow_id`.
- `GET /api/v1/retrieval/graph/export` exports the same authenticated-owner
  scope as `jsonl` node/edge/triple records or `rdf_jsonl`
  subject/predicate/object triples.
- `GET /api/v1/retrieval/graph/neighborhood` reads persisted contexts and
  returns a bounded owner-scoped subgraph around matching nodes/triples for
  GraphRAG/evidence exploration.

Graph-NER has a deterministic evaluation gate:

```bash
python scripts/evaluate-graph-ner.py
python scripts/evaluate-graph-ner.py --json
```

Cases live in `tests/fixtures/graph_ner_eval_cases.json`. The fixture set
covers lab-name concepts, UCUM unit mentions, patient identifier fields,
RxNorm-grounded medication concepts, diagnosis coding concepts, procedure
concepts, and FHIR resource/search-parameter nodes. The runner reports expected
node recall, expected edge recall, and normalized-code recall. CI, deploy, and
`scripts/release-check.sh` run the same gate so Graph-NER extraction regressions
are caught before release.

`retrieval_trace.safety_flags` is deterministic and auditable. Current flags are:

- `prompt_injection_pattern_in_query`: the retrieval query or query context
  looks like instruction injection and must be treated as untrusted data.
- `sensitive_field_context`: the query fields include healthcare-sensitive
  identifiers such as patient fields. Retrieval continues, but downstream
  handoff code should avoid treating the query text as executable instruction.

## Ranking Architecture

Retrieval is a two-stage architecture with deterministic defaults:

1. First-stage candidate retrieval uses query expansion, lexical overlap,
   configured embeddings, and reciprocal-rank fusion. Postgres deployments use
   full-text search and pgvector when available, then keep JSON/Python vector
   scoring as a fallback.
2. Optional second-stage reranking uses a SentenceTransformers CrossEncoder over
   only the top candidate set. This follows the standard retrieve-then-rerank
   pattern: the first stage is broad and efficient; the reranker is slower but
   can make better pairwise relevance decisions for the final list.
3. Source-aware MMR selection chooses the final `top_k` hits from the ranked
   candidate list. It keeps relevance as the primary signal while penalizing
   redundant chunks from sources already selected, which reduces repeated
   same-document evidence in operator review. `RetrievalPackage.diversity`
   records `selected_hits` so operators can inspect the relevance/redundancy
   tradeoff for each selected item; the same payload is mirrored into
   `handoff_context.diversity` for assistant and agent compatibility.
4. The final package preserves `lexical_score`, `vector_score`, `rerank_score`,
   `score_components`, `source_locator.ranking_boosts`, and
   `source_locator.ranking_boost_rules` per hit so workflow explanations can
   show why evidence was selected instead of hiding relevance behind a single
   opaque score.
5. The trace preserves `fusion_diagnostics` so API clients and the Retrieval UI
   can explain lexical/vector agreement without recomputing ranking internals.

Second-stage reranking is disabled by default because it downloads a model and
adds inference latency. Enable it only in environments that intentionally
provide local model dependencies and CPU/GPU capacity.

## Configuration

```text
OJT_STORAGE_BACKEND=postgres
OJT_DATABASE_URL=postgresql://ojtflow:ojtflow@localhost:5432/ojtflow
OJT_KNOWLEDGE_DIR=knowledge
OJT_EMBEDDING_PROVIDER=deterministic
OJT_EMBEDDING_MODEL=deterministic-hash-v0
OJT_EMBEDDING_DIMENSIONS=64
```

`OJT_EMBEDDING_PROVIDER` supports `deterministic`, `openai`, and `huggingface`.
Deterministic mode is for tests and offline demos only. OpenAI mode uses the
Embeddings API and reads `OJT_OPENAI_API_KEY`, falling back to `OPENAI_API_KEY`
when the project-specific variable is not set. Hugging Face mode uses
SentenceTransformers locally and can run on GPU with `OJT_HF_EMBEDDING_DEVICE=cuda`.

Recommended OpenAI semantic retrieval settings:

```text
OJT_EMBEDDING_PROVIDER=openai
OJT_EMBEDDING_MODEL=text-embedding-3-small
OJT_EMBEDDING_DIMENSIONS=384
OJT_OPENAI_API_KEY=...
```

`text-embedding-3-small` is used with 384 dimensions to match the local
`embedding vector(384)` schema and keep storage/query cost lower than the
model's default 1536-dimensional output. Both provider and model are validated
during settings load so runtime diagnostics cannot claim a provider that the
retrieval adapter is not actually using.

Recommended local GPU retrieval settings:

```text
OJT_EMBEDDING_PROVIDER=huggingface
OJT_EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
OJT_EMBEDDING_DIMENSIONS=384
OJT_HF_EMBEDDING_DEVICE=cuda
OJT_HF_EMBEDDING_BATCH_SIZE=32
OJT_HF_EMBEDDING_CACHE_DIR=var/huggingface
```

Install local embedding dependencies with:

```bash
uv pip install -e '.[embeddings-local]'
```

For Docker runs that need local Hugging Face embeddings or CrossEncoder
reranking inside the API container, build with:

```bash
OJT_PYTHON_EXTRAS=parsing,embeddings-local docker compose build api
```

Recommended local CrossEncoder reranking settings:

```text
OJT_RERANK_PROVIDER=huggingface
OJT_RERANK_MODEL=BAAI/bge-reranker-base
OJT_RERANK_DEVICE=cuda
OJT_RERANK_BATCH_SIZE=16
OJT_RERANK_CANDIDATE_LIMIT=20
OJT_RERANK_SCORE_WEIGHT=0.08
OJT_RETRIEVAL_DIVERSITY_ENABLED=true
OJT_RETRIEVAL_DIVERSITY_LAMBDA=0.72
OJT_RETRIEVAL_HNSW_EF_SEARCH=100
OJT_RETRIEVAL_FRAMEWORK=custom
OJT_RETRIEVAL_CANDIDATE_MULTIPLIER=4
OJT_RETRIEVAL_MIN_CANDIDATES=12
OJT_RETRIEVAL_VECTOR_WEIGHT=0.62
OJT_RETRIEVAL_BM25_WEIGHT=0.38
OJT_RUNTIME_SETTINGS_PATH=var/runtime_settings.json
```

`OJT_RERANK_PROVIDER` supports `none` and `huggingface`. The Hugging Face
adapter uses SentenceTransformers `CrossEncoder.predict` with query/document
pairs. `OJT_RERANK_CANDIDATE_LIMIT` keeps reranking bounded to the strongest
first-stage candidates, and `OJT_RERANK_SCORE_WEIGHT` controls how much the
external rerank score can refine the existing fusion score. Invalid provider,
device, batch, candidate-limit, or score-weight values fail settings load.

`OJT_RETRIEVAL_DIVERSITY_ENABLED` controls final source-aware MMR selection.
`OJT_RETRIEVAL_DIVERSITY_LAMBDA` is a probability-like value from `0` to `1`;
higher values favor relevance, lower values favor novelty. The default `0.72`
keeps relevance dominant while reducing duplicate-source evidence in the final
operator-visible list. Retrieval packages report the selection mode, lambda,
candidate source count, selected source count, and duplicate selected source
count under the first-class `diversity` field and mirror that data to
`handoff_context.diversity`.

Direct retrieval requests can override diversity for a specific query through
allowlisted filters:

```json
{
  "filters": {
    "diversity_enabled": true,
    "diversity_lambda": 0.35
  }
}
```

Use lower lambda values for broad review routes where source spread matters
more, and higher values for exact-source lookups where rank confidence matters
more.

`OJT_RETRIEVAL_HNSW_EF_SEARCH` controls the per-query pgvector HNSW search
candidate depth for the Postgres vector candidate pool. pgvector defaults this
value to 40; OJTFlow defaults to 100 for healthcare evidence retrieval where
missing a relevant source is usually worse than a small latency increase. The
adapter sets it transaction-locally before vector candidate retrieval, so the
setting affects only the current search query and does not leak into other
database sessions. Increase it when recall is weak; lower it when latency is the
stricter constraint.

Postgres reindexing stamps each chunk with an `embedding_generation_id` derived
from the configured embedding provider, model, and dimension count. Retrieval
checks candidate chunk metadata against the current generation ID and warns the
operator to reindex when stored vectors were produced by an older provider/model
configuration. This prevents silent use of stale vectors after switching between
deterministic, OpenAI, and local Hugging Face embedding modes.

Local trusted corpus files are read from `OJT_RETRIEVAL_CORPUS_DIRS`, defaulting
to `knowledge/corpus`. Supported corpus file extensions are `.md`, `.txt`,
`.json`, `.yaml`, `.yml`, and `.csv`. Reindexing is explicit through
`POST /api/v1/retrieval/reindex` so operators can control when model downloads,
embedding computation, and database vector updates happen.

`OJT_KNOWLEDGE_DIR` points at the trusted healthcare knowledge inventory used to
seed retrieval sources and schema evidence. Relative paths resolve from the
project root in local development; container deployments set an absolute path.
Named schema requests are strict. Workflow, validation, and direct retrieval
callers must use a profile returned by `GET /api/v1/schemas`, or set
`schema_id` to `null` for explicit no-schema processing. Missing requested
schemas fail before retrieval so the evidence package cannot imply a weaker
validation contract than the caller requested.

## Verification

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest
python scripts/evaluate-retrieval.py
cd frontend && npm run build
```

For Postgres:

```bash
docker compose up --build
```

The Docker image uses `pgvector/pgvector:pg16` so the optional vector column and
HNSW index are available. If pgvector is unavailable in a different deployment,
the migration keeps lexical retrieval and JSON embeddings operational.

## Durable Relevance Judgments

Operators can label retrieved evidence from the Retrieval console. The frontend
persists those labels through `PUT /api/v1/retrieval/judgments`, lists them with
`GET /api/v1/retrieval/judgments?query=...`, and removes them with
`DELETE /api/v1/retrieval/judgments/{judgment_id}`. Judgments are scoped to the
authenticated `owner_user_id` and keyed by `(owner_user_id, query_hash,
evidence_id)`, so rerunning the same query can hydrate prior labels for the
same evidence even when browser-local run IDs change.
Supported labels are `relevant`, `partial`, `irrelevant`, `unsafe`, `stale`,
and `source_policy_blocked`; legacy `not_relevant` remains accepted for old
records and API clients. `relevant` maps to rating `3`, `partial` maps to
rating `1`, and all non-positive labels map to rating `0`. `unsafe`, `stale`,
and `source_policy_blocked` are reviewer workflow labels: they are not positive
relevance signals and should be used when evidence is risky, outdated, or
blocked by source governance even if it textually matches the query.
`GET /api/v1/retrieval/judgments/summary` returns the same stored label
inventory as aggregate counts, average rating, latest update time, and sample
limit for the active user/query.
`POST /api/v1/retrieval/judgments/evaluate` accepts the active query, ranked
evidence IDs, and optional cutoff, then scores that ranked list against stored
judgments. It returns Coverage@k, HitRate@k, Precision@k, judged precision,
MAP@k, MRR@k, nDCG@k, per-value counts including unsafe/stale/policy-blocked
labels, contributing judgment IDs, unjudged evidence IDs,
`evaluation_readiness`, and policy-driven `recommendations[]`. The recommendation rules
are loaded from `knowledge/retrieval/evaluation_policy.json` by default and can
be overridden with `OJT_RETRIEVAL_EVALUATION_POLICY_PATH`. This is the runtime
counterpart to the offline evaluation harness: it makes current operator
searches measurable and actionable without copying labels into fixture files.
Postgres deployments use migration `020_retrieval_judgment_policy_labels.sql`
to expand the durable value constraint. SQLite local stores rebuild the
judgment table in place during startup when they detect the older constraint.
Reviewer labels and weak evaluation results also feed an active-learning queue.
`PUT /api/v1/retrieval/judgments` enqueues non-relevant and partial labels as
benchmark candidates, while `POST /api/v1/retrieval/judgments/evaluate`
enqueues low-confidence ranked results when coverage or positive-hit metrics are
weak. Queue items are deduped by `(owner_user_id, candidate_key)` so repeated
searches update the same candidate instead of inflating the backlog.
`GET /api/v1/retrieval/active-learning/candidates` lists the queue,
`GET /api/v1/retrieval/active-learning/summary` returns backlog counts, and
`PATCH /api/v1/retrieval/active-learning/candidates/{candidate_id}` lets a
reviewer accept, reject, promote, or archive a candidate. Postgres deployments
use migration `021_retrieval_active_learning_candidates.sql`; SQLite creates the
same table during local startup.
`evaluation_readiness` states whether the current labels are unlabeled, low
confidence, usable with gaps, or ready for tuning so sparse label sets do not
look like reliable ranking quality measurements.
The Retrieval UI can copy a `retrieval_judgment_evaluation` JSON report with
server metrics, local in-session metrics, stored-label summary,
recommendations, ranked evidence IDs, unjudged IDs, and contributing judgment
IDs for offline relevance-tuning notes.
The Retrieval cockpit also renders and exports a top-level
`readiness_checklist` that consolidates query health, required evidence-class
coverage, source spread, and governance/readiness action state. It is designed
as the first operator scan before deeper ranking, trace, or evidence-card
inspection.
Individual evidence-hit cards also export a `usability_summary` in copied
`retrieval_evidence_hit` reports. It is derived from matched terms, provenance,
concept/aspect grounding, evidence-bucket membership, and persisted judgment
state; it is an operator evidence-review aid, not a clinical conclusion.
The copied evaluation report also includes the active `query_profile`, and the
copied run-comparison report includes active/baseline query-profile summaries
so route or retrieval-mode changes remain visible during tuning.
Recent-run rows also show a compact run scope generated from the submitted
payload and returned package: quality status/score, coverage-gap count,
grounded concept count, search-aspect count, and active schema, format,
resource, domain, standard, source, trust, and field filters. When
`quality_summary.top_action` is present, the row shows it as the next readiness
action.
Copied run-comparison reports include active/baseline `run_id` and server
`search_signature` values so offline relevance notes can be tied back to the
exact normalized retrieval request.
The same reports include active/baseline `quality_summary` values and a
`deltas.quality_score` field, and the UI comparison diagnosis flags
`quality_summary_changed` when readiness status, score, or top action changes.
Copied comparison reports also include a top-level `summary` object with
stable/changed status, top diagnosis, quality before/after state, evidence
churn counts, retrieval deltas, changed dimensions, and judgment count so
offline relevance notes can start with a compact review summary before detailed
payload sections. The summary includes top-source before/after stability so the
same quick signal shown in the UI is available in copied reports.
Reports also include `recommended_actions[]`, derived from
the active quality top action, coverage diagnostics, query-profile/rule-pack
changes, quality-signal changes, evidence churn, and missing judgments. Each
recommended action includes priority, severity, source, action, and reason; the
list is sorted by priority before it is rendered or copied. Reports and the UI
also expose `recommended_action_summary` with action count, highest priority,
highest severity, source count, and source list. The comparison panel renders
the source list as compact chips with per-source action counts above detailed
action rows. It also renders an at-a-glance row for readiness status movement
with score delta, highest action priority, evidence overlap, result churn, and
top-source stability before detailed comparison sections. The
Retrieval UI renders the same recommended actions in the comparison panel so
operators do not need to copy JSON before seeing the next review steps.
Before the dense comparison tables, the UI also renders an operator summary
derived from the same typed comparison object: headline, evidence/quality/source
spread bullets, and review-focus chips. Copied comparison reports include this
as `operator_summary` so offline tuning notes remain readable without opening
the detailed metrics tree first.
The at-a-glance row and copied comparison report also include source-diversity
comparison: selected-source delta, duplicate selected-source delta,
candidate-source delta, selected-source overlap, added/removed/retained source
IDs, selection mode, and lambda. Duplicate-source regressions and diversity
policy changes are surfaced as recommended actions because healthcare evidence
review should not silently collapse to one source family after relevance tuning.
The copied run-comparison report also includes a compact `diagnosis[]` list
that names likely change drivers such as query-profile changes, rule-pack
changes, query-aspect plan changes, quality-signal changes, facet drift,
top-source changes, rank movement, and evidence churn. The UI comparison card
renders that diagnosis before the detailed comparison sections, then renders
the active/baseline profile comparison directly, including stable/changed
status. It also compares active-vs-baseline `query_aspects`, including added,
removed, and retained aspects, so relevance tuning can separate query-planning
coverage drift from ranking drift. The copied run-comparison report and UI
also compare coverage diagnostics, including improved, regressed, added,
removed, and retained standard/aspect coverage items.
Recent-run summaries include `correctiveActionSummary`, derived from backend
`recommended_action_summary` when present, with action count, highest priority,
highest severity, top action title, apply-filter count, broaden-query count,
and per-action-type counts. This summary is visible in recent-run rows and is
included in active/baseline copied comparison summaries. Recent-run rows render
the per-action-type counts as compact chips so operators can quickly see
whether a search needs filtering, broadening, review, or another remediation
class before opening detailed corrective-action rows. They also render a
plain-language `Run remediation` summary derived from the same package data, so
history scanability does not require opening trace JSON. Copied cockpit and
run-comparison JSON reports include the same remediation summary, including
active/baseline summaries for comparisons, so offline audit notes stay aligned
with the operator-facing history row. New payloads should use backend
`RetrievalPackage.remediation_summary`; browser fallback derivation exists only
for older packages.
It compares added, removed, and retained `quality_signals` so package
readiness regressions are visible in the same comparison view.
It also compares selected-hit facets for source type, clinical domain,
standard system, and trust level so coverage drift is visible alongside rank
movement.
Retrieval packages also copy sanitized active rule-pack metadata into
`handoff_context.retrieval_rule_packs`, including pack name, status, source,
environment variable, rule count, version, and content hash. The copied
`retrieval_judgment_evaluation` report includes those fingerprints so offline
relevance notes can be tied back to the exact query-expansion, diagnostic,
ranking, evaluation, and search-hint rule data active during the run.

Each durable judgment stores:

- query text plus SHA-256 query hash.
- evidence ID and optional source ID/type/version.
- UI value: `relevant`, `partial`, or `not_relevant`.
- graded rating from 0 to 3 for evaluation handoff.
- optional browser run ID, search signature, and metadata.

The current UI uses durable judgments for operator continuity and comparison
reports. The offline fixture evaluator remains file-backed for release checks;
a later evaluation dashboard can promote stored production judgments into
curated eval sets once review and governance rules are defined.
Recent-run comparison also includes active-vs-baseline rule-pack fingerprint
deltas. A relevance run should therefore be interpreted with both its request
payload and its active rule-pack inventory; if either changed, ranking movement
may be caused by configuration or data changes rather than the query alone.

## Evaluation Harness

The retrieval module includes a deterministic offline eval runner:

```bash
python scripts/evaluate-retrieval.py
python scripts/evaluate-retrieval.py --json
```

Cases live in `tests/fixtures/retrieval_eval_cases.json`. Each case defines a
query, optional schema/fields/resource context, `top_k`, filters, and expected
source IDs or graded source-level `judgments`. Legacy `expected_source_ids`
are treated as binary relevant judgments; new cases should prefer explicit
ratings from 0 to 3 so search tuning can measure rank quality instead of only
presence/absence. The runner evaluates the static trusted knowledge repository
and reports:

- hit@k: whether at least one expected source appears in the top `k`.
- coverage@k: fraction of returned hits that have an explicit judgment.
- recall@k: expected source coverage in the returned hits.
- precision@k: fraction of returned hits with a non-zero judgment.
- MAP@k: average precision across positively judged sources.
- MRR@k: reciprocal rank of the first positively judged returned source.
- NDCG@k: graded ranking quality against the ideal judged-source order.
- reciprocal rank: rank-aware score for the first expected source.
- selected source count: source diversity after final selection.
- source diversity@k: unique selected source ratio across the returned hits.
- unsupported-claim rate: unsupported rows in the evidence support matrix divided
  by all support rows.

The eval runner reads selected-source metrics from the first-class
`RetrievalPackage.diversity` contract and falls back to
`handoff_context.diversity` only for older packages. Unsupported-claim metrics
come from `RetrievalPackage.support_matrix`, which keeps evaluation aligned
with guarded answer synthesis.

The current fixture covers lab validation, FHIR Observation mapping, UCUM unit
checks, LOINC grounding, PHI review, prompt-injection review, RxNorm grounding,
diagnosis terminology, PubMed/MeSH routing, ClinicalTrials.gov routing, and
openFDA routing. The scheduled GitHub Actions workflow
`.github/workflows/retrieval-evaluation.yml` runs the same evaluator nightly and
uploads `retrieval-evaluation-summary.json` for trend review.

The release check runs this eval before Docker/E2E. The fixture set is small on
purpose: it is a smoke benchmark for healthcare grounding regressions, not a
replacement for a larger curated clinical retrieval benchmark. Add cases when
new standards, corpora, or workflow domains are added.

Metric choices follow standard ranked-retrieval evaluation practice:
coverage, precision/recall at a cutoff, MAP, NDCG, and reciprocal rank are the
core signals for whether known relevant evidence is retrieved early enough and
ordered well enough for a user or agent to trust the workflow. References:
OpenSearch Search Relevance Workbench pointwise evaluation
(`https://docs.opensearch.org/latest/search-plugins/search-relevance/evaluate-search-quality/`),
RAGAS retrieval metrics
(`https://docs.ragas.io/en/v0.3.7/concepts/metrics/available_metrics/`),
Stanford IR ranked retrieval evaluation
(`https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-ranked-retrieval-results-1.html`),
and NIST `trec_eval` (`https://github.com/usnistgov/trec_eval`).
