# Month 7 Analytics And External Data Workflows v0

This pass implements the Month 7 analytics and external-data foundation for
OJTFlow. It is deliberately a governed preview layer, not a silent production
ETL engine.

## Scope

Implemented backlog items:

- F146 OMOP mapping design for `person`, `observation`, `measurement`,
  `condition_occurrence`, `drug_exposure`, `visit_occurrence`, and `note`.
- F147 OMOP vocabulary candidate contract for linking FHIR-like resources to
  release-specific standard concept IDs.
- F148 OMOP export preview with row counts, concept coverage, unmapped fields,
  and data-quality warnings.
- F149 OHDSI Data Quality Dashboard compatibility notes and integration path.
- F150 Cohort/research workflow concept separated from clinical decision support.
- F151 External source connector registry with auth, rate-limit, license, and
  update cadence metadata.
- F152 External API cache metadata contract with source release/version and
  invalidation policy.
- F153 Source ingestion approval workflow before fetched documents become
  searchable.
- F154 Transparent external-link launchers for PubMed, ClinicalTrials.gov,
  openFDA, LOINC, UCUM, RxNav, and FHIR docs.
- F155 Provenance-preserving ETL export package for downstream analytics teams.

## Data-Driven Catalogs

The feature is configured through trusted knowledge files:

- `knowledge/analytics/omop_mapping_profile.json`
- `knowledge/analytics/omop_vocabulary_candidates.json`
- `knowledge/analytics/data_quality_dashboard_compatibility.json`
- `knowledge/analytics/cohort_research_workflow.json`
- `knowledge/source_catalog/external_connector_registry.json`
- `knowledge/source_catalog/external_api_cache_policy.json`
- `knowledge/source_catalog/source_ingestion_approval_policy.json`
- `knowledge/source_catalog/external_link_launchers.json`

The backend validates these files through Pydantic contracts before exposing
them. This keeps mappings, connector rules, cache metadata, and link templates
out of application logic.

## OMOP Preview Design

The OMOP preview starts from a reviewed or review-pending `ClinicalPackage`.
It reads FHIR-like resource records and applies catalog row rules:

- `Patient` -> `person`
- numeric `Observation.valueQuantity` -> `measurement`
- non-numeric `Observation` -> `observation`
- `Condition` -> `condition_occurrence`
- medication resources -> `drug_exposure`
- `Encounter` -> `visit_occurrence`
- `DocumentReference` and `DiagnosticReport` content refs -> `note`

The preview reports:

- row counts by target table;
- mapped field counts;
- required unmapped fields;
- vocabulary candidate count;
- standard concept coverage count and ratio;
- review and data-quality warnings.

The preview does not assign person IDs, standard concept IDs, or production
foreign keys. OMOP concept IDs are release-specific and must come from the
deployed OMOP vocabulary release after review.

## DQD Compatibility

The DQD compatibility catalog explains what OJTFlow can prepare before a real
OHDSI Data Quality Dashboard run:

- table count previews;
- required-field warnings;
- concept candidate coverage;
- provenance completeness signals.

OJTFlow does not replace DQD. The intended path is:

1. Build and review an OMOP export preview.
2. Resolve vocabulary candidates against the target vocabulary release.
3. Load production staging/OMOP tables.
4. Run OHDSI DQD against the target database.
5. Import DQD JSON as evidence and block downstream use on critical failures.

## External Source Governance

The external connector registry describes trusted source boundaries for:

- PubMed / NCBI E-utilities;
- ClinicalTrials.gov;
- openFDA;
- LOINC;
- UCUM;
- RxNav / RxNorm;
- HL7 FHIR docs.

Each connector declares auth requirements, rate-limit policy, license notes,
update cadence, allowed use, prohibited use, cache policy, and ingestion
approval requirements.

The link-launch endpoint only builds transparent URLs. It does not fetch,
cache, ingest, or index external content. Automated fetchers must enforce:

- external provider PHI policy;
- connector registry rules;
- cache metadata;
- source ingestion approval;
- audit logging.

## Source Ingestion Approval

Fetched or externally discovered documents start as candidates. They become
searchable only when the approval decision reaches `approved_searchable`.

The approval preview checks:

- connector registration;
- source URL and release/version metadata;
- license acceptance;
- PHI/sensitive-query status;
- data-steward approval.

This separates source discovery from retrieval ingestion and prevents newly
fetched documents from silently entering the trusted evidence corpus.

## ETL Export Manifest

The ETL export package includes:

- clinical package hash;
- OMOP preview;
- resource manifest with hashes;
- source refs from field provenance;
- provenance record count;
- audit refs;
- optional included resources.

The manifest is designed for downstream analytics teams that need reproducible
inputs and governance warnings. It is not a production OMOP database load.

## API Surface

All routes are under `/api/v1` and use the standard response envelope:

- `GET /api/v1/interoperability/analytics/omop/mapping-profile`
- `POST /api/v1/interoperability/analytics/omop/preview`
- `GET /api/v1/interoperability/analytics/omop/dqd-compatibility`
- `GET /api/v1/interoperability/analytics/cohort-research-workflow`
- `GET /api/v1/interoperability/external/connectors`
- `GET /api/v1/interoperability/external/cache-policy`
- `POST /api/v1/interoperability/external/cache/metadata`
- `GET /api/v1/interoperability/external/ingestion-approval-policy`
- `POST /api/v1/interoperability/external/ingestion/approval-preview`
- `GET /api/v1/interoperability/external/link-launchers`
- `POST /api/v1/interoperability/external/link-launch`
- `POST /api/v1/interoperability/export/etl-package`

## Standards And Primary Sources

- OHDSI OMOP Common Data Model: https://ohdsi.github.io/CommonDataModel/
- OHDSI Data Quality Dashboard: https://github.com/OHDSI/DataQualityDashboard
- HL7 FHIR: https://hl7.org/fhir/
- HL7 FHIR Bulk Data / NDJSON: https://hl7.org/fhir/uv/bulkdata/
- PubMed / NCBI E-utilities: https://www.ncbi.nlm.nih.gov/books/NBK25501/
- ClinicalTrials.gov API: https://clinicaltrials.gov/data-api/about-api
- openFDA APIs: https://open.fda.gov/apis/
- LOINC: https://loinc.org/
- UCUM service: https://ucum.nlm.nih.gov/ucum-service.html
- RxNav / RxNorm APIs: https://lhncbc.nlm.nih.gov/RxNav/APIs/

## Verification

Run focused verification:

```bash
OJT_STORAGE_BACKEND=memory PYTHONPATH=src pytest -q \
  tests/test_analytics_external.py \
  tests/test_api.py::test_api_contract_doc_covers_current_route_surface \
  tests/test_api.py::test_api_v1_route_handlers_use_response_envelopes \
  tests/test_api.py::test_private_api_routes_have_auth_dependency

PYTHONPATH=src python -m py_compile \
  src/ojtflow/core/contracts/analytics.py \
  src/ojtflow/interoperability/analytics.py \
  src/ojtflow/interfaces/api/routes/interoperability.py \
  src/ojtflow/interfaces/api/schemas.py
```
