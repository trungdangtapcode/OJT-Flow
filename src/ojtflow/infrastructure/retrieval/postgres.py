"""Postgres-backed healthcare retrieval adapter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ojtflow.core.contracts.enums import EvidenceSourceType, TrustLevel
from ojtflow.core.contracts.retrieval import RetrievalPackage, RetrievalQuery, RetrievalSource
from ojtflow.infrastructure.retrieval.corpus import load_local_corpus_chunks
from ojtflow.infrastructure.retrieval.engine import (
    DeterministicEmbeddingProvider,
    KnowledgeChunk,
    build_query_variants,
    chunk_metadata_json,
    default_healthcare_chunks,
    rank_chunks,
)
from ojtflow.infrastructure.storage.postgres import PostgresBackboneStore


class PostgresRetrievalRepository:
    """Stores trusted knowledge chunks in Postgres and ranks them for workflows."""

    def __init__(
        self,
        backbone: PostgresBackboneStore,
        knowledge_root: Path | str,
        embedding_provider: Any | None = None,
        corpus_dirs: tuple[Path, ...] | None = None,
        chunk_max_chars: int = 1200,
        chunk_overlap_chars: int = 160,
        seed_defaults: bool = True,
    ) -> None:
        self.backbone = backbone
        self.knowledge_root = Path(knowledge_root)
        self.embedding_provider = embedding_provider or DeterministicEmbeddingProvider()
        self.corpus_dirs = corpus_dirs or (self.knowledge_root / "corpus",)
        self.chunk_max_chars = chunk_max_chars
        self.chunk_overlap_chars = chunk_overlap_chars
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
            "corpus": corpus_result.__dict__ if corpus_result else None,
        }

    def _upsert_chunks(self, chunks: list[KnowledgeChunk]) -> None:
        if not chunks:
            return
        vector_dimensions = self._vector_column_dimensions()
        chunk_texts = [f"{chunk.title}\n{chunk.content}" for chunk in chunks]
        embeddings = self.embedding_provider.embed_documents(chunk_texts)
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                for chunk, embedding in zip(chunks, embeddings, strict=True):
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
                            chunk_metadata_json(chunk),
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
                            json.dumps(chunk.metadata, sort_keys=True),
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

    def search(self, query: RetrievalQuery) -> RetrievalPackage:
        chunks, postgres_warnings = self._load_candidate_chunks(query)
        if not chunks:
            postgres_warnings.append(
                "No retrieval chunks matched filters; returning empty package."
            )
        return rank_chunks(
            chunks,
            query,
            embedding_provider=self.embedding_provider,
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
                        document.standard_system
                    order by document.source_id
                    """
                )
                rows = cursor.fetchall()
        return [
            RetrievalSource(
                source_id=row["source_id"],
                source_type=EvidenceSourceType(row["source_type"]),
                title=row["title"],
                source_version=row["source_version"],
                trust_level=TrustLevel(row["trust_level"]),
                clinical_domain=row["clinical_domain"],
                standard_system=row["standard_system"],
                chunk_count=row["chunk_count"],
            )
            for row in rows
        ]

    def _load_candidate_chunks(
        self,
        query: RetrievalQuery,
    ) -> tuple[list[KnowledgeChunk], list[str]]:
        where_sql, filter_params = _filters_sql(query.filters)
        vector_dimensions = self._vector_column_dimensions()
        vector_literal: str | None = None
        if vector_dimensions == self.embedding_provider.dimensions:
            query_text = " ".join(build_query_variants(query))
            vector_literal = _vector_literal(self.embedding_provider.embed_query(query_text))

        params: list[Any] = [query.query, query.query]
        if vector_literal is not None:
            params.append(vector_literal)
        params.extend(filter_params)
        vector_select = (
            ", embedding <=> %s::vector as vector_distance"
            if vector_literal is not None
            else ", null::double precision as vector_distance"
        )
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
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
                        search_vector @@ websearch_to_tsquery('english', %s) as lexical_match
                        {vector_select}
                    from ojtflow.knowledge_chunks
                    {where_sql}
                    order by
                        lexical_match desc,
                        lexical_rank desc,
                        vector_distance asc nulls last,
                        updated_at desc
                    limit 200
                    """,
                    tuple(params),
                )
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
        return [_row_to_chunk(row) for row in rows], warnings

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
    for key in ("trust_level", "clinical_domain", "standard_system", "source_type"):
        value = filters.get(key)
        if value:
            clauses.append(f"{key} = %s")
            params.append(value)
    if not clauses:
        return "", params
    return "where " + " and ".join(clauses), params


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


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"
