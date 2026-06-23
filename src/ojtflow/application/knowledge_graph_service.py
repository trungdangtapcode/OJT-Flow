"""Read/query orchestration over the persistent knowledge graph.

Thin application service in front of the ``KnowledgeGraphRepository`` port. Callers pass the
caller's ``organization_id`` (``None`` → global only); the service never reaches into
infrastructure beyond the port, so API/frontend stay engine-agnostic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ojtflow.core.contracts.knowledge_graph import (
    KnowledgeGraphNode,
    KnowledgeGraphStats,
    KnowledgeGraphView,
)

if TYPE_CHECKING:
    from ojtflow.application.ports import KnowledgeGraphRepository


class KnowledgeGraphService:
    """Workspace-scoped queries over the corpus knowledge graph."""

    def __init__(self, repository: KnowledgeGraphRepository) -> None:
        self._repo = repository

    def search(
        self,
        *,
        q: str,
        organization_id: str | None,
        limit: int = 50,
    ) -> list[KnowledgeGraphNode]:
        return self._repo.search_concepts(q=q, organization_id=organization_id, limit=limit)

    def get_node(
        self,
        *,
        node_id: str,
        organization_id: str | None,
    ) -> KnowledgeGraphNode | None:
        return self._repo.get_concept(node_id=node_id, organization_id=organization_id)

    def neighborhood(
        self,
        *,
        node_id: str | None = None,
        q: str | None = None,
        depth: int = 1,
        limit: int = 100,
        organization_id: str | None,
    ) -> KnowledgeGraphView:
        if node_id:
            seeds = [node_id]
        elif q:
            seeds = [
                node.node_id
                for node in self._repo.search_concepts(
                    q=q, organization_id=organization_id, limit=min(limit, 25)
                )
            ]
        else:
            seeds = []
        return self._repo.neighborhood(
            seeds=seeds,
            depth=depth,
            limit=limit,
            organization_id=organization_id,
        )

    def stats(self, *, organization_id: str | None) -> KnowledgeGraphStats:
        return self._repo.stats(organization_id=organization_id)
