# Persistent Corpus Knowledge Graph (v0)

> **Storage engine:** This design uses **Neo4j** — the same property-graph engine the
> `graph-med` reference project runs on, queried with Cypher via the official `neo4j` Python
> driver. The system is **engine-agnostic behind the `KnowledgeGraphRepository` port (§4)**:
> `Neo4j` (default), `InMemory` (tests), and `Kùzu` adapters all ship, so the engine is a
> one-line config flip (`OJT_KNOWLEDGE_GRAPH_BACKEND`).
>
> **API caveat:** exact Cypher/DDL below is illustrative and must be confirmed against the
> deployed engine version during implementation.

## 1. Goal & principles

Turn the corpus (seeded **and** user-imported) from "documents → vectors" into a
**persistent, queryable knowledge graph**: concepts/entities as nodes, typed relations as
edges, every node/edge citing the source chunk it came from. Requirements:

- Coexist with vector retrieval — the graph **augments** pgvector search, doesn't replace it.
- **Incrementally built** as users import knowledge.
- **Scoped**: seeded knowledge is `global` (shared); user imports are `organization`-private,
  reusing the workspace model and the owner/org scoping already in the ingestion path.
- Reuse existing pieces: the working `graph-med` Neo4j ontology graph (HPO/ICD/UMLS),
  `clinical/terminology` (code normalization), `BackgroundJobService` + the queue/worker stack (async build), the
  private-corpus ingestion + redaction path, and the `GraphContextRecord` node/edge wire shape.
- Honor project invariants: **provenance + review gates + PHI safety**.

Distinction from today: the existing `graph_contexts` table is a **per-query, ephemeral** NER
handoff. This adds a **canonical, deduplicated, persistent** graph that accumulates across the
whole corpus, stored in Neo4j.

## 2. Why a graph DB (Neo4j) instead of relational tables

- Native multi-hop traversal (neighborhoods, paths) via Cypher instead of recursive SQL.
- `MERGE`-based idempotent upsert keys entity resolution cleanly.
- Provenance and concepts live in **one** graph, so "concept → source passages" is just an edge.
- **Proven for this workload:** the `graph-med` reference project runs on Neo4j; we verified its
  ontology import (HPO, ~200K nodes) runs successfully on a Neo4j instance.

### Engine choice: Neo4j (with a swappable port)

We use **Neo4j** — it is what `graph-med` uses, it is validated for this import workload, and it
brings the mature Cypher ecosystem (Browser/Bloom visualization, APOC, GDS graph algorithms) we
may want as the graph grows. Run **Community** for a single shared graph; **Enterprise** unlocks
per-tenant databases, RBAC, and hot backups if multi-tenant isolation at the DB level is needed.

Crucially the choice is **not load-bearing**: everything sits behind the
`KnowledgeGraphRepository` port (§4). The repo ships three adapters —
`Neo4jKnowledgeGraphRepository` (default), `InMemoryKnowledgeGraphRepository` (tests), and
`KuzuKnowledgeGraphRepository` (embedded alternative) — selected by
`OJT_KNOWLEDGE_GRAPH_BACKEND`. Swapping engines is a config flip plus one adapter, never a
change to contracts, services, API, or frontend.

**Ops note:** Neo4j is a separate JVM server, so it is a deployment service (compose container +
volume + credentials) rather than an embedded file. Budget heap/page-cache accordingly; see §5.

## 3. Graph schema (Neo4j graph-med + OJT overlay)

The default graph is Neo4j. The API reads graph-med's native ontology labels directly:
`IcdDisease`, `IcdChapter`, `IcdGroup`, `HpoPhenotype`, `HpoDisease`, and `Umls`, with
relationships such as `HAS_CHILD`, `HAS_PHENOTYPIC_FEATURE`, `UMLS_TO_ICD`, and
`UMLS_TO_HPO_PHENOTYPE`. OJT-imported corpus concepts are stored as an overlay using the
generic `Concept`/`Chunk`/`RELATED`/`MENTIONS` shape below.

