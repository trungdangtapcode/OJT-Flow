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
The LlamaIndex adapter builds a reusable in-process index for the current
trusted chunk generation and invalidates it on `reindex()`. Retrieval still
applies OJTFlow metadata filters before returning evidence. For framework
retrieval, those filters are also passed into LlamaIndex vector/BM25 retrievers
before ranking so healthcare metadata constraints such as `standard_system`,
`clinical_domain`, `source_type`, and `trust_level` shape the candidate pool
instead of being only a post-hoc UI filter. The trace reports
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
2. Candidate chunks are filtered by trust level, clinical domain, standard system, or source type.
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
10. Final selected hits are summarized into result facets by source type,
   clinical domain, standard system, and trust level.
11. Trace safety flags mark prompt-injection-like query text and sensitive field
   context without blocking retrieval.

The retrieval package now includes a `graph_context` handoff that extracts
entities and evidence triples from the retrieved claims. This is a
GraphRAG-lite context for validation/explanation workflows, not diagnosis,
treatment, triage, or medication advice.

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
- `knowledge/retrieval/ranking_boost_rules.json`: deterministic ranking boost
  rules for schema, field, trust-level, source-type, concept, and healthcare
  standard matches.
- `knowledge/retrieval/evaluation_policy.json`: runtime retrieval evaluation
  policy that converts durable judgment metrics into operator-facing tuning
  recommendations.
- `knowledge/retrieval/search_hint_targets.json`: target metadata for
  external medical search hints, including operator rationale and warnings.
- `knowledge/terminologies/fhir_search_parameters.json`: FHIR R4 search
  parameter templates for resource-level search hints.
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

Filter suggestions are a deterministic self-query feature: they recommend
metadata filters such as `clinical_domain=laboratory` or
`standard_system=UCUM`, but do not apply them silently. The analyzer loads those
rules from `knowledge/retrieval/filter_suggestion_rules.json`; each rule
declares a `rule_id`, filter field, filter value, reason, confidence, and match
criteria over detected concepts, standards, query-expansion rule IDs, and
controlled-vocabulary candidate metadata. Code still allowlists supported
filter fields (`clinical_domain`, `standard_system`, `source_type`, and
`trust_level`) before accepting registry rules.
`OJT_FILTER_SUGGESTION_RULES_PATH` can point the runtime to a
deployment-specific rule pack.

The Retrieval console shows confidence and whether each suggestion is already
applied. Supported suggestions can be applied explicitly from the trace panel,
which updates the query-builder filter state and reruns the search through the
same typed `/retrieval/search` request path.

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
with the standards inferred from query content. Warning diagnostics are copied
into `RetrievalTrace.warnings` for audit and UI visibility.

Ranking boost rules are loaded from `knowledge/retrieval/ranking_boost_rules.json`,
not hardcoded into the ranking engine. Each rule defines `rule_id`, `weight`,
`reason`, a required `match` condition, and optional `any_of` alternatives.
Supported match operators are intentionally narrow: schema ID in source ID,
requested fields in matched terms, detected format presence, applied
clinical-domain filter match, chunk trust level, source type, standard system,
matched query terms, detected concepts, and query-expansion rule IDs.
`OJT_RANKING_BOOST_RULES_PATH` can point the runtime to a deployment-specific
ranking policy. Applied boosts are copied into each hit's
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

Query analysis also emits `query_variant_details` alongside the legacy
`query_variants` list. Each detail records the variant text, source, reason,
and metadata such as matched rule IDs, schema ID, detected format, or controlled
vocabulary concept. The trace copies those details to
`trace.query_variant_details` so operator review can inspect query rewrites
without guessing why a variant was used.

Source-aware diversity metadata includes `selected_hits`, one row per final hit.
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

Research basis:

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

- `nodes`: query, evidence, healthcare standard, clinical concept, and data-field nodes.
- `edges`: auditable relationships such as `supports`, `mentions_field`, and
  `requests_resource`.
- `triples`: source/evidence triples for downstream Graph-NER/RAG handoff.

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
   same-document evidence in operator review. The diversity handoff context
   records `selected_hits` so operators can inspect the relevance/redundancy
   tradeoff for each selected item.
4. The final package preserves `lexical_score`, `vector_score`, `rerank_score`,
   `score_components`, `source_locator.ranking_boosts`, and
   `source_locator.ranking_boost_rules` per hit so workflow explanations can
   show why evidence was selected instead of hiding relevance behind a single
   opaque score.

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
count under `handoff_context.diversity`.

`OJT_RETRIEVAL_HNSW_EF_SEARCH` controls the per-query pgvector HNSW search
candidate depth for the Postgres vector candidate pool. pgvector defaults this
value to 40; OJTFlow defaults to 100 for healthcare evidence retrieval where
missing a relevant source is usually worse than a small latency increase. The
adapter sets it transaction-locally before vector candidate retrieval, so the
setting affects only the current search query and does not leak into other
database sessions. Increase it when recall is weak; lower it when latency is the
stricter constraint.

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
`GET /api/v1/retrieval/judgments/summary` returns the same stored label
inventory as aggregate counts, average rating, latest update time, and sample
limit for the active user/query.
`POST /api/v1/retrieval/judgments/evaluate` accepts the active query, ranked
evidence IDs, and optional cutoff, then scores that ranked list against stored
judgments. It returns Coverage@k, HitRate@k, Precision@k, judged precision,
MAP@k, MRR@k, nDCG@k, per-value counts, contributing judgment IDs, unjudged
evidence IDs, and policy-driven `recommendations[]`. The recommendation rules
are loaded from `knowledge/retrieval/evaluation_policy.json` by default and can
be overridden with `OJT_RETRIEVAL_EVALUATION_POLICY_PATH`. This is the runtime
counterpart to the offline evaluation harness: it makes current operator
searches measurable and actionable without copying labels into fixture files.

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
