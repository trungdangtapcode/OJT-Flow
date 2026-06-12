# OJTFlow 8-Month Feature Roadmap And Backlog

Research date: 2026-06-10

## Purpose

This document defines the next 7-8 months of OJTFlow product and engineering work.
It is intentionally broader than a sprint TODO list: it is a feature roadmap for
turning the current healthcare workflow backbone into an enterprise-ready product.

The plan is based on the current codebase shape:

- FastAPI backend with clean architecture boundaries under `src/ojtflow`.
- React/TypeScript frontend with dedicated Assistant, Retrieval, Workflow, Review,
  Audit, Settings, and Help surfaces.
- Postgres/Redis/Docker runtime, local file artifacts, workflow persistence,
  audit events, review gates, Google OAuth, and runtime settings.
- Deterministic parser, validator, converter, FHIR-like profiler, OCR evidence
  stub, retrieval service, Graph-NER handoff, OpenAI-backed assistant streaming,
  and MCP tool wrapper.
- Current healthcare format direction: messy input -> parsed profile ->
  validation -> FHIR-like clinical package -> evidence/provenance -> human review
  -> governed export or workflow output.

## External Research Anchors

Use these sources as design constraints when implementing the roadmap:

- HL7 FHIR: exchange, resources, search, provenance, audit, and implementation
  guide patterns: https://hl7.org/fhir/
- OHDSI OMOP CDM: analytics schema, standardized vocabularies, data quality
  dashboard, and cohort/research tooling: https://ohdsi.github.io/CommonDataModel/
- LOINC: lab, observation, measurement, and document terminology:
  https://loinc.org/
- UCUM: unit validation and conversion, including FHIR CodeSystem validation:
  https://ucum.nlm.nih.gov/ucum-service.html
- RxNorm/RxNav: medication terminology APIs and locally installable option:
  https://lhncbc.nlm.nih.gov/RxNav/
- DICOM: imaging metadata and medical imaging interoperability:
  https://www.dicomstandard.org/current
- NCBI E-utilities/PubMed: official biomedical literature API:
  https://www.ncbi.nlm.nih.gov/books/NBK25501/
- ClinicalTrials.gov API: clinical trial search and record metadata:
  https://clinicaltrials.gov/data-api/about-api
- openFDA APIs: FDA public datasets for drugs, devices, adverse events, labels,
  and recalls: https://open.fda.gov/apis/
- Postgres full-text search: lexical retrieval, ranking, dictionaries, and query
  parsing: https://www.postgresql.org/docs/current/textsearch.html
- pgvector: vector similarity, HNSW, IVFFlat, filtering, quantization, and
  production indexing: https://github.com/pgvector/pgvector
- LlamaIndex: ingestion pipelines, hybrid retrieval, query routing, graph/query
  engines, evaluation, observability, and agent patterns:
  https://developers.llamaindex.ai/python/framework/
- Nir Diamant RAG Techniques: practical advanced RAG recipes to adapt carefully,
  especially query transformation, reranking, routing, corrective RAG, GraphRAG,
  self-RAG, and evaluation: https://github.com/NirDiamant/RAG_Techniques
- Model Context Protocol: tools, resources, prompts, stateful transport,
  authorization, progress, cancellation, and consent boundaries:
  https://modelcontextprotocol.io/specification/2025-06-18
- OpenAI function calling and streaming: strict tool schemas and server-sent
  response streaming for user-visible model work:
  https://developers.openai.com/api/docs/guides/function-calling and
  https://developers.openai.com/api/docs/guides/streaming-responses
- OWASP LLM Top 10: prompt injection, insecure output handling, excessive agency,
  sensitive information disclosure, and related LLM application risks:
  https://owasp.org/www-project-top-10-for-large-language-model-applications/
- NIST AI RMF: AI risk governance, measurement, management, and trustworthy AI
  operating model: https://www.nist.gov/itl/ai-risk-management-framework

## Product Target

OJTFlow should target B2B healthcare data teams first:

- Data integration teams validating messy CSV, Excel, JSON, FHIR-like, and
  document-derived data before transformation.
- Clinical operations teams reviewing sensitive or low-confidence workflow
  changes.
- Healthcare AI teams needing evidence-grounded RAG, Graph-NER handoff, and
  auditable assistant/tool execution.
- Implementation teams mapping operational data into FHIR-like exchange packages
  and OMOP-ready analytics packages.

The end user should not need to understand every screen. The Assistant should be
the primary entry point, with UI pages used for inspection, review, configuration,
and audit.

## Roadmap Summary

| Month | Theme | Outcome |
| --- | --- | --- |
| Month 1 | Stabilize product spine | Clean runtime, reliable sessions, persistent chat, consistent UI, migration safety, and real-data dev workflow. |
| Month 2 | Document and file intelligence | Robust uploads, OCR/layout evidence, image/PDF/table extraction, source-linked parsing, and human-readable explanations. |
| Month 3 | Healthcare standards layer | ClinicalPackage v0, FHIR-like builders, terminology candidate contracts, LOINC/UCUM/RxNorm hooks, and provenance model. |
| Month 4 | Enterprise retrieval and RAG | Advanced hybrid retrieval, ingestion jobs, corpus governance, reranking, GraphRAG-lite, eval harness, and source quality controls. |
| Month 5 | Assistant and MCP productization | Real chat sessions, streaming tool timeline, governed tool approvals, remote MCP readiness, and role-aware assistant workflows. |
| Month 6 | Governance, compliance, and security | RBAC, tenant boundaries, audit export, PHI handling, policy engine, AI risk controls, and admin settings. |
| Month 7 | Analytics and interoperability | OMOP mapping path, Bulk FHIR/NDJSON, HL7 v2 starter adapter, DICOM metadata, external dataset connectors, and export packages. |
| Month 8 | Scale, quality, and enterprise release | Performance, observability, CI/CD, deployment hardening, evaluation dashboards, customer pilots, and release readiness. |

## Implementation Progress

Keep this section updated when roadmap items move from planning into code.

