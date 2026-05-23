# Scaffolding Backbone Plan

This is the first thing to build. The proposal has many advanced modules, but they should all plug into one shared system backbone. If this scaffold is weak, every later feature will invent its own contracts and the project will become hard to integrate. If this scaffold is strong, the system can grow from a JSON/CSV workflow into a medical AI platform without changing its core shape.

## Backbone Goal

Create a minimal but production-shaped repository scaffold that makes these concepts real from day one:

- Workflow state
- Workflow event stream
- Agent response contract
- Deterministic tool interface
- Evidence object
- Issue/risk object
- Human review object
- Audit object
- Storage references
- API contract
- Evaluation fixture pattern

Do not start with GraphRAG, SSL, OCR, DICOM, or segmentation. Start with the contracts that those features will eventually use.

## Proposed Repository Shape

```text
ojtflow/
  apps/
    api/
      app/
        main.py
        deps.py
        settings.py
        routes/
          workflows.py
          convert.py
          validate.py
          explain.py
          review.py
          health.py
        schemas/
          requests.py
          responses.py
      tests/
    web/
      README.md
  packages/
    core/
      ojtflow_core/
        ids.py
        time.py
        errors.py
        contracts/
          workflow.py
          events.py
          agent.py
          issue.py
          evidence.py
          review.py
          audit.py
          storage.py
        policy/
          risk_rules.py
          permissions.py
    data_tools/
      ojtflow_data_tools/
        detect.py
        parse_json.py
        parse_yaml.py
        parse_csv.py
        profile.py
        validate.py
        convert.py
        diff.py
        masking.py
    agents/
      ojtflow_agents/
        orchestrator.py
        parser_agent.py
        schema_agent.py
        validation_agent.py
        transformation_agent.py
        retrieval_agent.py
        explanation_agent.py
        safety_agent.py
        review_agent.py
    retrieval/
      ojtflow_retrieval/
        ingest.py
        chunking.py
        lexical.py
        vector.py
        hybrid.py
        evidence_pack.py
        evaluation.py
    graphner/
      ojtflow_graphner/
        entities.py
        relations.py
        extraction.py
        normalization.py
        graph_store.py
    medical/
      ojtflow_medical/
        fhir_like.py
        jp_core_aliases.py
        clinical_explanation.py
        ocr_contracts.py
        dicom_contracts.py
        visual_evidence.py
    mcp_servers/
      structured_data_server/
      schema_validation_server/
      rag_context_server/
      workflow_audit_server/
      human_review_server/
    storage/
      ojtflow_storage/
        models.py
        repositories.py
        migrations/
    evaluation/
      ojtflow_evaluation/
        fixtures.py
        metrics.py
        golden_workflows.py
        reports.py
  data/
    fixtures/
      structured/
      healthcare/
      prompt_injection/
      ocr_synthetic/
      dicom_public/
  knowledge/
    schemas/
    data_dictionaries/
    transformation_examples/
    error_library/
    governance/
  infra/
    docker/
    compose.yaml
    github-actions/
    terraform/
    helm/
  docs/
    api.md
    architecture.md
    governance.md
    demo_script.md
```

For the current repository, this can remain as planned scaffold documentation until code implementation begins. When implementation starts, create only the files needed for Phase 0 and Phase 1, then add later directories when the module becomes real.

## Dependency Rule

Every package depends inward toward `core`.

Allowed dependency direction:

```text
api -> agents -> data_tools
api -> retrieval
api -> storage
agents -> core
agents -> data_tools
agents -> retrieval
agents -> graphner
agents -> medical
data_tools -> core
retrieval -> core
graphner -> core
medical -> core
storage -> core
evaluation -> core
mcp_servers -> core + stable service packages
```

Forbidden:

- `core` must not depend on FastAPI, LangGraph, MCP, databases, cloud SDKs, or model providers.
- deterministic data tools must not call the LLM gateway.
- retrieval must not mutate workflow state directly.
- explanation must not create unsupported clinical claims.
- agents must not write files or export data except through approved tools.

## Core Domain Contracts

### Workflow State

The workflow state is the single source of truth for a run.

```json
{
  "workflow_id": "wf_uuid",
  "created_at": "2026-05-17T00:00:00Z",
  "status": "running",
  "user_instruction": "Clean this CSV, convert it to JSON, and explain anomalies",
  "input": {
    "dataset_ref": "storage://datasets/input-001",
    "input_hash": "sha256",
    "declared_format": "csv",
    "detected_format": "csv"
  },
  "intent": {
    "task_type": "clean_convert_explain",
    "target_format": "json",
    "requires_explanation": true
  },
  "schema_profile": null,
  "retrieved_context": [],
  "validation_report": null,
  "transformation_plan": null,
  "review": null,
  "output": null,
  "explanation": null,
  "risk_flags": [],
  "audit_event_refs": []
}
```

