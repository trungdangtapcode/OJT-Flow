# OJTFlow Master Implementation Plan

This plan converts the LaTeX proposal into an implementation blueprint. The core idea is to build OJTFlow as governed healthcare data workflow infrastructure: foundation models interpret intent and explain results, while deterministic tools perform parsing, validation, conversion, retrieval, review, and audit.

The first build target is not the advanced AI stack. The first target is the backbone: a typed workflow system with stable state, events, contracts, storage, API routes, and tool boundaries. Every later feature, including RAG, Graph-NER, OCR, DICOM, segmentation, and MLOps, should attach to that backbone instead of creating parallel paths.

## Product Boundary

OJTFlow should be positioned as an assistive platform for healthcare data transformation, validation, explanation, and review. It must not claim autonomous diagnosis, treatment, triage, or medication decision-making in the MVP.

Primary MVP workflow:

1. User uploads or pastes JSON, YAML, CSV, or FHIR-like data.
2. User gives a natural language instruction.
3. System creates a workflow run with immutable input reference and audit trace.
4. Parser detects format and profiles data.
5. Retrieval finds trusted schemas, examples, field definitions, rules, and prior accepted transformations.
6. Schema and validation agents identify schema candidates, confidence, data issues, and risk level.
7. Human review is triggered for ambiguous, destructive, sensitive, or medically consequential operations.
8. Deterministic tools run approved conversion or cleaning.
9. Explanation is assembled from validation results, retrieval evidence, tool outputs, and audit events.
10. Final response includes output, validation report, explanation report, provenance, and audit summary.

## Non-Negotiable Architecture Principles

- Model reasoning plans and explains; deterministic code mutates structured data.
- Every workflow has one shared state object and one audit event stream.
- Every agent returns structured results through a common response contract.
- Every tool call has typed inputs, typed outputs, validation, permission scope, and audit record.
- Retrieval context is trusted only when it comes from approved sources with metadata.
- User data, retrieved text, OCR text, and model outputs are all treated as untrusted until validated.
- Human review gates are part of normal workflow, not an exception path.
- Healthcare explanations cite evidence objects, validation findings, source IDs, and limitations.
- MVP uses synthetic or public data only; real PHI requires a separate governance path.

## System Layers

| Layer | Responsibility | MVP choice | Later extension |
| --- | --- | --- | --- |
| UI and API | Intake, workflow status, review decisions, output display | FastAPI plus simple Streamlit or React UI | Full review console and admin UI |
| Workflow backbone | State, events, routing, pause/resume, retries | Python service with LangGraph-ready state shape | LangGraph durable execution |
| Agents | Parser, schema, validation, transform, retrieval, explanation, safety, review | Python classes/functions behind contracts | Tool-using graph nodes |
| Tools | Deterministic parse, convert, validate, diff, mask, export | Direct Python services first | MCP servers with stdio/HTTP |
| Retrieval | Schema/docs/examples/rules lookup | Hybrid lexical + vector baseline | HyDE, reranker, hierarchy, GraphRAG |
| Medical graph | Entities, aliases, relations, evidence links | Simple graph tables/NetworkX prototype | Neo4j/Memgraph and GNN reranking |
| Storage | Workflows, datasets, schemas, reports, audit | SQLite for local MVP | PostgreSQL + pgvector + object store |
| Governance | Human review, PHI flags, audit, risk register | Typed policies and review routes | APPI/MHLW/PMDA pilot checklist |
| Observability | Logs, traces, metrics, evaluation records | Structured logs and local reports | OpenTelemetry, Grafana, Evidently |
| MLOps | Index/model versioning and evaluation gates | Manual version fields and reports | MLflow, Vertex/Kubeflow, GitOps |

## Build Order

### Phase 0: Scaffolding and Backbone

Goal: Create the project skeleton, typed contracts, workflow state, event model, storage model, and API shape before implementing advanced behavior.

Deliverables:

- Repository scaffold and package boundaries.
- Workflow state, event, issue, evidence, and agent result schemas.
- Initial API route map.
- Storage table design.
- Tool interface pattern.
- Human review state model.
- Audit logging rules.
- Golden-path demo fixture.

Acceptance:

- A developer can read the scaffold and understand where every future module belongs.
- No feature needs to invent its own state model or logging pattern.
- The same workflow ID can connect input, agents, tool calls, review, output, and explanation.

