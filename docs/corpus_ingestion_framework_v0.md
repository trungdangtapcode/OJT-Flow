# Corpus Ingestion Framework v0

OJTFlow retrieval now has a governed corpus-ingestion contract. The goal is to make every indexed healthcare knowledge artifact traceable before the project grows into larger medical corpora.

## Design

The framework has two layers:

1. **Adapter catalog**
   - File: `knowledge/source_catalog/corpus_adapters.json`
   - Contract: `CorpusAdapterCatalog`
   - Purpose: declares approved/candidate source adapters, licenses, release versions, access modes, ingestion modes, reviewer state, lifecycle state, source URLs, and local file paths.

2. **Ingestion manifest**
   - Endpoint: `GET /api/v1/retrieval/corpus/manifest`
   - Contract: `CorpusIngestionManifest`
   - Purpose: records observed local corpus files with hash, size, observed fetch time, matching adapter, license metadata, reviewer state, lifecycle state, and warnings.

The retrieval repositories consume the manifest when loading local corpus files. Chunks inherit manifest metadata, and `/api/v1/retrieval/sources` exposes reviewer/license/hash fields when the backend has them.

## Lifecycle States

Use these states consistently:

- `candidate`: known source adapter, not fully production-approved yet.
- `approved`: reviewed and allowed for current retrieval scope.
- `needs_review`: source can be inspected, but should not be treated as fully governed.
- `deprecated`: still visible for audit/history, but should be replaced.
- `blocked`: should not be indexed.
- `failed`: ingestion attempted but did not produce a usable artifact.

Uncataloged local corpus files are still discoverable, but the manifest marks them `needs_review` with `uncataloged_local_corpus_file`.

## Source Metadata

Each manifest item records:

- `adapter_id`
- `source_id`
- `release_version`
- `fetched_at`
- `fetch_time_source`
- `content_hash`
- `license`
- `reviewer_state`
- `lifecycle_state`
- `path` or `source_url`
- `warnings`

For local files, `fetched_at` currently comes from filesystem mtime and `fetch_time_source` is `filesystem_mtime`. External download adapters should replace that with real HTTP/API fetch time when live fetch jobs are implemented.

## API

### List Corpus Adapters

```http
GET /api/v1/retrieval/corpus/adapters
```

Returns the data-driven source adapter catalog.

### List Corpus Manifest

```http
GET /api/v1/retrieval/corpus/manifest
```

Returns the observed local corpus manifest for `knowledge/corpus`.

### Reindex Retrieval

```http
POST /api/v1/retrieval/reindex
```

The response now includes `data.corpus.manifest` when corpus indexing runs.

## Extension Rules

Add a new source by editing data first:

1. Add an adapter entry in `knowledge/source_catalog/corpus_adapters.json`.
2. Include license constraints and lifecycle/reviewer state.
3. Add local paths only for curated files committed to the repository.
4. Keep bulk datasets in ignored runtime storage, not git.
5. Add a parser/fetcher later only when the adapter contract is stable.

This keeps parsing, governance, retrieval ranking, and storage concerns separated.
