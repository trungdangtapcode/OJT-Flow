"""Deterministic retrieval utilities shared by retrieval adapters."""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any

from ojtflow.core.contracts.enums import EvidenceSourceType, TrustLevel
from ojtflow.core.contracts.evidence import Evidence
from ojtflow.core.contracts.retrieval import (
    RetrievalCoverage,
    RetrievalCoverageItem,
    RetrievalFacetBucket,
    RetrievalFacets,
    RetrievalHit,
    RetrievalPackage,
    RetrievalQuery,
    RetrievalQueryAnalysis,
    RetrievalSource,
    RetrievalSnippet,
    RetrievalTrace,
)
from ojtflow.core.policy.risk_rules import contains_prompt_injection, looks_sensitive_field
from ojtflow.infrastructure.retrieval.query_analysis import analyze_query

TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9_./%-]*", re.IGNORECASE)
SNIPPET_SEGMENT_PATTERN = re.compile(r"(?<=[.!?])\s+|\n{2,}|\r\n{2,}")
DEFAULT_EMBEDDING_DIMENSIONS = 64
RRF_K = 60
SNIPPET_MAX_CHARS = 280


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
        self.provider_name = "deterministic"
        self.model = "deterministic-hash-v0"

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

    def embed_query(self, text: str) -> list[float]:
        return self.embed(text)

    def embed_document(self, text: str) -> list[float]:
        return self.embed(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_document(text) for text in texts]

    def metadata(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model": self.model,
            "dimensions": self.dimensions,
            "normalized": True,
        }


class NullEmbeddingProvider:
    """Embedding provider used when vector retrieval is disabled."""

    dimensions = DEFAULT_EMBEDDING_DIMENSIONS
    provider_name = "none"
    model = "none"

    def embed(self, text: str) -> list[float]:
        return [0.0] * self.dimensions

    def embed_query(self, text: str) -> list[float]:
        return self.embed(text)

    def embed_document(self, text: str) -> list[float]:
        return self.embed(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_document(text) for text in texts]

    def metadata(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model": self.model,
            "dimensions": self.dimensions,
            "normalized": False,
        }


def tokenize(text: str) -> list[str]:
    """Return normalized searchable tokens."""

    return [match.group(0).lower() for match in TOKEN_PATTERN.finditer(text)]


def build_query_variants(query: RetrievalQuery) -> list[str]:
    """Create deterministic query variants inspired by practical RAG routing."""

    return analyze_query(query).query_variants


