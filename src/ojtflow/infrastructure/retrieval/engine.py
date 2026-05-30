"""Deterministic retrieval utilities shared by retrieval adapters."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any

from ojtflow.core.contracts.enums import EvidenceSourceType, TrustLevel
from ojtflow.core.contracts.evidence import Evidence
from ojtflow.core.contracts.retrieval import (
    RetrievalHit,
    RetrievalPackage,
    RetrievalQuery,
    RetrievalSource,
    RetrievalTrace,
)

TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9_./%-]*", re.IGNORECASE)
DEFAULT_EMBEDDING_DIMENSIONS = 64
RRF_K = 60


@dataclass(frozen=True)
class KnowledgeChunk:
    """One retrievable knowledge segment."""

    chunk_id: str
    source_id: str
    source_type: EvidenceSourceType
    title: str
    content: str
    source_version: str = "1.0.0"
    trust_level: TrustLevel = TrustLevel.APPROVED
    clinical_domain: str | None = None
    standard_system: str | None = None
    locator: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class DeterministicEmbeddingProvider:
    """Stable local embedding provider for tests, demos, and lexical fallback.

    This is not a semantic model. It gives the retrieval pipeline a deterministic
    vector signal so fusion, tracing, and provider boundaries can be tested
    without external credentials.
    """

    def __init__(self, dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in tokenize(text):
            digest = sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:2], "big") % self.dimensions
            weight = 1.0 + (digest[2] / 255.0)
            vector[index] += weight
        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            return vector
        return [value / magnitude for value in vector]


class NullEmbeddingProvider:
    """Embedding provider used when vector retrieval is disabled."""

    dimensions = DEFAULT_EMBEDDING_DIMENSIONS

    def embed(self, text: str) -> list[float]:
        return [0.0] * self.dimensions


def tokenize(text: str) -> list[str]:
    """Return normalized searchable tokens."""

    return [match.group(0).lower() for match in TOKEN_PATTERN.finditer(text)]


def build_query_variants(query: RetrievalQuery) -> list[str]:
    """Create deterministic query variants inspired by practical RAG routing."""

    variants = [query.query]
    if query.fields:
        variants.append(" ".join(query.fields))
        variants.append(f"healthcare fields {' '.join(query.fields)} validation units terminology")
    if query.schema_id:
        variants.append(f"{query.schema_id} schema required fields validation")
    if query.resource_type:
        variants.append(f"FHIR {query.resource_type} resource profile required shape")
    if query.detected_format:
        variants.append(f"{query.detected_format} parsing conversion data quality")

    deduped: list[str] = []
    seen: set[str] = set()
    for variant in variants:
        normalized = " ".join(variant.split())
        if normalized and normalized.lower() not in seen:
            seen.add(normalized.lower())
            deduped.append(normalized)
    return deduped


def rank_chunks(
    chunks: list[KnowledgeChunk],
    query: RetrievalQuery,
    *,
    embedding_provider: DeterministicEmbeddingProvider | NullEmbeddingProvider | None = None,
    strategy: str = "deterministic_hybrid",
    warnings: list[str] | None = None,
) -> RetrievalPackage:
    """Rank chunks using lexical overlap, deterministic vectors, and simple rerank boosts."""

    provider = embedding_provider or DeterministicEmbeddingProvider()
    variants = build_query_variants(query)
    query_text = " ".join(variants)
    query_tokens = set(tokenize(query_text))
    query_vector = provider.embed(query_text)

    lexical_ranked: list[tuple[KnowledgeChunk, float, list[str]]] = []
    vector_ranked: list[tuple[KnowledgeChunk, float]] = []
    for chunk in chunks:
        chunk_tokens = set(tokenize(f"{chunk.title} {chunk.content} {chunk.source_id}"))
        matched = sorted(query_tokens.intersection(chunk_tokens))
        lexical_score = _lexical_score(query_tokens, chunk_tokens, query.query, chunk)
        vector_score = cosine_similarity(
            query_vector,
            provider.embed(f"{chunk.title}\n{chunk.content}"),
        )
        lexical_ranked.append((chunk, lexical_score, matched))
        vector_ranked.append((chunk, vector_score))

    lexical_ranked.sort(key=lambda item: item[1], reverse=True)
    vector_ranked.sort(key=lambda item: item[1], reverse=True)
    lexical_positions = {
        chunk.chunk_id: rank
        for rank, (chunk, _, _) in enumerate(lexical_ranked, start=1)
    }
    vector_positions = {
        chunk.chunk_id: rank
        for rank, (chunk, _) in enumerate(vector_ranked, start=1)
    }
    lexical_scores = {chunk.chunk_id: score for chunk, score, _ in lexical_ranked}
    vector_scores = {chunk.chunk_id: score for chunk, score in vector_ranked}
    matched_terms = {chunk.chunk_id: matched for chunk, _, matched in lexical_ranked}

    hits: list[RetrievalHit] = []
    for chunk in chunks:
        lexical_rrf = 1.0 / (RRF_K + lexical_positions[chunk.chunk_id])
        vector_rrf = 1.0 / (RRF_K + vector_positions[chunk.chunk_id])
        rerank = _rerank_boost(chunk, query, matched_terms[chunk.chunk_id])
        score = lexical_rrf + vector_rrf + rerank
        evidence = evidence_from_chunk(chunk, confidence=min(0.99, 0.55 + score * 8))
        hits.append(
            RetrievalHit(
                evidence=evidence,
                score=round(score, 6),
                lexical_score=round(lexical_scores[chunk.chunk_id], 6),
                vector_score=round(vector_scores[chunk.chunk_id], 6),
                rerank_score=round(rerank, 6),
                matched_terms=matched_terms[chunk.chunk_id][:12],
                source_locator=chunk.locator,
            )
        )

    hits.sort(key=lambda hit: hit.score, reverse=True)
    top_hits = hits[: query.top_k]
    trace = RetrievalTrace(
        strategy=strategy,
        query_variants=variants,
        filters_applied=query.filters,
        candidates_seen=len(chunks),
        final_hit_ids=[hit.evidence.evidence_id for hit in top_hits],
        warnings=warnings or [],
    )
    return RetrievalPackage(
        hits=top_hits,
        evidence=[hit.evidence for hit in top_hits],
        trace=trace,
        handoff_context={
            "retrieval_contract": "retrieval_package.v0",
            "query_fields": query.fields,
            "schema_id": query.schema_id,
            "strategy": strategy,
        },
    )


def evidence_from_chunk(chunk: KnowledgeChunk, *, confidence: float) -> Evidence:
    """Convert an internal chunk to the public evidence contract."""

    locator = {
        **chunk.locator,
        "chunk_id": chunk.chunk_id,
        "title": chunk.title,
        "clinical_domain": chunk.clinical_domain,
        "standard_system": chunk.standard_system,
        "metadata": chunk.metadata,
    }
    return Evidence(
        source_type=chunk.source_type,
        source_id=chunk.source_id,
        source_version=chunk.source_version,
        claim=chunk.content,
        locator=locator,
        confidence=round(confidence, 4),
        trust_level=chunk.trust_level,
    )


def sources_from_chunks(chunks: list[KnowledgeChunk]) -> list[RetrievalSource]:
    """Build source inventory entries from chunks."""

    grouped: dict[str, list[KnowledgeChunk]] = {}
    for chunk in chunks:
        grouped.setdefault(chunk.source_id, []).append(chunk)
    sources: list[RetrievalSource] = []
    for source_id, source_chunks in sorted(grouped.items()):
        first = source_chunks[0]
        sources.append(
            RetrievalSource(
                source_id=source_id,
                source_type=first.source_type,
                title=first.title,
                source_version=first.source_version,
                trust_level=first.trust_level,
                clinical_domain=first.clinical_domain,
                standard_system=first.standard_system,
                chunk_count=len(source_chunks),
            )
        )
    return sources


def default_healthcare_chunks(knowledge_root: Path) -> list[KnowledgeChunk]:
    """Load project knowledge files and built-in healthcare standard scaffolds."""

    chunks = [
        KnowledgeChunk(
            chunk_id="chunk_schema_lab_result_required_fields_v1",
            source_id="schema:lab_result_v1",
            source_type=EvidenceSourceType.SCHEMA,
            title="Synthetic Lab Result Schema",
            content=(
                "Lab result records require date, patient_id, lab_name, value, and unit "
                "fields. Date should use ISO YYYY-MM-DD. Patient identifiers are "
                "sensitive in healthcare workflows."
            ),
            clinical_domain="laboratory",
            standard_system="ojtflow_schema",
            locator={"path": "knowledge/schemas/lab_result_v1.schema.json"},
        ),
        KnowledgeChunk(
            chunk_id="chunk_standard_fhir_observation_v0",
            source_id="standard:fhir_observation_r4",
            source_type=EvidenceSourceType.HEALTHCARE_STANDARD,
            title="FHIR Observation R4",
            source_version="R4",
            content=(
                "FHIR Observation represents measurements and assertions such as "
                "laboratory results. A FHIR-like Observation profile should preserve "
                "resourceType, status, code, subject, effective date, value, unit, and "
                "source evidence."
            ),
            clinical_domain="laboratory",
            standard_system="FHIR",
            locator={"standard": "HL7 FHIR R4 Observation"},
        ),
        KnowledgeChunk(
            chunk_id="chunk_terminology_loinc_lab_codes_v0",
            source_id="terminology:loinc",
            source_type=EvidenceSourceType.TERMINOLOGY_SYSTEM,
            title="LOINC Laboratory Terminology",
            content=(
                "LOINC is the preferred terminology direction for laboratory test "
                "identifiers. OJTFlow should retain original lab_name text and add "
                "normalized coding evidence only when confidence is explicit."
            ),
            clinical_domain="laboratory",
            standard_system="LOINC",
            locator={"standard": "LOINC"},
        ),
        KnowledgeChunk(
            chunk_id="chunk_terminology_ucum_units_v0",
            source_id="terminology:ucum",
            source_type=EvidenceSourceType.TERMINOLOGY_SYSTEM,
            title="UCUM Units",
            content=(
                "UCUM is the target unit vocabulary for computable laboratory units. "
                "Missing or ambiguous units require human review before downstream "
                "clinical or analytics use."
            ),
            clinical_domain="laboratory",
            standard_system="UCUM",
            locator={"standard": "UCUM"},
        ),
        KnowledgeChunk(
            chunk_id="chunk_terminology_rxnorm_medications_v0",
            source_id="terminology:rxnorm",
            source_type=EvidenceSourceType.TERMINOLOGY_SYSTEM,
            title="RxNorm Medication Terminology",
            content=(
                "RxNorm is the terminology direction for normalized medication concepts. "
                "It is a future adapter boundary and should not be inferred from "
                "unrelated lab data."
            ),
            clinical_domain="medication",
            standard_system="RxNorm",
            locator={"standard": "RxNorm"},
        ),
        KnowledgeChunk(
            chunk_id="chunk_standard_omop_analytics_v0",
            source_id="standard:omop_cdm",
            source_type=EvidenceSourceType.HEALTHCARE_STANDARD,
            title="OMOP Common Data Model",
            content=(
                "OMOP CDM is an analytics export direction for observational health data. "
                "It should be implemented as a downstream mapping after source evidence, "
                "validation issues, and coding confidence are preserved."
            ),
            clinical_domain="analytics",
            standard_system="OMOP",
            locator={"standard": "OMOP CDM"},
        ),
    ]

    file_specs = [
        (
            "chunk_dictionary_lab_fields_v1",
            "dictionary:lab_fields_v1",
            EvidenceSourceType.DATA_DICTIONARY,
            "Lab Fields Data Dictionary",
            knowledge_root / "data_dictionaries/lab_fields.md",
            "laboratory",
            "ojtflow_dictionary",
        ),
        (
            "chunk_governance_human_review_v1",
            "governance:human_review_triggers_v1",
            EvidenceSourceType.DATA_DICTIONARY,
            "Human Review Triggers",
            knowledge_root / "governance/human_review_triggers.md",
            "governance",
            "ojtflow_policy",
        ),
        (
            "chunk_example_csv_lab_to_json_v1",
            "example:csv_lab_to_json_records_v1",
            EvidenceSourceType.TRANSFORMATION_EXAMPLE,
            "CSV Lab To JSON Records",
            knowledge_root / "transformation_examples/csv_lab_to_json_records.md",
            "laboratory",
            "ojtflow_example",
        ),
    ]
    for (
        chunk_id,
        source_id,
        source_type,
        title,
        path,
        clinical_domain,
        standard_system,
    ) in file_specs:
        if not path.exists():
            continue
        chunks.append(
            KnowledgeChunk(
                chunk_id=chunk_id,
                source_id=source_id,
                source_type=source_type,
                title=title,
                content=path.read_text(encoding="utf-8").strip(),
                clinical_domain=clinical_domain,
                standard_system=standard_system,
                locator={"path": str(path.relative_to(knowledge_root.parent))},
            )
        )
    return chunks


def chunk_metadata_json(chunk: KnowledgeChunk) -> str:
    """Serialize chunk metadata for SQL storage."""

    return json.dumps(
        {
            "locator": chunk.locator,
            "metadata": chunk.metadata,
            "clinical_domain": chunk.clinical_domain,
            "standard_system": chunk.standard_system,
        },
        sort_keys=True,
    )


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=True))


def _lexical_score(
    query_tokens: set[str],
    chunk_tokens: set[str],
    query_text: str,
    chunk: KnowledgeChunk,
) -> float:
    if not query_tokens:
        return 0.0
    overlap = len(query_tokens.intersection(chunk_tokens)) / len(query_tokens)
    phrase_boost = 0.15 if query_text.lower() in chunk.content.lower() else 0.0
    title_boost = 0.08 if any(token in tokenize(chunk.title) for token in query_tokens) else 0.0
    return overlap + phrase_boost + title_boost


def _rerank_boost(chunk: KnowledgeChunk, query: RetrievalQuery, matched_terms: list[str]) -> float:
    boost = 0.0
    if query.schema_id and query.schema_id in chunk.source_id:
        boost += 0.04
    if query.fields and any(field.lower() in matched_terms for field in query.fields):
        boost += 0.035
    if chunk.trust_level == TrustLevel.APPROVED:
        boost += 0.025
    if chunk.standard_system in {"FHIR", "LOINC", "UCUM"} and {
        "lab",
        "unit",
        "fhir",
    }.intersection(matched_terms):
        boost += 0.02
    filter_domain = query.filters.get("clinical_domain")
    if filter_domain and filter_domain == chunk.clinical_domain:
        boost += 0.03
    return boost