| Date | Item | Status | Evidence |
| --- | --- | --- | --- |
| 2026-06-10 | F002 | Implemented | `/api/v1/runtime/readiness` reports settings, Postgres migrations, artifact paths, OAuth/auth config, Redis/session cache, embeddings, LLM, MCP tool registry, retrieval rule packs, workflow repository, schema inventory, retrieval inventory, and sampled storage consistency. |
| 2026-06-10 | F003 | Implemented | `PostgresMigrator` tracks checksums for applied migrations, rejects duplicate migration versions, rejects edited applied migrations, and now exposes a read-only manifest/database inspection report for readiness. |
| 2026-06-11 | F004 | Implemented | Added `/api/v1/runtime/migrations`, typed migration diagnostics, schema migration duration/failure fields for the runner, and a Settings page Schema migrations admin panel showing applied, pending, checksum-mismatched, unknown, duration, and failure state. |
| 2026-06-11 | F005 | Implemented | Added sanitized bootstrap classification for missing psycopg, missing DSN, malformed DSN, auth failure, DNS failure, refused/timeout network paths, missing extension, duplicate migration version, pending migrations, and migration history conflicts. |
| 2026-06-11 | F001 | Implemented | Added `OJT_PRODUCT_MODE` (`local_dev`, `demo`, `pilot`, `production`), `OJT_NO_MOCK_DATA`, effective no-mock policy, runtime config exposure, readiness policy checks, and Settings UI visibility. |
| 2026-06-11 | F006 | Implemented | Added typed storage consistency contracts, reusable workflow artifact scanner, `/api/v1/runtime/storage-consistency`, readiness integration, dataset metadata listing across memory/SQLite/Postgres, workflow-ref-to-dataset-row checks, dataset-row-to-file checks, dataset hash checks, unreferenced dataset row candidate counts, and retrieval knowledge/index consistency counters for seeded/corpus scopes. |
| 2026-06-11 | F007 | Implemented | Added sanitized storage repair candidates, `/api/v1/runtime/storage-repair-plan`, and `/api/v1/runtime/storage-repair-markers`. The marker command records orphaned dataset rows/files and mismatch candidates as runtime marker artifacts without deleting files or mutating workflow/dataset rows. |
| 2026-06-11 | F010 | Implemented | Added typed Assistant session/message contracts, explicit workflow refs, auto-extraction of nested workflow IDs from tool payloads, `AssistantSessionService`, memory/SQLite/Postgres repositories, Postgres migration 008, authenticated session/message API routes, frontend session sidebar loading, automatic user/assistant message persistence, and stream-event replay payloads. |
| 2026-06-11 | F011 | Implemented | Added authenticated session rename, archive, delete, and owner-scoped search across session titles and persisted message content. The Assistant sidebar now sends server-side search queries instead of relying on browser-only state. Retention controls and admin export remain separate governance backlog work. |
| 2026-06-11 | F012 | Implemented | The Assistant sidebar now loads backend sessions, creates/deletes persisted sessions, keeps temporary stream drafts only while a request is active, and reconciles against persisted chat detail after streaming completes. |
| 2026-06-11 | F013 | Implemented | Assistant stream requests now accept `session_id`, stamp SSE events with stream/session/sequence metadata, persist one replay artifact per stream in dedicated memory/SQLite/Postgres storage, expose `/api/v1/assistant/sessions/{session_id}/stream-replays`, and keep replay artifacts out of the normal chat transcript. |
| 2026-06-11 | F014 | Implemented | Added frontend API error events from the shared API client and a global diagnostic panel showing status, error code, endpoint, workflow ID, request ID, and a copyable payload. |
| 2026-06-11 | F015 | Implemented | Frontend requests send `X-Request-ID`; backend responses echo it; error envelopes include `error.request_id` and `details.request_id`; assistant stream events/replays carry the request ID; retrieval reindex jobs store it; workflow audit events persist it top-level and in metadata; workflow retrieval traces and direct retrieval search traces include it. |
| 2026-06-11 | F016 | Implemented | Added shared frontend API error diagnostic shaping, consistent page-level `code: message | Workflow ... | Request ...` formatting, and a global details panel rendering status, endpoint, workflow ID, request ID, sanitized details, and copyable diagnostic payload. |
| 2026-06-11 | F017 | Implemented | Added `frontend/src/data/page-guides.json` and a route-aware `PageGuide` renderer in the app shell so Assistant, Workbench, Workflows, Reviews, Retrieval, Audit, Schemas, Settings, and Help all get data-driven operator guidance. |
| 2026-06-11 | F018 | Started | Normalized the desktop app shell to one primary content scroll region below the top bar, kept mobile on normal document flow, and adjusted the workflow detail sticky offset for the new scroll container. Remaining work: browser-verify Assistant, Retrieval, Workflow detail, and Review subregion behavior across breakpoints. |
| 2026-06-11 | F008 | Implemented | Added typed `BackgroundJob` contracts, memory/SQLite/Postgres repositories, Postgres migration 009, job status/progress/error JSON, owner-scoped job listing, and durable metadata for retrieval reindex, file parse, OCR, embedding reindex, external ingestion, and export package jobs. |
| 2026-06-11 | F009 | Implemented | Added `BackgroundJobService` and sync local runner mode. `/api/v1/jobs/retrieval-reindex` creates a durable job, runs retrieval reindex synchronously by default, records output/errors, and runtime readiness reports the job repository with `queue_backed=false` until a worker queue is added. |
| 2026-06-11 | F019 | Implemented | Added `OJT_NO_MOCK_DATA` and effective no-mock policy in pilot/production modes. Workbench no longer auto-loads sample patient rows, hides starter fixtures when effective no-mock is enabled, and requires pasted/uploaded data from the user in production-like modes. |
| 2026-06-11 | F020 | Implemented | Settings validation rejects `OJT_LLM_PROVIDER=disabled` when `OJT_PRODUCT_MODE` is `pilot` or `production`; those modes also reject memory storage. |
| 2026-06-11 | F021 | Started | Added durable `file_parse` job creation through `POST /api/v1/parse/upload/jobs` and batch `POST /api/v1/parse/upload/batch/jobs` with sync local execution or queued mode. Queue-backed workers remain follow-up scope. |
| 2026-06-11 | F022 | Implemented | Added `UploadedArtifact` contracts, owner-scoped artifact repositories for memory/SQLite/Postgres, raw upload storage under `var/uploads/`, artifact list/get APIs, and Postgres migration 011. |
| 2026-06-11 | F023 | Started | Added owner-scoped raw upload deduplication by SHA-256 and byte size while preserving every upload record. Extracted-text dedupe remains follow-up because it needs extractor/version-aware normalization. |
| 2026-06-11 | F024 | Implemented | Added `ParsingPipelineTrace` and `ExtractionStepTrace` contracts with extractor, fallback path, warnings, character/token counts, confidence, output refs, and persisted trace list API. |
| 2026-06-11 | F025 | Implemented | Added a `DocumentExtractor` application port and `LocalDocumentExtractor` adapter around the existing MarkItDown/MinerU/OpenAI-vision extraction pipeline. |
| 2026-06-11 | F026 | Implemented | Promoted `openai_vision` to a first-class extractor option. Vision traces now include provider, model, billable cost basis, external-provider flag, and PHI-handling metadata. |
| 2026-06-11 | F027 | Implemented | Added optional `tesseract` local OCR extractor support behind the same `DocumentExtractor` path, with local/non-billable cost metadata and PHI host-handling trace metadata. |
| 2026-06-11 | F028 | Implemented | Added `POST /api/v1/parse/clipboard/images/jobs` so pasted image bytes create the same `UploadedArtifact`, dedupe, job, and trace path as file uploads. The Assistant paste UX now creates a durable clipboard parse job, streams extracted document context with artifact/trace IDs into the chat, and keeps normal attached-file behavior unchanged. |
| 2026-06-11 | F030 | Implemented | Added table extraction contracts: `TableExtractionProfile`, `ExtractedTable`, and `TableCell`, preserving source kind, page/sheet context, cell coordinates, confidence, and source locations. |
| 2026-06-11 | F036 | Started | Extended `SourceLocation` with page, bounding box, text span, sheet/table-cell references, and source refs so validation/OCR/table issues can point to exact source regions. Producer/UI wiring remains follow-up. |
| 2026-06-11 | F031 | Implemented | Added workbook profiling for upload traces: sheet count, visible/hidden sheets, row/column counts, header-row candidates, headers, merged-cell ranges, and warnings. Legacy `.xls` receives an explicit conversion/analyzer warning. |
| 2026-06-11 | F032 | Implemented | Added PDF scanned-vs-digital profiling with PyMuPDF/pypdf optional analyzers and explicit warnings when OCR is required or no analyzer is installed. |
| 2026-06-11 | F037 | Implemented | Added deterministic extraction quality scoring based on empty/short text, low extractor confidence, extractor warnings, PDF OCR requirement, and workbook structure warnings. |
| 2026-06-11 | F038 | Implemented | Added trace-level extraction explanations covering what was read, skipped, needs review, and limitations for user-facing support. |
| 2026-06-11 | F033 | Implemented | Added deterministic redaction preview with structured CSV sensitive-column masking, SSN/email/phone span detection, `POST /api/v1/parse/redaction-preview`, and trace-level redaction summaries before external provider handoff. |
| 2026-06-11 | F034 | Implemented | Added mode/source/sensitivity/tenant-aware artifact retention policy resolution with `OJT_ARTIFACT_RETENTION_RULES`, default mode policies, and per-artifact stamped retention metadata. |
| 2026-06-11 | F035 | Implemented | Added owner-scoped artifact download, metadata export, and access-event listing APIs backed by append-only memory/SQLite/Postgres artifact access logs and Postgres migration 012. |
| 2026-06-11 | F040 | Started | Added batch upload parse jobs with shared `batch_id`, `case_id`, and `project_id` metadata. Direct workflow creation from batch outputs remains follow-up. |
| 2026-06-11 | F029 | Implemented | Added a Workbench OCR evidence review panel backed by `POST /api/v1/ocr/evidence`. Operators can paste multi-page OCR field JSON, normalize it through the backend contract, inspect page-grouped bounding boxes, confidence, source refs, evidence IDs, and review-required flags. |
| 2026-06-11 | F070 | Implemented | Added `knowledge/source_catalog/source_trust_policies.json`, typed `RetrievalSourceTrustPolicyCatalog`, and `GET /api/v1/retrieval/source-policies` so authoritative healthcare sources carry domain, standard system, intended/prohibited use, refresh cadence, license constraints, ingestion mode, evidence tier, and reviewer policy. |
| 2026-06-11 | F073 | Implemented | Added data-driven retrieval strategy presets in `knowledge/retrieval/strategy_catalog.json` and `GET /api/v1/retrieval/strategies`, covering lexical-only, vector-only, hybrid RRF, metadata-filtered, high-recall review, and exact-source lookup with runtime requirements and risk controls. |
| 2026-06-11 | F105 | Implemented | Added data-driven Assistant tool permission policy in `knowledge/assistant/tool_permission_policies.json`, extended tool specs with permission tags, risk level, and approval reason, and surfaced this metadata in the Assistant tool catalog UI. |
| 2026-06-11 | F108 | Implemented | Added data-driven Assistant answer template contracts in `knowledge/assistant/answer_templates.json` and `GET /api/v1/assistant/answer-templates`, covering validation reports, retrieval answers, standards explanations, workflow status, review summaries, and export summaries with evidence/review constraints. |
| 2026-06-11 | F084 | Implemented | Added `RetrievalPackage.support_matrix` and `handoff_context.support_matrix`, giving retrieval/assistant/MCP clients a deterministic claim-to-evidence matrix with source IDs, locators, matched terms, scores, reasoning, warnings, and support status. |
| 2026-06-11 | F113 | Implemented | Added data-driven MCP resource catalog contracts in `knowledge/assistant/mcp_resources.json`, authenticated catalog API, and local FastMCP resource registration for assistant/retrieval governance resources. |
| 2026-06-11 | F114 | Implemented | Added data-driven MCP prompt catalog contracts in `knowledge/assistant/mcp_prompts.json`, authenticated catalog API, and local FastMCP prompt registration for standard healthcare operator tasks. |
| 2026-06-11 | F103 | Implemented | Added strict OpenAI planner output mode, planner-visible tool schemas with `additionalProperties=false`, all declared properties required, nullable optional inputs, and tests asserting the strict schema contract. |
| 2026-06-11 | F104 | Implemented | Added reloadable runtime controls for assistant planning/synthesis/vision models, OpenAI-compatible LLM endpoint, planning heartbeat interval, and retrieval embedding provider/model/dimensions, with Settings UI and API contract updates. |
| 2026-06-11 | F096 | Implemented | Made Assistant the default authenticated landing route after index and OAuth callback, kept Workflows as the operations queue, and added a real composer file drop zone that reuses the existing attachment extraction pipeline. |
| 2026-06-11 | F097 | Implemented | Moved ChatGPT-like session title generation to the backend: placeholder sessions are renamed on the first user message with PHI-guarded operational summaries, while the frontend creates `New chat` drafts and no longer performs title generation or automatic rename calls. |
| 2026-06-11 | F098 | Implemented | Completed the Assistant live timeline contract: planning events, streamed planner text, validated plan arguments, data-driven tool progress, collapsible tool results, streamed answer text, warnings, errors, and final response now render in chronological order inside the assistant turn. |
| 2026-06-11 | F099 | Implemented | Kept Assistant tool calls as inline collapsible cards inside the chat turn instead of a separate tool panel, and relabeled the UI section as a unified live timeline rather than tool-only output. |
| 2026-06-11 | F100 | Implemented | Added data-driven Assistant tool progress policies, backend `tool_progress` SSE events around actual tool execution, inline frontend progress rows, and an MCP resource exposing the progress policy catalog. |
| 2026-06-11 | F101 | Implemented | Added backend-aware cancellation: Assistant stream disconnects/stop actions persist replay status `cancelled`, cancellation renders in the live timeline, queued/running background jobs can be cancelled through an owner-scoped API, and Postgres migration 013 updates replay status constraints. |
| 2026-06-11 | F102 | Implemented | Added failed Assistant tool-call recovery actions: inline Retry resubmits the exact failed tool name and original arguments through structured `assistant_recovery.retry_tool`, while Continue creates a deterministic no-tool continuation that keeps unresolved failures visible. |
| 2026-06-11 | F106 | Implemented | Added one-use UI confirmation before write-enabled Assistant sends: the confirmation lists backend-advertised `requires_approval` tools with risk, scope, and approval reason, blocks unconfirmed `execute_write_actions=true`, and resets after each write-enabled turn. |
| 2026-06-11 | F107 | Implemented | Added data-driven Assistant memory policy in `knowledge/assistant/memory_policy.json`, typed memory contracts, memory/SQLite/Postgres repositories, Postgres migration 014, authenticated memory policy/snapshot/upsert/delete APIs, chat context injection that strips caller-spoofed memory, an MCP memory-policy resource, and an Advanced context UI editor for policy-allowed operational preferences only. |
| 2026-06-11 | F109 | Implemented | Assistant composer now supports multiple staged file attachments, multi-file clipboard paste, manual text snippets, removable selected context chips, workflow-to-Assistant context launch, and retrieval-run-to-Assistant context launch. The sent context preserves extracted attachment metadata/text, snippets, and selected workflow/retrieval refs in one structured payload. |
| 2026-06-11 | F110 | Implemented | Assistant evidence summaries now carry stable `evidence_id` and locator metadata, render Show evidence actions, and jump to anchored Assistant evidence cards. Workflow Detail and Retrieval hit cards expose matching evidence anchors, with async hash-scroll support for persisted workflow/retrieval evidence links. |
| 2026-06-11 | F041 | Implemented | Added `ClinicalPackage` contracts and `WorkflowState.clinical_package`, including raw input identity, FHIR-like bundle, OperationOutcome-like validation issues, evidence, review, audit refs, output refs, provenance, warnings, and handoff context. |
| 2026-06-11 | F042-F043, F048-F049 | Implemented | Added `knowledge/fhir/resource_profiles.json`, data-driven FHIR-like profile validation/search hints, and `lab_result_v1` resource builders for Patient, Observation, DiagnosticReport, and DocumentReference. Generated resources now carry source/derived/defaulted/review-required field provenance, and package handoff context includes profile IDs, source URLs, and search parameters. |
| 2026-06-11 | F044 | Implemented | Added `lab_result_v1` to FHIR-like Observation mapping for patient reference, effective date, code text, value quantity, and unit, with review warnings instead of silent semantic normalization. |
| 2026-06-11 | F047 | Implemented | Added OperationOutcome-like package issues derived from validation reports, preserving severity, code, diagnostics, source expression, issue ID, location, and review requirement. |
| 2026-06-11 | F046, F058-F059 | Implemented | Added workflow-scoped clinical package export for completed approved outputs, canonical package and FHIR-like Bundle hashes, FHIR-like Bundle projection with OperationOutcome and Provenance entries, and import validation that rehydrates exported packages without dropping evidence/review/provenance metadata. |
| 2026-06-11 | F050 | Implemented | Added workflow-level Provenance-like records for upload/extraction, parser, FHIR profiling, retrieval, validation, safety/review gates, assistant-created review and mapping tasks, converter output, retrieval-derived transformations, explanation, completion, and failure. Workflow Detail now renders provenance beside audit events, and ClinicalPackage handoff context links back to workflow provenance IDs. |
| 2026-06-12 | F051 | Implemented | Added sanitized AuditEvent-like export records to `GET /api/v1/audit/export`, projecting workflow events, review events, auth audit records, and Assistant/MCP tool execution records into a healthcare interoperability-friendly `AuditEvent`-shaped contract without exposing raw payloads. |
| 2026-06-11 | F052 | Implemented | Added review-gated `TerminologyCandidate` contract and deterministic LOINC candidate generation for `lab_result_v1.lab_name` from `knowledge/terminologies/medical_concepts.json`, carried in `ClinicalPackage.terminology_candidates`. |
| 2026-06-11 | F053 | Implemented | Added `UnitValidationResult`, `knowledge/terminologies/ucum_units.json`, and UCUM-like unit checks for `lab_result_v1.unit`, carried in `ClinicalPackage.unit_validations` with missing/unknown/not-preferred review flags. |
| 2026-06-11 | F056-F057, F060 | Implemented | Added a Workflow Detail Clinical Package tab that separates terminology source text, candidate codes, confidence, source terminology, reviewer state, unit checks, OperationOutcome-like issues, raw-to-resource field provenance, generated resource JSON, package warnings, and explicit FHIR-like/non-HL7-validation wording. |
| 2026-06-11 | F054-F055 | Implemented | Added data-driven RxNorm candidate generation for medication-like fields and license-aware SNOMED CT placeholder candidates for diagnosis/finding/problem/procedure/allergy fields, preserving source text and requiring review before semantic normalization. |
| 2026-06-11 | F045 | Implemented | Added first-class semantic normalization gates for lab names, units, dates, patient identifiers, diagnoses, medications, and procedures; gates link source values to FHIR-like target paths, terminology/unit candidates, provenance metadata, handoff context, and Workflow Detail review UI while preserving raw-source export behavior. |
| 2026-06-11 | F116 | Implemented | Added durable generic audit records for Assistant and MCP tool calls, with memory/SQLite/Postgres repositories, Postgres migration 015, owner-scoped `GET /api/v1/audit/records`, redacted tool input/output hashes, request/session/workflow/workflow-event correlation, and docs/tests. |
| 2026-06-11 | F115 | Implemented | Added a data-driven remote MCP deployment policy at `knowledge/assistant/remote_mcp_deployment_policy.json`, authenticated `GET /api/v1/assistant/mcp/remote-policy`, MCP resource `ojtflow://assistant/mcp/remote-policy`, and docs/tests. Remote exposure remains blocked until OAuth protected-resource metadata, resource indicators, per-user scoping, rate limits, and remote audit metadata are implemented and verified. |
| 2026-06-11 | F117 | Implemented | Added data-driven Assistant evaluation fixtures at `knowledge/assistant/evaluation_cases.json`, typed suite/case contracts, fixture loader, evaluation docs, and deterministic tests for tool selection, write-gate preservation, answer terms, and evidence-source requirements. |
| 2026-06-11 | F118 | Implemented | Added data-driven Assistant prompt-injection safety fixtures, loader, docs, and regression tests for uploaded data, retrieved chunks, tool descriptions, and user messages. LLM planner/synthesis payloads now mark uploaded data, tool arguments, and retrieved claims as untrusted content while preserving exact backend tool execution. |
| 2026-06-11 | F119 | Implemented | Added organization/workspace governance contracts, data-driven workspace defaults, memory/SQLite/Postgres repositories, Postgres migration 016, authenticated organization APIs, workspace settings merge/versioning, group creation, and docs/tests. RBAC enforcement and cross-resource ownership checks remain scoped to F120/F121. |
| 2026-06-11 | F120 | Implemented | Added data-driven RBAC role catalog for viewer, operator, reviewer, data steward, admin, auditor, and owner; permission-scope definitions; validated policy loader; effective role/permission computation on workspace responses; authenticated RBAC policy API; and docs/tests. Resource authorization enforcement remains scoped to F121. |
| 2026-06-11 | F121 | Implemented | Added shared `GovernanceService.require_permission(...)` enforcement, RBAC gates for workflows, reviews, artifact upload/download/export, source inventory, retrieval reindex/integrity, runtime settings/diagnostics, governance mutations, audit reads, and background reindex jobs; preserved owner-user scoping for workflows, reviews, chat sessions, artifacts, jobs, judgments, and audit records; and documented the authorization map in `docs/ownership_authorization_v0.md` with focused tests. |
| 2026-06-11 | F122 | Implemented | Added service-account identity for automation with `identity_type=service_account`, one-time `ojt_sa_` bearer token issuance, configurable token TTL/default role, memory/SQLite/Postgres storage, Postgres migration 017, workspace membership assignment with explicit RBAC role, authenticated list/create APIs, service-account-aware `/auth/me`, docs, and focused API/unit tests. |
| 2026-06-11 | F123 | Implemented | Added shared PHI classification contracts and data-driven classification rules for fields, rows, chunks, chat messages, generated outputs, validation reports, conversion output, assistant payloads, and retrieval evidence locators. |
| 2026-06-11 | F124 | Implemented | Added deterministic PHI redaction policy actions for masking, suppression, token placeholders, and review-gated reveal, with redaction preview API support and external-provider block recommendations. |
| 2026-06-11 | F125 | Implemented | Added no-raw-PHI logging guard, structured log scanner, development/CI scanner command, and docs for redacting formatted log messages, args, extra fields, key-value payloads, and CSV-shaped log text. |
| 2026-06-11 | F126 | Implemented | Added versioned external-provider policy contracts, runtime settings, OpenAI LLM/vision OCR/embedding enforcement before HTTP calls, MarkItDown OCR plugin gating, retrieval external-search hint suppression, docs, and focused tests. |
| 2026-06-11 | F127 | Implemented | Added data-driven prompt-injection policy contracts, policy loader, assessment/envelope helpers, Assistant LLM-bound untrusted wrappers for user data/documents/retrieved chunks/tool arguments, tool-metadata scanning and planner boundary metadata, authenticated policy API, docs, and focused tests. |
| 2026-06-11 | F128 | Implemented | Added generated-output validation contracts and policy helpers for Assistant plans, summaries, streamed summaries, and export descriptions; Assistant now validates LLM plans before execution/display and keeps deterministic fallback text when generated summaries fail validation. |
| 2026-06-11 | F129 | Implemented | Added owner-scoped JSON audit export packages with typed filters, coverage metadata, sanitized generic audit records, optional workflow event inclusion, explicit coverage for workflows/reviews/Assistant tool calls/auth/settings/source ingestion, docs, and focused API tests. |
| 2026-06-11 | F130 | Implemented | Added deterministic audit hash-chain fields, repository-level chain linking for memory/SQLite/Postgres audit records, Postgres migration 018, high-risk deployment config signal, runtime config exposure, docs, and focused persistence tests. |
| 2026-06-11 | F131 | Implemented | Added runtime config policy facts for review thresholds, retention, tool gates, and audit chain status; exposed external-provider PHI gates in the Assistant runtime settings form; added an Admin policy controls panel covering review, PHI, external providers, retention, tool gates, and audit status; and documented the admin policy page. |
| 2026-06-11 | F132 | Implemented | Added file-backed runtime settings history with actor, email, reason, old/new value presence, changed values, history listing API, rollback API, rollback history entries, docs, and focused rollback tests. |
| 2026-06-11 | F133 | Implemented | Added sanitized runtime secret health endpoint for OAuth, OpenAI, Postgres, and Redis configuration without exposing values; added secret configuration guide and API docs. |
| 2026-06-11 | F134 | Implemented | Added data-driven API rate limiting middleware with fixed-window memory/Redis stores, route-category policy for auth, Assistant chat, file upload, retrieval search, reindex, and external-provider-capable routes, 429 envelopes and rate-limit headers, runtime config exposure, docs, and focused tests. |
| 2026-06-11 | F135 | Implemented | Added data-driven abuse/cost policy for LLM request size, OpenAI vision OCR bytes, MarkItDown OCR plugin bytes, OpenAI embedding request size/input count, and batch ingestion total bytes; enforced limits before expensive provider calls or artifact creation; exposed sanitized runtime facts; and added docs/tests. |
| 2026-06-11 | F136 | Implemented | Added a data-driven NIST AI RMF-aligned risk register covering intended use, prohibited uses, limitations, severity, residual risk, monitoring signals, human oversight, controls, and evidence refs; exposed it through an admin API and Settings governance panel; added docs/tests. |
| 2026-06-11 | F137 | Implemented | Added a data-driven OWASP LLM Top 10 threat model covering all 2025 categories, OJTFlow surfaces, residual risk, monitoring signals, mitigation status, code refs, test refs, docs, admin API, and Settings governance panel. |
| 2026-06-11 | F138 | Implemented | Added data-driven non-diagnostic/non-treatment disclaimer policy, authenticated runtime disclaimer API, route-aware app-shell banners for Assistant, Workbench, Workflows, Reviews, Retrieval, Audit, Schemas, Settings, and Help, plus docs/tests. |
| 2026-06-11 | F139-F145 | Implemented | Added Month 7 interoperability adapters for Bulk FHIR NDJSON import/export, HL7 v2 MSH/PID/OBR/OBX parsing and Observation mapping with provenance, DICOM metadata profiling, ImagingStudy-like mapping without pixel processing, DocumentReference-like mapping, API endpoints, docs, and tests. |
| 2026-06-11 | F146-F155 | Implemented | Added Month 7 analytics and external-data workflow foundation: data-driven OMOP mapping profile, vocabulary candidate catalog, OMOP preview, DQD compatibility notes, cohort/research workflow boundaries, external connector registry, external API cache metadata, source ingestion approval preview, transparent source link launchers, ETL manifest export, API endpoints, docs, and tests. |
| 2026-06-11 | F156-F157, F173 | Implemented | Added data-driven performance budgets, bounded load-smoke scenarios, `scripts/performance-smoke.py`, CI/release-check performance gate, deployment smoke plan, `scripts/deployment-smoke.py` with public URL and frontend build-version summary, runtime admin APIs, docs, and tests. |
| 2026-06-11 | F162 | Implemented | Added explicit CI gates for backend tests, Postgres migration manifest integrity, frontend build, Docker build, retrieval eval, PHI log scan, performance smoke, and bounded Playwright smoke through the Docker stack; release-check now runs migration and performance gates locally. |
| 2026-06-11 | F158 | Started | Added a data-driven observability dashboard signal contract covering API, workflow, Assistant, retrieval, background jobs, governance/security, and LLM/OCR cost panels. Hosted metrics backend, OpenTelemetry export, and rendered dashboard remain follow-up scope. |
| 2026-06-11 | F083, F095 | Implemented | Added deterministic retrieval answer synthesis backed only by support matrices, ranked evidence, citations, and Graph-NER path refs. Unsupported evidence now produces explicit refusal or gaps, and stale/deprecated/review-needed/unapproved/version-mismatched sources produce first-class freshness warnings. |
| 2026-06-11 | F093-F094 | Implemented | Added data-driven GraphRAG-lite reranking from Graph-NER query/evidence paths, `graph_support` score components, support-matrix graph metadata, `handoff_context.graph_rag_lite`, and claim-to-triple guard metadata that marks strong clinical claims without graph support as review-required. |
| 2026-06-11 | F085-F086 | Implemented | Expanded retrieval evaluation into a 12-case healthcare benchmark covering lab validation, FHIR Observation mapping, UCUM, LOINC, PHI review, prompt-injection review, RxNorm, diagnosis terminology, PubMed/MeSH routing, ClinicalTrials.gov routing, and openFDA routing; added source-diversity and unsupported-claim-rate metrics; and added a scheduled nightly retrieval benchmark workflow with JSON artifact upload. |
| 2026-06-11 | F088 | Implemented | Added fixture-backed Graph-NER evaluation for lab names, units, identifiers, medications, diagnoses, procedures, and FHIR resource names/search parameters; added node, edge, and normalized-code recall metrics; and wired the evaluator into CI, deploy, release-check, release gates, docs, and focused tests. |
| 2026-06-11 | F089, F092 | Implemented | Added persisted Graph-NER context records for retrieval packages, with owner/workflow/request/search metadata, memory/SQLite/Postgres repositories, Postgres migration 019, owner-scoped graph listing and JSONL/RDF-like export APIs, API docs, and focused restart/API tests. |
| 2026-06-11 | F090 | Implemented | Added owner-scoped graph neighborhood retrieval over persisted Graph-NER records, with query criteria for text, node, evidence, source, normalized code, FHIR-like resource type, field, and relation; exposed a bounded API response for GraphRAG/evidence exploration with docs and focused tests. |
| 2026-06-11 | F074 | Implemented | Added data-driven query transformation rules for rewrite, step-back query, multi-query expansion, and optional HyDE-style hypothetical evidence variants; integrated them into query variant provenance, rule-pack fingerprints, docs, and focused tests. |
| 2026-06-11 | F075 | Implemented | Added a data-driven query router that selects an auditable retrieval strategy route from query profile, format, resource type, metadata filters, diagnostics, concepts, standards, and tokens; exposed route metadata in query analysis, package handoff, fusion diagnostics, docs, and focused tests. |
| 2026-06-11 | F091 | Implemented | Added a Retrieval graph query panel backed by authenticated graph context listing and graph neighborhood APIs, with current-run shortcuts for top evidence/node/source, persisted graph records, result counts, warnings, and node/edge/triple result rendering. |
| 2026-06-11 | F063-F068 | Implemented | Completed governed external medical source adapter coverage for LOINC, UCUM, RxNav/RxNorm, PubMed/NCBI E-utilities, ClinicalTrials.gov API v2, and openFDA with source trust policies, connector IDs, cache/provenance expectations, query transparency boundaries, docs, and catalog consistency tests. |
| 2026-06-11 | F087 | Implemented | Added a Retrieval regression dashboard in the admin retrieval workspace, backed by aggregate relevance judgment list/summary APIs and active-run evaluation metrics for coverage@k, precision@k, MAP, MRR, nDCG, readiness, unjudged hits, and recent labeled query slices. |
| 2026-06-11 | F061, F069-F070, F095 | Implemented | Added a retrieval source freshness gate with typed report contracts, `/api/v1/retrieval/freshness`, data-driven source readiness scoring from corpus adapters, trust policies, corpus manifest, and indexed inventory, plus a Retrieval page admin panel for stale, unindexed, unreviewed, or policy-missing sources. |
| 2026-06-11 | Month 4 hardening | Implemented | Added package-time source governance for ranked retrieval evidence: selected hits now carry source policy/adapter decisions in locators and handoff context, quality signals flag review-gated/blocked/unregistered sources, corrective actions route source-governance review, and seeded SNOMED CT, ICD-10-CM, OMOP, and MeSH source policies close governance gaps. |
| 2026-06-12 | F176 | Implemented | Added chunk-level corpus ingestion ledger contracts, `GET /api/v1/retrieval/corpus/ledger`, ledger metadata on indexed corpus chunks, corpus reindex ledger summary output, docs, and focused tests linking chunks to ingestion run IDs, raw artifact hashes, adapter catalog version, reviewer decision, and source locators. |
| 2026-06-12 | F177 | Implemented | Added active retrieval index manifest contracts and `GET /api/v1/retrieval/index-manifest`, with lexical/vector/graph components, generation IDs, embedding provider/model/dimensions, stale vector chunk detection, corpus ingestion run IDs, owner-scoped Graph-NER counts, docs, and focused tests. |
| 2026-06-12 | F186 | Implemented | Added data-driven corpus partition policy for global standards, tenant policies, and private documents; partition metadata on manifest items, chunks, source inventory, Postgres/static/LlamaIndex retrieval filters, authenticated partition catalog API, source inventory partition/visibility UI filters, and focused organization-scope tests. |
| 2026-06-12 | F178 | Implemented | Added approval-gated embedding reindex safety workflow with `GET /api/v1/retrieval/embedding-reindex/dry-run`, `POST /api/v1/jobs/embedding-reindex`, deterministic approval tokens, sanitized rollback markers, post-run manifest/quality comparison, docs, and focused tests. |
| 2026-06-12 | F179 | Implemented | Added data-driven medical source quality scoring with `knowledge/retrieval/source_quality_policy.json`, typed quality policy/score/signal contracts, per-source `quality` on `/api/v1/retrieval/freshness`, aggregate quality counts, Retrieval UI quality chips, docs, and focused tests. |
| 2026-06-12 | F180 | Implemented | Added route-specific retrieval budgets to `knowledge/retrieval/query_route_rules.json`, typed `RetrievalRouteBudget` output, budget parsing and validation, enforcement for candidate pool, returned hits, reranker candidate limit, source diversity, external-network warnings, trace/handoff metadata, docs, and focused tests. |
| 2026-06-12 | F181 | Implemented | Added data-driven citation locator normalization with `knowledge/retrieval/citation_locator_rules.json`, typed locator rule and normalized locator contracts, normalized locators on evidence/hits/support rows/citations, coverage for FHIR, PubMed, ClinicalTrials.gov, openFDA, UCUM, RxNorm, PDF pages, and internal sections, docs, and focused tests. |
| 2026-06-12 | F182 | Implemented | Added Graph-NER extraction provenance on graph nodes, edges, and triples, including extractor version, source evidence/chunk metadata, confidence, normalized-code candidates, candidate-review state, summary provenance counts, docs, and focused graph contract tests. |
| 2026-06-12 | F183 | Implemented | Added data-driven Graph-NER conflict detection for contradictory source claims, deprecated terminology mappings, conflicting units, and version-mismatched standard guidance; retrieval handoff now includes `graph_conflict_report`, answer synthesis review-gates conflicts, and focused tests cover direct and integrated paths. |
| 2026-06-12 | F184 | Implemented | Expanded durable retrieval judgments from relevance-only labels to reviewer workflow labels: relevant, partial, irrelevant, unsafe, stale, and source-policy-blocked; updated API/contracts, Postgres migration 020, SQLite local migration, UI controls, metrics/report counts, docs, and focused API/service/frontend build checks. |
| 2026-06-12 | F185 | Implemented | Added durable retrieval active-learning candidates with memory/SQLite/Postgres repositories, Postgres migration 021, API list/summary/enqueue/update routes, automatic queueing from reviewer judgments and low-confidence evaluations, Retrieval UI queue surfacing, docs, and focused service/API checks. |

