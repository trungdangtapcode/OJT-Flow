# Schema And Contracts

OJTFlow should avoid letting each module define its own payload shape. The backbone uses Pydantic contracts as the source of truth. Later, JSON Schema and OpenAPI can be generated from these contracts.

## Contract Ownership

| Contract | Owner file | Purpose |
| --- | --- | --- |
| `WorkflowState` | `src/ojtflow/core/contracts/workflow.py` | Current truth of a workflow |
| `WorkflowEvent` | `src/ojtflow/core/contracts/events.py` | Append-only audit timeline |
| `AgentResult` | `src/ojtflow/core/contracts/agent.py` | Standard agent output |
| `Issue` | `src/ojtflow/core/contracts/issue.py` | Validation, policy, or data-quality issue |
| `Evidence` | `src/ojtflow/core/contracts/evidence.py` | Source support for claims and actions |
| `HumanReview` | `src/ojtflow/core/contracts/review.py` | Review pause/resume object |
| `ToolSpec` | `src/ojtflow/core/contracts/tools.py` | Deterministic tool metadata |
| `DatasetRecord` | `src/ojtflow/core/contracts/storage.py` | Stored data metadata |
| `ValidationReport` | `src/ojtflow/core/contracts/data.py` | Validation result |
| `TransformationPlan` | `src/ojtflow/core/contracts/data.py` | Proposed or approved actions |
| `TransformationOutput` | `src/ojtflow/core/contracts/data.py` | Output ref/hash/diff |
| `ExplanationReport` | `src/ojtflow/core/contracts/data.py` | Evidence-grounded explanation |

## WorkflowState Schema

`WorkflowState` is the root object:

```json
{
  "workflow_id": "wf_...",
  "created_at": "ISO timestamp",
  "updated_at": "ISO timestamp",
  "status": "needs_human_review",
  "user_instruction": "Clean this CSV...",
  "input": {},
  "intent": {},
  "profile": {},
  "schema_profile": {},
  "retrieved_context": [],
  "validation_report": {},
  "transformation_plan": {},
  "review": {},
  "output": null,
  "explanation": null,
  "risk_flags": [],
  "audit_event_refs": []
}
```

Important rules:

- `input` stores references and hashes, not raw files.
- `profile` stores derived summaries.
- `retrieved_context` stores evidence objects.
- `validation_report` stores the issue list.
- `transformation_plan` stores actions and review flags.
- `review` stores human decision state.
- `output` stores output ref and hash.
- `explanation` stores supported claims and limitations.

## DatasetRecord Schema

Used by `DatasetStore`:

```json
{
  "dataset_id": "ds_...",
  "workflow_id": "wf_...",
  "source_kind": "inline",
  "declared_format": "csv",
  "detected_format": "csv",
  "byte_size": 1234,
  "sha256": "hex",
  "storage_ref": "memory://datasets/ds_..."
}
```

A production adapter can map `storage_ref` to:

- local file
- PostgreSQL row
- S3/GCS object
- restricted healthcare object store

## DataProfile Schema

Used after parse/profile:

```json
{
  "format": "csv",
  "row_count": 3,
  "column_count": 5,
  "fields": [
    {
      "name": "patient_id",
      "normalized_name": "patient_id",
      "inferred_types": ["string"],
      "sample_values": ["P001", "P002"],
      "missing_count": 0,
      "non_empty_count": 3,
      "unique_count": 3,
      "confidence": 1.0,
      "possible_phi": true
    }
  ],
  "warnings": []
}
```

## ValidationReport Schema

```json
{
  "report_id": "val_...",
  "valid": false,
  "schema_id": "lab_result_v1",
  "schema_confidence": 1.0,
  "severity_summary": {
    "info": 0,
    "warning": 3,
    "error": 0,
    "critical": 0
  },
  "issues": [],
  "requires_review": true
}
```

Validation does not automatically fix data. It reports issues and review requirements.

## Issue Schema

```json
{
  "issue_id": "iss_...",
  "kind": "missing_value",
  "severity": "warning",
  "message": "Required field 'unit' is empty on row 3",
  "location": {
    "row": 3,
    "column": "unit",
    "field": "unit",
    "source_ref": "memory://datasets/ds_..."
  },
  "suggested_action": "ask_user_or_clinician_before_filling",
  "requires_review": true,
  "metadata": {}
}
```

Issue kinds should stay stable because tests, UI, metrics, and review rules depend on them.

## Evidence Schema

```json
{
  "evidence_id": "ev_...",
  "source_type": "schema",
  "source_id": "schema:lab_result_v1",
  "source_version": "1.0.0",
  "claim": "Lab result records require date, patient_id, lab_name, value, and unit fields.",
  "locator": {},
  "confidence": 0.93,
  "trust_level": "approved"
}
```

Evidence source types include:

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

This is why OCR, DICOM, and vision can plug in later without a separate explanation architecture.

## HumanReview Schema

```json
{
  "review_id": "rev_...",
  "workflow_id": "wf_...",
  "status": "pending",
  "trigger": "reviewable_transformation_plan",
  "question": "Approve the proposed data cleaning and conversion actions before execution?",
  "proposed_action": {
    "plan_id": "plan_...",
    "actions": []
  },
  "allowed_decisions": ["approve", "approve_with_edits", "reject", "clarify"],
  "decision": null,
  "decision_payload": null,
  "decided_by": null,
  "decided_at": null
}
```

## TransformationPlan Schema

```json
{
  "plan_id": "plan_...",
  "target_format": "json",
  "actions": [
    {
      "action_id": "act_...",
      "action": "normalize_date",
      "field": "date",
      "affected_rows": [3],
      "reason": "Field 'date' has non-ISO date",
      "requires_review": true,
      "parameters": {
        "target_format": "YYYY-MM-DD",
        "original_value": "2026/01/02"
      }
    }
  ],
  "requires_review": true
}
```

Only an approved transformation plan should be executed.

## ToolSpec Schema

```json
{
  "name": "convert_csv_to_json",
  "version": "0.1.0",
  "input_model": "ConvertCsvToJsonInput",
  "output_model": "ConvertCsvToJsonOutput",
  "permission_scope": "data:transform",
  "allowed_agents": ["transformation_agent"],
  "requires_approval": false,
  "idempotent": true,
  "logs_sensitive_raw_data": false
}
```

MCP wrappers should preserve this schema instead of inventing separate tool metadata.

## Storage Tables Future Mapping

When replacing in-memory storage with a DB:

| Table | Main fields |
| --- | --- |
| `workflows` | `workflow_id`, `status`, `state_json`, `created_at`, `updated_at` |
| `workflow_events` | `event_id`, `workflow_id`, `actor`, `event_type`, `severity`, `metadata_json` |
| `datasets` | `dataset_id`, `workflow_id`, `storage_ref`, `sha256`, `format`, `byte_size` |
| `reviews` | `review_id`, `workflow_id`, `status`, `decision`, `payload_json` |
| `validation_reports` | `report_id`, `workflow_id`, `schema_id`, `valid`, `summary_json` |
| `evidence` | `evidence_id`, `workflow_id`, `source_type`, `source_id`, `claim`, `confidence` |
| `knowledge_sources` | `source_id`, `version`, `trust_level`, `path`, `metadata_json` |

## Schema Versioning Rule

Version these artifacts:

- workflow state schema
- API request/response schema
- knowledge schema
- validation schema
- prompt templates
- tool specs
- vector indexes
- graph snapshots
- OCR/vision model artifacts

Rules:

- adding an optional field: minor version
- changing field meaning: major version
- removing a field: major version and migration
- changing an enum value: major version unless a backward alias exists

