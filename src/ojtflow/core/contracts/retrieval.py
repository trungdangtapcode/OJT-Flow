"""Retrieval contracts for evidence-grounded workflow context."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.contracts.enums import EvidenceSourceType, TrustLevel
from ojtflow.core.contracts.evidence import Evidence


class RetrievalQuery(ContractModel):
    """Normalized retrieval request used by workflow and direct API paths."""

    query: str = Field(min_length=1)
    workflow_id: str | None = None
    fields: list[str] = Field(default_factory=list)
    schema_id: str | None = None
    detected_format: str | None = None
    resource_type: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    filters: dict[str, Any] = Field(default_factory=dict)


class RetrievalHit(ContractModel):
    """One ranked retrieval candidate with transparent scoring components."""

    evidence: Evidence
    score: float
    lexical_score: float = 0.0
    vector_score: float = 0.0
    rerank_score: float = 0.0
    matched_terms: list[str] = Field(default_factory=list)
    source_locator: dict[str, Any] = Field(default_factory=dict)


class RetrievalTrace(ContractModel):
    """Debuggable trace for retrieval strategy and candidate selection."""

    strategy: str
    query_variants: list[str] = Field(default_factory=list)
    filters_applied: dict[str, Any] = Field(default_factory=dict)
    candidates_seen: int = 0
    final_hit_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class RetrievalPackage(ContractModel):
    """Evidence package returned to workflow state and API callers."""

    hits: list[RetrievalHit] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    trace: RetrievalTrace
    handoff_context: dict[str, Any] = Field(default_factory=dict)


class RetrievalSource(ContractModel):
    """Inventory entry for available trusted retrieval sources."""

    source_id: str
    source_type: EvidenceSourceType
    title: str
    source_version: str | None = None
    trust_level: TrustLevel = TrustLevel.APPROVED
    clinical_domain: str | None = None
    standard_system: str | None = None
    chunk_count: int = 0