## Feature Backlog

### Month 1: Product Spine And Runtime Stability

- [x] F001 Define a `ProductMode` runtime contract for `local_dev`, `demo`, `pilot`, and `production`, with different safety defaults.
- [x] F002 Add a single runtime readiness endpoint that reports Postgres, Redis, storage paths, migrations, OAuth, LLM, embeddings, retrieval, and MCP status.
- [x] F003 Add migration checksum tracking so duplicate or edited migration versions fail with a clear diagnostic before the app serves traffic.
- [x] F004 Add a `schema_migrations` admin page that shows applied migrations, pending migrations, checksum, duration, and failure reason.
- [x] F005 Add database bootstrap diagnostics that distinguish missing dependency, bad DSN, auth failure, network failure, missing extension, and duplicate migration.
- [x] F006 Add a database consistency checker for workflow JSON refs, dataset refs, output refs, knowledge chunk refs, and missing local files.
- [x] F007 Add a repair command that can mark orphaned file artifacts and orphaned DB rows without deleting anything automatically.
- [x] F008 Add a background job table for reindexing, file parsing, OCR, embedding, external ingestion, and export jobs.
- [x] F009 Add a job runner abstraction with sync local mode first and a queue-backed mode later.
- [x] F010 Persist assistant chat sessions and messages in Postgres with owner, title, timestamps, tool calls, and workflow links.
- [x] F011 Add chat session rename, archive, delete, and search APIs.
- [x] F012 Add chat session sidebar loading from the backend instead of browser-only state.
- [x] F013 Store assistant stream events as replayable audit artifacts for support debugging.
- [x] F014 Add a frontend global error event panel with request ID, endpoint, status, error code, and copyable diagnostic payload.
- [x] F015 Add request correlation IDs from frontend request to backend logs, workflow events, assistant tool calls, and retrieval traces.
- [x] F016 Make API errors consistently render in UI using `error.code`, `error.message`, `error.details`, and optional `workflow_id`.
- [x] F017 Add an operator-friendly "what can I do here?" guide to every primary page, loaded from data files rather than hardcoded React text.
- [ ] F018 Normalize scroll regions across Assistant, Retrieval, Workflow detail, and Review pages so primary content and sidebars scroll predictably. _(Started: app shell content scroll and workflow detail sticky offset are normalized.)_
- [x] F019 Add a no-mock runtime policy flag that blocks demo fixtures from appearing in production-like modes.
- [x] F020 Add config validation that refuses `OJT_LLM_PROVIDER=disabled` when the deployment mode requires real assistant AI.

