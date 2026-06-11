# Assistant Answer Templates v0

## Purpose

Assistant answers need consistent operator-facing structure. OJTFlow now keeps
the answer-template registry in trusted data:

`knowledge/assistant/answer_templates.json`

The registry is exposed through:

`GET /api/v1/assistant/answer-templates`

This slice does not force every current chat response through new formatting.
It establishes the governed template contract used by future synthesis,
evaluation, and UI guidance.

## Templates

The v0 registry covers:

- validation report
- retrieval answer
- standards explanation
- workflow status
- review summary
- export summary

Each template declares:

- related tool names
- whether evidence is required
- conditions that require review
- output constraints
- named answer sections and their purpose

## Verification

Run:

```bash
python -m pytest tests/test_api.py::test_assistant_answer_templates_endpoint_returns_data_driven_contracts -q
```

The test verifies that the template endpoint loads data from `knowledge/` and
returns structured template sections.