Status values:

- `created`
- `running`
- `needs_human_review`
- `approved`
- `rejected`
- `completed`
- `failed`
- `cancelled`

### Workflow Event

Every meaningful action emits an event. Events are append-only.

```json
{
  "event_id": "evt_uuid",
  "workflow_id": "wf_uuid",
  "timestamp": "2026-05-17T00:00:00Z",
  "actor_type": "agent",
  "actor_id": "validation_agent",
  "event_type": "validation.completed",
  "severity": "info",
  "summary": "Validated 120 rows and found 3 warnings",
  "input_refs": ["storage://datasets/input-001"],
  "output_refs": ["storage://reports/validation-001"],
  "metadata": {
    "tool_name": "validate_schema",
    "schema_version": "lab_result_v2"
  }
}
```

Event families:

- `workflow.created`
- `workflow.started`
- `agent.started`
- `agent.completed`
- `agent.failed`
- `tool.called`
- `tool.completed`
- `tool.failed`
- `retrieval.completed`
- `validation.completed`
- `review.requested`
- `review.decided`
- `transformation.completed`
- `explanation.completed`
- `workflow.completed`
- `workflow.failed`

### Agent Result

All agents return the same envelope.

```json
{
  "status": "success",
  "summary": "CSV parsed successfully",
  "confidence": 0.94,
  "data": {},
  "issues": [],
  "evidence": [],
  "next_recommended_action": "validate_schema"
}
```

Allowed statuses:

- `success`
- `warning`
- `error`
- `needs_human_review`
- `blocked_by_policy`

### Issue Object

Issues should be precise enough to drive UI, review, and metrics.

```json
{
  "issue_id": "iss_uuid",
  "kind": "missing_value",
  "severity": "warning",
  "location": {
    "row": 17,
    "column": "unit",
    "source_ref": "storage://datasets/input-001"
  },
  "message": "Unit is missing for a lab result",
  "suggested_action": "ask_user_or_clinician",
  "requires_review": true
}
```

Severity values:

- `info`
- `warning`
- `error`
- `critical`

### Evidence Object

Evidence is the bridge between tools, retrieval, medical explainability, and audit.

```json
{
  "evidence_id": "ev_uuid",
  "source_type": "schema",
  "source_id": "schema:lab_result_v2",
  "source_version": "2.0.0",
  "locator": {
    "field": "loinc_code",
    "page": null,
    "bbox": null,
    "dicom_ref": null
  },
  "claim": "LOINC code is required for lab observations",
  "confidence": 0.91,
  "trust_level": "approved"
}
```

Source types:

- `input_data`
- `schema`
- `data_dictionary`
- `transformation_example`
- `validation_report`
- `tool_output`
- `human_decision`
- `audit_event`
- `ocr_box`
- `dicom_metadata`
- `image_mask`
- `video_track`

### Human Review Object

Review is a first-class state, not a side message.

```json
{
  "review_id": "rev_uuid",
  "workflow_id": "wf_uuid",
  "status": "pending",
  "trigger": "data_cleaning_changes",
  "question": "Approve filling missing region values with Unknown?",
  "proposed_action": {
    "fill_missing": {
      "field": "region",
      "value": "Unknown"
    }
  },
  "allowed_decisions": ["approve", "edit", "reject", "clarify"],
  "decision": null,
  "decided_by": null,
  "decided_at": null
}
```

Review triggers:

- Low schema confidence
- Data cleaning changes
- Row drops or imputation
- Sensitive or PHI-like fields detected
- External tool/API call
- Large or costly operation
- Medical consequence or clinical ambiguity
- Unsupported or conflicting evidence

### Tool Contract

All deterministic tools should follow one envelope.

```json
{
  "tool_name": "convert_csv_to_json",
  "tool_version": "0.1.0",
  "input_schema": "ConvertCsvToJsonInput",
  "output_schema": "ConvertCsvToJsonOutput",
  "permission_scope": "data:transform",
  "requires_approval": false,
  "idempotent": true,
  "logs_sensitive_raw_data": false
}
```

Tool implementation rules:

- Validate inputs before execution.
- Return structured outputs.
- Never execute generated code.
- Never silently repair data without reporting the change.
- Return warnings for lossy transformations.
- Emit audit events for calls and results.
- Revalidate transformed output.

## Initial API Scaffold

