import json
from pathlib import Path

from ojtflow.application.graph_service import GraphService
from ojtflow.application.workflow_service import WorkflowService
from ojtflow.core.contracts.graph import GraphContextRecord
from ojtflow.core.contracts.retrieval import RetrievalQuery
from ojtflow.infrastructure.retrieval.static import (
    StaticKnowledgeRepository,
    StaticRetrievalRepository,
)
from ojtflow.infrastructure.storage.in_memory import (
    InMemoryDatasetStore,
    InMemoryEventRepository,
    InMemoryGraphRepository,
    InMemoryWorkflowRepository,
)
from ojtflow.infrastructure.storage.sqlite import SQLiteBackboneStore, SQLiteGraphRepository


ROOT = Path(__file__).resolve().parents[1]


def _workflow_service(graph_repository) -> WorkflowService:
    return WorkflowService(
        datasets=InMemoryDatasetStore(),
        workflows=InMemoryWorkflowRepository(),
        events=InMemoryEventRepository(),
        knowledge=StaticKnowledgeRepository(ROOT / "knowledge"),
        retrieval=StaticRetrievalRepository(ROOT / "knowledge"),
        graph_repository=graph_repository,
    )


def test_workflow_service_persists_graph_context_for_direct_retrieval() -> None:
    graph_repository = InMemoryGraphRepository()
    service = _workflow_service(graph_repository)

    package = service.search_retrieval(
        RetrievalQuery(
            query="FHIR Observation HbA1c UCUM unit",
            fields=["unit"],
            resource_type="Observation",
        ),
        owner_user_id="usr_graph",
        request_id="req_graph",
    )

    graph_record = package.handoff_context["graph_record"]
    records = service.list_graph_contexts(owner_user_id="usr_graph")
    jsonl_export = service.export_graph_contexts(owner_user_id="usr_graph")
    rdf_export = service.export_graph_contexts(
        owner_user_id="usr_graph",
        export_format="rdf_jsonl",
    )

    assert graph_record["graph_id"] == records[0].graph_id
    assert records[0].owner_user_id == "usr_graph"
    assert records[0].request_id == "req_graph"
    assert records[0].query == "FHIR Observation HbA1c UCUM unit"
    assert records[0].resource_type == "Observation"
    assert records[0].node_count > 0
    assert records[0].triple_count > 0
    assert service.list_graph_contexts(owner_user_id="usr_other") == []

    assert jsonl_export.graph_count == 1
    assert jsonl_export.node_count == records[0].node_count
    assert jsonl_export.triple_count == records[0].triple_count
    assert jsonl_export.content_type == "application/x-ndjson"
    assert json.loads(jsonl_export.content.splitlines()[0])["graph_id"] == records[0].graph_id

    assert rdf_export.format == "rdf_jsonl"
    assert rdf_export.graph_count == 1
    assert rdf_export.content
    assert set(json.loads(rdf_export.content.splitlines()[0])) >= {
        "subject",
        "predicate",
        "object",
        "evidence_id",
    }


def test_sqlite_graph_repository_survives_restart(tmp_path: Path) -> None:
    db_path = tmp_path / "ojtflow.db"
    data_dir = tmp_path / "var"
    repository = SQLiteGraphRepository(SQLiteBackboneStore(db_path, data_dir))
    saved = GraphContextRecord(
        graph_id="graph_restart",
        owner_user_id="usr_graph",
        workflow_id="wf_graph",
        request_id="req_graph",
        search_signature="sig_graph",
        query="Observation HbA1c unit",
        resource_type="Observation",
        fields=["unit"],
        node_count=2,
        edge_count=1,
        triple_count=1,
        graph_context={
            "graph_contract": "graph_ner_handoff.v0",
            "summary": {"node_count": 2, "edge_count": 1, "triple_count": 1},
            "nodes": [
                {"node_id": "query:1", "kind": "query", "label": "Observation HbA1c unit"},
                {"node_id": "standard:ucum", "kind": "healthcare_standard", "label": "UCUM"},
            ],
            "edges": [
                {
                    "source": "query:1",
                    "target": "standard:ucum",
                    "relation": "mentions_standard",
                }
            ],
            "triples": [
                {
                    "subject": "Observation.valueQuantity.unit",
                    "predicate": "uses",
                    "object": "UCUM",
                    "evidence_id": "ev_ucum",
                }
            ],
        },
        created_at="2026-06-11T00:00:00+00:00",
    )

    repository.save_context(saved)
    restarted = SQLiteGraphRepository(SQLiteBackboneStore(db_path, data_dir))
    records = restarted.list_contexts(owner_user_id="usr_graph", workflow_id="wf_graph")
    export = GraphService(restarted).export_contexts(owner_user_id="usr_graph")

    assert [record.graph_id for record in records] == ["graph_restart"]
    assert records[0].graph_context["triples"][0]["object"] == "UCUM"
    assert export.graph_count == 1
    assert export.triple_count == 1
    assert json.loads(export.content.splitlines()[-1])["record_type"] == "triple"