**Node tables**
- `Concept(node_id STRING PRIMARY KEY, scope STRING, organization_id STRING, node_type STRING,
  label STRING, normalized_code STRING, code_system STRING, aliases STRING[], attributes STRING
  /*json*/, confidence DOUBLE, review_state STRING, created_at STRING, updated_at STRING,
  embedding DOUBLE[384] /*optional*/)`
- `Chunk(chunk_id STRING PRIMARY KEY, document_id STRING, source_id STRING, scope STRING,
  organization_id STRING, snippet STRING, created_at STRING)` — provenance is a first-class node.

**Relationship tables**
- `(:Chunk)-[:MENTIONS {confidence DOUBLE}]->(:Concept)` — provenance edge (the citation).
- `(:Concept)-[:RELATED {relation STRING, confidence DOUBLE, review_state STRING,
  created_at STRING, source_chunk_ids STRING[]}]->(:Concept)` — generic concept↔concept relation;
  `relation` carries the semantic type
  (`measured_by|treats|indicates|maps_to_code|same_as|part_of|derived_from`).
  **`source_chunk_ids` is the edge's provenance** — the chunk(s) whose text asserted this relation,
  each resolvable to the `Chunk.snippet` that stated it. Example: `(:Concept {label:'metformin'})
  -[:RELATED {relation:'treats', source_chunk_ids:['chunk_visit0610_003']}]->(:Concept {label:
  'Type 2 diabetes mellitus'})` cites the sentence *"Started metformin 500mg BID."* On re-import,
  the same relation `MERGE`s and **appends** new chunk ids (deduped), mirroring how a node
  accumulates `MENTIONS`. (Promote hot relations to dedicated rel tables later if traversal perf
  needs it.)

Scope is a **property**, not a separate database, so global∪org reads are a single `WHERE`.

## 4. Storage adapter (the only engine-specific part)

A `KnowledgeGraphRepository` **port** (in `application/ports.py`) keeps the rest of the system
engine-agnostic:

```
upsert_concepts(...)            append_provenance(chunk, mentions)
upsert_relations(..., source_chunk_id)   get_concept(node_id, scope, org)
neighborhood(seeds, depth, limit, scope, org)
search_concepts(q, scope, org)  stats(scope, org)
```

Implementations:
- `Neo4jKnowledgeGraphRepository` — default. Queries graph-med ontology nodes directly and
  stores OJT overlay nodes with Cypher `MERGE`.
- `InMemoryKnowledgeGraphRepository` — dict/adjacency for unit tests, same as the existing
  in-memory repos.
- `KuzuKnowledgeGraphRepository` — optional embedded alternative for local experiments.

Because the port is the seam, services / API / frontend never import a graph engine directly.

### Entity resolution (dedup/merge)
Deterministic `node_id` precedence:
1. `code_system:normalized_code` when a trusted code resolves (e.g. `loinc:2345-7`).
2. else `node_type:slug(normalized_label)`.
Scope is part of the key, so global and org concepts never collide. `MERGE` on `node_id`
makes ingestion idempotent; conflicting attributes are kept with provenance and, when they'd
change meaning, flagged `review_state='pending'` rather than overwritten.

## 5. Concurrency & deployment (Neo4j)

Neo4j runs as a separate service, matching graph-med. The graph-med annotation runtime also runs
as its own internal service (`graph-med-service`), and the API talks to it through
`OJT_GRAPH_MED_SERVICE_BASE_URL` instead of constructing graph-med internals in request handlers.
The graph-med service is the GPU-capable runtime boundary for local graph-med compute such as
GNN reranking or future local NER models. LLM calls still use the application's configured LLM
provider (`OJT_LLM_*`, e.g. `gpt-5-mini`) unless an explicit graph-med override endpoint is set.
Ontology import remains a graph-med-style batch job; API query paths are read-oriented, and OJT
corpus overlay writes use idempotent `MERGE`.

## 6. graph-med annotation/import pipeline

