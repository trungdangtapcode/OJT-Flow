# Medical Search Playbook

This playbook defines the retrieval behavior OJTFlow should prefer for
healthcare and medicine workflows. It draws from practical RAG patterns:
hybrid retrieval, query transformation, metadata-aware self-query, reranking,
facet diagnostics, and coverage checks. The goal is evidence grounding, not
autonomous clinical decision-making.

## Retrieval Stack

Use a layered search stack:

1. Query analysis detects clinical concepts, standards, data format, schema, and
   safety context.
2. Controlled-vocabulary candidates are loaded from local seed data and later
   from official terminology adapters.
3. Query variants expand abbreviations and standard terms without changing user
   intent.
4. Metadata filters are suggested and shown to the operator; they are not
   silently applied.
5. Hybrid retrieval combines lexical and vector search.
6. Reranking refines top candidates when a reranker is configured.
7. Source-aware diversity prevents one document family from dominating the final
   context.
8. Coverage diagnostics report missing expected standards such as FHIR, LOINC,
   UCUM, RxNorm, OMOP, or MeSH.

## Medical Query Patterns

Laboratory query:

- Example: `serum glucose missing unit FHIR Observation`
- Expected standards: FHIR, LOINC, UCUM.
- Useful evidence: lab schema, LOINC concept, UCUM unit policy, FHIR
  Observation search parameters, human review triggers.

Medication query:

- Example: `metformin dose RxNorm`
- Expected standards: RxNorm and FHIR when resource context is present.
- Useful evidence: RxNorm candidate, MedicationRequest search parameters,
  public label or adverse-event datasets when safety context is explicit.

Literature query:

- Example: `PubMed systematic review HbA1c units`
- Expected standards: MeSH and PubMed field behavior.
- Useful evidence: MeSH descriptor candidates, title/abstract term groups,
  publication type filters, and warning text about Automatic Term Mapping.

Analytics query:

- Example: `OMOP analytics export lab observations`
- Expected standards: OMOP plus source standards such as FHIR, LOINC, UCUM.
- Useful evidence: source data validation, mapping confidence, and lossy
  transformation warnings.

## Dataset Use

Do:

- Use official public APIs and downloads when available.
- Cache normalized terminology responses with source URLs and retrieval time.
- Keep bulk source datasets outside git and store only curated seed snapshots or
  reproducible source catalogs in `knowledge/`.
- Separate patient-facing education, clinical terminology, regulatory data, and
  interoperability standards in metadata.

Do not:

- Commit licensed bulk terminology files directly.
- Treat literature or regulatory search as a clinical recommendation.
- Convert units or assign medical codes silently.
- Hide query rewrites, source filters, or missing coverage warnings.

## Enterprise Expansion Path

The seed knowledge should grow through adapters:

- MeSH RDF or REST snapshots for literature subject headings.
- RxNav API cache for RxNorm concepts and drug products.
- LOINC licensed download or terminology service adapter for lab concepts.
- FHIR package loader for resource definitions, profiles, and SearchParameters.
- openFDA adapter for public label and adverse-event evidence.
- ClinicalTrials.gov adapter for study records and eligibility criteria.

Each adapter should produce the same retrieval artifacts: source metadata,
chunks, concept candidates, evidence, coverage diagnostics, and audit events.