### Workflow API

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/api/v1/workflows` | POST | Start a governed workflow |
| `/api/v1/workflows/{id}` | GET | Fetch state, output, explanation, audit summary |
| `/api/v1/workflows/{id}/events` | GET/SSE | Stream or poll workflow progress |
| `/api/v1/review/{id}` | POST | Submit approve/edit/reject/clarify decision |

### Direct Tool API

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/api/v1/convert` | POST | Direct deterministic JSON/YAML/CSV conversion |
| `/api/v1/validate` | POST | Validate data against provided or inferred schema |
| `/api/v1/explain` | POST | Generate grounded explanation from existing report/evidence |
| `/api/v1/health` | GET | Health check |

The direct APIs are useful for testing and demos. The workflow API is the real product path.

## Initial Database Tables

For SQLite MVP, keep schemas simple but migration-ready.

| Table | Purpose |
| --- | --- |
| `workflows` | Current workflow state and status |
| `workflow_events` | Append-only event stream |
| `datasets` | Dataset references, hashes, metadata, storage path |
| `schemas` | Registered schema metadata and current version |
| `validation_reports` | Validation report payloads and summaries |
| `transformation_outputs` | Output references, hashes, format, diff summary |
| `reviews` | Pending and completed human review decisions |
| `evidence` | Source IDs, claims, confidence, provenance |
| `audit_logs` | Security-sensitive audit events |
| `knowledge_sources` | RAG source metadata |
| `retrieval_runs` | Query, top-k source IDs, scores, retrieval mode |

Do not store unnecessary raw PHI in logs. Demo data should be synthetic.

## Minimal Workflow State Machine

```text
created
  -> running
  -> needs_human_review
      -> approved -> running
      -> rejected -> cancelled
      -> clarify  -> running
  -> completed
  -> failed
```

The orchestrator should decide whether to pause based on risk rules, agent confidence, validation severity, and explicit user options.

## First Vertical Slice

The first working slice should be intentionally small:

Input:

```csv
date,patient_id,lab_name,value,unit
2026-01-01,P001,HbA1c,7.4,%
2026/01/02,P002,HbA1c,,
bad-date,P003,Glucose,120,mg/dL
```

Instruction:

```text
Clean this CSV, convert it to JSON, and explain anomalies.
```

Expected behavior:

1. Create workflow.
2. Detect CSV.
3. Profile rows, columns, missingness, date inconsistency.
4. Retrieve a lab result schema fixture.
5. Validate required fields and date format.
6. Propose cleaning actions.
7. Pause for review because filling missing values or normalizing dates changes meaning.
8. On approval, run deterministic conversion.
9. Return JSON, validation report, explanation, evidence, and audit trail.

This slice proves the backbone without needing advanced AI.

## Scaffold Acceptance Checklist

- `core` contracts are importable without web, DB, LLM, or cloud dependencies.
- Workflow state has stable typed fields.
- Every agent can return a common `AgentResult`.
- Every issue has severity, location, message, and review flag.
- Every evidence object can cite schema, validation, tool, human, OCR, DICOM, image, or video source.
- Review objects can pause and resume workflows.
- Tool contracts declare permissions and approval requirements.
- Events are append-only and tied to `workflow_id`.
- API route names and request/response schemas are stable.
- Storage design can work in SQLite now and PostgreSQL later.
- Golden-path fixture exists and can be used for tests.
- No later module needs to bypass the backbone.

## Implementation Sequence for the Scaffold

1. Create package structure for `core`, `data_tools`, `agents`, `storage`, and `apps/api`.
2. Implement Pydantic contracts in `core/contracts`.
3. Implement deterministic parser and profiler shells in `data_tools`.
4. Implement a simple in-memory or SQLite workflow repository.
5. Implement workflow creation and status API.
6. Implement direct parse/profile/validate/convert functions.
7. Implement event emission.
8. Implement review pause/resume state.
9. Add golden workflow fixture and tests.
10. Only then add model gateway, retrieval, and MCP wrappers.

## Backbone Risks

| Risk | Impact | Control |
| --- | --- | --- |
| State shape changes too often | Breaks agents and API | Version workflow state early |
| Agents return free-form text | Hard to test and audit | Enforce `AgentResult` envelope |
| Tools mutate data silently | Unsafe and unexplainable | Require diffs, reports, and review gates |
| Retrieval mixes trusted and untrusted content | RAG poisoning | Add trust metadata from the first ingest design |
| Medical claims appear in explanation without support | Safety and credibility issue | Use supported-claim map and limitations |
| Advanced modules arrive before core workflow | Integration failure | Phase gates block research modules until MVP works |

## Definition of Done

The scaffold is done when a new developer can answer these questions from the code and docs:

- Where does workflow state live?
- How does an agent report success, failure, warnings, evidence, and next action?
- How does a deterministic tool declare input, output, permission, and review needs?
- How is human review represented?
- How is an explanation tied to evidence?
- How are audit events created?
- Where will RAG, Graph-NER, OCR, DICOM, and vision evidence plug in later?

If those answers are obvious, the backbone is strong enough to build on.