Input: uploaded clinical text or files from the `/knowledge` graph import UI. The import path is
graph-med only: it requires the graph-med Neo4j ontology and ICD vector index. NER/NED uses the
application's configured LLM and embedding providers by default, so the same `gpt-5-mini` path
that powers `/assistant` powers graph-med annotation unless a graph-med-specific override is
configured. GPU is reserved for graph-med runtime compute such as GNN reranking, graph export
consumers, or future local NER models; it is not a vLLM requirement. There is no production
fallback to the local coded registry, Graph-NER, sample data, or co-occurrence edge synthesis.

Per import:
1. **Status gate** — verify graph-med ontology labels/indexes are present in Neo4j, annotation
   providers are configured/reachable, and the graph-med GPU runtime is available when
   `OJT_GRAPH_MED_REQUIRE_GPU=true`. If any required dependency is missing, return
   `dependency_unavailable` and write nothing.
2. **LLM NER** — call the configured application LLM provider to extract patient entities from
   `concat_text`/`narrative_text`.
3. **Candidate lookup** — embed each entity with the configured application embedding provider
   and query the graph-med ICD vector index (`icd_disease_embedding`) for candidates.
4. **LLM NED/linking** — call the configured application LLM provider to choose the linked ICD concept or
   reject the candidate set.
5. **Resolve & upsert** — upsert only graph-med-linked ICD concepts and `Chunk`/`MENTIONS`
   provenance. Relation edges should come from graph-med ontology or reviewed mappings, not from
   deterministic co-occurrence.

Idempotency is limited to stable import identifiers and Neo4j `MERGE`; the clinical extraction
and linking behavior is graph-med/LLM-backed, not registry-matched.

## 7. Scoping & visibility

- Seeded corpus (`knowledge/corpus/*`) → `scope='global'`, `organization_id=''`, readable by all.
- User imports → `scope='organization'`, `organization_id=<caller workspace>`, visible only to
  that workspace.
