# No Raw PHI Logging Guard v0

F125 adds runtime and CI guardrails to reduce the chance that raw PHI appears in
application logs.

This is a defensive guard, not a compliance guarantee. Application code should
still avoid logging request bodies, uploaded content, extracted text, model
prompts, raw retrieval chunks, and unredacted tool arguments.

## Runtime Guard

`ojtflow.observability.logging_guard.NoRawPhiFilter` sanitizes Python
`logging.LogRecord` values before handlers format them.

It covers:

- log message strings;
- `%s` formatting arguments;
- structured `extra={...}` fields;
- nested dict/list/tuple values.

It uses the PHI redaction preview engine for general text and adds log-specific
guards for assignment-shaped values such as:

```text
patient_id=P001 ssn=123-45-6789 email=patient@example.com
```

The FastAPI app factory installs the filter through
`install_no_raw_phi_filter()` so API exception logging and route logging pass
through the guard by default.

## Scanner

Development and CI can run:

```bash
PYTHONPATH=src python scripts/scan-no-raw-phi.py --self-test --allow-missing
```

By default the scanner checks `logs/` and `var/logs/` if they exist. Explicit
paths can be supplied:

```bash
PYTHONPATH=src python scripts/scan-no-raw-phi.py --paths logs api.log
```

The scanner fails on raw-looking PHI values such as SSNs, emails, phone numbers,
and sensitive `key=value` assignments. It ignores known redaction placeholders:

- `[REDACTED:...]`
- `[TOKEN:...]`
- `[REVIEW_REQUIRED:...]`

## CI

`.github/workflows/ci.yml` runs the scanner after backend tests. The CI step uses
`--self-test --allow-missing` so fresh runners without log directories still
verify scanner behavior and scan logs when those directories exist.

## Limitations

- The guard is high-recall but not exhaustive.
- It does not authorize logging sensitive data.
- It does not scan binary artifacts, databases, uploaded files, or object stores.
- It does not replace audit hashing/redaction for tool calls.
- It does not prove HIPAA de-identification.

## Verification

Run:

```bash
OJT_STORAGE_BACKEND=memory PYTHONPATH=src pytest -q tests/test_logging_guard.py tests/test_audit_records.py
PYTHONPATH=src python scripts/scan-no-raw-phi.py --self-test --allow-missing
```
