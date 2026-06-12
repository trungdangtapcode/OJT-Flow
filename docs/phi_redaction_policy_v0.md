# PHI Redaction Policy Engine v0

F124 adds a deterministic redaction policy engine on top of the shared PHI
classification contract. PHI detection and redaction behavior are intentionally
separate:

- `PhiClassificationPolicy` decides what looks like PHI or sensitive healthcare
  data.
- `RedactionPolicy` decides what action to apply to each finding.

This separation keeps parsing, validation, retrieval, assistant chat, and export
surfaces from growing their own redaction rules.

## Actions

The v0 engine supports four actions:

- `mask`: replace the value with a typed placeholder such as
  `[REDACTED:SSN]`.
- `suppress`: remove the value while preserving the surrounding format where
  possible. In CSV this leaves an empty cell.
- `tokenize_placeholder`: replace the value with a deterministic placeholder
  such as `[TOKEN:SSN:69f09b1d23b0]`.
- `review_gated_reveal`: replace the value with `[REVIEW_REQUIRED:KIND]` and
  mark the preview as requiring review.

`tokenize_placeholder` is not a reversible token vault. It is a stable local
placeholder for previews, demos, and downstream mapping tests. A production token
vault needs separate storage, key management, rotation, access policy, and audit.

## Public API

`POST /api/v1/parse/redaction-preview` accepts:

```json
{
  "data": "patient_id,ssn,value\nP001,123-45-6789,7.4\n",
  "input_format": "csv",
  "redaction_action": "tokenize_placeholder"
}
```

`redaction_action` is optional. When omitted, the policy chooses the action:

- Direct identifiers and contact identifiers default to `mask`.
- Clinical context, demographics, and free-text sensitive fields default to
  `review_gated_reveal` so clinically meaningful content is not silently erased.

The public API does not accept `reveal_approved`. Review-approved raw reveal is
an internal hook for later review workflows; browser/API callers receive review
markers instead of raw values.

## Response Metadata

`RedactionPreview` returns:

- `policy_id` and `policy_version`.
- `redacted_text`.
- `matches`, including `action`, `status`, `rule_id`, optional `token`, and
  `reveal_requires_review`.
- `phi_classification`.
- `action_summary`.
- `requires_review`.
- `reveal_required`.
- `external_provider_block_recommended`.

Raw matched values are not copied into match metadata. `value_preview` remains
masked.

## Extension Rules

- Add new PHI detectors to `PhiClassificationPolicy`, not the redaction engine.
- Add new behavior to `RedactionPolicy`, not parser/profile/validation modules.
- Do not send raw reveal through public APIs without a review decision,
  permission check, and audit event.
- Do not treat `tokenize_placeholder` as anonymization or de-identification.
- Preserve source shape for previews when practical, especially CSV rows.

## Verification

Run:

```bash
OJT_STORAGE_BACKEND=memory PYTHONPATH=src pytest -q tests/test_redaction.py tests/test_phi_classification.py
```
