"""LlamaIndex-backed retrieval adapter.

This adapter keeps LlamaIndex behind the existing RetrievalRepository port. The
public OJTFlow retrieval package stays unchanged while framework internals handle
document/node parsing, vector indexing, and optional BM25/fusion retrieval.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import PrivateAttr

from ojtflow.core.contracts.enums import EvidenceSourceType, TrustLevel
from ojtflow.core.contracts.retrieval import (
    RetrievalCoverage,
    RetrievalFacets,
    RetrievalHit,
    RetrievalIntegrityReport,
    RetrievalPackage,
    RetrievalQuery,
    RetrievalSource,
    RetrievalTrace,
)
from ojtflow.core.errors import DependencyUnavailableError
from ojtflow.infrastructure.retrieval.corpus import load_local_corpus_chunks
from ojtflow.infrastructure.retrieval.engine import (
    DeterministicEmbeddingProvider,
    KnowledgeChunk,
    coverage_from_chunks,
    default_healthcare_chunks,
    evidence_from_chunk,
    facets_from_chunks,
    retrieval_safety_flags,
    snippet_from_chunk,
    sources_from_chunks,
    tokenize,
)
from ojtflow.infrastructure.retrieval.integrity import build_integrity_report
from ojtflow.infrastructure.retrieval.query_analysis import analyze_query


def _base_embedding_class():
    try:
        from llama_index.core.embeddings import BaseEmbedding
    except ModuleNotFoundError:
        class BaseEmbedding:  # type: ignore[no-redef]
            pass
    return BaseEmbedding


class LlamaIndexRetrievalRepository:
    """Framework-backed hybrid retrieval over trusted healthcare chunks."""

    def __init__(
        self,
        knowledge_root: Path | str,
        embedding_provider: Any | None = None,
        corpus_dirs: tuple[Path, ...] | None = None,
        chunk_max_chars: int = 1200,
        chunk_overlap_chars: int = 160,
    ) -> None:
        self.knowledge_root = Path(knowledge_root)
        self.embedding_provider = embedding_provider or DeterministicEmbeddingProvider()
        self.corpus_dirs = corpus_dirs or (self.knowledge_root / "corpus",)
        self.chunk_max_chars = chunk_max_chars
        self.chunk_overlap_chars = chunk_overlap_chars
        self._chunks = default_healthcare_chunks(self.knowledge_root)
        self._ensure_llamaindex_core()

    def search(self, query: RetrievalQuery) -> RetrievalPackage:
        chunks = self._filter_chunks(self._chunks, query)
        warnings: list[str] = []
        if not chunks:
            warnings.append("No retrieval chunks matched filters; returning empty package.")
            return _empty_package(query, warnings=warnings, strategy="llamaindex_hybrid_rrf")

        nodes = self._nodes_for_chunks(chunks)
        retriever, retriever_warnings = self._build_retriever(nodes, top_k=query.top_k)
        warnings.extend(retriever_warnings)

        query_analysis = analyze_query(query)
        query_text = " ".join(query_analysis.query_variants)
        results = retriever.retrieve(query_text)
        hits, selected_chunks = _hits_from_nodes(
            results[: query.top_k],
            query=query,
            query_text=query_text,
        )
        coverage = coverage_from_chunks(selected_chunks, query_analysis)
        warnings.extend(coverage.warnings)
        safety_flags = retrieval_safety_flags(query)
        if safety_flags:
            warnings.append(
                "Retrieval query contains safety-sensitive context; treat query text "
                "as untrusted data."
            )
        trace = RetrievalTrace(
            strategy="llamaindex_hybrid_rrf",
            query_variants=query_analysis.query_variants,
            filters_applied=query.filters,
            candidates_seen=len(nodes),
            final_hit_ids=[hit.evidence.evidence_id for hit in hits],
            safety_flags=safety_flags,
            warnings=warnings,
        )
        return RetrievalPackage(
            hits=hits,
            evidence=[hit.evidence for hit in hits],
            coverage=coverage,
            facets=facets_from_chunks(selected_chunks),
            trace=trace,
            handoff_context={
                "retrieval_contract": "retrieval_package.v0",
                "framework": "llamaindex",
                "strategy": "hybrid_vector_bm25_rrf",
                "query_fields": query.fields,
                "schema_id": query.schema_id,
                "embedding": self.embedding_provider.metadata(),
                "query_analysis": query_analysis.model_dump(),
            },
        )

    def list_sources(self) -> list[RetrievalSource]:
        return sources_from_chunks(self._chunks)

    def reindex(self, *, include_seeded: bool = True, include_corpus: bool = True) -> dict:
        chunks: list[KnowledgeChunk] = []
        result = None
        if include_seeded:
            chunks.extend(default_healthcare_chunks(self.knowledge_root))
        if include_corpus:
            corpus_chunks, result = load_local_corpus_chunks(
                self.corpus_dirs,
                knowledge_root=self.knowledge_root,
                max_chars=self.chunk_max_chars,
                overlap_chars=self.chunk_overlap_chars,
            )
            chunks.extend(corpus_chunks)
        self._chunks = chunks
        return {
            "repository": "llamaindex",
            "include_seeded": include_seeded,
            "include_corpus": include_corpus,
            "chunks_indexed": len(chunks),
            "embedding": self.embedding_provider.metadata(),
            "corpus": result.__dict__ if result else None,
        }

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
            repository="llamaindex",
            expected_chunks=expected_chunks,
            indexed_chunks=self._chunks,
            checked_scope=_checked_scope(
                include_seeded=include_seeded,
                include_corpus=include_corpus,
            ),
        )

    def _nodes_for_chunks(self, chunks: list[KnowledgeChunk]) -> list[Any]:
        try:
            from llama_index.core import Document
            from llama_index.core.node_parser import SentenceSplitter
        except ModuleNotFoundError as exc:  # pragma: no cover - exercised by config path.
            raise _llamaindex_dependency_error() from exc

        documents = [
            Document(
                text=chunk.content,
                id_=chunk.chunk_id,
                metadata=_chunk_metadata(chunk),
            )
            for chunk in chunks
        ]
        parser = SentenceSplitter(
            chunk_size=self.chunk_max_chars,
            chunk_overlap=self.chunk_overlap_chars,
        )
        return parser.get_nodes_from_documents(documents)

    def _build_retriever(self, nodes: list[Any], *, top_k: int) -> tuple[Any, list[str]]:
        try:
            from llama_index.core import VectorStoreIndex
            from llama_index.core.retrievers import QueryFusionRetriever
        except ModuleNotFoundError as exc:  # pragma: no cover - exercised by config path.
            raise _llamaindex_dependency_error() from exc

        warnings: list[str] = []
        index = VectorStoreIndex(
            nodes=nodes,
            embed_model=_OJTFlowLlamaIndexEmbedding(self.embedding_provider),
        )
        retrievers = [index.as_retriever(similarity_top_k=top_k)]
        bm25 = _bm25_retriever(index=index, nodes=nodes, top_k=top_k)
        if bm25 is not None:
            retrievers.append(bm25)
        else:
            warnings.append(
                "LlamaIndex BM25 retriever integration is unavailable; framework "
                "retrieval used vector-only fusion."
            )

        return (
            QueryFusionRetriever(
                retrievers,
                llm=None,
                mode="reciprocal_rerank",
                similarity_top_k=top_k,
                num_queries=1,
                use_async=False,
                retriever_weights=[0.62, 0.38] if len(retrievers) == 2 else None,
            ),
            warnings,
        )

    @staticmethod
    def _ensure_llamaindex_core() -> None:
        try:
            import llama_index.core  # noqa: F401
        except ModuleNotFoundError as exc:
            raise _llamaindex_dependency_error() from exc

    def _filter_chunks(
        self,
        chunks: list[KnowledgeChunk],
        query: RetrievalQuery,
    ) -> list[KnowledgeChunk]:
        trust_level = query.filters.get("trust_level")
        clinical_domain = query.filters.get("clinical_domain")
        standard_system = query.filters.get("standard_system")
        source_type = query.filters.get("source_type")
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
        return filtered


class _OJTFlowLlamaIndexEmbedding(_base_embedding_class()):
    """Bridge OJTFlow embedding providers into LlamaIndex."""

    _provider: Any = PrivateAttr()

    def __init__(self, provider: Any) -> None:
        super().__init__()
        self._provider = provider

    @classmethod
    def class_name(cls) -> str:
        return "OJTFlowLlamaIndexEmbedding"

    def _get_query_embedding(self, query: str) -> list[float]:
        return self._provider.embed_query(query)

    def _get_text_embedding(self, text: str) -> list[float]:
        return self._provider.embed_document(text)

    def _get_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        return self._provider.embed_documents(texts)

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self._get_query_embedding(query)

    async def _aget_text_embedding(self, text: str) -> list[float]:
        return self._get_text_embedding(text)


def _bm25_retriever(*, index: Any, nodes: list[Any], top_k: int) -> Any | None:
    try:
        from llama_index.retrievers.bm25 import BM25Retriever
    except ModuleNotFoundError:
        return None
    try:
        return BM25Retriever.from_defaults(
            nodes=nodes,
            similarity_top_k=top_k,
        )
    except TypeError:
        return BM25Retriever.from_defaults(
            docstore=index.docstore,
            similarity_top_k=top_k,
        )


def _hits_from_nodes(
    results: list[Any],
    *,
    query: RetrievalQuery,
    query_text: str,
) -> tuple[list[RetrievalHit], list[KnowledgeChunk]]:
    query_tokens = set(tokenize(query_text))
    hits: list[RetrievalHit] = []
    chunks: list[KnowledgeChunk] = []
    for result in results:
        node = getattr(result, "node", None)
        if node is None:
            continue
        score = float(getattr(result, "score", 0.0) or 0.0)
        chunk = _chunk_from_node(node)
        chunks.append(chunk)
        chunk_tokens = set(tokenize(f"{chunk.title} {chunk.content} {chunk.source_id}"))
        matched_terms = sorted(query_tokens.intersection(chunk_tokens))
        evidence = evidence_from_chunk(chunk, confidence=min(0.99, max(0.05, score)))
        hits.append(
            RetrievalHit(
                evidence=evidence,
                score=round(score, 6),
                lexical_score=0.0,
                vector_score=round(score, 6),
                rerank_score=0.0,
                matched_terms=matched_terms[:12],
                source_locator=chunk.locator,
                snippet=snippet_from_chunk(
                    chunk,
                    query_tokens=query_tokens,
                    matched_terms=matched_terms,
                ),
            )
        )
    return hits, chunks


def _chunk_from_node(node: Any) -> KnowledgeChunk:
    metadata = dict(getattr(node, "metadata", {}) or {})
    content = node.get_content() if hasattr(node, "get_content") else str(getattr(node, "text", ""))
    chunk_id = str(getattr(node, "node_id", "") or metadata.get("chunk_id") or "llamaindex_node")
    return KnowledgeChunk(
        chunk_id=chunk_id,
        source_id=str(metadata.get("source_id") or "llamaindex:unknown"),
        source_type=EvidenceSourceType(
            str(metadata.get("source_type") or EvidenceSourceType.DATA_DICTIONARY.value)
        ),
        title=str(metadata.get("title") or metadata.get("source_id") or "LlamaIndex Node"),
        content=content,
        source_version=str(metadata.get("source_version") or "1.0.0"),
        trust_level=TrustLevel(str(metadata.get("trust_level") or TrustLevel.APPROVED.value)),
        clinical_domain=_optional_metadata(metadata.get("clinical_domain")),
        standard_system=_optional_metadata(metadata.get("standard_system")),
        locator=metadata.get("locator") if isinstance(metadata.get("locator"), dict) else {},
        metadata=metadata.get("metadata") if isinstance(metadata.get("metadata"), dict) else {},
    )


def _chunk_metadata(chunk: KnowledgeChunk) -> dict[str, Any]:
    return {
        "chunk_id": chunk.chunk_id,
        "source_id": chunk.source_id,
        "source_type": chunk.source_type.value,
        "title": chunk.title,
        "source_version": chunk.source_version,
        "trust_level": chunk.trust_level.value,
        "clinical_domain": chunk.clinical_domain,
        "standard_system": chunk.standard_system,
        "locator": chunk.locator,
        "metadata": chunk.metadata,
    }


def _empty_package(
    query: RetrievalQuery,
    *,
    warnings: list[str],
    strategy: str,
) -> RetrievalPackage:
    query_analysis = analyze_query(query)
    safety_flags = retrieval_safety_flags(query)
    return RetrievalPackage(
        hits=[],
        evidence=[],
        coverage=RetrievalCoverage(),
        facets=RetrievalFacets(),
        trace=RetrievalTrace(
            strategy=strategy,
            query_variants=query_analysis.query_variants,
            filters_applied=query.filters,
            candidates_seen=0,
            final_hit_ids=[],
            safety_flags=safety_flags,
            warnings=warnings,
        ),
        handoff_context={
            "retrieval_contract": "retrieval_package.v0",
            "framework": "llamaindex",
            "query_analysis": query_analysis.model_dump(),
        },
    )


def _optional_metadata(value: Any) -> str | None:
    return str(value) if value is not None and str(value).strip() else None


def _checked_scope(*, include_seeded: bool, include_corpus: bool) -> str:
    scopes = []
    if include_seeded:
        scopes.append("seeded")
    if include_corpus:
        scopes.append("corpus")
    return "+".join(scopes) or "none"


def _llamaindex_dependency_error() -> DependencyUnavailableError:
    return DependencyUnavailableError(
        "OJT_RETRIEVAL_FRAMEWORK=llamaindex requires: pip install -e '.[rag-framework]'"
    )
