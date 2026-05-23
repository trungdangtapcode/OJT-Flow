# Extension Points

The current backbone implements only the first vertical slice. Larger modules from the proposal must connect through the points below so the system does not split into separate architectures.

## Extension Map

| Future module | Connects through | Must not do |
| --- | --- | --- |
| Real RAG | implement `KnowledgeRepository` or a new retrieval port | mutate workflow state directly |
| MCP | wrap deterministic tools through MCP servers | let LLMs call tools without permission/review checks |
| Graph-NER | produce `Evidence`, graph nodes/edges, schema-match signals | create a separate explanation path outside `ExplanationReport` |
| OCR | produce `OcrField` and `Evidence(source_type=ocr_box)` | automatically write medical records when confidence is low |
| DICOM | produce `DicomReference` and metadata evidence | claim diagnosis |
| Segmentation/vision | produce `VisualEvidenceArtifact` and `Evidence(image_mask)` | present output as a clinical conclusion |
| Persistent DB | implement repository ports | reshape domain contracts around DB tables |
| LangGraph | replace or wrap orchestration runtime | bypass workflow state/event contracts |
| MLOps | version model/index/schema artifacts | deploy artifacts without evaluation gates |

## RAG Integration

Current:

```python
class StaticKnowledgeRepository:
    def get_schema(...)
    def search(...) -> list[Evidence]
```

Target:

```text
KnowledgeRepository
  -> KnowledgeIngestion
  -> Chunker
  -> LexicalIndex
  -> VectorIndex
  -> Reranker
  -> EvidencePack
```

The return type remains `Evidence[]`.

Add fields later if needed:

- retrieval run ID
- query text
- top-k scores
- index version
- source freshness
- missing evidence warnings

## MCP Integration

Current execution:

```text
WorkflowService -> agent -> direct Python function
```

Target execution:

```text
WorkflowService
  -> agent
  -> ToolRegistry
  -> MCP client
  -> MCP server
  -> deterministic tool
  -> ToolResult
  -> event log
```

Planned MCP servers:

- `structured-data-server`
- `schema-validation-server`
- `rag-context-server`
- `workflow-audit-server`
- `human-review-server`

Each MCP server must enforce:

- input schema
- output schema
- permission scope
- agent allowlist
- approval flag
- audit event

## Graph-NER Integration

Graph-NER should run after parse/profile and before or during retrieval:

```text
ParsedData + DataProfile
  -> GraphNerExtractor
  -> entities + relations
  -> graph storage
  -> Evidence[]
  -> schema matching support
```

Graph-NER output should feed:

- schema candidate ranking
- PHI/sensitive field detection
- FHIR/OMOP/JP Core mapping
- explanation evidence
- review triggers

It must preserve:

- source row/column
- confidence
- normalized ID
- review flag

## OCR Integration

OCR should not bypass the structured workflow. It should create a structured extraction workflow:

```text
document upload
  -> OCR adapter
  -> OcrField[]
  -> field validation
  -> human review for low confidence/sensitive fields
  -> structured data conversion
```

`OcrField` maps to evidence:

```text
page + bbox + field value -> Evidence(source_type=ocr_box)
```

## DICOM And Visual AI Integration

DICOM metadata and visual outputs should enter as evidence artifacts:

```text
DICOM metadata -> DicomReference -> Evidence(dicom_metadata)
Mask/box/track -> VisualEvidenceArtifact -> Evidence(image_mask/video_track)
```

The explanation agent can then say:

- what artifact was generated
- where it came from
- confidence
- review requirement
- limitation

It must not claim autonomous diagnosis or treatment.

## Persistent Storage Integration

Replace in-memory adapters by implementing ports:

```python
DatasetStore
WorkflowRepository
EventRepository
KnowledgeRepository
```

Recommended sequence:

1. SQLite adapter for local persistence.
2. PostgreSQL adapter for workflows/events/reviews.
3. Object store adapter for raw datasets/outputs.
4. pgvector/Qdrant adapter for retrieval.
5. Graph DB adapter for Graph-NER.

Do not change `WorkflowService` when swapping adapters.

## LangGraph Integration

LangGraph can replace custom orchestration when the workflow becomes complex.

Graph nodes should map to existing agents:

- safety precheck
- parser
- retrieval
- schema matching
- validation
- review gate
- transformation
- post-validation
- explanation
- audit summary

State should still be `WorkflowState` or a strict superset of it.

## Frontend / Review UI Integration

The UI should consume the existing API:

- `POST /api/v1/workflows`
- `GET /api/v1/workflows/{id}`
- `GET /api/v1/workflows/{id}/events`
- `POST /api/v1/review/{id}`

First UI view:

- input panel
- workflow timeline
- validation issue table
- proposed action panel
- approve/edit/reject buttons
- output preview
- evidence/explanation panel

The UI should not implement business rules. It displays `WorkflowState` and posts review decisions.

## Evaluation Integration

Every extension should add fixtures and tests:

- RAG: expected source IDs for queries
- Graph-NER: expected entity/relation extraction
- OCR: field-level ground truth and bbox checks
- DICOM: metadata fixture checks
- vision: artifact schema checks
- MCP: tool schema and permission tests
- DB: repository contract tests

No extension is integrated until it passes through:

```text
workflow state + events + evidence + review gate + tests
```

