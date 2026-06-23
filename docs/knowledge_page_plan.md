# Medical Knowledge Page Plan

## Goal

Create a simple `/knowledge` page for people to search approved medical and healthcare data information without exposing the full operator-heavy retrieval cockpit.

The page should feel like a normal knowledge search product:

- one clear search box;
- plain answer summary;
- ranked source cards;
- visible citations/evidence;
- no diagnosis or treatment claims;
- no hidden keyword-only fallback.

## Product Positioning

This page is for medical information lookup inside the product's trusted corpus.

Safe wording:

- "Search approved medical knowledge."
- "Find evidence from trusted healthcare sources."
- "Review source-backed information."

Do not say:

- "Medical advice."
- "Diagnosis assistant."
- "Treatment recommendation."
- "Doctor replacement."
- "Searches all medical knowledge on the internet."

## Backend Behavior

Use the existing retrieval API:

```text
POST /api/v1/retrieval/search
```

Expected retrieval path:

1. User enters a medical question.
2. Backend embeds the query with the configured real embedding provider.
3. Backend searches Postgres pgvector using vector similarity.
4. Backend returns ranked evidence chunks, answer metadata, warnings, and citations.
5. UI displays the answer and sources.

The page should not introduce a new keyword-only search path.

## LLM Behavior

Default `/knowledge` search should not call the LLM.

It may call:

- embedding provider for semantic retrieval;
- pgvector search;
- local evidence answer synthesis already returned by retrieval.

If we add "Ask Assistant" later, that should be an explicit separate button and clearly marked as LLM-backed.

## Page Structure

Route:

```text
/knowledge
```

Navigation label:

```text
Knowledge
```

Main layout:

1. Search header
   - Title: `Medical Knowledge`
   - Subtitle: `Search source-backed medical and healthcare data information.`
   - Small disclaimer: `For workflow education and evidence review only. Not medical advice.`

2. Search box
   - Large single input or textarea.
   - Placeholder examples:
     - `What does HbA1c mean?`
     - `How should FHIR Observation represent lab units?`
     - `What is UCUM used for in lab results?`
   - Button: `Search`

3. Optional compact controls
   - Top K: default `5`.
   - Trust level: default `approved`.
   - Advanced filters collapsed by default:
     - standard system;
     - clinical domain;
     - source type.

4. Results
   - Answer card first.
   - Source cards second.
   - Warnings third.
   - Technical trace collapsed.

## Result Display

### Answer Card

Show:

- answer text from `RetrievalPackage.answer.answer_text`;
- status badge:
  - supported;
  - partial;
  - review required;
  - refused;
- confidence/readiness if present;
- warning if human review is required.

If no supported answer:

```text
No enough source-backed evidence was found for this question.
```

### Source Cards

For each `RetrievalHit`:

- source title or source ID;
- evidence claim;
- score;
- trust level;
- source type;
- citation/source ID;
- matched snippet if available.

Keep cards concise. Put raw ranking components behind details.

### Safety Copy

Show consistently:

```text
This page summarizes retrieved evidence from configured sources. It is not medical advice.
```

## Frontend Files To Add/Change

Add:

```text
frontend/src/features/knowledge/knowledge-page.tsx
```

Optionally split later:

```text
frontend/src/features/knowledge/components/knowledge-search-box.tsx
frontend/src/features/knowledge/components/knowledge-answer-card.tsx
frontend/src/features/knowledge/components/knowledge-source-card.tsx
```

Change:

```text
frontend/src/App.tsx
frontend/src/components/layout/app-shell.tsx
```

Use existing API function:

```ts
searchRetrieval(payload)
```

## Request Payload

Default payload:

```ts
{
  query,
  top_k: 5,
  fields: [],
  schema_id: null,
  detected_format: null,
  resource_type: null,
  clinical_domain: null,
  standard_system: null,
  source_type: null,
  trust_level: "approved",
  filters: {}
}
```

## UX Rules

- Do not expose retrieval diagnostics on first load.
- Do not show graph/RAG internals unless the user opens details.
- Do not show "lexical", "BM25", "ranking weights", or "candidate fusion" on the main page.
- Always show sources for non-empty answers.
- Empty state should show practical example questions.
- Error state should explain whether semantic retrieval is unavailable.

## Acceptance Criteria

- `/knowledge` appears in sidebar navigation.
- User can enter a medical question and click Search.
- Page calls `POST /api/v1/retrieval/search`.
- Page displays answer text when backend returns one.
- Page displays ranked evidence source cards.
- Page displays no-answer state when retrieval returns no supported evidence.
- Page does not claim diagnosis or treatment advice.
- Page does not add keyword-only retrieval.
- Page build passes:

```bash
cd frontend
npm run build
```

## Non-Goals

- Do not replace `/retrieval`.
- Do not remove advanced retrieval cockpit.
- Do not add a new backend search engine.
- Do not call LLM by default.
- Do not create medical advice features.

## Future Upgrade

Later we can add:

- popular medical knowledge topics;
- saved searches;
- source category filters;
- "Ask Assistant with these sources";
- user feedback on source usefulness;
- multilingual Vietnamese search examples;
- public patient-friendly explanations generated only from cited evidence.
