# Quarantined AI Tests

These tests were removed from the real AI smoke path because they could produce
green results without proving live product behavior.

## Removed Files

- `tests/test_graph_ner_evaluation.py`
  - Reason: duplicated a subset of live retrieval checks and only proved that
    Graph-NER metadata appeared on a positive query. It did not reject unrelated
    hits, did not require assistant citations, and did not exercise negative RAG
    behavior.

- `tests/test_production_semantic_rag_guardrails.py`
  - Reason: overlapped with `tests/test_real_gpu_api_smoke.py` and still allowed
    weak assistant evidence assertions. The replacement smoke requires real
    provider metadata, vector-hit metadata, expected source IDs, citation linkage,
    and strict negative-query rejection.

## Not Product Evidence

Older unit tests that use fake planners, static retrieval repositories,
dependency overrides, or deterministic assistant fallback may still be useful as
unit tests, but they must not be cited as evidence that the live AI/RAG product
works. Real AI product evidence is now concentrated in:

- `tests/test_real_gpu_api_smoke.py`

That file is expected to fail when the live backend returns unrelated retrieval
hits, retrieves no evidence for a positive RAG question, fabricates citations, or
runs with fake/non-semantic provider metadata.

## Upload/Image Endpoint Tests Removed From Product Evidence

- Removed endpoint-style tests from `tests/test_document_intake.py` that used
  `httpx.ASGITransport`, FastAPI dependency overrides, in-memory repositories,
  `FakeDocumentExtractor`, and fake PNG bytes. Those tests could pass without a
  running API, authentication, Postgres artifact storage, or real OCR.
- Removed `tests/test_document_intake.py::test_file_parse_job_persists_trace_and_extracted_text_ref`
  because it asserted trace metadata produced by `FakeDocumentExtractor`, not a
  real parser/OCR path.
- Removed fake upload/image success tests from `tests/test_document_parsing.py`:
  - `test_file_workflow_extraction_failure_is_persisted`;
  - `test_image_auto_extraction_uses_openai_vision_when_markitdown_is_empty`;
  - `test_image_auto_extraction_reports_missing_vision_key_when_markitdown_is_empty`;
  - `test_markitdown_converter_enables_ocr_plugin_when_configured`;
  - `test_markitdown_converter_keeps_plain_mode_when_ocr_disabled`;
  - `test_api_upload_rejects_unsupported_extension`;
  - `test_api_upload_enforces_size_limit`;
  - `test_api_upload_honors_configured_extension_allowlist`;
  - `test_api_upload_workflow_rejects_blank_instruction`;
  - `test_api_upload_workflow_rejects_missing_instruction`;
  - `test_api_upload_workflow_normalizes_form_text`;
  - `test_api_extract_only_uses_standard_envelope`;
  - `test_api_upload_csv_workflow_bypasses_optional_extractors`;
  - `test_api_upload_csv_workflow_returns_structured_error_for_decode_failure`.
  These used fake images, fake OpenAI responses, fake workflow services,
  monkeypatched extraction, MarkItDown constructor fakes, in-memory storage, or
  ASGI-only clients. They cannot prove that real upload or image intake works in
  the running product.

The real upload/image product checks now live in
`tests/test_real_gpu_api_smoke.py`:

- Workbench multipart CSV upload creates a real workflow from a real CSV through
  the running API;
- Assistant file attachment extraction sends a real CSV to `/parse/extract`;
- Assistant pasted-image upload sends a valid generated PNG through
  `/parse/clipboard/images/jobs` with `extractor=auto`, the same route used by
  the frontend clipboard path.
