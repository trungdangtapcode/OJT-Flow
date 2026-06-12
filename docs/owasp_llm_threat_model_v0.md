# OWASP LLM Threat Model v0

OJTFlow keeps a data-driven OWASP LLM threat model at:

```text
knowledge/security/owasp_llm_threat_model.json
```

Config:

```env
OJT_OWASP_LLM_THREAT_MODEL_PATH=knowledge/security/owasp_llm_threat_model.json
```

The threat model uses the OWASP Top 10 for LLM Applications 2025 categories as
the review frame:

- LLM01 Prompt Injection
- LLM02 Sensitive Information Disclosure
- LLM03 Supply Chain
- LLM04 Data and Model Poisoning
- LLM05 Improper Output Handling
- LLM06 Excessive Agency
- LLM07 System Prompt Leakage
- LLM08 Vector and Embedding Weaknesses
- LLM09 Misinformation
- LLM10 Unbounded Consumption

Primary reference:

- OWASP Top 10 for LLM Applications: https://genai.owasp.org/llm-top-10/

## API

`GET /api/v1/runtime/owasp-llm-threat-model` returns the validated model for
users with `admin:read`.

The Settings page renders the same API as a read-only threat-model panel.
Operators can inspect category coverage, residual risk, monitoring signals,
mitigation status, code references, and test references.

## Required Fields

Each category includes:

- OWASP category ID and name
- official OWASP category URL
- risk statement
- applicable OJTFlow surfaces
- mitigations
- mitigation owner role
- mitigation status
- implementation references
- test references
- monitoring signals
- residual risk and residual risk note
- roadmap and evidence references

## Review Rules

The loader rejects duplicate or missing OWASP category IDs. The focused test
also checks that every mitigation maps to existing implementation and test
files. This keeps the threat model tied to shipped controls instead of becoming
a static compliance checklist.

## Current Scope

The v0 threat model is centered on OJTFlow's active LLM/RAG surfaces:

- Assistant planning and answer synthesis
- uploaded files, clipboard images, OCR, and extracted document text
- healthcare retrieval chunks, embeddings, and pgvector search
- MCP/local tool execution and future remote MCP exposure
- PHI classification, redaction, external provider policy, and no-raw-PHI logs
- generated output validation, evidence support matrices, rate limits, and cost controls

The threat model is an engineering governance artifact. It is not a replacement
for legal, compliance, clinical-safety, or third-party security review.

Verification:

```bash
OJT_STORAGE_BACKEND=memory PYTHONPATH=src pytest -q tests/test_owasp_llm_threat_model.py
```
