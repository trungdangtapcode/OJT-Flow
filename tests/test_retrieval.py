from pathlib import Path

from ojtflow.core.contracts.enums import EvidenceSourceType
from ojtflow.core.contracts.retrieval import RetrievalQuery
from ojtflow.infrastructure.retrieval.engine import (
    DeterministicEmbeddingProvider,
    build_query_variants,
)
from ojtflow.infrastructure.retrieval.static import StaticRetrievalRepository


ROOT = Path(__file__).resolve().parents[1]


def test_query_variants_include_fields_schema_and_format() -> None:
    variants = build_query_variants(
        RetrievalQuery(
            query="Clean lab CSV",
            fields=["date", "unit"],
            schema_id="lab_result_v1",
            detected_format="csv",
        )
    )

    assert variants[0] == "Clean lab CSV"
    assert any("date unit" in variant for variant in variants)
    assert any("lab_result_v1 schema" in variant for variant in variants)
    assert any("csv parsing conversion" in variant for variant in variants)


def test_static_retrieval_ranks_healthcare_evidence_with_trace() -> None:
    repository = StaticRetrievalRepository(ROOT / "knowledge")
    package = repository.search(
        RetrievalQuery(
            query="HbA1c lab CSV missing units FHIR Observation",
            fields=["date", "patient_id", "lab_name", "value", "unit"],
            schema_id="lab_result_v1",
            top_k=5,
            filters={"trust_level": "approved"},
        )
    )

    source_ids = {item.source_id for item in package.evidence}
    assert "schema:lab_result_v1" in source_ids
    assert "terminology:ucum" in source_ids
    assert package.trace.strategy == "static_hybrid_rrf"
    assert package.trace.candidates_seen >= 5
    assert package.hits[0].score >= package.hits[-1].score


def test_static_retrieval_filters_by_standard_system() -> None:
    repository = StaticRetrievalRepository(ROOT / "knowledge")
    package = repository.search(
        RetrievalQuery(
            query="laboratory units",
            top_k=3,
            filters={"standard_system": "UCUM", "trust_level": "approved"},
        )
    )

    assert package.evidence
    assert all(item.source_id == "terminology:ucum" for item in package.evidence)
    assert package.evidence[0].source_type == EvidenceSourceType.TERMINOLOGY_SYSTEM


def test_deterministic_embedding_is_stable() -> None:
    provider = DeterministicEmbeddingProvider(dimensions=16)

    assert provider.embed("lab unit") == provider.embed("lab unit")
    assert len(provider.embed("lab unit")) == 16