### Month 2: Document, Image, Clipboard, And File Intelligence

- [ ] F021 Make upload parsing asynchronous for large PDFs, images, spreadsheets, and multi-file batches. _(Started: durable `file_parse` jobs can run immediately or remain queued; batch uploads exist; real worker mode remains.)_
- [x] F022 Add a first-class `UploadedArtifact` contract with file hash, MIME type, extension, byte size, source, user, and retention policy.
- [ ] F023 Add deduplication by content hash for uploaded documents and extracted text. _(Started: raw upload dedupe is implemented; extracted-text dedupe remains.)_
- [x] F024 Add a parsing pipeline trace with extractor chosen, fallback path, warnings, token/character counts, and confidence.
- [x] F025 Add MarkItDown extraction as one extractor option behind a common `DocumentExtractor` port.
- [x] F026 Add OpenAI vision OCR as a separate extractor option with explicit cost, model, and PHI handling metadata.
- [x] F027 Add local OCR adapter option for Tesseract or PaddleOCR behind the same extractor contract.
- [x] F028 Add image clipboard paste support that creates the same artifact/evidence records as file upload.
- [x] F029 Add multi-page OCR evidence UI with page thumbnails, bounding boxes, confidence, field labels, and source refs.
- [x] F030 Add table extraction contracts for PDFs, Excel, CSV, and screenshots, preserving cell coordinates and row provenance.
- [x] F031 Add spreadsheet workbook parsing with sheet-level profiles, header detection, merged-cell warnings, and hidden-sheet warnings.
- [x] F032 Add PDF scanned-vs-digital detection and a clear warning when OCR is required.
- [x] F033 Add document redaction preview for PHI-like text before sending content to external LLM/OCR providers.
- [x] F034 Add configurable upload retention rules by mode, tenant, source type, and sensitivity class.
- [x] F035 Add artifact download/export access controls and audit events.
- [ ] F036 Add source-linked validation issues where each issue can point to row, cell, page, bounding box, or text span. _(Started: contract supports row/cell/page/bbox/text-span references; producers and UI links remain.)_
- [x] F037 Add document extraction quality scoring based on empty text, low OCR confidence, conflicting extractors, and malformed tables.
- [x] F038 Add user-facing extraction explanation: what was read, what was skipped, and what needs review.
- [ ] F039 Add a file intake wizard that lets users choose "validate data", "extract fields", "profile FHIR", "find standards", or "ask assistant".
- [ ] F040 Add batch upload workflow creation for multiple related files with shared case/project metadata. _(Started: batch parse jobs and shared metadata exist; direct workflow creation from batch outputs remains.)_