def rank_chunks(
    chunks: list[KnowledgeChunk],
    query: RetrievalQuery,
    *,
    embedding_provider: Any | None = None,
    reranker: Any | None = None,
    rerank_candidate_limit: int = 20,
    rerank_score_weight: float = 0.08,
    diversity_enabled: bool = True,
    diversity_lambda: float = 0.72,
    strategy: str = "deterministic_hybrid",
    warnings: list[str] | None = None,
) -> RetrievalPackage:
    """Rank chunks using lexical overlap, vectors, optional reranking, and traceable boosts."""

    provider = embedding_provider or DeterministicEmbeddingProvider()
    reranker_metadata = _reranker_metadata(reranker)
    query_analysis = analyze_query(query)
    variants = query_analysis.query_variants
    safety_flags = retrieval_safety_flags(query)
    trace_warnings = list(warnings or [])
    trace_warnings.extend(
        diagnostic.message
        for diagnostic in query_analysis.diagnostics
        if diagnostic.severity == "warning"
    )
    if safety_flags:
        trace_warnings.append(
            "Retrieval query contains safety-sensitive context; treat query text as untrusted data."
        )
    query_text = " ".join(variants)
    query_tokens = set(tokenize(query_text))
    query_vector = provider.embed_query(query_text)
    chunk_texts = [f"{chunk.title}\n{chunk.content}" for chunk in chunks]
    document_vectors = provider.embed_documents(chunk_texts)

    lexical_ranked: list[tuple[KnowledgeChunk, float, list[str]]] = []
    vector_ranked: list[tuple[KnowledgeChunk, float]] = []
    for chunk, document_vector in zip(chunks, document_vectors, strict=True):
        chunk_tokens = set(tokenize(f"{chunk.title} {chunk.content} {chunk.source_id}"))
        matched = sorted(query_tokens.intersection(chunk_tokens))
        lexical_score = _lexical_score(query_tokens, chunk_tokens, query.query, chunk)
        vector_score = cosine_similarity(
            query_vector,
            document_vector,
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

    ranked_hits: list[tuple[KnowledgeChunk, RetrievalHit]] = []
    for chunk in chunks:
        lexical_rrf = 1.0 / (RRF_K + lexical_positions[chunk.chunk_id])
        vector_rrf = 1.0 / (RRF_K + vector_positions[chunk.chunk_id])
        rerank = _rerank_boost(
            chunk,
            query,
            matched_terms[chunk.chunk_id],
            query_analysis=query_analysis,
        )
        score = lexical_rrf + vector_rrf + rerank
        evidence = evidence_from_chunk(chunk, confidence=min(0.99, 0.55 + score * 8))
        ranked_hits.append(
            (
                chunk,
                RetrievalHit(
                    evidence=evidence,
                    score=round(score, 6),
                    lexical_score=round(lexical_scores[chunk.chunk_id], 6),
                    vector_score=round(vector_scores[chunk.chunk_id], 6),
                    rerank_score=round(rerank, 6),
                    matched_terms=matched_terms[chunk.chunk_id][:12],
                    source_locator=chunk.locator,
                    snippet=snippet_from_chunk(
                        chunk,
                        query_tokens=query_tokens,
                        matched_terms=matched_terms[chunk.chunk_id],
                    ),
                ),
            )
        )

    ranked_hits.sort(key=lambda item: item[1].score, reverse=True)
    if _reranker_enabled(reranker) and ranked_hits:
        candidates = ranked_hits[: max(1, rerank_candidate_limit)]
        external_scores = reranker.score(query_text, [chunk for chunk, _ in candidates])
        if external_scores:
            for chunk, hit in candidates:
                external_score = external_scores.get(chunk.chunk_id, 0.0)
                contribution = external_score * rerank_score_weight
                hit.score = round(hit.score + contribution, 6)
                hit.rerank_score = round(hit.rerank_score + contribution, 6)
                hit.evidence.confidence = round(min(0.99, 0.55 + hit.score * 8), 4)
            ranked_hits.sort(key=lambda item: item[1].score, reverse=True)

    selected_ranked_hits, diversity_metadata = _select_diverse_hits(
        ranked_hits,
        top_k=query.top_k,
        enabled=diversity_enabled,
        lambda_mult=diversity_lambda,
    )
    top_hits = [hit for _, hit in selected_ranked_hits]
    selected_chunks = [chunk for chunk, _ in selected_ranked_hits]
    facets = facets_from_chunks(selected_chunks)
    coverage = coverage_from_chunks(selected_chunks, query_analysis)
    trace_warnings.extend(coverage.warnings)
    if diversity_metadata["duplicate_selected_source_count"]:
        trace_warnings.append(
            "Retrieval results include repeated source IDs after diversity selection."
        )
    trace = RetrievalTrace(
        strategy=strategy,
        query_variants=variants,
        filters_applied=query.filters,
        candidates_seen=len(chunks),
        final_hit_ids=[hit.evidence.evidence_id for hit in top_hits],
        safety_flags=safety_flags,
        warnings=trace_warnings,
    )
    return RetrievalPackage(
        hits=top_hits,
        evidence=[hit.evidence for hit in top_hits],
        coverage=coverage,
        facets=facets,
        trace=trace,
        handoff_context={
            "retrieval_contract": "retrieval_package.v0",
            "query_fields": query.fields,
            "schema_id": query.schema_id,
            "strategy": strategy,
            "safety_flags": safety_flags,
            "embedding": provider.metadata(),
            "reranker": reranker_metadata,
            "diversity": diversity_metadata,
            "query_analysis": query_analysis.model_dump(),
        },
    )


def coverage_from_chunks(
    chunks: list[KnowledgeChunk],
    query_analysis: RetrievalQueryAnalysis,
) -> RetrievalCoverage:
    """Report whether final hits cover standards inferred from the query."""

    standard_counts = Counter(chunk.standard_system for chunk in chunks if chunk.standard_system)
    items = [
        _standard_coverage_item(standard, standard_counts)
        for standard in _expected_standard_values(query_analysis.standards)
    ]
    warnings = [
        item.reason
        for item in items
        if item.status == "missing" and item.severity == "warning"
    ]
    return RetrievalCoverage(standard_system=items, warnings=warnings)


def facets_from_chunks(chunks: list[KnowledgeChunk]) -> RetrievalFacets:
    """Build final-hit facets for operator scan/filter UX."""

    return RetrievalFacets(
        source_type=_facet_buckets(chunk.source_type.value for chunk in chunks),
        clinical_domain=_facet_buckets(chunk.clinical_domain for chunk in chunks),
        standard_system=_facet_buckets(chunk.standard_system for chunk in chunks),
        trust_level=_facet_buckets(chunk.trust_level.value for chunk in chunks),
    )


def retrieval_safety_flags(query: RetrievalQuery) -> list[str]:
    """Return deterministic safety flags for user-controlled retrieval context."""

    inspected_text = " ".join(
        value
        for value in [
            query.query,
            *query.fields,
            query.schema_id or "",
            query.detected_format or "",
            query.resource_type or "",
        ]
        if value
    )
    flags: list[str] = []
    if contains_prompt_injection(inspected_text):
        flags.append("prompt_injection_pattern_in_query")
    if any(looks_sensitive_field(field) for field in query.fields):
        flags.append("sensitive_field_context")
    return flags


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


def snippet_from_chunk(
    chunk: KnowledgeChunk,
    *,
    query_tokens: set[str],
    matched_terms: list[str],
) -> RetrievalSnippet:
    """Extract the most query-relevant sentence/window from a chunk."""

    content = _snippet_source_text(chunk.content)
    if not content:
        content = chunk.title
    segments = _snippet_segments(content)
    ranked_segments = [
        (
            _snippet_score(segment_text, query_tokens=query_tokens, matched_terms=matched_terms),
            start,
            end,
            segment_text,
        )
        for start, end, segment_text in segments
    ]
    ranked_segments.sort(
        key=lambda item: (
            item[0],
            -abs(len(item[3]) - SNIPPET_MAX_CHARS),
        ),
        reverse=True,
    )
    _, start, _end, text = (
        ranked_segments[0] if ranked_segments[0][0] > 0 else (0.0, *segments[0])
    )
    cropped_start, cropped_text = _crop_snippet(
        text,
        start_char=start,
        matched_terms=matched_terms,
    )
    snippet_terms = [
        term
        for term in matched_terms
        if term in set(tokenize(cropped_text))
    ][:8]
    return RetrievalSnippet(
        text=cropped_text,
        start_char=cropped_start,
        end_char=cropped_start + len(cropped_text),
        matched_terms=snippet_terms,
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
        KnowledgeChunk(
            chunk_id="chunk_standard_mesh_pubmed_search_v0",
            source_id="standard:mesh_pubmed_search",
            source_type=EvidenceSourceType.HEALTHCARE_STANDARD,
            title="MeSH and PubMed Search",
            content=(
                "MeSH is the controlled vocabulary direction for biomedical literature "
                "subject searching. PubMed search should combine MeSH review with "
                "title/abstract text words, field tags, publication type filters, and "
                "Search Details review before being treated as a final evidence strategy."
            ),
            clinical_domain="literature",
            standard_system="MeSH",
            locator={"standard": "NLM MeSH and PubMed"},
        ),
        KnowledgeChunk(
            chunk_id="chunk_standard_clinicaltrials_gov_api_v0",
            source_id="standard:clinicaltrials_gov_api",
            source_type=EvidenceSourceType.HEALTHCARE_STANDARD,
            title="ClinicalTrials.gov API v2",
            content=(
                "ClinicalTrials.gov API v2 provides study search for clinical trial "
                "context. OJTFlow search hints should prefer condition, intervention, "
                "recruitment status, eligibility, NCT identifier, and dataTimestamp "
                "verification before trial records are used as workflow evidence."
            ),
            clinical_domain="literature",
            standard_system="ClinicalTrials.gov",
            locator={"standard": "ClinicalTrials.gov API v2"},
        ),
        KnowledgeChunk(
            chunk_id="chunk_standard_openfda_drug_apis_v0",
            source_id="standard:openfda_drug_apis",
            source_type=EvidenceSourceType.HEALTHCARE_STANDARD,
            title="openFDA Drug APIs",
            content=(
                "openFDA drug APIs provide public drug label, adverse event, NDC, "
                "recall, and Drugs@FDA retrieval context. OJTFlow should treat FAERS "
                "adverse event records as signal context only and preserve endpoint, "
                "query, date, product identity, and limitations in evidence."
            ),
            clinical_domain="medication",
            standard_system="openFDA",
            locator={"standard": "openFDA drug APIs"},
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
        (
            "chunk_terminology_medical_concepts_v1",
            "terminology:medical_concepts_v1",
            EvidenceSourceType.TERMINOLOGY_SYSTEM,
            "Medical Concept Seed Registry",
            knowledge_root / "terminologies/medical_concepts.json",
            "multi_domain",
            "ojtflow_terminology",
        ),
        (
            "chunk_source_catalog_official_healthcare_sources_v1",
            "catalog:official_healthcare_sources_v1",
            EvidenceSourceType.DATA_DICTIONARY,
            "Official Healthcare Source Catalog",
            knowledge_root / "source_catalog/official_healthcare_sources.json",
            "multi_domain",
            "ojtflow_source_catalog",
        ),
        (
            "chunk_standard_fhir_search_parameters_r4_v1",
            "standard:fhir_search_parameters_r4_v1",
            EvidenceSourceType.HEALTHCARE_STANDARD,
            "FHIR R4 Search Parameter Seed",
            knowledge_root / "terminologies/fhir_search_parameters.json",
            "interoperability",
            "FHIR",
        ),
        (
            "chunk_standard_clinical_data_standards_map_v1",
            "standard:clinical_data_standards_map_v1",
            EvidenceSourceType.HEALTHCARE_STANDARD,
            "Clinical Data Standards Map",
            knowledge_root / "corpus/clinical_data_standards_map.md",
            "multi_domain",
            "ojtflow_standard_map",
        ),
        (
            "chunk_dictionary_medical_search_playbook_v1",
            "dictionary:medical_search_playbook_v1",
            EvidenceSourceType.DATA_DICTIONARY,
            "Medical Search Playbook",
            knowledge_root / "corpus/medical_search_playbook.md",
            "retrieval",
            "ojtflow_retrieval",
        ),
        (
            "chunk_catalog_public_dataset_ingestion_plan_v1",
            "catalog:public_dataset_ingestion_plan_v1",
            EvidenceSourceType.DATA_DICTIONARY,
            "Public Dataset Ingestion Plan",
            knowledge_root / "corpus/public_dataset_ingestion_plan.md",
            "multi_domain",
            "ojtflow_source_catalog",
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


def _facet_buckets(values: Iterable[object | None]) -> list[RetrievalFacetBucket]:
    counts = Counter(str(value) for value in values if value)
    return [
        RetrievalFacetBucket(value=value, count=count)
        for value, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]


def _expected_standard_values(standards: list[str]) -> list[str]:
    mapped: list[str] = []
    for standard in standards:
        if standard in {
            "FHIR",
            "LOINC",
            "UCUM",
            "RxNorm",
            "OMOP",
            "MeSH",
            "ClinicalTrials.gov",
            "openFDA",
        }:
            mapped.append(standard)
        elif standard == "OJTFlow policy":
            mapped.append("ojtflow_policy")
        elif standard == "OJTFlow schema":
            mapped.append("ojtflow_schema")
    return _dedupe_strings(mapped)


def _standard_coverage_item(
    standard: str,
    counts: Counter,
) -> RetrievalCoverageItem:
    selected_count = int(counts.get(standard, 0))
    if selected_count:
        return RetrievalCoverageItem(
            field="standard_system",
            value=standard,
            selected_count=selected_count,
            status="covered",
            severity="info",
            reason=f"Selected evidence includes {standard} grounding.",
        )
    return RetrievalCoverageItem(
        field="standard_system",
        value=standard,
        selected_count=0,
        status="missing",
        severity="warning",
        reason=f"Query analysis expected {standard} grounding, but no selected evidence used that standard.",
    )


def _dedupe_strings(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped


def _snippet_source_text(content: str) -> str:
    text = re.sub(r"^#{1,6}\s+", "", content, flags=re.MULTILINE)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _snippet_segments(content: str) -> list[tuple[int, int, str]]:
    segments: list[tuple[int, int, str]] = []
    cursor = 0
    for match in SNIPPET_SEGMENT_PATTERN.finditer(content):
        end = match.start()
        segment = content[cursor:end].strip()
        if segment:
            start = content.find(segment, cursor, end + len(segment))
            segments.append((start, start + len(segment), segment))
        cursor = match.end()
    tail = content[cursor:].strip()
    if tail:
        start = content.find(tail, cursor)
        segments.append((start, start + len(tail), tail))
    if not segments and content:
        segments.append((0, len(content), content))
    return segments


def _snippet_score(
    text: str,
    *,
    query_tokens: set[str],
    matched_terms: list[str],
) -> float:
    text_tokens = set(tokenize(text))
    matched = set(matched_terms)
    if not text_tokens:
        return 0.0
    exact_overlap = len(text_tokens.intersection(matched))
    query_overlap = len(text_tokens.intersection(query_tokens))
    density = exact_overlap / max(1, len(text_tokens))
    return exact_overlap * 2.0 + query_overlap * 0.25 + density


def _crop_snippet(
    text: str,
    *,
    start_char: int,
    matched_terms: list[str],
) -> tuple[int, str]:
    if len(text) <= SNIPPET_MAX_CHARS:
        return start_char, text
    lower_text = text.lower()
    first_match = min(
        (
            index
            for term in matched_terms
            if term
            for index in [lower_text.find(term.lower())]
            if index >= 0
        ),
        default=0,
    )
    local_start = max(0, first_match - SNIPPET_MAX_CHARS // 3)
    local_end = min(len(text), local_start + SNIPPET_MAX_CHARS)
    local_start = max(0, local_end - SNIPPET_MAX_CHARS)
    raw = text[local_start:local_end]
    leading_trim = len(raw) - len(raw.lstrip())
    return start_char + local_start + leading_trim, raw.strip()


def _rerank_boost(
    chunk: KnowledgeChunk,
    query: RetrievalQuery,
    matched_terms: list[str],
    *,
    query_analysis: RetrievalQueryAnalysis,
) -> float:
    boost = 0.0
    if query.schema_id and query.schema_id in chunk.source_id:
        boost += 0.08
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
    concepts = set(query_analysis.detected_concepts)
    if chunk.standard_system == "LOINC" and "hba1c_laboratory_test" in concepts:
        boost += 0.08
    if chunk.standard_system == "UCUM" and "unit_normalization" in concepts:
        boost += 0.05
    if chunk.standard_system == "FHIR" and "fhir_observation_profile" in concepts:
        boost += 0.05
    if chunk.standard_system == "ClinicalTrials.gov" and "clinical_trial_search" in concepts:
        boost += 0.08
    if chunk.standard_system == "openFDA" and "regulatory_drug_safety_search" in concepts:
        boost += 0.08
    if chunk.source_type == EvidenceSourceType.TRANSFORMATION_EXAMPLE and (
        "csv_tabular_quality" in concepts
        or query.detected_format
        or {"convert", "conversion", "transformation", "example"}.intersection(matched_terms)
    ):
        boost += 0.09
    filter_domain = query.filters.get("clinical_domain")
    if filter_domain and filter_domain == chunk.clinical_domain:
        boost += 0.03
    return boost


def _reranker_enabled(reranker: Any | None) -> bool:
    return bool(reranker and getattr(reranker, "enabled", False))


def _reranker_metadata(reranker: Any | None) -> dict[str, Any]:
    if reranker is None:
        return {"provider": "none", "model": "none", "enabled": False}
    metadata = getattr(reranker, "metadata", None)
    if callable(metadata):
        return metadata()
    return {
        "provider": getattr(reranker, "provider_name", "unknown"),
        "model": getattr(reranker, "model", "unknown"),
        "enabled": _reranker_enabled(reranker),
    }


def _select_diverse_hits(
    ranked_hits: list[tuple[KnowledgeChunk, RetrievalHit]],
    *,
    top_k: int,
    enabled: bool,
    lambda_mult: float,
) -> tuple[list[tuple[KnowledgeChunk, RetrievalHit]], dict[str, Any]]:
    if not enabled or top_k <= 1 or len(ranked_hits) <= 1:
        selected = ranked_hits[:top_k]
        return selected, _diversity_metadata(
            ranked_hits,
            selected,
            enabled=enabled,
            lambda_mult=lambda_mult,
        )

    clamped_lambda = max(0.0, min(1.0, lambda_mult))
    candidates = list(ranked_hits)
    selected: list[tuple[KnowledgeChunk, RetrievalHit]] = [candidates.pop(0)]
    relevance = _normalized_hit_relevance(ranked_hits)

    while candidates and len(selected) < top_k:
        best_index = 0
        best_score = float("-inf")
        for index, candidate in enumerate(candidates):
            chunk, hit = candidate
            redundancy = max(
                _chunk_redundancy(chunk, selected_chunk)
                for selected_chunk, _ in selected
            )
            mmr_score = (
                clamped_lambda * relevance[hit.evidence.evidence_id]
                - (1.0 - clamped_lambda) * redundancy
            )
            if mmr_score > best_score:
                best_score = mmr_score
                best_index = index
        selected.append(candidates.pop(best_index))

    return selected, _diversity_metadata(
        ranked_hits,
        selected,
        enabled=enabled,
        lambda_mult=clamped_lambda,
    )


def _normalized_hit_relevance(
    ranked_hits: list[tuple[KnowledgeChunk, RetrievalHit]],
) -> dict[str, float]:
    scores = [hit.score for _, hit in ranked_hits]
    minimum = min(scores)
    maximum = max(scores)
    if maximum == minimum:
        return {hit.evidence.evidence_id: 1.0 for _, hit in ranked_hits}
    span = maximum - minimum
    return {
        hit.evidence.evidence_id: (hit.score - minimum) / span
        for _, hit in ranked_hits
    }


def _chunk_redundancy(left: KnowledgeChunk, right: KnowledgeChunk) -> float:
    source_similarity = 1.0 if left.source_id == right.source_id else 0.0
    left_tokens = set(tokenize(f"{left.title} {left.content}"))
    right_tokens = set(tokenize(f"{right.title} {right.content}"))
    token_similarity = _jaccard_similarity(left_tokens, right_tokens)
    return max(source_similarity, token_similarity)


def _jaccard_similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left.intersection(right)) / len(left.union(right))


def _diversity_metadata(
    ranked_hits: list[tuple[KnowledgeChunk, RetrievalHit]],
    selected: list[tuple[KnowledgeChunk, RetrievalHit]],
    *,
    enabled: bool,
    lambda_mult: float,
) -> dict[str, Any]:
    candidate_sources = {chunk.source_id for chunk, _ in ranked_hits}
    selected_sources = [chunk.source_id for chunk, _ in selected]
    return {
        "enabled": enabled,
        "selection_mode": "mmr_source_diversity" if enabled else "score_order",
        "lambda": round(lambda_mult, 4),
        "candidate_source_count": len(candidate_sources),
        "selected_source_count": len(set(selected_sources)),
        "duplicate_selected_source_count": len(selected_sources) - len(set(selected_sources)),
    }
