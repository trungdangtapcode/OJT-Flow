"""Persistent corpus knowledge-graph contracts.

A canonical, deduplicated, provenance-backed graph that accumulates across the whole
corpus (seeded ``global`` knowledge and ``organization``-scoped user imports). Distinct
from :mod:`ojtflow.core.contracts.graph`, which models the per-query, ephemeral Graph-NER
handoff. See ``docs/corpus_knowledge_graph_v0.md``.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel, NonBlankStr


GraphScope = Literal["global", "organization"]
"""``global`` = seeded/shared knowledge; ``organization`` = workspace-private import."""

GraphReviewState = Literal["accepted", "pending", "rejected"]
"""Review gate state; meaning-changing merges/normalizations enter as ``pending``."""


class KnowledgeGraphChunk(ContractModel):
    """Provenance node: the source passage a concept/relation was extracted from."""

    chunk_id: NonBlankStr
    scope: GraphScope
    organization_id: str = ""
    document_id: NonBlankStr | None = None
    source_id: NonBlankStr | None = None
    snippet: str = ""
    created_at: NonBlankStr


class KnowledgeGraphMention(ContractModel):
    """Citation edge ``(:Chunk)-[:MENTIONS]->(:Concept)`` — node-level provenance."""

    chunk_id: NonBlankStr
    node_id: NonBlankStr
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class KnowledgeGraphNode(ContractModel):
    """A canonical concept/entity node, deduplicated by ``node_id`` within a scope."""

    node_id: NonBlankStr
    scope: GraphScope
    organization_id: str = ""
    node_type: NonBlankStr
    label: NonBlankStr
    normalized_code: str | None = None
    code_system: str | None = None
    aliases: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    review_state: GraphReviewState = "accepted"
    created_at: NonBlankStr
    updated_at: NonBlankStr
    # Resolved node-level provenance (chunks that MENTION this concept).
    source_chunk_ids: list[str] = Field(default_factory=list)


class KnowledgeGraphEdge(ContractModel):
    """A typed concept->concept relation; ``source_chunk_ids`` is its provenance.

    Mirrors the node ``MENTIONS`` pattern: a single relation can be asserted by many
    chunks, so provenance is a list. ``source_snippets`` is the UI-resolved text of those
    chunks (the exact sentence that asserted the link), populated on read.
    """

    source_node_id: NonBlankStr
    target_node_id: NonBlankStr
    relation: NonBlankStr
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    review_state: GraphReviewState = "accepted"
    created_at: NonBlankStr
    source_chunk_ids: list[str] = Field(default_factory=list)
    source_snippets: list[str] = Field(default_factory=list)


class KnowledgeGraphStats(ContractModel):
    """Counts for the scope the caller can read (global ∪ caller org)."""

    node_count: int = Field(ge=0)
    edge_count: int = Field(ge=0)
    chunk_count: int = Field(ge=0)
    nodes_by_type: dict[str, int] = Field(default_factory=dict)
    nodes_by_scope: dict[str, int] = Field(default_factory=dict)
    generated_at: NonBlankStr


class GraphMedStatus(ContractModel):
    """Runtime readiness of the graph-med ontology + annotation service path."""

    enabled: bool
    available: bool
    ontology_loaded: bool
    gpu_required: bool = False
    gpu_available: bool = False
    gnn_endpoint_configured: bool = False
    gnn_endpoint_reachable: bool = False
    embedding_endpoint_configured: bool
    llm_endpoint_configured: bool
    embedding_endpoint_reachable: bool = False
    llm_endpoint_reachable: bool = False
    icd_vector_index: NonBlankStr
    icd_disease_count: int = Field(ge=0)
    hpo_phenotype_count: int = Field(ge=0)
    umls_count: int = Field(ge=0)
    message: str


class GraphMedPatientEntity(ContractModel):
    """graph-med patient NER entity shape."""

    source: Literal["concat", "narrative"]
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    text: NonBlankStr
    label: NonBlankStr
    assertion: Literal["present", "negated", "uncertain"]
    temporality: Literal["acute", "chronic", "recurrent", "history", "unspecified"]
    rationale: NonBlankStr


class GraphMedLinkedEntity(GraphMedPatientEntity):
    """graph-med NED entity linked to an ICD code, or explicit abstention."""

    icd_id: str | None = None
    icd_label: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    linking_rationale: NonBlankStr


class GraphMedAnnotationRequest(ContractModel):
    """Internal graph-med service annotation request."""

    patient_id: NonBlankStr
    encounter_id: NonBlankStr
    concat_text: str = ""
    narrative_text: str = ""


class KnowledgeGraphImportResult(ContractModel):
    """Result of a graph-med-backed import into the workspace graph."""

    backend: Literal["graph-med"]
    status: Literal["imported", "unavailable"]
    chunks: int = Field(ge=0)
    nodes: int = Field(ge=0)
    edges: int = Field(ge=0)
    entities: int = Field(ge=0)
    linked_entities: int = Field(ge=0)
    message: str
    graph_med_status: GraphMedStatus
    annotations: list[GraphMedLinkedEntity] = Field(default_factory=list)


class KnowledgeGraphView(ContractModel):
    """Bounded subgraph for the UI: nodes + provenance-backed edges + counts."""

    nodes: list[KnowledgeGraphNode] = Field(default_factory=list)
    edges: list[KnowledgeGraphEdge] = Field(default_factory=list)
    seed_node_ids: list[NonBlankStr] = Field(default_factory=list)
    node_count: int = Field(ge=0)
    edge_count: int = Field(ge=0)
    depth: int = Field(ge=0, le=2)
    generated_at: NonBlankStr


class KnowledgeGraphImportRequest(ContractModel):
    """Caller-scoped request to fold text/a document into the workspace subgraph."""

    text: str | None = None
    document_id: NonBlankStr | None = None
    source_id: NonBlankStr | None = None
    patient_id: NonBlankStr | None = None
    encounter_id: NonBlankStr | None = None
    concat_text: str | None = None
    narrative_text: str | None = None
