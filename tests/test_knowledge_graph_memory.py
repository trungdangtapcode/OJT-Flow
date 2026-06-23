"""Unit tests for the in-memory persistent knowledge-graph repository.

Mirrors the worked example in ``docs/corpus_knowledge_graph_v0.md`` (HbA1c / metformin /
Type 2 diabetes) and the §14 test plan: entity resolution + idempotency, edge provenance,
scope isolation, and bounded neighborhood.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

from ojtflow.core.contracts.knowledge_graph import (
    KnowledgeGraphChunk,
    KnowledgeGraphEdge,
    KnowledgeGraphMention,
    KnowledgeGraphNode,
)
from ojtflow.infrastructure.storage.knowledge_graph_memory import (
    InMemoryKnowledgeGraphRepository,
)

NOW = "2026-06-22T00:00:00+00:00"
APP_FACTORY_PATH = Path(__file__).resolve().parents[1] / "src/ojtflow/interfaces/api/app.py"


def _node(node_id: str, label: str, node_type: str, *, scope="organization", org="org_acme",
          review_state="accepted", code=None, system=None) -> KnowledgeGraphNode:
    return KnowledgeGraphNode(
        node_id=node_id,
        scope=scope,
        organization_id=org if scope == "organization" else "",
        node_type=node_type,
        label=label,
        normalized_code=code,
        code_system=system,
        review_state=review_state,
        created_at=NOW,
        updated_at=NOW,
    )


def _seed_acme(repo: InMemoryKnowledgeGraphRepository) -> None:
    repo.upsert_concepts(
        [
            _node("loinc:4548-4", "HbA1c", "observation", code="4548-4", system="loinc"),
            _node("condition:type-2-diabetes-mellitus", "Type 2 diabetes mellitus",
                  "condition", review_state="pending"),
            _node("rxnorm:6809", "metformin", "medication", code="6809", system="rxnorm"),
        ]
    )
    repo.upsert_relations(
        [
            KnowledgeGraphEdge(
                source_node_id="loinc:4548-4",
                target_node_id="condition:type-2-diabetes-mellitus",
                relation="indicates",
                confidence=0.86,
                created_at=NOW,
            )
        ],
        source_chunk_id="chunk_visit0610_003",
    )
    repo.upsert_relations(
        [
            KnowledgeGraphEdge(
                source_node_id="rxnorm:6809",
                target_node_id="condition:type-2-diabetes-mellitus",
                relation="treats",
                created_at=NOW,
            )
        ],
        source_chunk_id="chunk_visit0610_003",
    )
    repo.append_provenance(
        KnowledgeGraphChunk(
            chunk_id="chunk_visit0610_003",
            scope="organization",
            organization_id="org_acme",
            document_id="visit_2026-06-10",
            snippet="HbA1c 8.2%. Type 2 diabetes mellitus. Started metformin 500mg BID.",
            created_at=NOW,
        ),
        [
            KnowledgeGraphMention(chunk_id="chunk_visit0610_003", node_id="loinc:4548-4"),
            KnowledgeGraphMention(
                chunk_id="chunk_visit0610_003",
                node_id="condition:type-2-diabetes-mellitus",
            ),
            KnowledgeGraphMention(chunk_id="chunk_visit0610_003", node_id="rxnorm:6809"),
        ],
    )


def test_upsert_is_idempotent_and_accumulates_provenance() -> None:
    repo = InMemoryKnowledgeGraphRepository()
    _seed_acme(repo)
    # Re-import the same concept from a second document.
    repo.upsert_concepts([_node("loinc:4548-4", "HbA1c", "observation",
                                code="4548-4", system="loinc")])
    repo.append_provenance(
        KnowledgeGraphChunk(
            chunk_id="chunk_discharge_009",
            scope="organization",
            organization_id="org_acme",
            snippet="HbA1c improved to 7.1%.",
            created_at=NOW,
        ),
        [KnowledgeGraphMention(chunk_id="chunk_discharge_009", node_id="loinc:4548-4")],
    )
    stats = repo.stats(organization_id="org_acme")
    assert stats.node_count == 3  # no duplicate HbA1c
    hba1c = repo.get_concept(node_id="loinc:4548-4", organization_id="org_acme")
    assert hba1c is not None
    assert hba1c.source_chunk_ids == ["chunk_visit0610_003", "chunk_discharge_009"]


def test_edge_carries_source_provenance_resolved_to_snippet() -> None:
    repo = InMemoryKnowledgeGraphRepository()
    _seed_acme(repo)
    view = repo.neighborhood(seeds=["rxnorm:6809"], depth=1, organization_id="org_acme")
    treats = next(e for e in view.edges if e.relation == "treats")
    assert treats.source_node_id == "rxnorm:6809"
    assert treats.target_node_id == "condition:type-2-diabetes-mellitus"
    assert treats.source_chunk_ids == ["chunk_visit0610_003"]
    assert any("metformin" in snippet for snippet in treats.source_snippets)


def test_edge_provenance_accumulates_across_documents() -> None:
    repo = InMemoryKnowledgeGraphRepository()
    _seed_acme(repo)
    repo.upsert_relations(
        [
            KnowledgeGraphEdge(
                source_node_id="rxnorm:6809",
                target_node_id="condition:type-2-diabetes-mellitus",
                relation="treats",
                created_at=NOW,
            )
        ],
        source_chunk_id="chunk_discharge_009",
    )
    view = repo.neighborhood(seeds=["rxnorm:6809"], depth=1, organization_id="org_acme")
    treats = next(e for e in view.edges if e.relation == "treats")
    assert treats.source_chunk_ids == ["chunk_visit0610_003", "chunk_discharge_009"]


def test_neighborhood_respects_depth() -> None:
    repo = InMemoryKnowledgeGraphRepository()
    _seed_acme(repo)
    d1 = repo.neighborhood(seeds=["loinc:4548-4"], depth=1, organization_id="org_acme")
    ids1 = {n.node_id for n in d1.nodes}
    assert ids1 == {"loinc:4548-4", "condition:type-2-diabetes-mellitus"}
    assert "rxnorm:6809" not in ids1  # metformin is two hops away

    d2 = repo.neighborhood(seeds=["loinc:4548-4"], depth=2, organization_id="org_acme")
    assert {n.node_id for n in d2.nodes} == {
        "loinc:4548-4",
        "condition:type-2-diabetes-mellitus",
        "rxnorm:6809",
    }


def test_scope_isolation_org_cannot_read_other_org_but_sees_global() -> None:
    repo = InMemoryKnowledgeGraphRepository()
    _seed_acme(repo)
    repo.upsert_concepts(
        [_node("loinc:4548-4", "HbA1c (reference)", "observation",
               scope="global", code="4548-4", system="loinc")]
    )

    # org_beta sees the global reference, never org_acme's private concepts.
    beta_hits = repo.search_concepts(q="HbA1c", organization_id="org_beta")
    assert [n.scope for n in beta_hits] == ["global"]
    assert repo.get_concept(
        node_id="condition:type-2-diabetes-mellitus", organization_id="org_beta"
    ) is None

    # org_acme resolves the most specific (its own org-scoped) concept.
    acme = repo.get_concept(node_id="loinc:4548-4", organization_id="org_acme")
    assert acme is not None and acme.scope == "organization"


def test_global_only_read_when_no_org() -> None:
    repo = InMemoryKnowledgeGraphRepository()
    _seed_acme(repo)
    assert repo.stats(organization_id=None).node_count == 0  # nothing global yet
    repo.upsert_concepts([_node("snomed:73211009", "Diabetes mellitus", "condition",
                                scope="global")])
    assert repo.stats(organization_id=None).node_count == 1


def test_knowledge_graph_router_is_registered() -> None:
    app_source = APP_FACTORY_PATH.read_text(encoding="utf-8")
    assert "knowledge_graph," in app_source
    assert 'app.include_router(knowledge_graph.router, prefix="/api/v1")' in app_source


def test_graph_med_native_node_mapping() -> None:
    from ojtflow.infrastructure.storage.knowledge_graph_neo4j import (
        _graph_med_node_from_row,
    )

    node = _graph_med_node_from_row(
        ["Resource", "IcdDisease"],
        {"id": "E11.9", "label": "Type 2 diabetes mellitus"},
    )

    assert node is not None
    assert node.node_id == "graph-med:icd_disease:E11.9"
    assert node.scope == "global"
    assert node.code_system == "ICD-10"
    assert node.node_type == "icd_disease"


@pytest.mark.skipif(
    importlib.util.find_spec("neo4j") is None or not os.getenv("OJT_NEO4J_TEST_URI"),
    reason="neo4j driver absent or OJT_NEO4J_TEST_URI unset (live instance required)",
)
def test_neo4j_adapter_roundtrip() -> None:
    from ojtflow.infrastructure.storage.knowledge_graph_neo4j import (
        Neo4jKnowledgeGraphRepository,
    )

    repo = Neo4jKnowledgeGraphRepository(
        os.environ["OJT_NEO4J_TEST_URI"],
        user=os.getenv("OJT_NEO4J_TEST_USER", "neo4j"),
        password=os.getenv("OJT_NEO4J_TEST_PASSWORD", "testpassword123"),
        database=os.getenv("OJT_NEO4J_TEST_DATABASE", "neo4j"),
    )
    repo.bootstrap()
    repo._rows("MATCH (n) DETACH DELETE n")
    _seed_acme(repo)
    view = repo.neighborhood(seeds=["rxnorm:6809"], depth=1, organization_id="org_acme")
    treats = next(e for e in view.edges if e.relation == "treats")
    assert treats.source_chunk_ids == ["chunk_visit0610_003"]
    assert any("metformin" in s for s in treats.source_snippets)
    assert repo.get_concept(node_id="rxnorm:6809", organization_id="org_beta") is None
    repo.close()


@pytest.mark.skipif(
    importlib.util.find_spec("kuzu") is None,
    reason="kuzu not installed (optional 'graph' extra)",
)
def test_kuzu_adapter_roundtrip(tmp_path) -> None:
    from ojtflow.infrastructure.storage.knowledge_graph_kuzu import (
        KuzuKnowledgeGraphRepository,
    )

    repo = KuzuKnowledgeGraphRepository(tmp_path / "kuzu" / "corpus")
    repo.bootstrap()
    _seed_acme(repo)
    view = repo.neighborhood(seeds=["rxnorm:6809"], depth=1, organization_id="org_acme")
    treats = next(e for e in view.edges if e.relation == "treats")
    assert treats.source_chunk_ids == ["chunk_visit0610_003"]