### Month 3: Healthcare Standards And Clinical Package Layer

- [x] F041 Define `ClinicalPackage` Pydantic contracts for raw input, clinical bundle, validation, evidence, provenance, review, audit refs, and handoff context.
- [x] F042 Add FHIR-like resource builders for `Patient`, `Observation`, `DiagnosticReport`, and `DocumentReference`.
- [x] F043 Add resource-level field provenance so every generated FHIR-like element has source evidence or an explicit derived-value note.
- [x] F044 Add `lab_result_v1` to FHIR-like `Observation` mapping with patient reference, effective date, code text, value quantity, and unit.
- [x] F045 Add review gates for semantic normalization of lab names, units, dates, patient IDs, diagnoses, medications, and procedures.
- [x] F046 Add FHIR-like `Bundle` export for approved workflow outputs.
- [x] F047 Add FHIR `OperationOutcome`-like validation output for profile errors and warnings.
- [x] F048 Add lightweight FHIR profile registry files for supported resource families and required fields.
- [x] F049 Add FHIR search parameter generation for profile outputs and retrieval hints.
- [x] F050 Add Provenance-like internal records for parser, converter, assistant, reviewer, and retrieval-derived transformations.
- [x] F051 Add AuditEvent-like export for workflow events, review events, auth events, and tool execution.
- [x] F052 Add LOINC candidate generation contract for observation names without automatically replacing source text.
- [x] F053 Add UCUM validation contract for units with source unit, normalized candidate, validation result, and review requirement.
- [x] F054 Add RxNorm candidate generation contract for medication fields.
- [x] F055 Add SNOMED CT placeholder contract for diagnoses/findings with license-aware implementation notes.
- [x] F056 Add terminology evidence UI that separates source text, candidate code, confidence, source terminology, and reviewer decision.
- [x] F057 Add clinical package diff view showing raw fields vs generated resources vs approved changes.
- [x] F058 Add canonical package export as JSON with all evidence and review metadata included.
- [x] F059 Add package import validation so OJTFlow can reload its own exported package without losing provenance.
- [x] F060 Add clear wording in UI and docs that v0 output is FHIR-like unless validated by a real FHIR validator.

