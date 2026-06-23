"""Graph-med service orchestration tests."""

from __future__ import annotations

import pytest

from ojtflow.application.graph_med_service import GraphMedService
from ojtflow.core.contracts.knowledge_graph import (
    GraphMedLinkedEntity,
    GraphMedStatus,
)
from ojtflow.core.errors import DependencyUnavailableError
from ojtflow.infrastructure.storage.knowledge_graph_memory import (
    InMemoryKnowledgeGraphRepository,
)


def _status(*, available: bool = True) -> GraphMedStatus:
    return GraphMedStatus(
        enabled=True,
        available=available,
        ontology_loaded=available,
        embedding_endpoint_configured=True,
        llm_endpoint_configured=True,
        embedding_endpoint_reachable=available,
        llm_endpoint_reachable=available,
        icd_vector_index="icd_disease_embedding",
        icd_disease_count=12221 if available else 0,
        hpo_phenotype_count=0,
        umls_count=0,
        message="ok" if available else "graph-med unavailable",
    )


class FakeGraphMedAnnotator:
    def __init__(self, *, available: bool = True) -> None:
        self._available = available

    def status(self) -> GraphMedStatus:
        return _status(available=self._available)

    def annotate_text(
        self,
        *,
        patient_id: str,
        encounter_id: str,
        concat_text: str,
        narrative_text: str,
    ) -> list[GraphMedLinkedEntity]:
        return [
            GraphMedLinkedEntity(
                source="narrative",
                start=0,
                end=9,
                text="pneumonia",
                label="Diseases of the respiratory system",
                assertion="present",
                temporality="acute",
                rationale="Clinical problem mention.",
                icd_id="J18.9",
                icd_label="Pneumonia, unspecified",
                confidence=0.91,
                linking_rationale="Best graph-med ICD candidate.",
            )
        ]


def test_graph_med_service_imports_linked_icd_concept_with_provenance() -> None:
    repo = InMemoryKnowledgeGraphRepository()
    service = GraphMedService(repo, graph_med_annotator=FakeGraphMedAnnotator())

    result = service.import_text(
        text="pneumonia",
        organization_id="org_acme",
        document_id="doc_1",
    )

    assert result.backend == "graph-med"
    assert result.entities == 1
    assert result.linked_entities == 1
    concept = repo.get_concept(node_id="icd-10:J18.9", organization_id="org_acme")
    assert concept is not None
    assert concept.label == "Pneumonia, unspecified"
    assert concept.source_chunk_ids == ["import_91639a9c1a0f"]


def test_graph_med_service_fails_closed_when_unavailable() -> None:
    repo = InMemoryKnowledgeGraphRepository()
    service = GraphMedService(
        repo,
        graph_med_annotator=FakeGraphMedAnnotator(available=False),
    )

    with pytest.raises(DependencyUnavailableError):
        service.import_text(text="pneumonia", organization_id="org_acme")

    assert repo.stats(organization_id="org_acme").node_count == 0
