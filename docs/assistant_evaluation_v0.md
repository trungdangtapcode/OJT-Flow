# Assistant Evaluation Fixtures v0

## Purpose

OJTFlow keeps Assistant evaluation cases in trusted data instead of scattering
them across ad hoc tests. The v0 suite covers natural-language tool selection,
write-gate preservation, basic answer faithfulness, and evidence grounding for
healthcare workflow tasks.

Source of truth:

- `knowledge/assistant/evaluation_cases.json`

Loader:

- `src/ojtflow/infrastructure/assistant_evaluations.py`

Verification:

```bash
python -m pytest tests/test_assistant_evaluations.py -q
```

## Case Shape

Each case declares:

- user `message`
- structured `context`
- whether write actions are allowed
- expected tool names and statuses
- required and forbidden answer terms
- minimum evidence summary count
- required evidence source IDs
- faithfulness notes for humans extending the suite

## Extension Rules

Add cases when a new Assistant capability changes tool selection, evidence
grounding, or write-gate behavior. Keep fixture payloads small and synthetic.
Do not store real PHI. Use `forbidden_answer_terms` for common hallucination or
unsafe-clinical-advice patterns that should never appear in deterministic
answers.
