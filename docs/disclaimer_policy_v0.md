# Disclaimer Policy v0

OJTFlow keeps user-facing clinical and compliance boundary text in:

```text
knowledge/governance/disclaimer_policy.json
```

Config:

```env
OJT_DISCLAIMER_POLICY_PATH=knowledge/governance/disclaimer_policy.json
```

## Purpose

The policy makes OJTFlow's intended use explicit across the UI:

- healthcare data operations
- parsing and extraction review
- validation and evidence retrieval
- workflow review and governed export preparation

It also states the forbidden boundary:

- no diagnosis
- no treatment recommendation
- no triage
- no patient-specific medical advice
- no autonomous clinical approval
- no bypassing human review gates

## API

`GET /api/v1/runtime/disclaimers` returns the validated policy for authenticated
users. It is not admin-only because the boundary text is part of normal end-user
operation.

## UI Surfaces

The app shell renders a route-aware banner from the backend policy. Current
surfaces:

- global
- Assistant
- Workbench
- Workflows
- Workflow detail
- Reviews
- Retrieval
- Audit
- Schemas
- Settings
- Help

Each message includes:

- title
- message
- severity
- review requirement
- prohibited uses
- human review text
- evidence limitation text

## Extension Pattern

Edit `knowledge/governance/disclaimer_policy.json`; do not hardcode new
clinical-boundary wording in React components. The frontend maps route paths to
surface IDs and displays the backend-provided message.

Verification:

```bash
OJT_STORAGE_BACKEND=memory PYTHONPATH=src pytest -q tests/test_disclaimers.py
```
