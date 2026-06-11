# AI Risk Register v0

OJTFlow keeps a data-driven AI risk register at:

```text
knowledge/governance/ai_risk_register.json
```

Config:

```env
OJT_AI_RISK_REGISTER_PATH=knowledge/governance/ai_risk_register.json
```

The register is aligned to NIST AI RMF 1.0 and NIST AI 600-1, the Generative AI
Profile. NIST describes the AI RMF Core as organized around the Govern, Map,
Measure, and Manage functions, and the Generative AI Profile as a companion
resource for generative AI risk management.

Primary references:

- NIST AI RMF Core: https://airc.nist.gov/airmf-resources/airmf/5-sec-core/
- NIST AI Risk Management Framework: https://www.nist.gov/itl/ai-risk-management-framework
- NIST AI 600-1 Generative AI Profile: https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence

## API

`GET /api/v1/runtime/ai-risk-register` returns the validated register for users
with `admin:read`.

The Settings page renders the same API as a read-only AI risk register panel.
Operators can see the active intended use, prohibited uses, risk severities,
NIST function coverage, monitoring signals, human oversight expectations, and
implementation references without editing source files.

## Required Fields

Each risk entry includes:

- intended use
- limitation
- NIST AI RMF function mappings
- generative-AI risk areas
- severity, likelihood, and residual risk
- owner role
- monitoring signals
- human oversight requirement
- controls and implementation references
- evidence references

## Current Scope

The v0 register focuses on OJTFlow’s current product risks:

- clinical misuse or diagnostic overreach
- PHI disclosure to external providers
- prompt injection through untrusted content
- weak or unsupported evidence
- cost or abuse spikes from LLM/OCR/embedding/batch ingestion

The register is an operational governance artifact, not a legal compliance
certification.

## Extension Pattern

Add or update risks in `knowledge/governance/ai_risk_register.json`. Keep each
entry specific enough that an operator can answer four questions:

- What use is allowed?
- What limitation or failure mode is still present?
- What signal should be monitored?
- Which human role must oversee the residual risk?

Each control should point to a code file, policy JSON file, or docs page that
can be inspected during security review. Planned controls are allowed, but they
must remain visible as `status: "planned"` or `status: "partial"` until shipped.

Verification:

```bash
OJT_STORAGE_BACKEND=memory PYTHONPATH=src pytest -q tests/test_ai_risk_register.py
```
