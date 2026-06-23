"""In-memory persistent knowledge-graph repository (tests / demos, no ``kuzu`` dep).

Implements :class:`ojtflow.application.ports.KnowledgeGraphRepository`. Storage keys
encode scope (``(scope, organization_id, node_id)``) so global and org concepts never
collide (§4). Reads return ``global ∪ caller org``; within a scope a bare ``node_id``
resolves to the most specific visible concept (org preferred over global).
"""

from __future__ import annotations

from copy import deepcopy

from ojtflow.core.contracts.knowledge_graph import (
    KnowledgeGraphChunk,
    KnowledgeGraphEdge,
    KnowledgeGraphMention,
    KnowledgeGraphNode,
    KnowledgeGraphStats,
    KnowledgeGraphView,
)
from ojtflow.core.time import utc_now

ConceptKey = tuple[str, str, str]  # (scope, organization_id, node_id)
EdgeKey = tuple[str, str, str]  # (source_node_id, target_node_id, relation)


def _merge_unique(existing: list[str], incoming: list[str]) -> list[str]:
    seen = list(existing)
    for value in incoming:
        if value and value not in seen:
            seen.append(value)
    return seen


class InMemoryKnowledgeGraphRepository:
    """Dict/adjacency knowledge graph; same shape as the other in-memory repos."""

    def __init__(self) -> None:
        self._concepts: dict[ConceptKey, KnowledgeGraphNode] = {}
        self._edges: dict[EdgeKey, KnowledgeGraphEdge] = {}
        self._chunks: dict[str, KnowledgeGraphChunk] = {}

    def bootstrap(self) -> None:  # no schema to create in memory
        return None

    # -- writes ------------------------------------------------------------------
    def upsert_concepts(self, concepts: list[KnowledgeGraphNode]) -> None:
        for concept in concepts:
            key: ConceptKey = (concept.scope, concept.organization_id, concept.node_id)
            existing = self._concepts.get(key)
            if existing is None:
                self._concepts[key] = deepcopy(concept)
                continue
            existing.label = concept.label
            existing.node_type = concept.node_type
            existing.confidence = concept.confidence
            existing.review_state = concept.review_state
            existing.aliases = _merge_unique(existing.aliases, concept.aliases)
            existing.source_chunk_ids = _merge_unique(
                existing.source_chunk_ids, concept.source_chunk_ids
            )
            if concept.normalized_code:
                existing.normalized_code = concept.normalized_code
            if concept.code_system:
                existing.code_system = concept.code_system
            existing.attributes = {**existing.attributes, **concept.attributes}
            existing.updated_at = concept.updated_at or utc_now().isoformat()

    def upsert_relations(
        self,
        relations: list[KnowledgeGraphEdge],
        *,
        source_chunk_id: str | None = None,
    ) -> None:
        for relation in relations:
            key: EdgeKey = (
                relation.source_node_id,
                relation.target_node_id,
                relation.relation,
            )
            chunk_ids = list(relation.source_chunk_ids)
            if source_chunk_id:
                chunk_ids.append(source_chunk_id)
            existing = self._edges.get(key)
            if existing is None:
                stored = deepcopy(relation)
                stored.source_chunk_ids = _merge_unique([], chunk_ids)
                stored.source_snippets = []
                self._edges[key] = stored
                continue
            existing.confidence = relation.confidence
            existing.review_state = relation.review_state
            existing.source_chunk_ids = _merge_unique(existing.source_chunk_ids, chunk_ids)

    def append_provenance(
        self,
        chunk: KnowledgeGraphChunk,
        mentions: list[KnowledgeGraphMention],
    ) -> None:
        self._chunks[chunk.chunk_id] = deepcopy(chunk)
        for mention in mentions:
            node = self._resolve_for_scope(
                mention.node_id, chunk.scope, chunk.organization_id
            )
            if node is not None:
                node.source_chunk_ids = _merge_unique(
                    node.source_chunk_ids, [chunk.chunk_id]
                )

    # -- reads -------------------------------------------------------------------
    def get_concept(
        self,
        *,
        node_id: str,
        organization_id: str | None,
    ) -> KnowledgeGraphNode | None:
        node = self._visible(organization_id).get(node_id)
        return deepcopy(node) if node is not None else None

    def neighborhood(
        self,
        *,
        seeds: list[str],
        depth: int = 1,
        limit: int = 100,
        organization_id: str | None,
    ) -> KnowledgeGraphView:
        depth = max(0, min(depth, 2))
        limit = max(1, min(limit, 1000))
        visible = self._visible(organization_id)

        frontier = {node_id for node_id in seeds if node_id in visible}
        collected: dict[str, KnowledgeGraphNode] = {
            node_id: visible[node_id] for node_id in frontier
        }
        edges: dict[EdgeKey, KnowledgeGraphEdge] = {}

        for _ in range(depth):
            layer = set(frontier)  # snapshot: expand exactly one hop per depth step
            next_frontier: set[str] = set()
            for key, edge in self._edges.items():
                src, tgt, _relation = key
                if src not in visible or tgt not in visible:
                    continue
                if src not in layer and tgt not in layer:
                    continue
                edges.setdefault(key, edge)
                for endpoint in (src, tgt):
                    if endpoint not in collected:
                        collected[endpoint] = visible[endpoint]
                        next_frontier.add(endpoint)
            if not next_frontier:
                break
            frontier = next_frontier

        nodes = [deepcopy(node) for node in list(collected.values())[:limit]]
        node_ids = {node.node_id for node in nodes}
        out_edges: list[KnowledgeGraphEdge] = []
        for (src, tgt, _relation), edge in edges.items():
            if src in node_ids and tgt in node_ids:
                resolved = deepcopy(edge)
                resolved.source_snippets = [
                    self._chunks[chunk_id].snippet
                    for chunk_id in resolved.source_chunk_ids
                    if chunk_id in self._chunks and self._chunks[chunk_id].snippet
                ]
                out_edges.append(resolved)

        return KnowledgeGraphView(
            nodes=nodes,
            edges=out_edges,
            seed_node_ids=[node_id for node_id in seeds if node_id in visible],
            node_count=len(nodes),
            edge_count=len(out_edges),
            depth=depth,
            generated_at=utc_now().isoformat(),
        )

    def search_concepts(
        self,
        *,
        q: str,
        organization_id: str | None,
        limit: int = 50,
    ) -> list[KnowledgeGraphNode]:
        needle = q.strip().lower()
        limit = max(1, min(limit, 1000))
        matches: list[KnowledgeGraphNode] = []
        for node in self._visible(organization_id).values():
            haystack = [node.label.lower(), *(alias.lower() for alias in node.aliases)]
            if node.normalized_code:
                haystack.append(node.normalized_code.lower())
            if not needle or any(needle in value for value in haystack):
                matches.append(deepcopy(node))
        matches.sort(key=lambda node: node.label.lower())
        return matches[:limit]

    def stats(self, *, organization_id: str | None) -> KnowledgeGraphStats:
        visible = self._visible(organization_id)
        nodes_by_type: dict[str, int] = {}
        nodes_by_scope: dict[str, int] = {}
        for node in visible.values():
            nodes_by_type[node.node_type] = nodes_by_type.get(node.node_type, 0) + 1
            nodes_by_scope[node.scope] = nodes_by_scope.get(node.scope, 0) + 1
        edge_count = sum(
            1
            for (src, tgt, _relation) in self._edges
            if src in visible and tgt in visible
        )
        chunk_count = sum(
            1
            for chunk in self._chunks.values()
            if chunk.scope == "global"
            or (organization_id is not None and chunk.organization_id == organization_id)
        )
        return KnowledgeGraphStats(
            node_count=len(visible),
            edge_count=edge_count,
            chunk_count=chunk_count,
            nodes_by_type=nodes_by_type,
            nodes_by_scope=nodes_by_scope,
            generated_at=utc_now().isoformat(),
        )

    # -- scope helpers -----------------------------------------------------------
    def _visible(self, organization_id: str | None) -> dict[str, KnowledgeGraphNode]:
        """Map node_id -> visible concept, preferring org-scoped over global."""
        globals_: dict[str, KnowledgeGraphNode] = {}
        orgs: dict[str, KnowledgeGraphNode] = {}
        for (scope, org, node_id), node in self._concepts.items():
            if scope == "global":
                globals_[node_id] = node
            elif organization_id is not None and org == organization_id:
                orgs[node_id] = node
        return {**globals_, **orgs}

    def _resolve_for_scope(
        self,
        node_id: str,
        scope: str,
        organization_id: str,
    ) -> KnowledgeGraphNode | None:
        node = self._concepts.get((scope, organization_id, node_id))
        if node is not None:
            return node
        return self._concepts.get(("global", "", node_id))
