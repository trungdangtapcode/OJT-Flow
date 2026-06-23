# PHI Classification Contract v0

OJTFlow classifies PHI and sensitive healthcare data as a governance signal across
the backend. The classifier is not a HIPAA de-identification engine and does not
certify data as safe to disclose. It provides rule-based risk metadata so
workflow, review, assistant, retrieval, and export surfaces can make consistent
decisions before content leaves the system boundary.

The default policy is aligned to the identifier families described by the HHS
HIPAA de-identification guidance:
https://www.hhs.gov/hipaa/for-professionals/special-topics/de-identification/index.html

## Contract

`PhiClassification` is the shared summary:

- `classification_id`: stable generated identifier for the classification event.
- `target_type`: one of `field`, `row`, `document`, `chunk`, `chat_message`, or
  `generated_output`.
- `source_ref`: optional source reference such as a dataset URI, document path, or
  retrieval source ID.
- `risk_level`: `none`, `low`, `medium`, or `high`.
- `finding_count`: number of matched PHI findings.
- `categories`: compact category list, such as `direct_identifier`, `contact`,
  `clinical_context`, `demographic`, or `free_text_sensitive`.
- `findings`: row/field/source-level `PhiFinding` entries.
- `requires_review`: true when policy says the risk level must be human reviewed.
- `external_provider_block_recommended`: true when policy says the content should
  not be sent to external LLM/OCR providers without review or redaction.

`PhiFinding` captures one signal:

- `target_type`, `category`, `kind`, `confidence`, and `reason`.
- Optional `field`, `value_preview`, `source_ref`, and `location`.
- `value_preview` is masked; raw matched PHI is not copied into the finding.

## Policy

The active built-in policy lives in `src/ojtflow/core/policy/phi_policy.py` as a
`PhiClassificationPolicy`. It is deliberately data-shaped:

- `field_rules`: field-name token rules with category, kind, confidence, and
  reason.
- `pattern_rules`: regex rules for value/text detection.
- `high_risk_categories` and `medium_risk_categories`: risk rollup rules.
- `review_risk_levels`: risk levels requiring review.
- `external_provider_block_risk_levels`: risk levels that should block external
  provider use unless redacted or approved.

Organization-specific policies should be loaded into the same contract later;
parser, validation, assistant, and retrieval modules should not grow their own
PHI rule lists.

## Surfaces

The v0 classifier is wired into:

- `DataProfile.phi_classification` for parsed structured data and documents.
- `ValidationReport.phi_classification` for schema/policy validation output.
- `TransformationOutput.phi_classification` for generated JSON/YAML/CSV output.
- `RedactionPreview.phi_classification` for external-provider safety previews.
- `AssistantChatMessage.phi_classification` for persisted chat messages.
- `AssistantChatMessage.payload.phi_classification` so existing message storage
  persists classification without a schema migration.
- `Evidence.locator.phi_classification` for retrieved knowledge chunks.

## Risk Behavior

Default risk rollup:

- `high`: direct identifiers such as patient IDs, MRNs, SSNs, health-plan/account
  identifiers, IPs, URLs, or person-name fields.
- `medium`: contact, demographic, or clinical-context signals.
- `low`: policy findings outside high/medium categories.
- `none`: no findings.

The default policy recommends human review for any finding and recommends blocking
external providers for `medium` or `high` risk until redaction or approval.

## Design Rules

- PHI classification is metadata, not mutation.
- Redaction uses the same policy as classification.
- Validation may create issues from field profiles, but field-sensitive behavior
  should route through the PHI policy.
- Retrieval ranking must not change solely because a chunk contains PHI signals;
  the classification appears in evidence metadata for downstream safety handling.
- Chat persistence must expose classification after reload.
- New modules must attach `PhiClassification` instead of inventing local
  `possible_phi` dictionaries.

## Verification

Run:

```bash
OJT_STORAGE_BACKEND=memory PYTHONPATH=src pytest -q tests/test_phi_classification.py
OJT_STORAGE_BACKEND=memory PYTHONPATH=src pytest -q tests/test_data_tools.py tests/test_redaction.py tests/test_assistant_service.py tests/test_retrieval.py::test_retrieval_trace_flags_untrusted_query_context tests/test_workflow_service.py::test_workflow_pauses_for_review_then_completes_after_approval
```
