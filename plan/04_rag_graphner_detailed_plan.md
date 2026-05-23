# RAG, Graph-NER, and Representation Learning Detailed Plan

RAG and Graph-NER are the research backbone of OJTFlow, but they should be added after the core workflow is stable. Their job is to improve schema matching, transformation planning, medical terminology alignment, explanation faithfulness, and auditability.

## Retrieval Goal

Retrieve trusted project knowledge at the right time:

- schema documentation
- JSON Schema and Pydantic model descriptions
- CSV column definitions
- FHIR/OMOP/JP Core mapping notes
- transformation examples
- data dictionaries
- error library entries
- governance rules
- historical approved transformations

Retrieval output is evidence for planning and explanation. It is not a permission to mutate data.

## Knowledge Source Structure

```text
knowledge/
  schemas/
    lab_result_v1.schema.json
    fhir_observation_like_v1.md
  data_dictionaries/
    lab_fields.md
    patient_demographics.md
    jp_core_aliases.md
  transformation_examples/
    csv_lab_to_json_records.md
    fhir_observation_to_omop_measurement.md
  error_library/
    csv_malformed_rows.md
    missing_units.md
    prompt_injection_patterns.md
  governance/
    appi_sensitive_fields.md
    human_review_triggers.md
```

Each source should have metadata:

- source ID
- version
- trust level
- source type
- domain
- schema name
- fields
- language
- date
- owner

## Retrieval Pipeline

1. Ingest trusted documents.
2. Chunk by semantic boundaries.
3. Preserve source metadata.
4. Generate dense embeddings.
5. Build lexical index for exact field and code matches.
6. Store vectors in local FAISS or SQLite-backed files for MVP; design for pgvector/Qdrant later.
7. Build runtime query from user instruction, detected fields, schema candidates, validation issues, and target format.
8. Run metadata filters.
9. Retrieve top-k lexical and vector candidates.
10. Merge and deduplicate.
11. Optionally rerank.
12. Return evidence package with source IDs, scores, snippets, and confidence.

## Retrieval Result Contract

```json
{
  "retrieval_id": "ret_uuid",
  "query": "lab CSV missing unit validation",
  "mode": "hybrid",
  "filters": {
    "domain": "healthcare",
    "trust_level": "approved"
  },
  "results": [
    {
      "source_id": "schema:lab_result_v1",
      "chunk_id": "chunk_003",
      "score": 0.87,
      "source_type": "schema",
      "source_version": "1.0.0",
      "matched_fields": ["unit", "loinc_code"],
      "trust_level": "approved"
    }
  ],
  "confidence": "medium",
  "warnings": []
}
```

## Retrieval Ladder

Enable modules only when evaluation justifies them.

| Level | Method | Status |
| --- | --- | --- |
| 1 | Metadata filtering | Required |
| 2 | Lexical search for exact names, codes, fields | Required |
| 3 | Dense vector search | Required |
| 4 | Hybrid merge | Required |
| 5 | HyDE query expansion | Optional MVP+ |
| 6 | Cross-encoder or late-interaction reranking | Demo/research |
| 7 | Hierarchical retrieval | Stretch |
| 8 | GraphRAG local/global search | Stretch/research |
| 9 | GNN-based reranking | Future research |

## Graph-NER Goal

Graph-NER turns messy healthcare text, headers, schema paths, and extracted document fields into linked entities and relations.

Entity types:

- `PatientIdentifier`
- `Diagnosis`
- `Medication`
- `Procedure`
- `LabTest`
- `LabValue`
- `Unit`
- `Date`
- `Provider`
- `Department`
- `FHIRResource`
- `FHIRPath`
- `OMOPTable`
- `OMOPField`
- `JPCoreProfile`
- `SchemaField`
- `PHIField`
- `TransformationRule`
- `ValidationIssue`

Relation types:

- `HAS_VALUE`
- `HAS_UNIT`
- `OCCURRED_ON`
- `ALIAS_OF`
- `MAPS_TO`
- `HAS_FIELD`
- `VIOLATES`
- `VALIDATED_BY`
- `SUPPORTED_BY`
- `DERIVED_FROM`
- `APPROVED_BY`