Detailed file: `01_scaffolding_backbone.md`.

### Phase 1: Core Data Workflow

Goal: Ship a deterministic structured-data pipeline for JSON, YAML, CSV, and FHIR-like sample records.

Deliverables:

- Data intake and immutable input references.
- Format detection and parser reports.
- Data profiler for fields, rows, types, samples, missingness, duplicate keys, malformed rows.
- Schema inference and schema matching baseline.
- Validation reports with severity.
- Deterministic conversion among JSON/YAML/CSV.
- Transformation diff and output validation.
- Direct `/convert`, `/validate`, and workflow endpoints.

Acceptance:

- Curated conversion tests pass.
- Invalid inputs fail with structured errors.
- Returned outputs are validated before being exposed.
- Risky cleaning requests are paused for human review.

Detailed file: `02_core_workflow_detailed_plan.md`.

### Phase 2: Agents, MCP, and Human Review

Goal: Add the multi-agent workflow around stable deterministic services.

Deliverables:

- Orchestrator state machine.
- Agent contracts for parser, schema, validation, transformation, retrieval, explanation, safety, clinical explainability, and human review.
- Tool registry with role-scoped permissions.
- MCP-compatible wrappers after direct Python tools stabilize.
- Review queue and decision recording.
- SSE or polling endpoint for workflow progress.

Acceptance:

- End-to-end workflow trace shows which agent acted, which tools were called, and why review was required or skipped.
- Agents cannot bypass validation or write/export permissions.
- Human decisions become audit evidence.

Detailed file: `03_agents_mcp_detailed_plan.md`.

### Phase 3: RAG, Graph-NER, and Representation Learning

Goal: Ground plans and explanations in trusted project knowledge, then add research modules only behind evaluation gates.

Deliverables:

- Knowledge ingestion for schemas, data dictionaries, transformation examples, error guidance, and project docs.
- Metadata-aware retrieval baseline using lexical search plus embeddings.
- Retrieval evaluation set with expected source chunks.
- Evidence package in every final response.
- Graph-NER schema for medical entities, FHIR/OMOP/JP Core paths, PHI flags, relations, and aliases.
- Optional HyDE, reranking, GraphRAG, and SSL embedding experiments.

Acceptance:

- Retrieval records source IDs, versions, scores, and missing-evidence warnings.
- Clinical explanations do not rely on unsupported model rationales.
- Advanced retrieval or SSL modules are promoted only if they beat the baseline on measured metrics.

Detailed file: `04_rag_graphner_detailed_plan.md`.

### Phase 4: Medical Multimodal Track

Goal: Add OCR, DICOM, segmentation, detection/tracking, and visual evidence contracts without breaking the core structured-data backbone.

Deliverables:

- OCR document contract with page, block, table, checkbox, field, and bounding-box provenance.
- DICOM metadata contract with study/series/instance references.
- Visual evidence object for masks, boxes, heatmaps, frame tracks, and reviewer corrections.
- Synthetic Japanese/English clinical document fixtures.
- Public-data segmentation proof of concept if time permits.
- Japan-market schema aliases and JP Core/FHIR mapping notes.

Acceptance:

- Multimodal outputs are evidence artifacts, not autonomous medical claims.
- Low-confidence OCR or visual findings require review.
- Explanations can cite page/box/image/frame IDs.

Detailed file: `05_medical_multimodal_detailed_plan.md`.

### Phase 5: Security, Governance, Platform, and MLOps

Goal: Make the prototype credible for healthcare and Japan-market pilot discussions.

Deliverables:

- Threat model and risk register.
- APPI/MHLW/PMDA-aware governance checklist.
- PHI/sensitive field handling policy.
- Audit retention and logging policy.
- Docker Compose local deployment.
- GitHub Actions CI baseline.
- GCP-first deployment blueprint.
- Observability and MLOps design.

Acceptance:

- No raw PHI is required for the demo.
- Workflow logs contain hashes and references rather than unnecessary sensitive raw content.
- Every model, prompt, schema, vector index, graph snapshot, and tool version can be tied to an evaluation or approval record.

Detailed files: `06_security_governance_detailed_plan.md` and `07_platform_mlops_detailed_plan.md`.

### Phase 6: Evaluation, Hardening, and Demo

