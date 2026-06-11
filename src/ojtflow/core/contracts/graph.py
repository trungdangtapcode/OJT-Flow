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
