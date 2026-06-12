# Retrieval Governance Catalogs v0

## Purpose

Month 4 retrieval work needs explicit governance before adding larger corpora,
more embedding modes, and GraphRAG behavior. OJTFlow now has two data-driven
catalogs under `knowledge/`:

- `knowledge/source_catalog/source_trust_policies.json`
- `knowledge/retrieval/strategy_catalog.json`

These files are loaded through API endpoints instead of hardcoded route logic.

## Source Trust Policies

`GET /api/v1/retrieval/source-policies`

The response describes source-level governance:

- authority and standard system
- clinical scope
- intended and prohibited use
- refresh cadence
- license/access constraints
- ingestion mode
- evidence tier
- whether reviewer approval is expected

Use this before ingesting or presenting a source as trusted evidence. The
catalog is intentionally separate from raw source inventory, because source
inventory says what exists while source policy says what it is allowed to be
used for.

The current policy catalog covers:

- FHIR R4 implementation evidence
- LOINC laboratory terminology candidates
- UCUM unit validation evidence
- RxNav/RxNorm medication terminology candidates
- PubMed/NCBI E-utilities literature metadata and abstracts where allowed
- ClinicalTrials.gov API v2 trial registry metadata
- openFDA regulatory labels, adverse-event context, recalls, and device records

External-source records remain governed until approved. PubMed, trial, and
regulatory data can support source-linked review and explanation, but must not
be represented as clinical advice or autonomous decision support.

## Strategy Catalog

`GET /api/v1/retrieval/strategies`

The response describes retrieval/RAG strategy presets:

- lexical-only
- vector-only
- hybrid RRF
- metadata-filtered
- high-recall review
- exact-source lookup

Each strategy declares status, technique family, intended use, avoid-when
guidance, query transformations, runtime requirements, compatible filters, and
risk controls.

This does not force every strategy through a separate runtime branch yet. It
creates an auditable contract for UI routing, evaluation, and future strategy
selection.

## Source Freshness Gate

`GET /api/v1/retrieval/freshness`

The freshness gate turns the source catalogs into an operational readiness
report. It combines:

- `knowledge/source_catalog/corpus_adapters.json`
- `knowledge/source_catalog/source_trust_policies.json`
- the generated local corpus manifest
- the currently indexed retrieval source inventory

The report scores each source as `ready`, `watch`, `needs_review`, or
`blocked`. It checks lifecycle state, reviewer state, indexing presence, trust
policy coverage, last observed fetch/snapshot time, refresh cadence, and
whether a configured external source has a governed local snapshot.

Each source also includes a separate `quality` object. This is not the same as
the freshness readiness state: readiness answers whether the source can be used
operationally, while quality answers how strong the medical evidence source is
after combining trust policy coverage, evidence tier, lifecycle state, reviewer
state, freshness status, source/index coverage, and license or use restrictions.
The scorer is data-driven by
`knowledge/retrieval/source_quality_policy.json`. Operators can tune thresholds
and rule deltas without changing Python code, then verify the effect through
`average_quality_score`, `low_quality_count`, `quality_review_count`, and each
source's applied `quality.signals[]`.

The gate does not fetch external sites. It is the control surface that tells an
operator which source should be refreshed, approved, indexed, or kept out of
retrieval before relying on medical evidence. The Retrieval page renders this
report in the `Source freshness gate` panel next to integrity and source
inventory.

## Corpus Ingestion Ledger

`GET /api/v1/retrieval/corpus/ledger`

The ledger is the chunk-level lineage layer for governed retrieval. The source
manifest describes source files; the ledger describes the exact chunks that were
made searchable from those files.

Each ledger record links:

- the stable corpus ingestion run ID
- the source manifest item ID
- the indexed chunk ID
- raw artifact hash and chunk content hash
- adapter ID and adapter catalog version
- reviewer decision and lifecycle state
- chunk profile, parser, source path, source URL, and character span

The retrieval index also carries the ledger record ID and ingestion run ID in
`KnowledgeChunk.metadata`, so search results, source inventories, and future
index manifests can trace evidence back to the governed ingestion input without
storing raw payloads in the ledger response.

The ledger intentionally does not block current indexing behavior by itself. If
a source is indexed while its reviewer state is `needs_review` or deprecated,
the record makes that visible through `index_decision`,
`approved_for_indexing`, and reviewer/lifecycle fields. Enforcement belongs in
source approval and production-mode policy gates.

## Retrieval Index Manifest

`GET /api/v1/retrieval/index-manifest`

The index manifest is the runtime counterpart to the corpus manifest and ledger.
It reports the currently active retrieval indexes:

- lexical index generation ID derived from chunk IDs, source versions, and
  content hashes
- vector embedding generation ID derived from provider, model, and dimensions
- stale vector chunk counts when stored chunk metadata does not match the active
  embedding generation
- corpus ingestion run IDs present in indexed chunks
- owner-scoped persisted Graph-NER graph counts and graph generation ID when
  graph persistence is configured

Use this endpoint before and after reindex jobs, embedding provider changes, or
corpus approval updates. It is intentionally admin-readable because it describes
runtime index state and source lineage, even though it does not expose raw
corpus text.

## Embedding Reindex Safety Workflow

`GET /api/v1/retrieval/embedding-reindex/dry-run`

`POST /api/v1/jobs/embedding-reindex`

Embedding reindexing is approval-gated because provider/model/dimension changes
can invalidate vector similarity behavior for every retrieval answer. The v0
workflow is:

1. Fetch the dry-run report with the intended `include_seeded` and
   `include_corpus` scope.
2. Inspect the current index manifest, stale-vector count, chunk/source counts,
   corpus ingestion run IDs, and warnings.
3. Submit the returned `approval_token` unchanged to
   `POST /api/v1/jobs/embedding-reindex`.
4. The backend validates that the token still matches the current dry-run
   payload before creating the job.
5. The sync runner writes a sanitized rollback marker under
   `var/repair_markers/embedding_reindex`, runs retrieval reindex, captures the
   after-manifest, and stores a post-run quality comparison on the job output.

The job output contains:

- dry-run report without the raw approval token
- rollback marker metadata and marker ref hash
- retrieval reindex output
- after-manifest
- quality comparison with chunk/source/stale-vector deltas

This is not automatic rollback. The marker records the pre-reindex manifest and
rollback instructions so operators can compare the active index against backups
or rerun the prior corpus/embedding configuration.

## Verification

Run:

```bash
PYTHONPATH=src python -m pytest tests/test_retrieval.py::test_retrieval_freshness_report_flags_governance_and_index_gaps tests/test_retrieval.py::test_medical_source_quality_policy_loads_from_trusted_data tests/test_retrieval.py::test_corpus_ingestion_ledger_links_chunks_to_source_run tests/test_retrieval.py::test_static_retrieval_index_manifest_reports_active_generations tests/test_retrieval.py::test_embedding_reindex_safety_report_marker_and_comparison tests/test_api.py::test_openapi_exposes_core_request_examples tests/test_api.py::test_api_routes_require_session_envelope tests/test_api.py::test_api_direct_convert_validate_fhir_ocr_and_error tests/test_api.py::test_embedding_reindex_job_requires_dry_run_approval -q
```

The tests verify OpenAPI response models, authentication boundaries, and that
catalog data loads from `knowledge/`. The freshness test verifies that source
readiness is computed from governance catalogs, corpus manifest data, and the
retrieval source inventory.

Additional catalog consistency checks verify that every external connector in
`knowledge/source_catalog/external_connector_registry.json` has a matching
retrieval corpus adapter and source trust policy.
