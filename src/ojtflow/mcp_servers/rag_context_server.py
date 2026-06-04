"""MCP server: RAG context and knowledge retrieval tools.

Wraps ojtflow's StaticRetrievalRepository so an AI agent can search
the trusted healthcare knowledge base through MCP before generating
explanations or validating data.

Run locally:
    python -m ojtflow.mcp_servers.rag_context_server
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from ojtflow.core.contracts.retrieval import RetrievalQuery
from ojtflow.infrastructure.retrieval.static import StaticRetrievalRepository

mcp = FastMCP(
    "ojtflow-rag-context",
    instructions=(
        "Tools for retrieving trusted healthcare knowledge before generating explanations. "
        "Always search for relevant context before making clinical claims. "
        "Only cite source_ids returned by these tools — never invent citations. "
        "HyDE hint: you can pass a hypothetical answer as the query to improve retrieval."
    ),
)

_KNOWLEDGE_ROOT = Path(__file__).resolve().parents[4] / "knowledge"


def _repo() -> StaticRetrievalRepository:
    return StaticRetrievalRepository(_KNOWLEDGE_ROOT)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def search_knowledge(
    query: str,
    top_k: int = 5,
    trust_level: str | None = None,
    clinical_domain: str | None = None,
    standard_system: str | None = None,
) -> dict[str, Any]:
    """Search the trusted healthcare knowledge base for relevant context.

    Use this before generating any clinical explanation or validation summary.
    Pass a natural language query describing what you need evidence for.

    Args:
        query: Natural language search query (e.g. 'HbA1c normal range LOINC').
        top_k: Maximum number of results to return (default 5, max 20).
        trust_level: Optional filter — 'authoritative', 'informational', or 'experimental'.
        clinical_domain: Optional filter — e.g. 'laboratory', 'medications', 'vitals'.
        standard_system: Optional filter — e.g. 'LOINC', 'SNOMED', 'FHIR', 'OMOP'.

    Returns:
        evidence: List of retrieved evidence chunks with source IDs and scores.
        retrieval_mode: Strategy used (hybrid BM25 + vector).
        warnings: Any retrieval warnings (e.g. no chunks matched filters).
        source_ids: List of source IDs to cite in explanations.
    """
    top_k = min(top_k, 20)
    filters: dict[str, str] = {}
    if trust_level:
        filters["trust_level"] = trust_level
    if clinical_domain:
        filters["clinical_domain"] = clinical_domain
    if standard_system:
        filters["standard_system"] = standard_system

    rq = RetrievalQuery(query=query, top_k=top_k, filters=filters)
    package = _repo().search(rq)

    evidence_out = [
        {
            "source_id": ev.source_id,
            "content": ev.content,
            "trust_level": ev.trust_level.value if ev.trust_level else None,
            "relevance_score": ev.relevance_score,
            "standard_system": ev.standard_system,
            "clinical_domain": ev.clinical_domain,
            "metadata": ev.metadata,
        }
        for ev in package.evidence
    ]

    return {
        "evidence": evidence_out,
        "retrieval_mode": package.retrieval_mode,
        "warnings": package.warnings,
        "source_ids": [ev.source_id for ev in package.evidence],
        "result_count": len(evidence_out),
    }


@mcp.tool()
def list_knowledge_sources() -> dict[str, Any]:
    """List all knowledge sources available in the retrieval index.

    Returns:
        sources: List of available sources with IDs, domains, and trust levels.
        count: Total number of source chunks indexed.
    """
    sources = _repo().list_sources()
    sources_out = [
        {
            "source_id": s.source_id,
            "title": s.title,
            "trust_level": s.trust_level.value if s.trust_level else None,
            "clinical_domain": s.clinical_domain,
            "standard_system": s.standard_system,
            "chunk_count": s.chunk_count,
        }
        for s in sources
    ]
    return {"sources": sources_out, "count": len(sources_out)}


@mcp.tool()
def get_retrieval_confidence_package(query: str) -> dict[str, Any]:
    """Run a search and return confidence metadata alongside results.

    Useful when the AI needs to decide whether evidence is strong enough
    to support a clinical claim, or whether to abstain.

    Args:
        query: Search query string.

    Returns:
        has_evidence: Whether any evidence was found.
        top_score: Highest relevance score found.
        confidence_level: 'high' (>0.7), 'medium' (0.4-0.7), 'low' (<0.4), or 'none'.
        recommendation: Whether to cite, warn, or abstain.
        evidence: Top 3 evidence chunks.
    """
    rq = RetrievalQuery(query=query, top_k=3)
    package = _repo().search(rq)

    top_score = max((ev.relevance_score for ev in package.evidence), default=0.0)
    if top_score > 0.7:
        confidence_level = "high"
        recommendation = "cite retrieved sources in explanation"
    elif top_score > 0.4:
        confidence_level = "medium"
        recommendation = "cite with caveat — evidence is partial"
    elif package.evidence:
        confidence_level = "low"
        recommendation = "warn user that evidence is weak — consider clinician review"
    else:
        confidence_level = "none"
        recommendation = "abstain from clinical claim — no evidence found"

    evidence_out = [
        {
            "source_id": ev.source_id,
            "content": ev.content,
            "relevance_score": ev.relevance_score,
        }
        for ev in package.evidence
    ]

    return {
        "has_evidence": bool(package.evidence),
        "top_score": top_score,
        "confidence_level": confidence_level,
        "recommendation": recommendation,
        "evidence": evidence_out,
        "warnings": package.warnings,
    }


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


@mcp.resource("ojtflow://knowledge/sources")
def knowledge_sources_resource() -> str:
    """JSON list of all knowledge sources in the retrieval index."""
    sources = _repo().list_sources()
    return json.dumps(
        [
            {
                "source_id": s.source_id,
                "title": s.title,
                "trust_level": s.trust_level.value if s.trust_level else None,
                "clinical_domain": s.clinical_domain,
            }
            for s in sources
        ],
        indent=2,
    )


@mcp.resource("ojtflow://knowledge/retrieval-guide")
def retrieval_guide() -> str:
    """Guidelines for using OJTFlow's RAG retrieval tools responsibly."""
    guide = {
        "principle": "Only cite source_ids returned by search_knowledge. Never invent citations.",
        "abstention_rule": "If confidence_level is 'none' or 'low', do not make clinical claims.",
        "hyde_tip": "Pass a hypothetical answer as the query to improve recall for vague questions.",
        "filters": {
            "trust_level": ["authoritative", "informational", "experimental"],
            "clinical_domain": ["laboratory", "medications", "vitals", "diagnoses"],
            "standard_system": ["LOINC", "SNOMED", "FHIR", "OMOP", "RxNorm"],
        },
        "max_top_k": 20,
    }
    return json.dumps(guide, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