### Month 4: Retrieval, RAG, Corpus, And Graph-NER

Month 4 is the evidence layer for the whole product. The target is not a
generic chatbot RAG feature. It is a governed healthcare retrieval subsystem
that can explain why a workflow validation issue, terminology candidate,
clinical package field, or assistant answer is supported by trusted sources.

The system should treat retrieval as an auditable pipeline:

1. Source registration: every source enters through a catalog record with owner,
   license, allowed use, release/version, fetch method, refresh cadence, reviewer
   state, and prohibited-use notes.
2. Ingestion: adapters fetch or import source material into immutable raw
   artifacts, then create normalized documents with hashes and source locators.
3. Chunking: source-specific chunking profiles preserve section headings,
   resource names, field names, table rows, API record IDs, page/line refs, and
   source URLs so answer citations are inspectable.
4. Indexing: lexical, metadata, vector, and graph indexes are built with explicit
   generation IDs. Provider/model/dimension changes must mark indexes stale
   rather than silently mixing embeddings.
5. Query planning: the router classifies intent, clinical domain, safety risk,
   data format, requested standard, and source filters before choosing retrieval
   strategy.
6. Retrieval and reranking: hybrid search collects candidates, applies metadata
   filters, reranks with cross-encoder or deterministic fallback, diversifies by
   source, and records all ranking decisions.
7. Graph-NER: entities and relations are extracted from query/data/evidence,
   normalized to terminology candidates when possible, persisted as graph
   context, and used for GraphRAG-lite expansion.
8. Synthesis: answers are generated only from the support matrix. Unsupported
   claims become gaps, warnings, or review tasks instead of confident text.
9. Evaluation: every change to chunking, embeddings, reranking, routing, or
   graph expansion must run against retrieval and Graph-NER benchmark fixtures.

Healthcare source priority should be explicit:

- Tier 1: official standards and terminology sources such as HL7 FHIR, UCUM,
  RxNorm/RxNav, LOINC metadata where license allows, ClinicalTrials.gov,
  PubMed/NCBI metadata, openFDA, and local approved enterprise policy documents.
- Tier 2: organization-approved implementation guides, mapping specs, SOPs,
  data dictionaries, and customer-specific validation rules.
- Tier 3: exploratory literature or external search results. These may inform
  review but should not override Tier 1/2 sources without human approval.

The Month 4 architecture should expose these primary contracts:

- `SourceCatalogEntry`: source identity, owner, trust tier, license, lifecycle,
  refresh cadence, connector, reviewer state, intended use, prohibited use.
- `IngestionRun`: source version, fetch timestamp, raw artifact refs, content
  hashes, adapter version, errors, warnings, approval state, request ID.
- `KnowledgeDocument`: normalized document metadata, source locators, standard
  system, clinical domain, release/version, document hash, retention policy.
- `KnowledgeChunk`: chunk text hash, source span/table/page locator, heading
  path, metadata facets, embedding generation ID, graph extraction refs.
- `RetrievalTrace`: query variants, route selected, filters, candidate counts,
  reranker decisions, fallback path, warnings, latency, request ID.
- `SupportMatrix`: answer claim, evidence chunk refs, graph path refs, scores,
  support status, freshness state, reviewer requirement, limitation text.
- `GraphContextRecord`: extracted node/edge/triple refs, normalized code
  candidates, source evidence refs, workflow refs, export IDs, owner scope.

The advanced RAG backlog should stay data-driven and configurable. Techniques
from practical RAG research should be adapted only when they improve traceable
healthcare evidence:

- Query rewriting and multi-query expansion for messy operator questions.
- Step-back querying for standards explanations where the user asks a narrow
  implementation question but needs broader context first.
- HyDE-style hypothetical evidence only when clearly labeled as synthetic query
  expansion and never stored as evidence.
- Corrective RAG when retrieved evidence is weak, stale, blocked, or too narrow.
- RAG-Fusion / reciprocal-rank fusion for hybrid lexical-vector candidates.
- Cross-encoder reranking in local GPU mode, with deterministic fallback.
- GraphRAG-lite for entity-neighborhood expansion after initial evidence is
  found, not before source trust and metadata filters are applied.
- Self-checking synthesis that refuses unsupported claims and emits explicit
  gaps, not hidden model confidence.

Month 4 is done only when these acceptance gates hold:

- Retrieval can answer "why is this validation issue true?" with cited evidence.
- Retrieval can answer "which standard/source supports this mapping?" with a
  support matrix and source locator.
- Retrieval can explain stale, deprecated, blocked, or review-gated sources.
- Graph-NER records are persisted, owner-scoped, exportable, and searchable.
- Embedding provider/model changes cannot silently reuse incompatible vectors.
- Weak retrieval produces corrective actions, not a fabricated answer.
- Admins can inspect source freshness, eval quality, and graph coverage.
- CI or scheduled jobs track retrieval quality and Graph-NER quality over time.

