"""Persistent Graph-NER context contracts."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel, NonBlankStr


GraphExportFormat = Literal["jsonl", "rdf_jsonl"]


class GraphContextRecord(ContractModel):
    """One persisted Graph-NER handoff context produced by retrieval."""

    graph_id: NonBlankStr
    owner_user_id: NonBlankStr | None = None
    workflow_id: NonBlankStr | None = None
    request_id: NonBlankStr | None = None
    search_signature: NonBlankStr | None = None
    query: NonBlankStr
    resource_type: NonBlankStr | None = None
    fields: list[NonBlankStr] = Field(default_factory=list)
    node_count: int = Field(ge=0)
    edge_count: int = Field(ge=0)
    triple_count: int = Field(ge=0)
    graph_context: dict[str, Any] = Field(default_factory=dict)
    created_at: NonBlankStr


class GraphExport(ContractModel):
    """JSONL export for persisted graph contexts."""

    format: GraphExportFormat
    content_type: NonBlankStr
    graph_count: int = Field(ge=0)
    node_count: int = Field(ge=0)
    edge_count: int = Field(ge=0)
    triple_count: int = Field(ge=0)
    generated_at: NonBlankStr
    content: str


class GraphNeighborhoodQuery(ContractModel):
    """Owner-scoped graph neighborhood lookup criteria."""

    workflow_id: NonBlankStr | None = None
    q: NonBlankStr | None = None
    node_id: NonBlankStr | None = None
    evidence_id: NonBlankStr | None = None
    source_id: NonBlankStr | None = None
    normalized_code: NonBlankStr | None = None
    resource_type: NonBlankStr | None = None
    field: NonBlankStr | None = None
    relation: NonBlankStr | None = None
    limit: int = Field(default=100, ge=1, le=1000)
    max_depth: int = Field(default=1, ge=0, le=2)


class GraphNeighborhood(ContractModel):
    """Bounded subgraph expanded from persisted Graph-NER contexts."""

    query: GraphNeighborhoodQuery
    source_graph_ids: list[NonBlankStr] = Field(default_factory=list)
    graph_count: int = Field(ge=0)
    node_count: int = Field(ge=0)
    edge_count: int = Field(ge=0)
    triple_count: int = Field(ge=0)
    matched_node_ids: list[NonBlankStr] = Field(default_factory=list)
    matched_evidence_ids: list[NonBlankStr] = Field(default_factory=list)
    nodes: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[dict[str, Any]] = Field(default_factory=list)
    triples: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[NonBlankStr] = Field(default_factory=list)
    generated_at: NonBlankStr
