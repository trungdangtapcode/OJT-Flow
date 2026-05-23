# Security, Governance, and Human Accountability Detailed Plan

OJTFlow handles user-provided data, model calls, retrieval, tool execution, and healthcare-like workflows. Security and governance must be part of the workflow design, not a final polish task.

## Governance Position

MVP intended use:

> OJTFlow supports healthcare data validation, transformation, retrieval, explanation, and review. It does not provide autonomous diagnosis, treatment, triage, medication recommendations, or final clinical decision-making.

This statement should appear in medical explanation output, demo docs, and governance notes.

## Threat Model

Primary assets:

- input datasets
- schema registry
- knowledge base
- retrieved context
- workflow state
- tool outputs
- audit logs
- review decisions
- model prompts and responses
- vector indexes and graph snapshots
- OCR/DICOM/visual evidence artifacts

Threats:

- prompt injection in user data
- prompt injection in retrieved documents
- sensitive information disclosure
- raw PHI in logs or prompts
- unsafe tool calls
- excessive agent permissions
- schema drift
- RAG poisoning
- unsupported medical claims
- unapproved export
- costly model/tool loops
- stale model/index/schema versions

## Controls by Layer

| Layer | Control |
| --- | --- |
| Input | file size limits, format validation, prompt-injection scan, PHI/sensitive field scan |
| Workflow | typed state, review gates, event stream, status transitions |
| Agents | role-scoped tools, permission allowlists, structured outputs |
| Tools | input validation, output validation, no generated code execution |
| Retrieval | trusted source metadata, separate untrusted user content, version filters |
| Explanation | supported-claim map, uncertainty, limitations, intended use |
| Storage | hashes, references, no unnecessary raw sensitive data in logs |
| API | auth-ready design, request validation, rate limits later |
| Deployment | secrets manager, least privilege, signed artifacts later |
| Monitoring | alerts for review bypass, PHI leakage, unsupported claims |

## Human Review Rules

Review is required when:

- schema confidence is low
- multiple schemas match
- cleaning changes values
- rows are dropped
- missing values are filled
- units are converted
- columns are semantically renamed
- sensitive or PHI-like fields are found
- external export is requested
- retrieval evidence is weak or conflicting
- a medical or clinically meaningful claim would be made
- OCR confidence is low
- DICOM/visual output affects interpretation
- operation is large, costly, or irreversible

Review decisions:

- approve
- approve with edits
- reject
- clarify
- cancel

All review decisions become evidence.

## Prompt Injection Controls

Rules:

- Store user instruction separately from user data.
- Mark all retrieved context as context, not instruction.
- Do not let data cells override system/developer instructions.
- Scan data and retrieved chunks for suspicious instruction patterns.
- Validate all model-generated plans against schema.
- Never execute generated code.
- Never give model output direct filesystem/cloud authority.

Seeded prompt-injection fixtures:

- CSV cell saying "ignore previous instructions"
- schema doc with malicious instruction
- YAML value pretending to be a system message
- OCR text containing hidden instructions

Expected result:

- Flag as risk.
- Continue only if safe.
- Do not follow embedded instruction.

## PHI and Sensitive Data Controls

MVP:

- Use synthetic data by default.
- Include PHI-like detectors for field names and simple patterns.
- Mask preview before explanation/export when sensitive fields found.
- Avoid storing raw sensitive content in workflow events.
- Use hashes and storage refs.

Sensitive field examples:

- patient ID
- name
- address
- phone
- email
- insurance number
- medical history
- diagnosis
- medication
- lab result
- imaging study ID

Japan/APPI note:

- Medical history is special care-required personal information.
- Pilot use must track consent/data-use purpose, access control, retention, and review.

## Audit Requirements

Every workflow should record:

- workflow ID
- user/session ID or placeholder
- timestamps
- input hash
- output hash
- dataset refs
- schema versions
- model version
- prompt/template version
- retrieval source IDs
- vector index version
- graph snapshot version
- tool calls
- validation report
- transformation diff
- review decisions
- final status
- safety flags

Audit reconstruction test:

Given a workflow ID, a reviewer should be able to answer:

- What data was provided?
- What did the system infer?
- Which schema/rules were used?
- What issues were found?
- What was changed?
- Who approved it?
- Which sources supported the explanation?
- Which tools ran?
- Which versions were active?

## Clinical Claim Support

Every clinical or healthcare claim in final explanation should be marked:

- `supported`
- `partially_supported`
- `unsupported`
- `requires_clinician_review`

Support can come from:

- validation report
- schema rule
- data dictionary
- retrieved guideline or standard
- tool output
- OCR/source artifact
- DICOM metadata
- visual artifact
- human decision

Unsupported claims must not be presented as fact.

## Japan-Market Governance Checklist

Create a checklist document with:

- APPI sensitive data handling
- consent/data-use purpose
- tenant isolation
- access control
- audit retention
- encryption
- backup/restore
- incident response
- MHLW medical information security mapping
- PMDA/SaMD intended-use boundary
- JP Core/FHIR compatibility notes
- cloud region and data residency assumptions
- approval workflow evidence

## Risk Register

Minimum fields:

- risk ID
- risk category
- description
- likelihood
- impact
- owner
- mitigation
- status
- evidence link

Initial risks:

- scope creep
- unreliable model output
- RAG quality issue
- prompt injection
- PHI leakage
- unsupported clinical explanation
- review gate bypass
- MCP tool misuse
- schema drift
- model/index version drift
- cloud cost overrun

## Acceptance Criteria

- Risk register exists before implementation expands beyond core workflow.
- Review gates are testable.
- Prompt-injection fixtures are blocked or flagged.
- PHI-like fields are detected in seeded cases.
- Explanation claims include support status.
- Audit reconstruction works for golden workflow.
- Intended-use limitation appears in healthcare explanations.
- No demo requires real PHI.

## Build Sequence

1. Define intended-use statement.
2. Add risk register template.
3. Add review trigger rules.
4. Add prompt-injection fixtures.
5. Add PHI/sensitive field scanner baseline.
6. Add audit event schema and reconstruction report.
7. Add claim support map.
8. Add APPI/MHLW/PMDA checklist.
9. Add tests for review gate bypass.
10. Add incident/runbook templates.

## Risks

| Risk | Control |
| --- | --- |
| Governance docs drift from implementation | Link checklist items to tests or controls |
| PHI detector has false negatives | Use synthetic data and high-recall heuristic baseline |
| Review fatigue | Trigger review only on meaningful risk |
| Audit logs store too much data | Store refs/hashes and summaries |
| SaMD boundary confusion | Repeat intended use and avoid diagnostic claims |