- [x] F061 Add a corpus ingestion framework with source adapters, license metadata, release version, fetch time, hash, and reviewer state.
- [x] F062 Add official source adapters for FHIR specification pages relevant to Patient, Observation, DiagnosticReport, DocumentReference, Provenance, and AuditEvent.
- [x] F063 Add official source adapter for LOINC release metadata and selected public guide pages, respecting login/license boundaries.
- [x] F064 Add UCUM service metadata ingestion for validation and conversion guidance.
- [x] F065 Add RxNav/RxNorm API metadata ingestion and monthly release tracking.
- [x] F066 Add PubMed/NCBI E-utilities connector for literature metadata and abstracts where allowed.
- [x] F067 Add ClinicalTrials.gov API connector for trial summaries and condition/intervention filters.
- [x] F068 Add openFDA connector for labels, adverse events, recalls, and device metadata where useful.
- [x] F069 Add source inventory lifecycle states: candidate, approved, deprecated, blocked, failed, and needs review.
- [x] F070 Add source-level trust policy with domain, standard system, clinical scope, intended use, refresh cadence, and license constraints.
- [x] F071 Add chunking profiles for standards docs, terminology pages, structured API records, PDFs, and internal policies.
- [x] F072 Add metadata extraction for resource type, standard system, clinical domain, field names, version, section heading, and source locator.
- [x] F073 Add hybrid retrieval strategy presets: lexical-only, vector-only, hybrid RRF, metadata-filtered, high-recall review, and exact-source lookup.
- [x] F074 Add query transformation strategies from RAG research: rewrite, decomposition, step-back query, HyDE optional mode, and multi-query expansion.
- [x] F075 Add query router that chooses strategy by query intent, data format, clinical domain, source filters, and risk flags.
- [x] F076 Add cross-encoder reranking for local GPU mode with a configurable model, candidate limit, and fallback.
- [x] F077 Add OpenAI embedding mode and local Hugging Face embedding mode with dimension compatibility checks and reindex requirements.
- [x] F078 Add vector index generation IDs so retrieval can detect stale embeddings after provider/model changes.
- [x] F079 Add pgvector HNSW/IVFFlat index management docs and migration path for large corpora.
- [x] F080 Add metadata filter pre-application for all retrieval frameworks, including LlamaIndex adapter parity.
- [x] F081 Add source-aware diversity selection that can be tuned per query route.
- [x] F082 Add corrective RAG behavior: if evidence is weak, ask for missing filters, broaden source scope, or trigger reindex suggestion.
- [x] F083 Add self-checking retrieval answer synthesis that refuses unsupported claims and returns missing-evidence gaps.
- [x] F084 Add evidence support matrix for each answer claim with source ID, chunk locator, matched terms, score, and reasoning.
- [x] F085 Add retrieval benchmark datasets for lab validation, FHIR mapping, UCUM unit checks, PHI review, and external medical search routing.
- [x] F086 Add nightly retrieval evaluation job that tracks recall@k, MRR, nDCG, coverage, source diversity, and unsupported-claim rate.
- [x] F087 Add retrieval regression dashboard in the UI for admins.
- [x] F088 Add Graph-NER entity extraction evaluation fixtures for lab names, units, identifiers, medications, diagnoses, procedures, and resource names.
- [x] F089 Add graph persistence for extracted entities/triples instead of only returning graph context in retrieval packages.
- [x] F090 Add graph neighborhood retrieval that expands evidence by normalized concept, resource type, source, and relation.
- [x] F091 Add graph query UI for entities, relationships, source evidence, and workflow references.
- [x] F092 Add knowledge graph export as JSONL or RDF-like triples for downstream tools.
- [x] F093 Add GraphRAG-lite answer path: retrieve chunks, extract entities, expand neighborhood, rerank with graph support, synthesize with citations.
- [x] F094 Add hallucination guard that compares answer claims to evidence triples and flags unsupported clinical assertions.
- [x] F095 Add source freshness warnings when retrieved medical standards are old, deprecated, or version-mismatched.
- [x] F176 Add a source-ingestion run ledger that links every indexed chunk to an approved ingestion run, raw artifact hash, adapter version, and reviewer decision.
- [x] F177 Add a retrieval index manifest endpoint that reports lexical/vector/graph index generation IDs, provider/model dimensions, stale status, and chunk counts.
- [x] F178 Add embedding reindex safety workflow: dry-run impact report, admin approval, background job execution, rollback marker, and post-run quality comparison.
- [x] F179 Add medical source quality scoring that combines trust tier, lifecycle state, freshness, license restrictions, reviewer state, and source coverage.
- [x] F180 Add route-specific retrieval budgets for max candidates, reranker limit, source diversity, external-network permission, and latency target.
- [x] F181 Add citation locator normalization for FHIR pages, PubMed records, ClinicalTrials.gov studies, openFDA records, UCUM entries, RxNorm concepts, PDF pages, and internal policy sections.
- [x] F182 Add Graph-NER extraction provenance per node and edge, including extractor version, source chunk, confidence, normalized-code candidates, and review state.
- [x] F183 Add graph conflict detection for contradictory source claims, deprecated terminology mappings, conflicting units, and version-mismatched standard guidance.
- [x] F184 Add retrieval judgement workflow so reviewers can label evidence hits as relevant, irrelevant, unsafe, stale, or source-policy-blocked.
- [x] F185 Add active-learning queue that converts low-confidence retrieval, unsupported claims, and reviewer corrections into benchmark candidates.
- [x] F186 Add tenant-scoped corpus partitions and source policies so enterprise customers can separate global standards, tenant policies, and private documents.
- [ ] F187 Add PHI-safe private corpus ingestion with redaction preview, retention policy stamping, and external-provider blocking by default.
- [ ] F188 Add PubMed/ClinicalTrials/openFDA query transparency records showing exact external query, filters, result IDs, cache hit state, and rate-limit metadata.
- [ ] F189 Add retrieval observability spans for ingestion, chunking, embedding, lexical search, vector search, reranking, graph expansion, synthesis, and support-matrix validation.
- [ ] F190 Add answer-grounding regression tests that compare final assistant text against support matrices and fail on uncited medical claims.
- [ ] F191 Add source-drift monitoring that alerts when official source releases change, indexes are stale, or nightly benchmarks regress.
- [ ] F192 Add graph coverage dashboard for node/edge counts by domain, normalized terminology coverage, unsupported-claim rates, and reviewer backlog.
- [ ] F193 Add configurable local model registry for embedding, reranking, NER, and relation extraction models with hardware requirements and fallback policy.
- [ ] F194 Add LlamaIndex adapter parity tests that prove the framework path preserves OJTFlow filters, source governance, support matrix output, and audit traces.
- [ ] F195 Add retrieval disaster-recovery export/import for source catalog, ingestion manifests, chunk manifests, vector generation metadata, graph records, and relevance judgements.

Recommended Month 4 continuation order:

1. Build the source-ingestion ledger and retrieval index manifest first
   (F176-F178). Without this, large-corpus retrieval cannot prove exactly which
   source version, embedding generation, and reviewer state produced an answer.
2. Add evidence quality scoring, route budgets, locator normalization, and
   Graph-NER extraction provenance next (F179-F182). These make the retrieval
   output understandable and reviewable by enterprise users.
3. Add graph conflict detection, relevance judgement workflow, and active
   learning queue (F183-F185). These close the loop between poor answers,
   reviewer feedback, and benchmark growth.
4. Add tenant/private corpus controls and external-query transparency
   (F186-F188). This is required before customer policy documents or sensitive
   data dictionaries become searchable.
5. Add retrieval observability, answer-grounding regression, source-drift
   monitoring, graph coverage dashboards, model registry, LlamaIndex parity, and
   disaster-recovery export/import (F189-F195). These make Month 4 operational
   enough for pilot and enterprise evaluation.

### Month 5: Assistant, Streaming, MCP, And Operator Workflows

- [x] F096 Make Assistant the default end-user landing page with task starters and file drop zone.
- [x] F097 Add persistent ChatGPT-like sessions backed by Postgres, with backend-owned title generation.
- [x] F098 Stream planning text, tool arguments, tool progress, tool results, and final answer in a single chronological message timeline.
- [x] F099 Add collapsible tool cards inline between assistant messages instead of a separate long tool panel.
- [x] F100 Add tool-call progress events for long parsing, retrieval, OCR, embedding, and workflow operations.
- [x] F101 Add cancellation support for active assistant streams and backend jobs.
- [x] F102 Add retry and continue actions for failed assistant tool calls.
- [x] F103 Add strict OpenAI tool schemas with `additionalProperties=false` and required nullable fields where needed.
- [x] F104 Add model/provider settings for planning model, synthesis model, vision model, embedding model, and local model endpoint.
- [x] F105 Add per-tool permissions: read-only, write-gated, admin-only, external-network, PHI-sensitive, and destructive.
- [x] F106 Add user confirmation UI before write-gated assistant actions such as creating workflow, approving review, exporting package, or reindexing corpus.
- [x] F107 Add assistant memory only for safe operational preferences, never raw PHI or uploaded content.
- [x] F108 Add assistant answer templates for validation report, retrieval answer, standards explanation, workflow status, review summary, and export summary.
- [x] F109 Add assistant attachment support for multiple files, pasted images, text snippets, and selected workflow/retrieval context.
- [x] F110 Add assistant "show evidence" action that jumps to the exact source row, page box, chunk, or workflow event.
- [x] F111 Add assistant "create review task" action for unresolved data quality or terminology decisions.
- [x] F112 Add assistant "generate mapping draft" action that creates a review-gated transform plan instead of directly transforming data.
- [x] F113 Add MCP resources for workflows, reviews, retrieval sources, schemas, and knowledge source inventory.
- [x] F114 Add MCP prompts for standard tasks such as validate lab CSV, profile FHIR, find UCUM evidence, and inspect pending reviews.
- [x] F115 Add remote MCP deployment design with OAuth/resource indicators, per-user scoping, rate limits, and audit.
- [x] F116 Add MCP tool-call audit events linked to assistant chat sessions and workflow events.
- [x] F117 Add agent evaluation fixtures for natural-language tool selection and final answer faithfulness.
- [x] F118 Add assistant safety tests for prompt injection in uploaded data, tool descriptions, retrieved chunks, and user messages.

