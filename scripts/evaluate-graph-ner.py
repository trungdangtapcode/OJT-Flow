#!/usr/bin/env python3
"""Run rule-based Graph-NER evaluation fixtures."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ojtflow.application.graph_ner_evaluation import (  # noqa: E402
    evaluate_graph_ner,
    load_graph_ner_eval_cases,
)
from ojtflow.application.graph_ner_service import GraphNERService  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate rule-based Graph-NER extraction quality.",
    )
    parser.add_argument(
        "--cases",
        default="tests/fixtures/graph_ner_eval_cases.json",
        help="Path to Graph-NER eval case JSON.",
    )
    parser.add_argument(
        "--min-node-recall",
        default=1.0,
        type=float,
        help="Minimum mean expected-node recall required to pass.",
    )
    parser.add_argument(
        "--min-edge-recall",
        default=1.0,
        type=float,
        help="Minimum mean expected-edge recall required to pass.",
    )
    parser.add_argument(
        "--min-normalized-code-recall",
        default=1.0,
        type=float,
        help="Minimum mean normalized-code recall required to pass.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a compact text report.",
    )
    args = parser.parse_args()

    summary = evaluate_graph_ner(
        GraphNERService(),
        load_graph_ner_eval_cases(_resolve_path(args.cases)),
        min_mean_node_recall=args.min_node_recall,
        min_mean_edge_recall=args.min_edge_recall,
        min_mean_normalized_code_recall=args.min_normalized_code_recall,
    )
    if args.json:
        print(summary.model_dump_json(indent=2))
    else:
        print(_format_summary(summary.model_dump()))
    return 0 if summary.passed else 1


def _resolve_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def _format_summary(summary: dict) -> str:
    lines = [
        "Graph-NER evaluation",
        f"  cases: {summary['case_count']}",
        f"  mean node recall: {summary['mean_node_recall']:.3f}",
        f"  mean edge recall: {summary['mean_edge_recall']:.3f}",
        f"  mean normalized-code recall: {summary['mean_normalized_code_recall']:.3f}",
        f"  missing nodes: {summary['total_missing_nodes']}",
        f"  missing edges: {summary['total_missing_edges']}",
        f"  missing normalized codes: {summary['total_missing_normalized_codes']}",
        f"  passed: {summary['passed']}",
        "",
        "Cases",
    ]
    for result in summary["results"]:
        status = (
            "PASS"
            if not result["missing_node_ids"] and not result["missing_edge_keys"]
            else "WARN"
        )
        lines.append(
            "  "
            f"{status} {result['case_id']}: "
            f"nodes={result['matched_node_count']}/{result['expected_node_count']}, "
            f"edges={result['matched_edge_count']}/{result['expected_edge_count']}, "
            f"codes={result['matched_normalized_code_count']}/"
            f"{result['expected_normalized_code_count']}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