## Graph-NER Output Contract

```json
{
  "entities": [
    {
      "entity_id": "ent_uuid",
      "text": "HbA1c",
      "type": "LabTest",
      "normalized_id": "LOINC:4548-4",
      "source_ref": "row:17,column:lab_name",
      "confidence": 0.92,
      "requires_review": false
    }
  ],
  "relations": [
    {
      "relation_id": "rel_uuid",
      "head": "LOINC:4548-4",
      "relation": "HAS_VALUE",
      "tail": "7.4 %",
      "evidence": "row:17",
      "confidence": 0.88
    }
  ],
  "graph_updates": ["node:LabTest", "edge:HAS_VALUE"],
  "requires_review": false
}
```

## Initial Graph Storage

Start simple:

- PostgreSQL-style tables in design
- SQLite tables for local
- NetworkX for experiments

Tables:

- `graph_nodes`
- `graph_edges`
- `entity_mentions`
- `normalization_candidates`
- `graph_snapshots`

Every node and edge must store:

- provenance
- confidence
- source ID
- version
- PHI risk level
- created workflow ID

## Graph Retrieval Modes

Local entity search:

- User asks about a field or schema.
- System retrieves exact entity node, aliases, field definitions, validation rules, and examples.

Schema matching:

- Input columns become candidate entities.
- Alias edges and data dictionaries suggest schema field matches.
- Low confidence triggers review.

Global summary:

- Later GraphRAG can summarize communities such as lab observations, medication mappings, or approval patterns.

## Self-Supervised Representation Learning

SSL is optional until retrieval baseline is measured.

Pretext pairs:

- JSON/YAML/CSV versions of same dataset
- schema field and data dictionary definition
- field alias pairs
- validation issue and relevant rule
- rejected transformation and safety rule
- OCR field and schema field
- graph neighbors with `ALIAS_OF` or `MAPS_TO`

Candidate methods:

- contrastive sentence embeddings
- TSDAE-style denoising
- SimCSE-style dropout positives
- BYOL-style no-negative learning for safe positives
- tabular SSL for row/table profiles

Promotion metrics:

- Recall@k
- nDCG@10
- MRR
- schema-hit rate
- cluster purity
- nearest-neighbor review quality
- latency
- embedding variance and collapse checks

## Evaluation Set

Create curated queries:

- "Which schema matches columns patient_id, lab_name, value, unit?"
- "How should missing units be handled?"
- "What does LOINC code mean in the lab schema?"
- "Map FHIR Observation to an OMOP measurement-like table."
- "Which fields are APPI-sensitive?"
- "Why should date normalization require review?"
- "Which source supports masking patient identifiers?"

Each query should have expected source IDs.

## Acceptance Criteria

- Retrieval separates trusted knowledge from user-provided data.
- Source IDs and versions are included in every retrieval result.
- Empty or weak retrieval produces warnings.
- Explanation agent can cite retrieved evidence.
- Graph-NER outputs provenance and confidence.
- PHI-like entities are high-recall and reviewable.
- Advanced retrieval modules are gated by evaluation.

## Build Sequence

1. Create knowledge source metadata schema.
2. Build ingestion and chunking.
3. Implement lexical retrieval.
4. Add dense embedding retrieval.
5. Merge into hybrid retrieval.
6. Build retrieval evaluation set.
7. Add evidence package to workflow output.
8. Build Graph-NER entity/relation contract.
9. Add dictionary/regex/rule-based extractor baseline.
10. Add normalization table for FHIR/OMOP/JP Core aliases.
11. Add graph storage prototype.
12. Run SSL or reranking experiments only after baseline metrics exist.

## Risks

| Risk | Control |
| --- | --- |
| Retrieval returns irrelevant schema | Metadata filters and evaluation set |
| HyDE text treated as evidence | Mark HyDE as query-only, never evidence |
| Graph extraction creates noisy duplicates | Fixed ontology and canonical IDs |
| SSL distracts from MVP | Gate it behind retrieval baseline |
| Medical terminology normalization is incomplete | Label confidence and require review |
