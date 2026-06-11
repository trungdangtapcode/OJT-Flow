"""Postgres-backed healthcare retrieval adapter."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from ojtflow.core.contracts.enums import EvidenceSourceType, TrustLevel
from ojtflow.core.contracts.retrieval import (
    RetrievalIntegrityReport,
    RetrievalPlan,
    RetrievalPackage,
    RetrievalQuery,
    RetrievalSource,
)
from ojtflow.infrastructure.retrieval.corpus import load_local_corpus_chunks
from ojtflow.infrastructure.retrieval.engine import (
    DeterministicEmbeddingProvider,
    KnowledgeChunk,
    build_query_variants,
    chunk_metadata_json,
    default_healthcare_chunks,
    diversity_settings_from_query,
    rank_chunks,
)
from ojtflow.infrastructure.retrieval.integrity import build_integrity_report
from ojtflow.infrastructure.retrieval.query_analysis import build_retrieval_plan
from ojtflow.infrastructure.storage.postgres import PostgresBackboneStore


POSTGRES_CANDIDATE_POOL_LIMIT = 200


class PostgresRetrievalRepository:
    """Stores trusted knowledge chunks in Postgres and ranks them for workflows."""

    def __init__(
        self,
        backbone: PostgresBackboneStore,
        knowledge_root: Path | str,
        embedding_provider: Any | None = None,
        reranker: Any | None = None,
        rerank_candidate_limit: int = 20,
        rerank_score_weight: float = 0.08,
        diversity_enabled: bool = True,
        diversity_lambda: float = 0.72,
        corpus_dirs: tuple[Path, ...] | None = None,
        chunk_max_chars: int = 1200,
        chunk_overlap_chars: int = 160,
        hnsw_ef_search: int = 100,
        seed_defaults: bool = True,
    ) -> None:
        self.backbone = backbone
        self.knowledge_root = Path(knowledge_root)
        self.embedding_provider = embedding_provider or DeterministicEmbeddingProvider()
        self.reranker = reranker
        self.rerank_candidate_limit = rerank_candidate_limit
        self.rerank_score_weight = rerank_score_weight
        self.diversity_enabled = diversity_enabled
        self.diversity_lambda = diversity_lambda
        self.corpus_dirs = corpus_dirs or (self.knowledge_root / "corpus",)
        self.chunk_max_chars = chunk_max_chars
        self.chunk_overlap_chars = chunk_overlap_chars
        self.hnsw_ef_search = hnsw_ef_search
        if seed_defaults:
            self.seed_defaults()

    def seed_defaults(self) -> None:
        """Idempotently load bundled healthcare knowledge into retrieval tables."""

        self._upsert_chunks(default_healthcare_chunks(self.knowledge_root))

    def reindex(self, *, include_seeded: bool = True, include_corpus: bool = True) -> dict:
        """Refresh the trusted retrieval index from configured sources."""

        chunks: list[KnowledgeChunk] = []
        corpus_result = None
        if include_seeded:
            chunks.extend(default_healthcare_chunks(self.knowledge_root))
        if include_corpus:
            corpus_chunks, corpus_result = load_local_corpus_chunks(
                self.corpus_dirs,
                knowledge_root=self.knowledge_root,
                max_chars=self.chunk_max_chars,
                overlap_chars=self.chunk_overlap_chars,
            )
            chunks.extend(corpus_chunks)

        if include_corpus:
            with self.backbone.connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        delete from ojtflow.knowledge_documents
                        where metadata #>> '{metadata,origin}' = 'local_corpus'
                        """
                    )
                connection.commit()

        self._upsert_chunks(chunks)
        return {
            "repository": "postgres",
            "include_seeded": include_seeded,
            "include_corpus": include_corpus,
            "chunks_indexed": len(chunks),
            "embedding": self.embedding_provider.metadata(),
            "embedding_generation_id": _embedding_generation_id(
                self.embedding_provider.metadata()
            ),
            "corpus": corpus_result.to_dict() if corpus_result else None,
        }

    def _upsert_chunks(self, chunks: list[KnowledgeChunk]) -> None:
        if not chunks:
            return
        vector_dimensions = self._vector_column_dimensions()
        embedding_metadata = self.embedding_provider.metadata()
        embedding_generation_id = _embedding_generation_id(embedding_metadata)
        chunk_texts = [f"{chunk.title}\n{chunk.content}" for chunk in chunks]
        embeddings = self.embedding_provider.embed_documents(chunk_texts)
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                for chunk, embedding in zip(chunks, embeddings, strict=True):
                    chunk_metadata = _chunk_metadata_with_embedding_generation(
                        chunk,
                        embedding_metadata=embedding_metadata,
                        embedding_generation_id=embedding_generation_id,
                    )
                    cursor.execute(
                        """
                        insert into ojtflow.knowledge_documents (
                            source_id, source_type, title, source_version, trust_level,
                            clinical_domain, standard_system, metadata
                        ) values (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                        on conflict(source_id) do update set
                            source_type = excluded.source_type,
                            title = excluded.title,
                            source_version = excluded.source_version,
                            trust_level = excluded.trust_level,
                            clinical_domain = excluded.clinical_domain,
                            standard_system = excluded.standard_system,
                            metadata = excluded.metadata,
                            updated_at = now()
                        """,
                        (
                            chunk.source_id,
                            chunk.source_type.value,
                            chunk.title,
                            chunk.source_version,
                            chunk.trust_level.value,
                            chunk.clinical_domain,
                            chunk.standard_system,
                            chunk_metadata_json(
                                _chunk_with_metadata(chunk, chunk_metadata)
                            ),
                        ),
                    )
                    cursor.execute(
                        """
                        insert into ojtflow.knowledge_chunks (
                            chunk_id, source_id, source_type, title,
                            source_version, trust_level, clinical_domain,
                            standard_system, content, locator, metadata,
                            embedding_json
                        ) values (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s::jsonb, %s::jsonb, %s::jsonb
                        )
                        on conflict(chunk_id) do update set
                            source_id = excluded.source_id,
                            source_type = excluded.source_type,
                            title = excluded.title,
                            source_version = excluded.source_version,
                            trust_level = excluded.trust_level,
                            clinical_domain = excluded.clinical_domain,
                            standard_system = excluded.standard_system,
                            content = excluded.content,
                            locator = excluded.locator,
                            metadata = excluded.metadata,
                            embedding_json = excluded.embedding_json,
                            updated_at = now()
                        """,
                        (
                            chunk.chunk_id,
                            chunk.source_id,
                            chunk.source_type.value,
                            chunk.title,
                            chunk.source_version,
                            chunk.trust_level.value,
                            chunk.clinical_domain,
                            chunk.standard_system,
                            chunk.content,
                            json.dumps(chunk.locator, sort_keys=True),
                            json.dumps(chunk_metadata, sort_keys=True),
                            json.dumps(embedding),
                        ),
                    )
                    if vector_dimensions == len(embedding):
                        cursor.execute(
                            """
                            update ojtflow.knowledge_chunks
                            set embedding = %s::vector
                            where chunk_id = %s
                            """,
                            (_vector_literal(embedding), chunk.chunk_id),
                        )
            connection.commit()

    def plan(self, query: RetrievalQuery) -> RetrievalPlan:
        return build_retrieval_plan(query)

    def search(self, query: RetrievalQuery) -> RetrievalPackage:
        chunks, postgres_warnings = self._load_candidate_chunks(query)
        diversity_enabled, diversity_lambda = diversity_settings_from_query(
            query,
            default_enabled=self.diversity_enabled,
            default_lambda=self.diversity_lambda,
        )
        if not chunks:
            postgres_warnings.append(
                "No retrieval chunks matched filters; returning empty package."
            )
        return rank_chunks(
            chunks,
            query,
            embedding_provider=self.embedding_provider,
            reranker=self.reranker,
            rerank_candidate_limit=self.rerank_candidate_limit,
            rerank_score_weight=self.rerank_score_weight,
            diversity_enabled=diversity_enabled,
            diversity_lambda=diversity_lambda,
            strategy="postgres_fts_vector_rrf",
            warnings=postgres_warnings,
        )

    def list_sources(self) -> list[RetrievalSource]:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select
                        document.source_id,
                        document.source_type,
                        document.title,
                        document.source_version,
                        document.trust_level,
                        document.clinical_domain,
                        document.standard_system,
                        document.metadata,
                        count(chunk.chunk_id)::int as chunk_count
                    from ojtflow.knowledge_documents document
                    left join ojtflow.knowledge_chunks chunk
                        on chunk.source_id = document.source_id
                    group by
                        document.source_id,
                        document.source_type,
                        document.title,
                        document.source_version,
                        document.trust_level,
                        document.clinical_domain,
                        document.standard_system,
                        document.metadata
                    order by document.source_id
                    """
                )
                rows = cursor.fetchall()
        sources: list[RetrievalSource] = []
        for row in rows:
            source_metadata = _source_metadata_from_document_metadata(row.get("metadata"))
            sources.append(
                RetrievalSource(
                    source_id=row["source_id"],
                    source_type=EvidenceSourceType(row["source_type"]),
                    title=row["title"],
                    source_version=row["source_version"],
                    trust_level=TrustLevel(row["trust_level"]),
                    clinical_domain=row["clinical_domain"],
                    standard_system=row["standard_system"],
                    chunk_count=row["chunk_count"],
                    authority=source_metadata.get("authority"),
                    access_mode=source_metadata.get("access_mode"),
                    ingestion_mode=source_metadata.get("ingestion_mode"),
                    license_id=source_metadata.get("license_id"),
                    license_name=source_metadata.get("license_name"),
                    reviewer_state=source_metadata.get("reviewer_state"),
                    lifecycle_state=source_metadata.get("lifecycle_state"),
                    content_hash=source_metadata.get("content_hash"),
                    canonical_source_id=source_metadata.get("canonical_source_id"),
                    chunk_profile=source_metadata.get("chunk_profile"),
                    resource_type=source_metadata.get("resource_type"),
                )
            )
        return sources

    def integrity_report(
        self,
        *,
        include_seeded: bool = True,
        include_corpus: bool = False,
    ) -> RetrievalIntegrityReport:
        expected_chunks: list[KnowledgeChunk] = []
        if include_seeded:
            expected_chunks.extend(default_healthcare_chunks(self.knowledge_root))
        if include_corpus:
            corpus_chunks, _result = load_local_corpus_chunks(
                self.corpus_dirs,
                knowledge_root=self.knowledge_root,
                max_chars=self.chunk_max_chars,
                overlap_chars=self.chunk_overlap_chars,
            )
            expected_chunks.extend(corpus_chunks)
        return build_integrity_report(
            repository="postgres",
            expected_chunks=expected_chunks,
            indexed_chunks=self._load_all_chunks(),
            checked_scope=_checked_scope(include_seeded=include_seeded, include_corpus=include_corpus),
        )

    def _load_candidate_chunks(
        self,
        query: RetrievalQuery,
    ) -> tuple[list[KnowledgeChunk], list[str]]:
        where_sql, filter_params = _filters_sql(query.filters)
        vector_dimensions = self._vector_column_dimensions()
        vector_literal: str | None = None
        query_text = " ".join(build_query_variants(query))
        if vector_dimensions == self.embedding_provider.dimensions:
            vector_literal = _vector_literal(self.embedding_provider.embed_query(query_text))

        if vector_literal is not None:
            sql = _hybrid_candidate_sql(where_sql)
            params: list[Any] = [
                query_text,
                query_text,
                vector_literal,
                *filter_params,
                POSTGRES_CANDIDATE_POOL_LIMIT,
                query_text,
                query_text,
                vector_literal,
                *filter_params,
                POSTGRES_CANDIDATE_POOL_LIMIT,
            ]
        else:
            sql = _lexical_candidate_sql(where_sql)
            params = [
                query_text,
                query_text,
                *filter_params,
                POSTGRES_CANDIDATE_POOL_LIMIT,
            ]

        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                if vector_literal is not None:
                    cursor.execute(
                        "select set_config('hnsw.ef_search', %s, true)",
                        (str(self.hnsw_ef_search),),
                    )
                cursor.execute(sql, tuple(params))
                rows = cursor.fetchall()

        warnings: list[str] = []
        if vector_dimensions is None:
            warnings.append(
                "Postgres pgvector column is unavailable; retrieval used full-text candidates "
                "and JSON/Python vector reranking."
            )
        elif vector_dimensions != self.embedding_provider.dimensions:
            warnings.append(
                "Postgres pgvector dimension does not match the configured embedding provider; "
                "retrieval used full-text candidates and JSON/Python vector reranking."
            )
        if rows and not any(row["lexical_match"] for row in rows):
            warnings.append(
                "No full-text match; ranked filtered knowledge chunks by fallback scoring."
            )
        stale_count = _stale_embedding_generation_count(
            rows,
            current_generation_id=_embedding_generation_id(
                self.embedding_provider.metadata()
            ),
        )
        if stale_count:
            warnings.append(
                "Postgres indexed embedding generation does not match the configured "
                f"embedding provider for {stale_count} candidate chunk(s); run retrieval reindex."
            )
        return [_row_to_chunk(row) for row in rows], warnings

    def _load_all_chunks(self) -> list[KnowledgeChunk]:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select
                        chunk_id,
                        source_id,
                        source_type,
                        title,
                        source_version,
                        trust_level,
                        clinical_domain,
                        standard_system,
                        content,
                        locator,
                        metadata
                    from ojtflow.knowledge_chunks
                    order by source_id, chunk_id
                    """
                )
                rows = cursor.fetchall()
        return [_row_to_chunk(row) for row in rows]

    def _vector_column_dimensions(self) -> int | None:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select format_type(attribute.atttypid, attribute.atttypmod) as data_type
                    from pg_attribute attribute
                    join pg_class class on class.oid = attribute.attrelid
                    join pg_namespace namespace on namespace.oid = class.relnamespace
                    where namespace.nspname = 'ojtflow'
                      and class.relname = 'knowledge_chunks'
                      and attribute.attname = 'embedding'
                      and not attribute.attisdropped
                    """
                )
                row = cursor.fetchone()
        if not row:
            return None
        data_type = str(row["data_type"])
        if not data_type.startswith("vector(") or not data_type.endswith(")"):
            return None
        try:
            return int(data_type.removeprefix("vector(").removesuffix(")"))
        except ValueError:
            return None


def _filters_sql(filters: dict[str, Any]) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    for key in ("trust_level", "clinical_domain", "standard_system", "source_type", "source_id"):
        value = filters.get(key)
        if value:
            clauses.append(f"{key} = %s")
            params.append(value)
    if not clauses:
        return "", params
    return "where " + " and ".join(clauses), params


def _lexical_candidate_sql(where_sql: str) -> str:
    return f"""
        select
            chunk_id,
            source_id,
            source_type,
            title,
            source_version,
            trust_level,
            clinical_domain,
            standard_system,
            content,
            locator,
            metadata,
            ts_rank_cd(
                search_vector,
                websearch_to_tsquery('english', %s)
            ) as lexical_rank,
            search_vector @@ websearch_to_tsquery('english', %s) as lexical_match,
            null::double precision as vector_distance,
            updated_at
        from ojtflow.knowledge_chunks
        {where_sql}
        order by
            lexical_match desc,
            lexical_rank desc,
            updated_at desc
        limit %s
    """


def _hybrid_candidate_sql(where_sql: str) -> str:
    vector_where_sql = _append_where_clause(where_sql, "embedding is not null")
    return f"""
        with lexical_candidates as (
            select
                chunk_id,
                source_id,
                source_type,
                title,
                source_version,
                trust_level,
                clinical_domain,
                standard_system,
                content,
                locator,
                metadata,
                ts_rank_cd(
                    search_vector,
                    websearch_to_tsquery('english', %s)
                ) as lexical_rank,
                search_vector @@ websearch_to_tsquery('english', %s) as lexical_match,
                embedding <=> %s::vector as vector_distance,
                updated_at
            from ojtflow.knowledge_chunks
            {where_sql}
            order by
                lexical_match desc,
                lexical_rank desc,
                updated_at desc
            limit %s
        ),
        vector_candidates as (
            select
                chunk_id,
                source_id,
                source_type,
                title,
                source_version,
                trust_level,
                clinical_domain,
                standard_system,
                content,
                locator,
                metadata,
                ts_rank_cd(
                    search_vector,
                    websearch_to_tsquery('english', %s)
                ) as lexical_rank,
                search_vector @@ websearch_to_tsquery('english', %s) as lexical_match,
                embedding <=> %s::vector as vector_distance,
                updated_at
            from ojtflow.knowledge_chunks
            {vector_where_sql}
            order by
                vector_distance asc nulls last,
                lexical_match desc,
                lexical_rank desc,
                updated_at desc
            limit %s
        )
        select distinct on (chunk_id)
            chunk_id,
            source_id,
            source_type,
            title,
            source_version,
            trust_level,
            clinical_domain,
            standard_system,
            content,
            locator,
            metadata,
            lexical_rank,
            lexical_match,
            vector_distance,
            updated_at
        from (
            select * from lexical_candidates
            union all
            select * from vector_candidates
        ) candidates
        order by
            chunk_id,
            lexical_match desc,
            lexical_rank desc,
            vector_distance asc nulls last,
            updated_at desc
    """


def _append_where_clause(where_sql: str, clause: str) -> str:
    if where_sql.strip():
        return f"{where_sql} and {clause}"
    return f"where {clause}"


def _row_to_chunk(row: dict[str, Any]) -> KnowledgeChunk:
    return KnowledgeChunk(
        chunk_id=row["chunk_id"],
        source_id=row["source_id"],
        source_type=EvidenceSourceType(row["source_type"]),
        title=row["title"],
        source_version=row["source_version"],
        trust_level=TrustLevel(row["trust_level"]),
        clinical_domain=row["clinical_domain"],
        standard_system=row["standard_system"],
        content=row["content"],
        locator=row["locator"] or {},
        metadata=row["metadata"] or {},
    )


def _chunk_with_metadata(chunk: KnowledgeChunk, metadata: dict[str, Any]) -> KnowledgeChunk:
    return KnowledgeChunk(
        chunk_id=chunk.chunk_id,
        source_id=chunk.source_id,
        source_type=chunk.source_type,
        title=chunk.title,
        content=chunk.content,
        source_version=chunk.source_version,
        trust_level=chunk.trust_level,
        clinical_domain=chunk.clinical_domain,
        standard_system=chunk.standard_system,
        locator=chunk.locator,
        metadata=metadata,
    )


def _chunk_metadata_with_embedding_generation(
    chunk: KnowledgeChunk,
    *,
    embedding_metadata: dict[str, Any],
    embedding_generation_id: str,
) -> dict[str, Any]:
    return {
        **chunk.metadata,
        "embedding_provider": embedding_metadata.get("provider"),
        "embedding_model": embedding_metadata.get("model"),
        "embedding_dimensions": embedding_metadata.get("dimensions"),
        "embedding_generation_id": embedding_generation_id,
    }


def _embedding_generation_id(embedding_metadata: dict[str, Any]) -> str:
    payload = {
        "provider": embedding_metadata.get("provider"),
        "model": embedding_metadata.get("model"),
        "dimensions": embedding_metadata.get("dimensions"),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"embgen:{sha256(encoded.encode('utf-8')).hexdigest()[:16]}"


def _stale_embedding_generation_count(
    rows: list[dict[str, Any]],
    *,
    current_generation_id: str,
) -> int:
    count = 0
    for row in rows:
        metadata = row.get("metadata")
        if not isinstance(metadata, dict):
            count += 1
            continue
        indexed_generation_id = metadata.get("embedding_generation_id")
        if indexed_generation_id != current_generation_id:
            count += 1
    return count


def _source_metadata_from_document_metadata(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    metadata = value.get("metadata", value)
    if not isinstance(metadata, dict):
        return {}
    return {
        key: metadata.get(key)
        for key in (
            "authority",
            "access_mode",
            "ingestion_mode",
            "license_id",
            "license_name",
            "reviewer_state",
            "lifecycle_state",
            "content_hash",
            "canonical_source_id",
            "chunk_profile",
            "resource_type",
        )
        if metadata.get(key) is not None
    }


def _checked_scope(*, include_seeded: bool, include_corpus: bool) -> str:
    scopes = []
    if include_seeded:
        scopes.append("seeded")
    if include_corpus:
        scopes.append("corpus")
    return "+".join(scopes) or "none"


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"
