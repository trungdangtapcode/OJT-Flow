# AuditEvent-Like Export v0

## Purpose

`GET /api/v1/audit/export` now includes `audit_events_like[]`, a sanitized
FHIR AuditEvent-like projection over:

- append-only workflow events;
- review events;
- authentication audit records;
- Assistant and MCP tool execution records;
- settings/source-ingestion/generic audit records when present.

The projection exists for healthcare compliance review and interoperability
handoff. It is not a claim of full HL7 FHIR conformance.

## Contract

Each `AuditEventLikeRecord` includes:

- `resourceType = "AuditEvent"`
- `audit_event_id`
- `category`
- `action`
- `recorded`
- `outcome`
- `outcome_desc`
- `workflow_id`
- `request_id`
- `source_event_ref`
- `source_record_ref`
- `agent[]`
- `source`
- `entity[]`
- `metadata`

Supported categories:

- `workflow_event`
- `review_event`
- `auth_event`
- `tool_execution`
- `setting_change`
- `source_ingestion`
- `generic_audit_record`

Actions follow the FHIR AuditEvent-style one-letter convention:

- `C`: create
- `R`: read/export/list
- `U`: update/decision/approval
- `D`: delete/revoke/logout
- `E`: execute/other event

Outcomes are `success`, `minor_failure`, or `serious_failure`.

## Sanitization

`audit_events_like[]` does not include raw uploaded data, raw tool arguments, raw
tool output, OAuth secrets, or local file content. Entities may include:

- workflow IDs;
- workflow event IDs;
- review IDs;
- assistant session/message IDs;
- artifact refs already present in workflow event refs;
- SHA-256 input/output hashes;
- source audit record IDs.

Generic audit records remain available in `records[]`, and raw workflow events
remain available in `workflow_events[]` for callers that need the original
OJTFlow contracts.

## Verification

Run:

```bash
python -m pytest tests/test_audit_records.py::test_audit_export_api_packages_records_events_and_coverage -q
```
