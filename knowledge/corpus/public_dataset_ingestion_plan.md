# Public Healthcare Dataset Ingestion Plan

This plan records which external datasets should become first-class retrieval
adapters as OJTFlow moves from seed knowledge to an enterprise knowledge base.

## Priority 1: Terminology

MeSH:

- Source: NLM MeSH XML/RDF download and MeSH RDF REST API.
- Retrieval value: controlled subject headings for PubMed/MEDLINE search.
- Adapter output: descriptor chunks, entry terms, tree numbers, qualifiers,
  descriptor URLs, and version metadata.
- Storage: bulk files under ignored runtime storage; curated seeds in
  `knowledge/terminologies/`.

RxNorm:

- Source: NLM RxNav API and RxNorm distribution.
- Retrieval value: drug name and RxCUI normalization.
- Adapter output: ingredient, semantic clinical drug, branded drug, dose form,
  status, and remapping metadata.
- Storage: API cache with release metadata and concept status.

LOINC:

- Source: LOINC public pages, licensed download, or FHIR terminology service.
- Retrieval value: lab test identity and FHIR Observation coding.
- Adapter output: code, long common name, component, property, time, system,
  scale, method, example units, and source version.
- Storage: licensed bulk files outside git; curated seed concepts in
  `knowledge/terminologies/`.

UCUM:

- Source: UCUM specification and NLM UCUM service.
- Retrieval value: computable units and unit validation.
- Adapter output: unit code, display, dimension, synonym, canonical form, and
  conversion policy.
- Storage: curated common units plus validator adapter.

## Priority 2: Interoperability Standards

FHIR R4:

- Source: HL7 FHIR core package and resource profile JSON.
- Retrieval value: resource shape, SearchParameters, references, code fields,
  quantity fields, and capability templates.
- Adapter output: resource chunks, profile evidence, SearchParameter catalog,
  and graph handoff schema.

OMOP CDM:

- Source: OMOP CDM documentation and vocabulary references.
- Retrieval value: analytics export targets after source evidence is preserved.
- Adapter output: table/field mapping constraints, vocabulary dependencies, and
  lossy transformation warnings.

## Priority 3: Evidence And Regulatory Data

PubMed/MEDLINE:

- Source: NLM E-utilities and PubMed baseline/update files.
- Retrieval value: literature evidence and citation-aware explanation packages.
- Adapter output: title, abstract, PMID, journal, date, publication type, MeSH
  headings, and provenance.

ClinicalTrials.gov:

- Source: ClinicalTrials.gov API v2.
- Retrieval value: trial records, eligibility criteria, interventions, outcomes,
  and recruitment status.
- Adapter output: NCT ID, status, conditions, interventions, arms, outcomes,
  eligibility, sponsor, and timestamps.

openFDA:

- Source: openFDA APIs and endpoint downloads.
- Retrieval value: public drug labeling, recall, adverse-event, and NDC evidence.
- Adapter output: endpoint, product identifiers, sections, event counts, warning
  labels, and public-data limitations.

## Ingestion Controls

Every adapter must record:

- source authority
- source URL
- retrieval timestamp
- source version or release date when available
- license/access notes
- content hash
- adapter version
- chunking strategy
- PHI status
- clinical decision support limitation

Every adapter must avoid:

- storing secrets in source metadata
- silently mixing terminology versions
- changing clinical meaning without review
- treating public adverse-event counts as incidence rates
- presenting literature retrieval as medical advice
