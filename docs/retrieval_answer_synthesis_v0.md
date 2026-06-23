# Retrieval Answer Synthesis v0

OJTFlow retrieval answers are evidence-only summaries. They do not ask an LLM to
invent or complete claims. The answer object is generated after ranking,
support-matrix construction, and Graph-NER handoff, so every claim can point
back to evidence IDs, source metadata, and graph path refs when available.

## Why This Exists

The retrieval package already exposed ranked hits, quality signals, support
rows, and Graph-NER context. That was useful for developers but too indirect
for Assistant, MCP, export, and UI consumers. Those callers need a single
backend-owned answer contract that says:

- whether the evidence can support an answer;
- what claims are cited;
- which weak or unsupported claims were excluded;
- what evidence gaps remain;
- whether source freshness, source lifecycle, or Graph-NER conflict detection
  requires review.

This prevents a downstream assistant or UI from treating a weak retrieval result
as a confident medical answer.

## Contract

`RetrievalPackage.answer` contains:

- `status`: `supported`, `partial`, `review_required`, or `refused`;
- `answer_text`: rule-based text built only from supported evidence rows;
- `claims[]`: answer claims tied to evidence IDs, citation IDs, and Graph-NER
  path refs, with `graph_guard` status for claim-to-triple checking;
- `citations[]`: cited evidence source IDs, versions, and locators;
- `unsupported_claims[]`: weak or unsupported support rows excluded from
  confident answer text;
- `missing_evidence_gaps[]`: reasons the answer is incomplete or refused;
- `freshness_warnings[]`: stale, deprecated, review-needed, unapproved, blocked,
  failed, or version-mismatched source warnings;
- `graph_path_summary`: Graph-NER path coverage for the answer.
- `metadata.claim_triple_guard`: summary counts for graph-supported,
  review-required, and not-required claims.
- `metadata.graph_conflict_summary`: summary counts for rule-based
  contradictory-claim, deprecated-mapping, unit-conflict, and version-mismatch
  graph conflicts.

The same payload is mirrored to `handoff_context.answer` for Assistant and MCP
clients.

## Policy

`knowledge/retrieval/answer_synthesis_policy.json` controls:

- support statuses allowed into answer text;
- statuses that require human review;
- source-version markers treated as stale;
- source lifecycle states treated as stale or blocking;
- claim-to-triple guard settings, including which support statuses require
  graph support and which clinical terms count as graph-guard-sensitive;
- refusal messages.

Use `OJT_RETRIEVAL_ANSWER_POLICY_PATH` to test a replacement policy without
editing source code.

## Verification

Focused tests:

```bash
OJT_STORAGE_BACKEND=memory PYTHONPATH=src pytest -q \
  tests/test_retrieval.py::test_retrieval_service_attaches_guarded_answer_with_citations \
  tests/test_retrieval.py::test_retrieval_answer_flags_clinical_claim_without_graph_triple_support \
  tests/test_retrieval.py::test_retrieval_answer_refuses_when_no_evidence_supports_query \
  tests/test_retrieval.py::test_retrieval_answer_warns_on_deprecated_source_version \
  tests/test_retrieval.py::test_retrieval_service_attaches_graph_conflict_report_and_review_answer
```

The first test checks cited answer synthesis through the application service.
The second checks the claim-to-triple guard for strong clinical claims without
graph support. The third checks refusal when no evidence supports the query. The
fourth checks source freshness warnings. The fifth checks that graph conflicts
force human review.