- Reads return **global ∪ caller's org** via Cypher `WHERE c.scope='global' OR
  (c.scope='organization' AND c.organization_id=$org)`.
- A private concept resolving to the same code as a global one is linked with `same_as`, **not**
  merged across the scope boundary (recommended; keeps tenancy clean). _Open decision: link vs
  merge — see §12._

## 8. Ingestion hooks (the "import more knowledge" path)

- **Seeded build/refresh:** extend the retrieval **reindex** job to also enqueue a `kg_build`
  background job (`BackgroundJobService`, queue-backed). Global scope.
- **User import:** the existing private-corpus ingestion (`ingest_private_document` → redaction
  → chunks → embeddings) gains a follow-on `kg_update` job scoped to
  `(owner_user_id, organization_id)`. Importing a document automatically folds it into the
  workspace subgraph.
- **Explicit import endpoint:** text/file import that funnels into the same
  redact → chunk → `kg_update` pipeline.
- Jobs are owner-scoped and resumable (reuse `BackgroundJobRepository`); the single KG writer
  consumes them serially.

## 9. Contracts, services, wiring

- **Contracts** (`core/contracts/knowledge_graph.py`): `KnowledgeGraphNode`,
  `KnowledgeGraphEdge`, `KnowledgeGraphChunk`, `KnowledgeGraphView` (nodes+edges+stats for the
  UI — can mirror `GraphNeighborhood`'s shape so the frontend reuses types),
  `KnowledgeGraphImportRequest`.
- **Port** (`application/ports.py`): `KnowledgeGraphRepository` (§4) with `Neo4j` + `InMemory`
  implementations and optional `Kuzu`.
- **Services** (`application/` + `infrastructure/graph_med/`):
  `KnowledgeGraphService` is read/query only; `GraphMedService` owns status + import
  orchestration through the `GraphMedAnnotationPort`. The main API uses an HTTP adapter to the
  internal `graph-med-service`; that service uses the direct graph-med Neo4j/LLM/embedding client.
  Production imports fail closed if graph-med is unavailable.
- **Dependency:** add `neo4j` under a new `graph` extra in `pyproject.toml`
  (`[project.optional-dependencies]`), built into the image like `parsing`/`embeddings-local`.

## 10. API

- `GET  /api/v1/knowledge-graph/search?q=` → matching concepts (global ∪ org).
- `GET  /api/v1/knowledge-graph/nodes/{node_id}` → concept + provenance (source passages).
- `GET  /api/v1/knowledge-graph/neighborhood?node_id=&depth=&limit=` → bounded subgraph
  (reuse `GraphNeighborhoodQuery` bounds: `max_depth ≤ 2`, `limit ≤ 1000`). Returned **edges**
  include `relation`, `confidence`, and `source_chunk_ids` with resolved `snippet`s, so the UI can
  cite each link, not just each node.
- `POST /api/v1/knowledge-graph/import` → enqueue `kg_update` for the caller's workspace.
- `GET  /api/v1/knowledge-graph/stats` → counts by scope/type.

All `require_authentication`; reads scoped to the caller's workspace; writes gated by
`GovernanceService.require_permission` (new `knowledge:write` or reuse `data:transform`).

## 11. Frontend `/knowledge`

Add a **Graph** tab beside the existing search (`features/knowledge/knowledge-page.tsx`):
- Reuse `features/retrieval/components/graph-query-panel.tsx` as the rendering base; add a
  force-directed view with **node click → side panel** (label, code, provenance snippets,
  "search this concept" pivot back to vector search) and **edge click → side panel** showing the
  relation, confidence, and the **source sentence(s)** resolved from `RELATED.source_chunk_ids` —
  so clicking "Metformin —treats→ Type 2 diabetes" reveals *which document/sentence* asserted it.
- **Rendering lib:** force-directed view via **Cytoscape.js** (or `react-force-graph`), fed by the
  neighborhood API (§10); backend-agnostic. For dev/debugging, use Neo4j Browser/Bloom against
  the same graph-med database.
- **Import knowledge** action (text paste / file upload) → `POST /knowledge-graph/import`, with
  job-status polling (jobs API already exists).
- Client fns in `api.ts` (`searchGraph`, `getGraphNode`, `getGraphNeighborhood`,
  `importKnowledge`) + types from the KG contracts.

## 12. Safety & governance (non-negotiable)

- Private imports are **redacted** (`RedactionPreview`) before extraction; PHI never becomes a
  node label; private nodes are org-scoped and never promoted to `global`.
- Code normalization is **review-gated** (no silent auto-replacement); meaning-changing merges
  set `review_state='pending'` and surface in the existing review queue.
- Every node **and edge** is **provenance-backed**: nodes via `Chunk`/`MENTIONS`, relations via
  `RELATED.source_chunk_ids` (§3). Nothing — node *or* link — enters the graph without a citable
  source chunk; e.g. the `Metformin —treats→ Type 2 diabetes` edge resolves to the exact sentence
  that asserted it.

**Open decision:** private-import concept matching a global concept → **link via `same_as`**
(recommended; clean tenancy) vs **merge into the global node** (simpler graph, leakier boundary).

## 13. Phasing

1. Port + contracts + `InMemory` + `Neo4j` repos; graph-med-compatible Neo4j reads; `graph`
   extra; Neo4j service/config in compose.
2. Builder over the **seeded** corpus (global graph) + `kg_build` on reindex; read APIs.
3. `/knowledge` graph tab (view + provenance panel).
4. **User import → `kg_update`** (org-scoped) + import UI.
5. Node embeddings + review-gated normalization/merges (graph-aware retrieval, review queue).

## 14. Testing

- Unit: `InMemoryKnowledgeGraphRepository` (resolution/merge/neighborhood),
  `GraphMedService` dependency-gating/import orchestration, graph-med adapter response parsing,
  scope isolation
  (org A cannot read org B).
- Integration: import → `kg_update` job → graph reflects new concepts; API neighborhood bounds.
- Neo4j adapter: a focused suite gated on a live Neo4j URI, exercising graph-med native labels,
  `MERGE` idempotency, and Cypher neighborhood traversal.
