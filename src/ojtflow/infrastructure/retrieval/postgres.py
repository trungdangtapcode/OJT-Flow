"""Postgres-backed healthcare retrieval adapter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ojtflow.core.contracts.enums import EvidenceSourceType, TrustLevel
from ojtflow.core.contracts.retrieval import RetrievalPackage, RetrievalQuery, RetrievalSource
from ojtflow.infrastructure.retrieval.engine import (
    DeterministicEmbeddingProvider,
    KnowledgeChunk,
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
        embedding_provider: DeterministicEmbeddingProvider | None = None,
        seed_defaults: bool = True,
    ) -> None:
        self.backbone = backbone
        self.knowledge_root = Path(knowledge_root)
        self.embedding_provider = embedding_provider or DeterministicEmbeddingProvider()
        if seed_defaults:
            self.seed_defaults()

    def seed_defaults(self) -> None:
        """Idempotently load bundled healthcare knowledge into retrieval tables."""

        chunks = default_healthcare_chunks(self.knowledge_root)
        has_vector = self._has_vector_column()
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                for chunk in chunks:
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
                    embedding = self.embedding_provider.embed(f"{chunk.title}\n{chunk.content}")
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
                    if has_vector:
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
        params = [query.query, query.query, *filter_params]
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
                    from ojtflow.knowledge_chunks
                    {where_sql}
                    order by lexical_match desc, lexical_rank desc, updated_at desc
                    limit 200
                    """,
                    tuple(params),
                )
                rows = cursor.fetchall()

        warnings: list[str] = []
        if rows and not any(row["lexical_match"] for row in rows):
            warnings.append(
                "No full-text match; ranked filtered knowledge chunks by fallback scoring."
            )
        return [_row_to_chunk(row) for row in rows], warnings

    def _has_vector_column(self) -> bool:
        with self.backbone.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select exists (
                        select 1
                        from information_schema.columns
                        where table_schema = 'ojtflow'
                          and table_name = 'knowledge_chunks'
                          and column_name = 'embedding'
                    ) as has_vector
                    """
                )
                row = cursor.fetchone()
        return bool(row and row["has_vector"])


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
