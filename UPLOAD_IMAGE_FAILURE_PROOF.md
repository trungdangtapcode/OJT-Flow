# Upload/Image/PDF Smoke Proof

Generated: 2026-06-21, live local API at `http://127.0.0.1:18000`.

This is not a mocked test result. The smoke checks hit the running backend with
real auth, configured Postgres/Redis, a real CSV payload, a generated
hospital-style scanned diabetes follow-up PDF, and a generated PNG image of the
same document. The auth token is loaded from local environment files and is not
recorded here.

## Environment Confirmed

Health check:

```text
GET http://127.0.0.1:18000/health
HTTP 200
{"status":"ok"}
```

Listening services observed:

```text
127.0.0.1:18000  OJTFlow API
0.0.0.0:15432    Postgres
0.0.0.0:16379    Redis
```

## Generated Test Asset

The smoke test generates the document bytes at runtime in
`tests/test_real_gpu_api_smoke.py`.

Primary real-case PDF:

- one-page image-only scanned PDF, no hidden text layer;
- table-style hospital/portal layout with boxes and table borders;
- header: `RIVER CITY HOSPITAL`;
- synthetic patient info: `MAYA TRAN`, `DOB 1978-04-12`, `MRN MRN-004219`;
- provider: `DR AMY LEE`;
- visit date: `2026-06-11`;
- reason: diabetes follow-up;
- problem list: type 2 diabetes, hyperlipidemia;
- lab table:
  - HbA1c `7.4 %`, flag `HIGH`;
  - Glucose `182 MG/DL`, flag `HIGH`;
  - Creatinine `0.9 MG/DL`, flag `NORMAL`;
  - LDL `138 MG/DL`, flag `HIGH`;
- medications: metformin, atorvastatin, lisinopril;
- assessment/plan/follow-up;
- signature/footer.

Saved artifacts:

- `.qa/smoke-artifacts/diabetes_followup_ground_truth.json`
- `.qa/smoke-artifacts/real-smoke-digital-diabetes-followup-visit.pdf`
- `.qa/smoke-artifacts/real-smoke-scanned-diabetes-followup-visit.pdf`
- `.qa/smoke-artifacts/real-smoke-scanned-diabetes-followup-visit.png`
- `.qa/smoke-artifacts/real-smoke-bad-scan-diabetes-followup-visit.pdf`
- `.qa/smoke-artifacts/real-smoke-patient-portal-diabetes-followup-summary.pdf`

No Pillow/reportlab/PyMuPDF dependency is used to generate these files.

The current smoke wires the scanned PDF and PNG into the live API tests. The
digital-text, bad-scan, and patient-portal PDFs are generated artifacts for the
next OCR-evaluation expansion.

## Truth Oracle

The smoke no longer accepts “some text came back” as a pass.

The OCR tests require the generated clinical facts to appear in the returned
text:

- hospital header;
- visit date and reason;
- problem list;
- all four lab rows with values, units, and flags;
- medication list;
- assessment, plan, follow-up.

PHI/context fields must either be preserved exactly or explicitly redacted:

- patient name;
- DOB;
- MRN;
- provider;
- signature.

Known bad OCR confusions fail the test.

## Latest Full Smoke

Command:

```bash
make real-smoke
```

Result:

```text
11 passed
```

## Focused OCR Smoke

Command:

```bash
bash -lc 'set -a; source .env; source .env.smoke.local; set +a; scripts/run-real-smoke-tests --no-build -k "scanned_diabetes_followup_pdf or clipboard_image"'
```

Result:

```text
2 passed
```

## Bottom Line

Current verified state:

- Workbench CSV upload: works.
- Assistant CSV attachment: works.
- Assistant table-style scanned diabetes follow-up PDF: works on this run.
- Assistant table-style PNG/image upload: works on this run.
- Full real smoke suite: green on this run.

This proves the current smoke oracle can catch wrong OCR values, redaction
behavior, and missing clinical facts for the generated document. It still does
not prove broad real-world OCR accuracy across arbitrary hospital PDFs.
