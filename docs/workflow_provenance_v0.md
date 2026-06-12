# Workflow Provenance v0

## Purpose

`WorkflowState.provenance[]` is the workflow-level lineage contract. It records
how a workflow moved from input artifact to parsing, retrieval, validation,
review, conversion, explanation, and completion.

This is separate from generic audit records:

- workflow provenance explains data lineage and transformation context;
- generic audit records explain security-sensitive actions, actors, hashes, and
  exportable compliance history;
- workflow events remain the append-only operational timeline.

Each provenance record references one or more workflow events through
`event_refs` so the three layers stay connected without duplicating raw payloads.

## Record Shape

`WorkflowProvenanceRecord` includes:

- `provenance_id`
- `activity`
- `agent`
- `event_refs`
- `source_refs`
- `target_refs`
- `evidence_ids`
- `issue_ids`
- `review_ids`
- `request_id`
- `occurred_at`
- `summary`
- `metadata`

Supported activities are:

- `workflow`
- `assistant`
- `upload`
- `extract`
- `parse`
- `profile`
- `retrieve_evidence`
- `validate`
- `policy_review`
- `review`
- `convert`
- `retrieval_derived_transform`
- `explain`
- `failure`

## Workflow Coverage

The workflow service appends provenance from the same boundary that appends
workflow events. Current coverage includes:

- workflow creation and uploaded dataset refs;
- document extraction from raw file artifacts to extracted text artifacts;
- parser runs, including review-resume re-parsing before conversion;
- FHIR-like profiling;
- trusted retrieval evidence selection;
- validation reports and issue IDs;
- safety and human-review gates;
- assistant-created mapping drafts and review tasks;
- conversion output refs and transformation plan IDs;
- retrieval-derived conversion records linked to evidence IDs;
- explanation generation;
- workflow completion and failure.

`handoff_context.provenance_summary` exposes record count, activity counts, and
the latest provenance ID for UI and downstream tools.

## Clinical Package Link

`ClinicalPackage.handoff_context.workflow_provenance_ids` links package exports
back to workflow-level provenance. Package-specific Provenance-like records
remain in `ClinicalPackage.provenance` for FHIR-like bundle projection, while
workflow provenance captures the broader end-to-end path, including assistant
and upload/extraction lineage.

## UI

Workflow Detail -> Audit now shows:

- `Workflow provenance`: lineage records with activity, agent, linked refs,
  summary, and timestamp;
- `Audit timeline`: append-only workflow events.

Older persisted workflows may have empty provenance lists. They remain loadable
because the field defaults to an empty list.

## Verification

Run:

```bash
python -m pytest tests/test_workflow_service.py::test_workflow_pauses_for_review_then_completes_after_approval tests/test_workflow_service.py::test_clean_lab_workflow_builds_clinical_package_with_field_provenance -q
npm --prefix frontend run build
```
