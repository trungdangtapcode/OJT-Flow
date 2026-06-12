"""Retrieval index manifest builders."""

from __future__ import annotations

import json
from collections.abc import Sequence
from hashlib import sha256
from pathlib import Path
from typing import Any

from ojtflow.core.contracts.retrieval import (
    RetrievalIndexComponent,
    RetrievalIndexManifest,
    RetrievalIndexManifestSummary,
)
from ojtflow.core.time import utc_now
from ojtflow.infrastructure.retrieval.engine import KnowledgeChunk


def build_retrieval_index_manifest(
    *,
    repository: str,
    retrieval_framework: str,
    knowledge_root: Path,
    chunks: Sequence[KnowledgeChunk],
    embedding_metadata: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    warnings: Sequence[str] = (),
) -> RetrievalIndexManifest:
    """Build an operational manifest for active retrieval indexes."""

    chunk_list = list(chunks)
    source_count = len({chunk.source_id for chunk in chunk_list})
    lexical_generation_id = _lexical_generation_id(chunk_list)
    embedding_generation_id = _embedding_generation_id(embedding_metadata)
    stale_chunk_count = sum(
        1
        for chunk in chunk_list
        if _stored_embedding_generation_id(chunk)
        and _stored_embedding_generation_id(chunk) != embedding_generation_id
    )
    corpus_run_ids = sorted(
        {
            run_id
            for chunk in chunk_list
            if (run_id := _optional_str(chunk.metadata.get("ingestion_run_id")))
        }
    )
    components = [
        RetrievalIndexComponent(
            component_id="lexical",
            status="ready" if chunk_list else "empty",
            generation_id=lexical_generation_id if chunk_list else None,
            chunk_count=len(chunk_list),
            source_count=source_count,
            metadata={
                "index_family": "metadata_plus_full_text",
                "generation_basis": "chunk_ids_source_versions_content_hashes",
            },
        ),
        RetrievalIndexComponent(
            component_id="vector",
            status=_vector_status(chunk_list, stale_chunk_count),
            generation_id=embedding_generation_id if chunk_list else None,
            expected_generation_id=embedding_generation_id,
            provider=_optional_str(embedding_metadata.get("provider")),
            model=_optional_str(embedding_metadata.get("model")),
            dimensions=_optional_int(embedding_metadata.get("dimensions")),
            chunk_count=len(chunk_list),
            source_count=source_count,
            stale_chunk_count=stale_chunk_count,
            warnings=(
                [
                    "Some chunks were embedded with a different provider/model/dimension generation."
                ]
                if stale_chunk_count
                else []
            ),
            metadata={
                "normalized": bool(embedding_metadata.get("normalized")),
                "stored_generation_present_count": sum(
                    1 for chunk in chunk_list if _stored_embedding_generation_id(chunk)
                ),
            },
        ),
        RetrievalIndexComponent(
            component_id="graph",
            status="not_available",
            warnings=["Graph index metadata must be attached by the workflow graph service."],
        ),
    ]
    return RetrievalIndexManifest(
        version="retrieval_index_manifest.v1",
        generated_at=utc_now().isoformat(),
        repository=repository,
        retrieval_framework=retrieval_framework,
        knowledge_root=_display_path(knowledge_root),
        corpus_ingestion_run_ids=corpus_run_ids,
        embedding_generation_id=embedding_generation_id,
        lexical_generation_id=lexical_generation_id if chunk_list else None,
        summary=_summary(components),
        components=components,
        warnings=list(warnings),
        metadata=metadata or {},
    )


def _summary(
    components: Sequence[RetrievalIndexComponent],
) -> RetrievalIndexManifestSummary:
    component_list = list(components)
    lexical = next(
        (component for component in component_list if component.component_id == "lexical"),
        None,
    )
    graph = next(
        (component for component in component_list if component.component_id == "graph"),
        None,
    )
    return RetrievalIndexManifestSummary(
        component_count=len(component_list),
        ready_component_count=sum(1 for item in component_list if item.status == "ready"),
        stale_component_count=sum(1 for item in component_list if item.status == "stale"),
        unavailable_component_count=sum(
            1 for item in component_list if item.status == "not_available"
        ),
        chunk_count=lexical.chunk_count if lexical else 0,
        source_count=lexical.source_count if lexical else 0,
        stale_chunk_count=sum(item.stale_chunk_count for item in component_list),
        graph_count=graph.graph_count if graph else 0,
        node_count=graph.node_count if graph else 0,
        edge_count=graph.edge_count if graph else 0,
        triple_count=graph.triple_count if graph else 0,
    )


def _vector_status(chunks: Sequence[KnowledgeChunk], stale_chunk_count: int) -> str:
    if not chunks:
        return "empty"
    if stale_chunk_count:
        return "stale"
    return "ready"


def _lexical_generation_id(chunks: Sequence[KnowledgeChunk]) -> str:
    payload = [
        {
            "chunk_id": chunk.chunk_id,
            "source_id": chunk.source_id,
            "source_version": chunk.source_version,
            "content_hash": (
                chunk.metadata.get("chunk_content_hash")
                or chunk.metadata.get("content_hash")
                or sha256(chunk.content.encode("utf-8")).hexdigest()
            ),
        }
        for chunk in sorted(chunks, key=lambda item: item.chunk_id)
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"lexidx:{sha256(encoded.encode('utf-8')).hexdigest()[:16]}"


def _embedding_generation_id(embedding_metadata: dict[str, Any]) -> str:
    payload = {
        "provider": embedding_metadata.get("provider"),
        "model": embedding_metadata.get("model"),
        "dimensions": embedding_metadata.get("dimensions"),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"embgen:{sha256(encoded.encode('utf-8')).hexdigest()[:16]}"


def _stored_embedding_generation_id(chunk: KnowledgeChunk) -> str | None:
    return _optional_str(chunk.metadata.get("embedding_generation_id"))


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: object) -> int | None:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return max(parsed, 0)


def _display_path(path: Path) -> str:
    return str(path)
