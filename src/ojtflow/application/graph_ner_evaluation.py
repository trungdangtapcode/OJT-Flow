"""Fixture-backed evaluation for deterministic Graph-NER extraction."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic import Field, model_validator

from ojtflow.application.graph_ner_service import GraphNERService
from ojtflow.core.contracts.base import ContractModel, NonBlankStr
from ojtflow.core.contracts.enums import EvidenceSourceType
from ojtflow.core.contracts.evidence import Evidence
from ojtflow.core.contracts.retrieval import RetrievalQuery


class GraphNEREvalEvidence(ContractModel):
    """Evidence claim used as Graph-NER input in an evaluation case."""

    source_id: NonBlankStr
    claim: NonBlankStr
    source_type: EvidenceSourceType = EvidenceSourceType.HEALTHCARE_STANDARD
    locator: dict[str, Any] = Field(default_factory=dict)

    def to_evidence(self) -> Evidence:
        return Evidence(
            source_type=self.source_type,
            source_id=self.source_id,
            claim=self.claim,
            locator=self.locator,
        )


class GraphNEREvalExpectedNode(ContractModel):
    """One expected Graph-NER node and optional node-level assertions."""

    node_id: NonBlankStr
    node_type: NonBlankStr | None = None
    normalized_code: NonBlankStr | None = None
    rule_source: NonBlankStr | None = None


class GraphNEREvalExpectedEdge(ContractModel):
    """One expected Graph-NER edge."""

    source: NonBlankStr
    relation: NonBlankStr
    target: NonBlankStr

    def key(self) -> str:
        return _edge_key(
            {
                "source": self.source,
                "relation": self.relation,
                "target": self.target,
            }
        )


class GraphNEREvalCase(ContractModel):
    """One labeled Graph-NER fixture."""

    case_id: NonBlankStr
    description: NonBlankStr
    query: NonBlankStr
    fields: list[str] = Field(default_factory=list)
    resource_type: str | None = None
    evidence: list[GraphNEREvalEvidence] = Field(default_factory=list)
    expected_nodes: list[GraphNEREvalExpectedNode] = Field(default_factory=list)
    expected_edges: list[GraphNEREvalExpectedEdge] = Field(default_factory=list)

    @model_validator(mode="after")
    def _has_expectations(self) -> "GraphNEREvalCase":
        if not self.expected_nodes and not self.expected_edges:
            raise ValueError("Graph-NER eval cases require expected nodes or edges.")
        return self

    def to_query(self) -> RetrievalQuery:
        return RetrievalQuery(
            query=self.query,
            fields=self.fields,
            resource_type=self.resource_type,
        )


class GraphNEREvalCaseResult(ContractModel):
    """Graph extraction metrics for one case."""

    case_id: NonBlankStr
    description: NonBlankStr
    expected_node_count: int
    matched_node_count: int
    node_recall: float
    expected_edge_count: int
    matched_edge_count: int
    edge_recall: float
    expected_normalized_code_count: int
    matched_normalized_code_count: int
    normalized_code_recall: float
    missing_node_ids: list[NonBlankStr] = Field(default_factory=list)
    missing_edge_keys: list[NonBlankStr] = Field(default_factory=list)
    missing_normalized_codes: list[NonBlankStr] = Field(default_factory=list)
    graph_node_count: int
    graph_edge_count: int
    graph_triple_count: int


class GraphNEREvalSummary(ContractModel):
    """Aggregate metrics for Graph-NER fixtures."""

    case_count: int
    mean_node_recall: float
    mean_edge_recall: float
    mean_normalized_code_recall: float
    total_missing_nodes: int
    total_missing_edges: int
    total_missing_normalized_codes: int
    passed: bool
    thresholds: dict[str, float]
    results: list[GraphNEREvalCaseResult]


def load_graph_ner_eval_cases(path: Path) -> list[GraphNEREvalCase]:
    """Load Graph-NER evaluation fixtures from JSON."""

    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("Graph-NER evaluation fixture must be a JSON list.")
    return [GraphNEREvalCase.model_validate(item) for item in raw]


def evaluate_graph_ner(
    service: GraphNERService,
    cases: list[GraphNEREvalCase],
    *,
    min_mean_node_recall: float = 1.0,
    min_mean_edge_recall: float = 1.0,
    min_mean_normalized_code_recall: float = 1.0,
) -> GraphNEREvalSummary:
    """Evaluate deterministic Graph-NER extraction against labeled fixtures."""

    results = [_evaluate_case(service, case) for case in cases]
    if not results:
        raise ValueError("At least one Graph-NER evaluation case is required.")
    mean_node = _mean(result.node_recall for result in results)
    mean_edge = _mean(result.edge_recall for result in results)
    mean_code = _mean(result.normalized_code_recall for result in results)
    thresholds = {
        "min_mean_node_recall": min_mean_node_recall,
        "min_mean_edge_recall": min_mean_edge_recall,
        "min_mean_normalized_code_recall": min_mean_normalized_code_recall,
    }
    return GraphNEREvalSummary(
        case_count=len(results),
        mean_node_recall=round(mean_node, 6),
        mean_edge_recall=round(mean_edge, 6),
        mean_normalized_code_recall=round(mean_code, 6),
        total_missing_nodes=sum(len(result.missing_node_ids) for result in results),
        total_missing_edges=sum(len(result.missing_edge_keys) for result in results),
        total_missing_normalized_codes=sum(
            len(result.missing_normalized_codes) for result in results
        ),
        passed=(
            mean_node >= min_mean_node_recall
            and mean_edge >= min_mean_edge_recall
            and mean_code >= min_mean_normalized_code_recall
        ),
        thresholds=thresholds,
        results=results,
    )


def _evaluate_case(
    service: GraphNERService,
    case: GraphNEREvalCase,
) -> GraphNEREvalCaseResult:
    graph = service.build_graph_context(
        [item.to_evidence() for item in case.evidence],
        case.to_query(),
    )
    nodes = {str(node["id"]): node for node in graph.get("nodes", []) if "id" in node}
    edge_keys = {_edge_key(edge) for edge in graph.get("edges", [])}

    missing_nodes: list[str] = []
    missing_codes: list[str] = []
    matched_node_count = 0
    matched_code_count = 0
    expected_code_count = sum(1 for node in case.expected_nodes if node.normalized_code)
    for expected in case.expected_nodes:
        node = nodes.get(expected.node_id)
        if node is None:
            missing_nodes.append(expected.node_id)
            if expected.normalized_code:
                missing_codes.append(expected.normalized_code)
            continue
        if expected.node_type and node.get("type") != expected.node_type:
            missing_nodes.append(f"{expected.node_id}:type={expected.node_type}")
            continue
        if expected.rule_source and node.get("rule_source") != expected.rule_source:
            missing_nodes.append(f"{expected.node_id}:rule_source={expected.rule_source}")
            continue
        matched_node_count += 1
        if expected.normalized_code:
            if node.get("normalized_code") == expected.normalized_code:
                matched_code_count += 1
            else:
                missing_codes.append(expected.normalized_code)

    expected_edge_keys = [edge.key() for edge in case.expected_edges]
    missing_edges = [key for key in expected_edge_keys if key not in edge_keys]
    summary = graph.get("summary") if isinstance(graph.get("summary"), dict) else {}
    return GraphNEREvalCaseResult(
        case_id=case.case_id,
        description=case.description,
        expected_node_count=len(case.expected_nodes),
        matched_node_count=matched_node_count,
        node_recall=round(_recall(matched_node_count, len(case.expected_nodes)), 6),
        expected_edge_count=len(case.expected_edges),
        matched_edge_count=len(expected_edge_keys) - len(missing_edges),
        edge_recall=round(
            _recall(
                len(expected_edge_keys) - len(missing_edges),
                len(expected_edge_keys),
            ),
            6,
        ),
        expected_normalized_code_count=expected_code_count,
        matched_normalized_code_count=matched_code_count,
        normalized_code_recall=round(_recall(matched_code_count, expected_code_count), 6),
        missing_node_ids=missing_nodes,
        missing_edge_keys=missing_edges,
        missing_normalized_codes=missing_codes,
        graph_node_count=int(summary.get("node_count", len(nodes))),
        graph_edge_count=int(summary.get("edge_count", len(edge_keys))),
        graph_triple_count=int(summary.get("triple_count", 0)),
    )


def _edge_key(edge: dict[str, Any]) -> str:
    return f"{edge.get('source')}|{edge.get('relation')}|{edge.get('target')}"


def _recall(matched: int, expected: int) -> float:
    if expected == 0:
        return 1.0
    return matched / expected


def _mean(values: Iterable[float]) -> float:
    collected = list(values)
    return sum(collected) / len(collected)
