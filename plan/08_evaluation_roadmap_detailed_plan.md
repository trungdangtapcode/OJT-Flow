# Evaluation, Roadmap, and Release Detailed Plan

Evaluation should prove OJTFlow is reliable, safe, and honest about its limits. The project should measure deterministic correctness, retrieval quality, explanation faithfulness, review behavior, security controls, and medical governance readiness.

## Evaluation Dimensions

| Dimension | Metric | MVP target |
| --- | --- | --- |
| Conversion correctness | structural equivalence and round-trip consistency | at least 95 percent curated tests |
| Validation accuracy | seeded issue detection | at least 90 percent |
| Retrieval relevance | relevant source in top 5 | at least 80 percent |
| Retrieval ranking | Recall@k, nDCG@10, MRR, schema-hit rate | baseline before advanced modules |
| Graph-NER | entity F1, normalization accuracy, relation F1 | high recall for PHI, at least 85 percent demo F1 |
| Explanation faithfulness | supported claims / total claims | at least 95 percent demo cases |
| Human review safety | risky actions routed to review | no critical bypass |
| Security | prompt injection and unsafe tool-call tests | no unapproved destructive action |
| Auditability | reconstruct completed workflow | 100 percent demo workflows |
| OCR | CER/WER, field F1, box provenance | report by document type |
| Segmentation | Dice, IoU, HD95 | research/demo only |
| Japan readiness | checklist completion | complete for pilot proposal |

## Fixture Plan

Structured fixtures:

- valid JSON
- invalid JSON
- nested JSON
- valid YAML
- unsafe YAML tag
- valid CSV
- CSV with quoted commas
- CSV with missing values
- CSV with malformed rows
- CSV with inconsistent date formats
- CSV with prompt injection cell
- CSV with PHI-like fields

Healthcare fixtures:

- synthetic lab result CSV
- synthetic patient demographics CSV
- FHIR-like Observation JSON
- FHIR-like Patient JSON
- OMOP-like measurement table
- JP Core alias examples

Knowledge fixtures:

- schema docs
- data dictionary
- transformation examples
- error guidance
- APPI-sensitive fields note
- human review trigger policy

Multimodal fixtures:

- synthetic Japanese/English lab form
- OCR field extraction ground truth
- public/synthetic DICOM metadata
- optional mask artifact

## Golden Workflows

### Golden Workflow 1: Clean CSV to JSON

Purpose:

- prove core workflow, validation, review, conversion, explanation, and audit

Expected:

- parse CSV
- identify missing unit and date inconsistency
- retrieve lab schema
- request review for cleaning
- convert after approval
- explain anomalies with evidence

### Golden Workflow 2: Prompt Injection Defense

Purpose:

- prove user data cannot become instruction

Expected:

- flag suspicious cell
- continue safe validation or pause
- do not follow embedded instruction
- audit safety flag

### Golden Workflow 3: Schema Ambiguity

Purpose:

- prove low-confidence schema matching triggers review

Expected:

- multiple schema candidates
- review prompt asks user to select or clarify
- chosen schema stored as human decision evidence

### Golden Workflow 4: OCR Field Review

Purpose:

- prove multimodal evidence can enter same review backbone

Expected:

- OCR fields with page/bbox provenance
- low-confidence field requires review
- corrected value becomes evidence

### Golden Workflow 5: Medical Explanation Safety

Purpose:

- prove explanation separates data facts from clinical claims

Expected:

- intended-use statement included
- unsupported claims blocked or marked
- limitation says no diagnosis/treatment recommendation

## 12-Week Roadmap

| Week | Theme | Deliverable |
| --- | --- | --- |
| 1 | Backbone | scaffold, contracts, architecture, risk register |
| 2 | Intake | parser, profiler, fixtures, API smoke test |
| 3 | Validation | conversion tools, schema validation, reports |
| 4 | Orchestration | agents, review gate, workflow trace |
| 5 | Graph-NER | entity schema, baseline extraction, graph prototype |
| 6 | Retrieval | hybrid retrieval, benchmark, evidence package |
| 7 | SSL | weak pairs, embedding experiment, promotion report |
| 8 | Explainability | reranker/GraphRAG interface, claim support map |
| 9 | Multimodal/Japan | OCR/DICOM contracts, JP Core aliases, checklist |
| 10 | Vision/MLOps | segmentation artifact or design, CI/CD/GCP blueprint |
| 11 | Hardening | security tests, monitoring design, evaluation report |
| 12 | Release | final demo, docs, slides, roadmap |

## Release Gates

### Gate 1: Backbone

Required:

- contracts
- state machine
- event model
- API map
- storage design
- golden fixture

Decision:

- proceed to code implementation

### Gate 2: MVP Core

Required:

- parse/validate/convert workflow
- review gate
- audit trace
- tests

Decision:

- proceed to retrieval and research modules

### Gate 3: Retrieval

Required:

- retrieval benchmark
- top-k sources with IDs and versions
- relevance metrics
- empty retrieval behavior

Decision:

- enable or reject advanced retrieval modules

### Gate 4: Medical Safety

Required:

- PHI/prompt injection tests
- supported-claim map
- intended-use statement
- human review coverage

Decision:

- approve final medical demo flows

### Gate 5: Final Readiness

Required:

- reproducible demo
- CI evidence
- evaluation report
- risk register
- governance checklist
- known limitations
- post-MVP roadmap

Decision:

- submit and present

## Final Demo Script

Recommended demo path:

1. Show messy lab CSV.
2. Submit instruction: "Clean this CSV, convert it to JSON, and explain anomalies."
3. Show workflow timeline.
4. Show parser/profile result.
5. Show retrieved schema and rules.
6. Show validation issues.
7. Show review prompt for date normalization and missing values.
8. Approve or edit action.
9. Show converted JSON.
10. Show explanation with evidence IDs, limitations, and audit trail.
11. Show prompt-injection fixture blocked.
12. Show Japan/medical governance checklist and roadmap.

Optional:

- show OCR field extraction review
- show DICOM or segmentation evidence artifact

## Evaluation Report Structure

```text
1. Executive summary
2. Intended use and non-goals
3. Test fixtures
4. Core workflow metrics
5. Retrieval metrics
6. Graph-NER metrics
7. Explanation faithfulness review
8. Human review and safety tests
9. Security tests
10. Multimodal demo metrics if included
11. Japan governance checklist
12. Known limitations
13. Post-MVP roadmap
```

## Known Limitations to State Clearly

- MVP does not diagnose, treat, or triage.
- MVP uses synthetic and public data.
- FHIR/OMOP/JP Core support starts as schema-aware fixtures and mappings, not full certified interoperability.
- OCR/vision outputs are assistive research artifacts.
- Retrieval quality depends on curated trusted sources.
- Advanced retrieval and SSL are promoted only if measured.
- Real clinical deployment requires formal governance, data agreements, security review, and regulatory classification.

## Acceptance Criteria

- Every golden workflow can run or be demonstrated from reproducible fixtures.
- Evaluation report includes both successes and limitations.
- Safety failures block final demo flows until fixed.
- Metrics are tied to source fixtures and code versions.
- Final package explains the backbone, not just the AI features.

## Risks

| Risk | Control |
| --- | --- |
| Metrics are too vague | Define fixture-level expected outputs |
| Demo depends on live model luck | Use deterministic tools and cache/stub optional model responses |
| Advanced features are unfinished | Present them as gated roadmap unless they pass tests |
| Safety issues appear late | Seed prompt-injection and review tests early |
| Evaluation report is disconnected from code | Generate reports from fixtures where possible |
