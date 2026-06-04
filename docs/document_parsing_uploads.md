# Document Parsing Uploads

## Scope

PR #1 adds document upload support to the existing OJTFlow workflow backbone.
The feature is intentionally conservative:

- upload routes accept multipart files;
- the API validates filename, extension, extractor choice, empty files, and size;
- the raw upload is stored as an immutable artifact;
- extracted markdown/text is stored as a derived artifact;
- workflow parsing, validation, review, transformation, and explanation run from the derived text artifact;
- failed extraction/parsing is persisted as a failed workflow with audit events and returned as a structured API error;
- structured text uploads (`.csv`, `.json`, `.yaml`, `.md`, `.txt`) bypass optional document
  extractors and go directly through deterministic parsing.

The upload feature does not claim production OCR, FHIR compliance, diagnosis, treatment, or autonomous medical interpretation.

## Runtime Configuration

| Setting | Default | Purpose |
| --- | --- | --- |
| `OJT_MAX_UPLOAD_BYTES` | `26214400` | Maximum uploaded file size in bytes. Must be positive. |
| `OJT_MAX_INLINE_DATA_BYTES` | `1048576` | Maximum inline text/JSON payload size for pasted workflow, conversion, validation, FHIR profile, and OCR evidence requests. Must be positive. Larger inputs should use upload workflows. |
| `OJT_UPLOAD_READ_CHUNK_BYTES` | `1048576` | Read chunk size for multipart uploads. Must be positive. |
| `OJT_ALLOWED_UPLOAD_EXTENSIONS` | Built-in allowlist | Comma-separated extension allowlist. Values may include or omit the leading dot. This may only narrow supported upload extensions. |

Default supported extensions:

```text
.pdf,.docx,.xlsx,.xls,.pptx,.png,.jpg,.jpeg,.tiff,.tif,.bmp,.gif,.webp,.html,.htm,.md,.txt,.csv,.json,.yaml,.yml
```

Old Office formats such as `.doc` and `.ppt` are not enabled by default because the current dependency declaration does not guarantee reliable support for them.

Configured upload extensions are normalized to lowercase, deduplicated, and
validated during settings load. Values must be simple supported upload
extensions such as `.csv` or `.pdf`; unsupported or unsafe values such as
`.exe`, `.tar.gz`, paths, wildcards, or extensions containing spaces are
rejected before the API starts accepting traffic.

## Dependencies

`python-multipart` is a base dependency because FastAPI validates multipart route parameters when the app is built.

Document extraction dependencies remain optional:

```bash
pip install 'ojtflow[parsing]'
```

adds MarkItDown for lightweight extraction. For heavier PDF/image extraction experiments:

```bash
pip install 'ojtflow[parsing-full]'
```

adds MinerU / `magic-pdf`. MinerU is optional because it has larger runtime and model requirements.

Structured text uploads do not require either optional extractor package. For
example, uploading a CSV through `/parse/upload/workflow` stores the raw file,
stores a derived UTF-8 text artifact, records `extractor_used=direct_text_upload`,
and then uses the normal CSV parser.

## API Routes

```text
POST /api/v1/parse/extract
POST /api/v1/parse/upload/workflow
GET  /api/v1/parse/extractors
```

`/parse/extract` previews extracted markdown/text and metadata.

`/parse/upload/workflow` creates a full workflow from an uploaded file.
If the workflow fails after the run has been created, for example a non-UTF-8
CSV upload, the route returns an error envelope with `error.workflow_id` and the
failed workflow remains available through `GET /api/v1/workflows/{workflow_id}`.

Both upload routes return the standard API envelope:

```json
{
  "data": {},
  "error": null
}
```

Expected structured upload errors:

- `413 upload_too_large`
- `415 unsupported_upload`
- `422 tool_execution_error`

## Persistence Model

For workflow uploads, OJTFlow stores two artifacts:

1. `uploaded_file_raw`: original bytes, original sanitized filename, source format, SHA-256, and byte size.
2. `uploaded_file_extracted_text`: derived markdown/text, extraction metadata, warnings, SHA-256, and storage ref.

`WorkflowState.input` points to the derived text artifact once extraction succeeds so review resume can re-parse deterministic text. The raw artifact remains linked under `workflow.handoff_context.raw_upload` for audit and reproducibility.
For structured text uploads, `WorkflowState.input.declared_format` is the
detected parser format (`csv`, `json`, `yaml`, or `markdown`) instead of forced
markdown.

## Security Notes

- Uploaded filenames are never used as paths.
- Filenames with path separators, null bytes, missing names, unsupported extensions, or excessive length are rejected.
- MarkItDown plugins are disabled by default.
- Extractor choice is validated server-side.
- Empty files are rejected.
- File size is enforced while reading chunks.
- Client MIME type is treated as advisory only; extension policy is enforced server-side.

## Migration Note

Any deployment that already runs the API must install the updated base dependency set so `python-multipart` is available. Existing text workflows, review workflows, storage tables, and conversion endpoints are unchanged.
