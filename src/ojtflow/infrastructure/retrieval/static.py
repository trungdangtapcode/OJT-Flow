"""Static retrieval adapters for tests and local fallback."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ojtflow.core.contracts.enums import EvidenceSourceType, TrustLevel
from ojtflow.core.contracts.evidence import Evidence
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
    default_healthcare_chunks,
    diversity_settings_from_query,
    rank_chunks,
    sources_from_chunks,
)
from ojtflow.infrastructure.retrieval.integrity import build_integrity_report
from ojtflow.infrastructure.retrieval.query_analysis import build_retrieval_plan


class StaticKnowledgeRepository:
    """Loads trusted schemas and fixture evidence from local files."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.schemas_dir = self.root / "schemas"

    def get_schema(self, schema_id: str | None) -> dict | None:
        if not schema_id:
            return None
        path = self.schemas_dir / f"{schema_id}.schema.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list_schemas(self) -> list[dict]:
        """Return lightweight schema registry entries for the product UI."""

        schemas: list[dict] = []
        for path in sorted(self.schemas_dir.glob("*.schema.json")):
            schema = json.loads(path.read_text(encoding="utf-8"))
            properties = schema.get("properties", {})
            schemas.append(
                {
                    "schema_id": schema.get("$id", path.name.removesuffix(".schema.json")),
                    "title": schema.get("title", schema.get("$id", path.stem)),
                    "version": schema.get("version", "unversioned"),
                    "required": schema.get("required", []),
                    "field_count": len(properties),
                    "fields": [
                        {
                            "name": name,
                            "type": definition.get("type", "unknown"),
                            "description": definition.get("description"),
                        }
                        for name, definition in properties.items()
                    ],
                    "source_ref": str(path.relative_to(self.root.parent)),
                }
            )
        return schemas

    def search(self, query: str, *, top_k: int = 5) -> list[Evidence]:
        """Backward-compatible evidence search for existing callers."""

        package = StaticRetrievalRepository(self.root).search(
            RetrievalQuery(query=query, top_k=top_k)
        )
        return package.evidence


class StaticRetrievalRepository:
    """Deterministic hybrid retrieval over local healthcare knowledge chunks."""

    def __init__(
        self,
        root: Path | str,
        embedding_provider: Any | None = None,
        reranker: Any | None = None,
        rerank_candidate_limit: int = 20,
        rerank_score_weight: float = 0.08,
        diversity_enabled: bool = True,
        diversity_lambda: float = 0.72,
        corpus_dirs: tuple[Path, ...] | None = None,
        chunk_max_chars: int = 1200,
        chunk_overlap_chars: int = 160,
    ) -> None:
        self.root = Path(root)
        self.embedding_provider = embedding_provider or DeterministicEmbeddingProvider()
        self.reranker = reranker
        self.rerank_candidate_limit = rerank_candidate_limit
        self.rerank_score_weight = rerank_score_weight
        self.diversity_enabled = diversity_enabled
        self.diversity_lambda = diversity_lambda
        self.corpus_dirs = corpus_dirs or (self.root / "corpus",)
        self.chunk_max_chars = chunk_max_chars
        self.chunk_overlap_chars = chunk_overlap_chars
        self._chunks = default_healthcare_chunks(self.root)

    def plan(self, query: RetrievalQuery) -> RetrievalPlan:
        return build_retrieval_plan(query)

    def search(self, query: RetrievalQuery) -> RetrievalPackage:
        chunks = self._filter_chunks(self._chunks, query)
        diversity_enabled, diversity_lambda = diversity_settings_from_query(
            query,
            default_enabled=self.diversity_enabled,
            default_lambda=self.diversity_lambda,
        )
        warnings = (
            []
            if chunks
            else ["No retrieval chunks matched filters; returning empty package."]
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
            strategy="static_hybrid_rrf",
            warnings=warnings,
            knowledge_root=self.root,
        )

    def list_sources(self) -> list[RetrievalSource]:
        return sources_from_chunks(self._chunks)

    def reindex(self, *, include_seeded: bool = True, include_corpus: bool = True) -> dict:
        chunks: list[KnowledgeChunk] = []
        result = None
        if include_seeded:
            chunks.extend(default_healthcare_chunks(self.root))
        if include_corpus:
            corpus_chunks, result = load_local_corpus_chunks(
                self.corpus_dirs,
                knowledge_root=self.root,
                max_chars=self.chunk_max_chars,
                overlap_chars=self.chunk_overlap_chars,
            )
            chunks.extend(corpus_chunks)
        self._chunks = chunks
        return {
            "repository": "static",
            "include_seeded": include_seeded,
            "include_corpus": include_corpus,
            "chunks_indexed": len(chunks),
            "corpus": result.to_dict() if result else None,
        }

    def integrity_report(
        self,
        *,
        include_seeded: bool = True,
        include_corpus: bool = False,
    ) -> RetrievalIntegrityReport:
        expected_chunks: list[KnowledgeChunk] = []
        if include_seeded:
            expected_chunks.extend(default_healthcare_chunks(self.root))
        if include_corpus:
            corpus_chunks, _result = load_local_corpus_chunks(
                self.corpus_dirs,
                knowledge_root=self.root,
                max_chars=self.chunk_max_chars,
                overlap_chars=self.chunk_overlap_chars,
            )
            expected_chunks.extend(corpus_chunks)
        return build_integrity_report(
            repository="static",
            expected_chunks=expected_chunks,
            indexed_chunks=self._chunks,
            checked_scope=_checked_scope(include_seeded=include_seeded, include_corpus=include_corpus),
        )

    def _filter_chunks(
        self,
        chunks: list[KnowledgeChunk],
        query: RetrievalQuery,
    ) -> list[KnowledgeChunk]:
        trust_level = query.filters.get("trust_level")
        clinical_domain = query.filters.get("clinical_domain")
        standard_system = query.filters.get("standard_system")
        source_type = query.filters.get("source_type")
        source_id = query.filters.get("source_id")
        filtered = chunks
        if trust_level:
            filtered = [chunk for chunk in filtered if chunk.trust_level == TrustLevel(trust_level)]
        if clinical_domain:
            filtered = [chunk for chunk in filtered if chunk.clinical_domain == clinical_domain]
        if standard_system:
            filtered = [chunk for chunk in filtered if chunk.standard_system == standard_system]
        if source_type:
            filtered = [
                chunk
                for chunk in filtered
                if chunk.source_type == EvidenceSourceType(source_type)
            ]
        if source_id:
            filtered = [chunk for chunk in filtered if chunk.source_id == source_id]
        return filtered


def _checked_scope(*, include_seeded: bool, include_corpus: bool) -> str:
    scopes = []
    if include_seeded:
        scopes.append("seeded")
    if include_corpus:
        scopes.append("corpus")
    return "+".join(scopes) or "none"
