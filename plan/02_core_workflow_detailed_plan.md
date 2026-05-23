# Core Workflow Detailed Plan

The core workflow is the first real product feature. It proves that OJTFlow can transform and explain structured data safely without relying on the model as the executor.

## Scope

MVP formats:

- JSON
- YAML
- CSV
- FHIR-like JSON fixtures
- Bulk FHIR-like NDJSON as a later Phase 1 extension

MVP operations:

- Detect format
- Parse data
- Profile structure and values
- Infer simple schema
- Match registered schema fixture
- Validate data
- Propose cleaning actions
- Require review for semantic changes
- Convert between JSON/YAML/CSV
- Produce diff, warnings, output hash, validation report, and explanation-ready evidence

Out of scope for this phase:

- Real patient data
- Autonomous clinical interpretation
- Model-generated code execution
- Full FHIR validation engine
- GraphRAG, SSL training, OCR, DICOM, segmentation

## Components

### Data Intake

Responsibilities:

- Accept pasted text or uploaded file.
- Record declared format, detected format, filename, size, hash, and storage reference.
- Store raw input in dataset storage, not in workflow event logs.
- Reject files over configured size limit.
- Reject binary content unless routed to future OCR/DICOM handlers.

Initial metadata:

```json
{
  "dataset_id": "ds_uuid",
  "workflow_id": "wf_uuid",
  "source_kind": "upload",
  "declared_format": "csv",
  "detected_format": "csv",
  "byte_size": 1234,
  "sha256": "hash",
  "storage_ref": "storage://datasets/ds_uuid/input.csv"
}
```

### Format Detection

Detection priority:

1. Explicit user option if valid.
2. File extension if provided.
3. Syntax parser probes.
4. Content heuristics.

Detection should return confidence and reasons.

```json
{
  "format": "csv",
  "confidence": 0.92,
  "reasons": ["comma-delimited header", "consistent row count"],
  "warnings": []
}
```

### Parsing

JSON:

- Parse with standard JSON library.
- Detect duplicate keys if feasible.
- Preserve order where useful.

YAML:

- Parse with safe loader.
- Reject unsafe tags.
- Report anchors/aliases if they affect output.

CSV:

- Sniff delimiter.
- Handle quoted commas.
- Detect header row.
- Detect inconsistent row length.
- Preserve original row number.

FHIR-like JSON:

- Detect `resourceType`.
- Detect `Bundle.entry`.
- Store resource path references for validation and explanation.

### Profiling

Profile outputs should support schema inference, validation, and explanation.

Fields:

- row count
- column count
- column names
- inferred primitive types
- sample values
- missing counts
- uniqueness
- min/max for numeric/date fields
- malformed row count
- possible PHI/sensitive field names
- date format patterns
- categorical values and cardinality

### Schema Inference

MVP inference should be conservative.

For each field:

- name
- normalized name
- observed type candidates
- requiredness estimate
- missingness rate
- examples
- confidence
- possible aliases

Do not pretend that inferred schema is authoritative. Label it as inferred and ask for review if there are multiple plausible matches.

### Schema Registry

Start with file-based schemas in `knowledge/schemas`.

Recommended fixtures:

- `sales_report_v1`
- `lab_result_v1`
- `patient_demographics_v1`
- `fhir_observation_like_v1`
- `medication_request_like_v1`

Each schema should include:

- schema ID
- version
- field names
- required fields
- types
- allowed values
- units if relevant
- aliases
- data dictionary links
- validation examples

### Validation

Validation report should distinguish syntax, schema, semantic, safety, and policy issues.

Issue categories:

- `syntax_error`
- `malformed_row`
- `missing_required_field`
- `missing_value`
- `type_mismatch`
- `invalid_enum`
- `date_format_inconsistency`
- `unit_mismatch`
- `duplicate_key`
- `duplicate_row`
- `schema_mismatch`
- `possible_phi`
- `prompt_injection_pattern`
- `unsupported_operation`

Validation output:

```json
{
  "valid": false,
  "schema_id": "lab_result_v1",
  "schema_confidence": 0.84,
  "severity_summary": {
    "critical": 0,
    "error": 1,
    "warning": 3,
    "info": 2
  },
  "issues": [],
  "requires_review": true
}
```

### Cleaning Plan

Cleaning is not automatic when it changes meaning.

Safe automatic actions:

- Trim whitespace in header names while preserving original names in metadata.
- Normalize line endings.
- Convert CSV records to JSON strings without changing values.

Review-required actions:

