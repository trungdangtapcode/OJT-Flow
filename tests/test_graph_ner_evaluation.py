import json
import subprocess
from pathlib import Path

from ojtflow.application.graph_ner_evaluation import (
    GraphNEREvalCase,
    GraphNEREvalExpectedNode,
    evaluate_graph_ner,
    load_graph_ner_eval_cases,
)
from ojtflow.application.graph_ner_service import GraphNERService


ROOT = Path(__file__).resolve().parents[1]


def test_graph_ner_eval_fixture_passes() -> None:
    cases = load_graph_ner_eval_cases(ROOT / "tests/fixtures/graph_ner_eval_cases.json")
    summary = evaluate_graph_ner(GraphNERService(), cases)

    assert summary.passed is True
    assert summary.case_count == 7
    assert summary.mean_node_recall == 1.0
    assert summary.mean_edge_recall == 1.0
    assert summary.mean_normalized_code_recall == 1.0
    assert summary.total_missing_nodes == 0
    assert summary.total_missing_edges == 0
    assert summary.total_missing_normalized_codes == 0
    assert {
        "lab_name_concepts",
        "ucum_unit_mentions",
        "identifier_fields",
        "medication_rxnorm_resource",
        "diagnosis_condition_resource",
        "procedure_concept",
        "diagnostic_report_resource",
    } == {result.case_id for result in summary.results}


def test_graph_ner_eval_fails_missing_expected_node() -> None:
    summary = evaluate_graph_ner(
        GraphNERService(),
        [
            GraphNEREvalCase(
                case_id="missing_expected_node",
                description="Missing expected nodes should fail the gate.",
                query="HbA1c",
                expected_nodes=[
                    GraphNEREvalExpectedNode(
                        node_id="clinical_concept:missing_marker",
                        node_type="clinical_concept",
                    )
                ],
            )
        ],
    )

    assert summary.passed is False
    assert summary.total_missing_nodes == 1
    assert summary.results[0].missing_node_ids == ["clinical_concept:missing_marker"]


def test_graph_ner_eval_cli_outputs_json_summary() -> None:
    result = subprocess.run(
        [
            str(ROOT / "scripts/evaluate-graph-ner.py"),
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    summary = json.loads(result.stdout)

    assert summary["passed"] is True
    assert summary["case_count"] == 7
    assert summary["mean_node_recall"] == 1.0
    assert summary["mean_edge_recall"] == 1.0
    assert summary["mean_normalized_code_recall"] == 1.0