Goal: Prove the system works, explain what it does not do, and prepare a reproducible demonstration.

Deliverables:

- Curated test fixtures.
- Evaluation report.
- Demo script.
- Final architecture report.
- Known limitations and post-MVP roadmap.
- Submission package.

Acceptance:

- Conversion correctness meets target on curated tests.
- Validation detects seeded issues.
- Human review catches destructive, sensitive, ambiguous, or low-confidence actions.
- Clinical explanation claims are supported by validation, retrieval, tool output, or human decision evidence.

Detailed file: `08_evaluation_roadmap_detailed_plan.md`.

## Recommended 12-Week Delivery Shape

| Week | Theme | Main outcome |
| --- | --- | --- |
| 1 | Scaffolding, scope, governance | Backbone docs, repo skeleton, contracts, risk register |
| 2 | Intake and profiling | Parser, profiler, workflow IDs, fixtures |
| 3 | Conversion and validation | Deterministic conversion, schema validation, reports |
| 4 | Agents and review | Orchestrated workflow, tool calls, review gate |
| 5 | Graph-NER foundation | Entity/relation schema, alias mapping, graph prototype |
| 6 | Retrieval baseline | Hybrid retrieval, source metadata, benchmark |
| 7 | SSL experiment | Weak pair generation and embedding comparison |
| 8 | Reranking and explanation | Evidence package, supported-claim map, uncertainty |
| 9 | OCR, DICOM, Japan readiness | Document/DICOM contracts, APPI/JP Core checklist |
| 10 | Vision and MLOps | Segmentation artifact or design, GCP/CI/CD blueprint |
| 11 | Hardening | Security tests, monitoring design, integrated evaluation |
| 12 | Final demo | Report, demo script, slides, post-MVP plan |

## Team Ownership Model

| Slot | Primary ownership | Success responsibility |
| --- | --- | --- |
| Backend/Architecture | API, workflow state, deterministic tools, storage, review, integration | Make the system reliable as workflow infrastructure |
| AI/Retrieval/Medical AI | LLM gateway, agents, RAG, Graph-NER, SSL, OCR/vision research, explainability | Make outputs evidence-grounded and research credible |
| Platform/Governance/QA | CI/CD, GCP, containers, monitoring, security, APPI/MHLW/PMDA checklist, evaluation package | Make the prototype deployable, testable, auditable, and Japan-ready |

## Phase Gates

| Gate | Required evidence | Decision |
| --- | --- | --- |
| Backbone gate | Shared state, events, schemas, API map, storage model, scaffold tree | Begin implementation only when feature ownership is clear |
| MVP gate | End-to-end parse, validate, review, convert, explain workflow | Continue to research features only after core workflow is stable |
| Retrieval gate | Recall@k, nDCG@10, schema-hit rate, source coverage, latency | Promote advanced retrieval only if it improves measured quality |
| SSL gate | Baseline vs adapted embedding report, collapse checks, held-out retrieval | Promote adapted embeddings only with clear gain |
| Multimodal gate | OCR/DICOM/vision evidence artifacts with review behavior | Keep as assistive/research unless separately approved |
| Clinical safety gate | PHI checks, unsupported-claim checks, review gate coverage, audit reconstruction | No demo flow can bypass governance |
| Final readiness gate | CI evidence, evaluation report, risk register, demo package, roadmap | Submit as research-backed, production-shaped prototype |

## Success Metrics

- Conversion correctness: at least 95 percent on curated deterministic tests.
- Validation accuracy: at least 90 percent detection on seeded malformed, missing, and type mismatch cases.
- Retrieval relevance: at least 80 percent relevant sources in top 5 for MVP queries.
- Explanation quality: average reviewer score at least 4/5 for clarity and usefulness.
- Evidence faithfulness: at least 95 percent of clinical explanation claims supported in demo cases.
- Human review safety: no critical risky action proceeds without review.
- Auditability: 100 percent reconstruction for completed demo workflows.
- Simple conversion latency: p95 under 3 seconds locally for demo-sized inputs.
- Complex demo workflow latency: p95 under 15 to 30 seconds depending on model calls.

## First Action

Create the scaffolding described in `01_scaffolding_backbone.md`. That document is the backbone. It defines the repository shape, domain contracts, state machine, events, tool boundaries, storage tables, and acceptance tests that the rest of the system depends on.
