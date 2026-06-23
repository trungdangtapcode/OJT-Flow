# Test Audit Report

## Scope

This audit covers the AI/RAG product-evidence tests, not the whole unit-test
suite. Unit tests that use fakes or static fixtures may still be useful for
internal behavior checks, but they are not evidence that the live AI/RAG product
works.

## Current AI Smoke Suite

- Real smoke file kept: `tests/test_real_gpu_api_smoke.py`
- Duplicate/weak AI smoke files removed:
  - `tests/test_graph_ner_evaluation.py`
  - `tests/test_production_semantic_rag_guardrails.py`
- Quarantine note: `tests/QUARANTINED_AI_TESTS.md`
- Live upload/image failure proof: `UPLOAD_IMAGE_FAILURE_PROOF.md`
- Smoke runner updated: `scripts/run-real-smoke-tests` now runs only the real
  AI smoke file.

## Meaningful Tests Added

The remaining smoke tests require:

- running API at `OJT_REAL_SMOKE_API_BASE_URL`;
- real bearer token via `OJT_REAL_SMOKE_AUTH_TOKEN`;
- visible GPU through `torch.cuda` or `nvidia-smi`;
- Postgres and Redis runtime configuration;
- real OpenAI/HuggingFace embedding metadata;
- real OpenAI LLM metadata;
- no fake/mock/stub/hash/random/lexical provider metadata;
- vector retrieval metadata on returned evidence;
- expected FHIR/LOINC source IDs for a Vietnamese HbA1c/FHIR query;
- answer citations that link to retrieved source IDs;
- no ranked hits for unrelated negative queries;
- assistant positive RAG answers with retrieved evidence and source IDs;
- assistant negative RAG refusal without fabricated citations.
- Workbench multipart CSV upload through `/parse/upload/workflow`;
- Assistant file attachment extraction through `/parse/extract`;
- Assistant table-style scanned diabetes follow-up PDF extraction through
  `/parse/extract`;
- Assistant table-style pasted-image handling through `/parse/clipboard/images/jobs`;
- exact generated clinical-fact oracle for the scanned diabetes follow-up
  document, including lab table values, units, flags, medications, plan, and
  PHI preserved-or-redacted context.

## Latest Real Run

Command:

```bash
make real-smoke
```

Result:

- 11 passed
- 0 failed
- 0 skipped

The Makefile loaded `.env` first, then `.env.smoke.local`.

Current status:

- `make real-smoke` reached the running API at `OJT_REAL_SMOKE_API_BASE_URL`.
- The smoke runner used the exported smoke auth environment from Make.
- The live runtime, semantic retrieval, Graph-RAG handoff, Workbench file upload
  workflow, assistant CSV attachment extraction, assistant table-style scanned
  PDF extraction, assistant table-style PNG extraction, assistant positive RAG,
  and assistant negative RAG checks passed.
- Earlier live runs caught real failures: PDF HTTP 500, OCR confusions in doctor
  name / FHIR text, and empty assistant RAG evidence. Those checks remain in the
  smoke file as regression guards.

## Failure Modes Covered

- Positive FHIR/HbA1c retrieval must rank `standard:fhir_observation_r4` top-1.
- Positive FHIR/HbA1c retrieval must include `terminology:loinc`.
- Retrieval answer citations must point to retrieved source IDs.
- Negative cafe parking, payroll tax, and passport queries must return no ranked
  retrieval hits.
- Assistant positive RAG must return retrieved evidence and cited source IDs.
- Assistant negative RAG must refuse without source IDs or fabricated citations.
- Workbench file upload must complete a real workflow from a real CSV.
- Assistant file attachment extraction must return text for a real CSV.
- Assistant pasted-image upload must accept a table-style scanned hospital PNG
  and return extracted text through the same `extractor=auto` path used by the
  frontend.
- Assistant file attachment extraction must return text for a table-style
  scanned diabetes follow-up PDF with no hidden text layer.
- OCR output must preserve generated clinical facts exactly: HbA1c 7.4 %, glucose
  182 mg/dL, creatinine 0.9 mg/dL, LDL 138 mg/dL, medication list,
  assessment/plan, and follow-up.
- Patient/provider/MRN/DOB context must either be preserved or explicitly
  redacted.

## Known Blind Spots

- These smoke tests do not prove end-to-end clinical correctness.
- They do not measure retrieval accuracy over a large external labeled corpus.
- They do not prove GPU is used for embedding when the configured provider is
  OpenAI; they prove the host GPU is visible and the live API uses real provider
  metadata.
- They do not replace lower-level unit tests for prompt-injection wrappers,
  RBAC, storage contracts, or parser behavior.

## 100% Pass Rate

The latest live Makefile run is green, but the pass rate is only meaningful
because the smoke now has a generated ground-truth oracle. It is still not a
claim of broad real-world OCR accuracy across arbitrary hospital PDFs.