### Month 6: Governance, Security, Privacy, And Enterprise Administration

- [x] F119 Add tenant/organization model with users, roles, groups, and workspace-level settings.
- [x] F120 Add RBAC roles for viewer, operator, reviewer, data steward, admin, and auditor.
- [x] F121 Add ownership checks across workflows, reviews, chat sessions, artifacts, source inventory, runtime settings, and exports.
- [x] F122 Add service-account identity for ingestion jobs, CI, and automation.
- [x] F123 Add PHI classification contract for fields, rows, documents, chunks, chat messages, and generated outputs.
- [x] F124 Add PHI redaction policy engine with masking, suppression, tokenization placeholder, and review-gated reveal.
- [x] F125 Add no-raw-PHI logging guard and log scanner for development and CI.
- [x] F126 Add configurable external-provider policy controlling which data can be sent to OpenAI, OCR, embedding APIs, and external search APIs.
- [x] F127 Add prompt-injection policy that treats user data, documents, retrieved chunks, and tool metadata as untrusted.
- [x] F128 Add output validation for LLM-generated plans, summaries, and export descriptions before UI display or storage mutation.
- [x] F129 Add audit export endpoint for workflows, reviews, assistant tool calls, auth events, setting changes, and source ingestion.
- [x] F130 Add immutable audit hash chain for high-risk deployment mode.
- [x] F131 Add admin policy page for review thresholds, PHI handling, external providers, retention, and tool gates.
- [x] F132 Add runtime setting history with who changed what, old value, new value, reason, and rollback.
- [x] F133 Add secret configuration guide and runtime secret health checks without exposing secret values.
- [x] F134 Add rate limiting for auth, assistant chat, file upload, retrieval search, reindex, and external connectors.
- [x] F135 Add abuse and cost controls for LLM calls, OCR calls, embedding reindex, and batch ingestion.
- [x] F136 Add NIST AI RMF-aligned risk register covering intended use, limitations, monitoring, and human oversight.
- [x] F137 Add OWASP LLM Top 10 threat model with concrete mitigations mapped to code and tests.
- [x] F138 Add legal/compliance disclaimer surfaces for non-diagnostic, non-treatment, human-reviewed intended use.

### Month 7: Interoperability, Analytics, And External Data Workflows

- [x] F139 Add Bulk FHIR NDJSON import parser for selected resource types with streaming validation.
- [x] F140 Add Bulk FHIR NDJSON export for approved clinical packages.
- [x] F141 Add HL7 v2 starter parser for MSH, PID, OBR, and OBX lab result messages.
- [x] F142 Add HL7 v2 to FHIR-like Observation mapping with source segment provenance.
- [x] F143 Add DICOM metadata parser for study, series, instance, modality, laterality, accession, and de-identification status.
- [x] F144 Add ImagingStudy-like mapping for DICOM metadata, no pixel processing by default.
- [x] F145 Add DocumentReference mapping for uploaded PDFs, images, notes, and extracted reports.
- [x] F146 Add OMOP mapping design for Person, Observation, Measurement, ConditionOccurrence, DrugExposure, VisitOccurrence, and Note.
- [x] F147 Add OMOP vocabulary candidate contract that can link FHIR-like resources to standard concept IDs.
- [x] F148 Add OMOP export preview with row counts, concept coverage, unmapped fields, and data quality warnings.
- [x] F149 Add OHDSI Data Quality Dashboard compatibility notes and future integration path.
- [x] F150 Add cohort/research workflow concept draft that remains separate from clinical decision support.
- [x] F151 Add external source connector registry with auth requirements, rate limits, license notes, and update cadence.
- [x] F152 Add external API call cache with source release/version metadata and invalidation policy.
- [x] F153 Add source ingestion approval workflow before newly fetched documents are searchable.
- [x] F154 Add external-link launchers for PubMed, ClinicalTrials.gov, openFDA, LOINC, UCUM, RxNav, and FHIR docs with query transparency.
- [x] F155 Add provenance-preserving export package for downstream ETL and analytics teams.

### Month 8: Scale, Quality, Deployment, And Release Readiness

- [x] F156 Add load tests for workflow creation, retrieval search, assistant stream, upload parsing, and reindexing.
- [x] F157 Add performance budgets for p50/p95 API latency, assistant first-token latency, retrieval latency, and upload processing time.
- [ ] F158 Add observability dashboard with API metrics, job metrics, retrieval metrics, LLM cost, error rate, and queue depth. _(Started: data-driven dashboard signal contract exists; hosted metrics backend/rendered dashboard remain.)_
- [ ] F159 Add structured logs with request IDs, workflow IDs, user IDs, tenant IDs, and redaction status.
- [ ] F160 Add OpenTelemetry traces for assistant stream, retrieval pipeline, document extraction, and workflow orchestration.
- [ ] F161 Add production Docker Compose profile and cloud deployment manifests with explicit env docs.
- [x] F162 Add CI gates for backend tests, frontend build, migration duplicate check, repo hygiene, retrieval eval, and critical Playwright smoke tests.
- [ ] F163 Add seed-free production mode that requires real configured auth, storage, LLM, and source inventory.
- [ ] F164 Add demo mode that is explicitly labeled and isolated from production data.
- [ ] F165 Add release checklist for security, migration, data retention, external providers, OAuth, logs, and backup/restore.
- [ ] F166 Add backup and restore procedure for Postgres plus file artifacts.
- [ ] F167 Add disaster recovery drill for database restore and artifact consistency validation.
- [ ] F168 Add customer pilot onboarding guide with sample non-PHI datasets, known limitations, and support checklist.
- [ ] F169 Add admin manual covering runtime settings, retrieval source governance, user roles, review policies, and troubleshooting.
- [ ] F170 Add end-user tutorial path: upload data, ask assistant, inspect evidence, approve review, export package.
- [ ] F171 Add evaluator guide for B2B buyers explaining architecture, standards, governance, and limitations.
- [ ] F172 Add security review packet with threat model, dataflow, dependency inventory, and known residual risks.
- [x] F173 Add deployment smoke test command that prints public URL, API health, auth status, retrieval status, and frontend build version.
- [ ] F174 Add release candidate tag process after all blocking checks pass.
- [ ] F175 Add post-release monitoring plan with incident triage, rollback, and regression evaluation.

## Dependency Order

1. Stabilize runtime and persistence before adding more AI behavior.
2. Make uploads, artifacts, evidence, and chat sessions durable before adding
   large document/RAG features.
3. Add clinical package/provenance contracts before exporting FHIR-like or OMOP
   outputs.
4. Add source governance before ingesting large external corpora.
5. Add retrieval evaluation before tuning embeddings, reranking, and GraphRAG.
6. Add role/tenant/security policy before remote MCP or enterprise pilots.
7. Add export and interoperability features only after review gates and evidence
   provenance are reliable.
8. Add scale/performance work once the product path is stable enough to measure.

## Top 20 Recommended Next Features

These should be handled first because they unlock the rest:

1. F002 runtime readiness endpoint.
2. F003 migration checksum tracking.
3. F006 database and artifact consistency checker.
4. F010 persistent assistant chat sessions.
5. F014 global frontend error diagnostic panel.
6. F017 page-level guide content from data files.
7. F021 async upload parsing.
8. F022 `UploadedArtifact` contract.
9. F024 parsing pipeline trace.
10. F028 clipboard image artifact support.
11. F041 `ClinicalPackage` contract.
12. F043 field-level provenance for generated clinical resources.
13. F061 corpus ingestion framework.
14. F073 retrieval strategy presets.
15. F084 evidence support matrix.
16. F086 nightly retrieval evaluation job.
17. F097 persistent ChatGPT-like sessions.
18. F098 unified streaming message/tool timeline.
19. F105 per-tool permissions.
20. F119 tenant/organization model.

## Explicit Non-Goals Until Governance Exists

- Do not present OJTFlow as clinical decision support.
- Do not auto-diagnose, recommend treatment, or make medication decisions.
- Do not normalize sensitive clinical meaning without review.
- Do not send raw PHI to external providers without explicit policy and user
  approval.
- Do not expose remote MCP tools before OAuth, tenant scoping, rate limits, and
  audit are implemented.
- Do not load large third-party corpora directly into git.
- Do not hide demo/mock data inside production-like screens.
- Do not call output "FHIR compliant" until it passes real FHIR validation.
