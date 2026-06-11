# Retrieval Support Matrix v0

## Purpose

Retrieval answers need auditable claim-to-evidence support. OJTFlow now returns
an explicit support matrix in every retrieval package:

`RetrievalPackage.support_matrix`

The same object is also copied into:

`RetrievalPackage.handoff_context.support_matrix`

Assistant, MCP, UI, and export clients should use this matrix when explaining
why a source supports an answer. Free-text answers should not invent evidence
relationships outside this contract.

## Row Contract

Each row connects one evidence claim to one ranked hit:

- `claim_id`
- `claim`
- `support_status`: `strong`, `partial`, `weak`, or `unsupported`
- `evidence_id`
- `source_id`
- `source_type`
- `source_version`
- `source_locator`
- `matched_terms`
- `score`
- `confidence`
- `reasoning`
- `warnings`

The matrix is deterministic. It uses existing retrieval scoring, bucket
coverage, source locators, matched terms, and hit match explanations. It does
not ask the LLM to decide whether a source supports a claim.

## Intended Use

- Retrieval UI: show whether each source has enough grounding for operator use.
- Assistant synthesis: cite only evidence rows present in the matrix.
- MCP clients: inspect `source_locator`, `matched_terms`, and `reasoning`
  without parsing raw hit internals.
- Export/review flows: flag weak or unsupported rows before downstream handoff.

## Verification

Run:

```bash
python -m pytest tests/test_api.py::test_api_direct_convert_validate_fhir_ocr_and_error -q
```

The test checks that retrieval search returns `support_matrix`, that row IDs
align with ranked hits, and that the handoff context carries the same matrix.
