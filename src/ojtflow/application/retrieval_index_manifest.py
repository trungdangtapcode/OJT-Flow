"""Application helpers for retrieval index manifests."""

from __future__ import annotations

import json
from collections.abc import Sequence
from hashlib import sha256

from ojtflow.core.contracts.graph import GraphContextRecord
from ojtflow.core.contracts.retrieval import (
    RetrievalIndexComponent,
    RetrievalIndexManifest,
    RetrievalIndexManifestSummary,
)


def attach_graph_index_metadata(
    manifest: RetrievalIndexManifest,
    graph_records: Sequence[GraphContextRecord],
) -> RetrievalIndexManifest:
    """Attach owner-scoped persisted Graph-NER index metadata to a manifest."""

    records = list(graph_records)
    graph_generation_id = _graph_generation_id(records) if records else None
    graph_component = RetrievalIndexComponent(
        component_id="graph",
        status="ready" if records else "empty",
        generation_id=graph_generation_id,
        graph_count=len(records),
        node_count=sum(record.node_count for record in records),
        edge_count=sum(record.edge_count for record in records),
        triple_count=sum(record.triple_count for record in records),
        metadata={
            "generation_basis": "graph_ids_search_signatures_counts",
            "owner_scoped": True,
        },
    )
    components = [
        graph_component if component.component_id == "graph" else component
        for component in manifest.components
    ]
    return manifest.model_copy(
        update={
            "graph_generation_id": graph_generation_id,
            "components": components,
            "summary": _summary(components),
        }
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


def _graph_generation_id(records: Sequence[GraphContextRecord]) -> str:
    payload = [
        {
            "graph_id": record.graph_id,
            "search_signature": record.search_signature,
            "node_count": record.node_count,
            "edge_count": record.edge_count,
            "triple_count": record.triple_count,
            "created_at": record.created_at,
        }
        for record in sorted(records, key=lambda item: item.graph_id)
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"graphidx:{sha256(encoded.encode('utf-8')).hexdigest()[:16]}"
