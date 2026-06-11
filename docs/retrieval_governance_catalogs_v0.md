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

## Verification

Run:

```bash
python -m pytest tests/test_api.py::test_openapi_documents_contract_models tests/test_api.py::test_authentication_required_for_protected_routes tests/test_api.py::test_retrieval_sources_presets_and_search_options_are_data_driven -q
```

The tests verify OpenAPI response models, authentication boundaries, and that
catalog data loads from `knowledge/`.

Additional catalog consistency checks verify that every external connector in
`knowledge/source_catalog/external_connector_registry.json` has a matching
retrieval corpus adapter and source trust policy.