- Fill missing values.
- Drop rows.
- Normalize dates.
- Map columns to different semantic names.
- Convert units.
- Mask sensitive fields before export.
- Resolve conflicting schema candidates.

Cleaning plan:

```json
{
  "plan_id": "plan_uuid",
  "actions": [
    {
      "action": "normalize_date",
      "field": "date",
      "from_patterns": ["YYYY/MM/DD"],
      "to_pattern": "YYYY-MM-DD",
      "affected_rows": [2],
      "requires_review": true,
      "reason": "Date format inconsistency"
    }
  ]
}
```

### Conversion

Conversion tools:

- `json_to_yaml`
- `yaml_to_json`
- `csv_to_json`
- `json_to_csv`
- `csv_to_yaml` via parsed intermediary
- `yaml_to_csv` via parsed intermediary

Rules:

- Preserve values exactly unless an approved transformation says otherwise.
- Keep row numbers and source references where possible.
- Use deterministic ordering for generated output when practical.
- Return warnings for lossy conversions, such as nested JSON to flat CSV.
- Validate output after conversion.

### Transformation Diff

Diff should summarize what changed in business terms and machine terms.

Examples:

- `format_changed: csv -> json`
- `rows_preserved: 120/120`
- `fields_renamed: []`
- `values_modified: 0`
- `rows_dropped: 0`
- `date_values_normalized: 1`
- `sensitive_fields_masked: ["patient_id"]`

## API Behavior

### Direct Convert

Use for deterministic smoke tests and simple user tasks.

Request:

```json
{
  "input_format": "csv",
  "target_format": "json",
  "data": "a,b\n1,2\n",
  "options": {
    "orientation": "records"
  }
}
```

Response:

```json
{
  "status": "success",
  "output_format": "json",
  "output": "[{\"a\":\"1\",\"b\":\"2\"}]",
  "warnings": [],
  "metadata": {
    "row_count": 1
  }
}
```

### Workflow Start

Use for full governed behavior.

Request:

```json
{
  "instruction": "Clean this CSV, convert it to JSON, and explain anomalies.",
  "input_format": "csv",
  "target_format": "json",
  "data": "date,patient_id,lab_name,value,unit\n...",
  "options": {
    "require_human_review": true,
    "schema_name": "lab_result_v1"
  }
}
```

Response:

```json
{
  "workflow_id": "wf_uuid",
  "status": "needs_human_review",
  "summary": "CSV parsed. Validation found missing values and date inconsistency.",
  "review_id": "rev_uuid"
}
```

## Test Plan

### Unit Tests

- JSON valid and invalid parsing.
- YAML safe parsing and unsafe tag rejection.
- CSV quoted commas, missing cells, extra cells, no header, malformed rows.
- Type inference for string, integer, float, date, boolean.
- Schema validation required fields, optional fields, enums, types.
- Conversion round trips where lossless.
- Lossy conversion warnings.

### Integration Tests

- CSV to JSON workflow without review when no semantic changes are requested.
- CSV cleaning workflow pauses for review.
- Rejected review cancels transformation.
- Approved review resumes transformation.
- Prompt injection in CSV cell is flagged and never treated as instruction.
- Sensitive fields produce risk flags and masking recommendation.

### Golden Workflow

The golden workflow should include:

- messy lab CSV
- lab schema fixture
- transformation example
- validation issues
- review decision
- final JSON
- explanation report
- audit event list

## Acceptance Criteria

- Parser errors are structured and user-readable.
- Converted outputs validate against target representation rules.
- Validation reports include issue locations.
- Cleaning actions that change meaning require review.
- Workflow can be reconstructed from events.
- Direct APIs and workflow APIs share the same underlying deterministic tools.
- No model call is required for deterministic parse/validate/convert tests.

## Risks and Controls

| Risk | Control |
| --- | --- |
| CSV edge cases consume time | Use Python CSV library and limit MVP behavior |
| Inferred schema looks too authoritative | Label inferred schema and confidence clearly |
| Conversion loses nested structure | Warn and require explicit flattening options |
| Medical fields imply diagnosis | Keep output as data quality and schema explanation only |
| Prompt injection embedded in data | Separate instruction and data, flag suspicious strings |

## Deliverables

- Core data tool package.
- Format detection and parsing tests.
- Profiling and schema inference report.
- Validation report contract.
- Conversion tools.
- Transformation diff contract.
- Golden workflow fixture.
- API endpoints for `/convert`, `/validate`, and `/workflows`.
