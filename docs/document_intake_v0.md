# Document Intake V0

This document describes the Month 2 file-intelligence backbone now available in
the backend. The goal is to make uploads durable and traceable before adding
advanced OCR, table extraction, and clipboard UX.

## Current System

The existing product already supports synchronous document upload through
`POST /api/v1/parse/upload/workflow`. That route reads file bytes, extracts text,
and starts a workflow in one request.

The new intake path separates those responsibilities:

1. Register the uploaded file as an `UploadedArtifact`.
2. Deduplicate raw bytes by owner, SHA-256 hash, and byte size.
3. Create a durable `file_parse` background job.
4. Run extraction through the `DocumentExtractor` port.
5. Store extracted text as a dataset record.
6. Persist a `ParsingPipelineTrace` with extractor, fallback, warnings, counts,
   confidence, and output refs.

Local dev can still run the job immediately with `execute_now=true`. A future
queue-backed runner can process the same job contract without changing clients.

## API

### Create Upload Parse Job

`POST /api/v1/parse/upload/jobs`

Multipart fields:

| Field | Type | Default | Notes |
| --- | --- | --- | --- |
| `file` | file | required | Uses configured extension and size limits. |
| `extractor` | string | `auto` | `auto`, `markitdown`, `mineru`, `openai_vision`, or `tesseract`. |
| `execute_now` | boolean | `true` | `false` leaves a queued durable job. |

Response envelope:

```json
{
  "data": {
    "job": {
      "job_id": "job_...",
      "job_type": "file_parse",
      "status": "succeeded"
    },
    "artifact": {
      "artifact_id": "art_...",
      "filename": "lab.csv",
      "mime_type": "text/csv",
      "byte_size": 42,
      "sha256": "...",
      "source": "upload",
      "storage_ref": "file:///.../var/uploads/blob_....csv",
      "duplicate_of_artifact_id": null
    },
    "trace": {
      "trace_id": "trace_...",
      "artifact_id": "art_...",
      "source_format": "csv",
      "requested_extractor": "auto",
      "extractor_chosen": "markitdown",
      "warnings": [],
      "char_count": 120,
      "token_count_estimate": 30,
      "confidence": 0.95,
      "text_storage_ref": "file:///.../var/datasets/ds_....txt"
    }
  },
  "error": null
}
```

### List Uploaded Artifacts

`GET /api/v1/parse/artifacts?limit=100`

Returns user-owned artifact metadata. Raw file bytes are not returned.

### Create Clipboard Image Parse Job

`POST /api/v1/parse/clipboard/images/jobs`

JSON body:

```json
{
  "data_base64": "iVBORw0KGgo...",
  "filename": "clipboard.png",
  "mime_type": "image/png",
  "extractor": "auto",
  "execute_now": false
}
```

The response shape is the same as `POST /api/v1/parse/upload/jobs`, with
`artifact.source` set to `clipboard`.

### Get Uploaded Artifact

`GET /api/v1/parse/artifacts/{artifact_id}`

Returns one user-owned artifact metadata record.

### List Parse Traces

`GET /api/v1/parse/artifacts/{artifact_id}/traces`

Returns extraction traces for that artifact, newest first.

## Storage

Raw upload bytes are stored under `var/uploads/`. Extracted text is stored through
the existing `DatasetStore` and uses the configured backend metadata tables.

Postgres tables:

- `ojtflow.uploaded_artifacts`
- `ojtflow.document_parse_traces`

SQLite local tables with the same logical fields are created by the SQLite
backbone initializer.

## Deduplication

Deduplication is owner-scoped in v0:

- The first upload for `(owner_user_id, sha256, byte_size)` becomes canonical.
- Later identical uploads create a new artifact row with
  `duplicate_of_artifact_id` set.
- Duplicate rows reuse the canonical `storage_ref`.

This avoids duplicate bytes while preserving a user-visible upload/audit record.
Extracted-text dedupe is still a follow-up because it needs extractor-version and
normalization metadata to avoid merging incompatible outputs.

## Extension Points

- `DocumentExtractor` is the application port for MarkItDown, MinerU, OpenAI
  vision, and future local OCR adapters.
- OpenAI vision OCR is selectable as `openai_vision`. Its trace metadata includes
  provider, model, billable cost basis, and PHI-handling warning so external
  provider use is visible in audit/support views.
- Local Tesseract OCR is selectable as `tesseract` when Pillow, pytesseract, and
  the Tesseract binary are installed. Its trace metadata marks execution as local
  and non-billable, with a PHI-handling note for host storage/log policy.
- `ParsingPipelineTrace.steps` can represent multi-stage extraction later:
  scanned-PDF detection, OCR, layout parsing, table extraction, redaction preview,
  and validation handoff.
- `SourceLocation` now supports row/column, page, bounding box, text span, sheet
  and table-cell coordinates. Validation issues, OCR evidence, and extracted
  table cells should point through this common contract.
- `TableExtractionProfile`, `ExtractedTable`, and `TableCell` define the
  canonical table output shape for CSV, Excel, PDF, HTML, and screenshots. Actual
  high-quality table parsers are still follow-up adapters.
- `UploadedArtifact.retention_policy` is stamped at intake now; tenant/mode
  retention rules will become configurable in a later Month 2 item.

## Remaining Month 2 Work

- Real queue worker mode for long-running parse jobs.
- Multi-file batch uploads.
- Extracted-text deduplication with extractor/version awareness.
- Frontend paste UX wired to the clipboard image artifact endpoint.
- OCR page evidence, table coordinate contracts, spreadsheet profiling, and
  redaction preview.
