# Backend v0 Release Candidate Checklist

Status: backend v0 scaffold hardened for demo candidate.

## Required Checks

- [x] FastAPI application imports successfully.
- [x] Public endpoints use `{data, error}` envelope.
- [x] Postgres-backed workflow/event/dataset persistence exists.
- [x] Versioned SQL migration exists.
- [x] Docker Compose starts Postgres and API services.
- [x] SQLite fallback persistence exists.
- [x] Local file-backed input/output storage exists.
- [x] Workflow steps are separate from audit events.
- [x] Human review pause/resume is restart-safe.
- [x] Parser/converter/validation tests pass.
- [x] API workflow/review tests pass.
- [x] FHIR-like profile endpoint exists.
- [x] OCR evidence endpoint exists.
- [x] Demo flow documentation exists.
- [x] API contract v0 documentation exists.

## Freeze Rule

After this release candidate, backend changes should be limited to:

- correctness bugs
- test fixes
- documentation corrections
- demo-blocking reliability issues

Do not add new advanced AI modules until the demo branch is stable.
