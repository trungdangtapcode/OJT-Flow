# QA Request: Medical Knowledge Page

Please write or run QA checks for the new `/knowledge` page without changing product code.

Scope:
- Route and sidebar: `/knowledge` is reachable from the sidebar as `Knowledge`.
- Search behavior: submitting a query calls `POST /api/v1/retrieval/search`.
- No assistant call: search must not call assistant/chat endpoints.
- Payload defaults: `top_k=5`, `trust_level=approved`, `fields=[]`, and filter fields mirror the visible controls.
- Results: answer text, citation/source IDs, source cards, trust/source labels, snippets, and retrieval details render when present.
- Empty state: no result/evidence states do not fabricate an answer.
- Error state: retrieval/provider failures show `Knowledge search unavailable`.
- Safety copy: page does not claim diagnosis, treatment, triage, internet search, or clinician replacement.
- Responsive UI: search form, filters, answer, and source cards remain readable on desktop and mobile.

Recommended manual/live checks:
- Use a known positive query such as `What does HbA1c mean?`.
- Use a no-answer query outside the corpus.
- Use an unavailable retrieval/backend state if safe in the QA environment.
