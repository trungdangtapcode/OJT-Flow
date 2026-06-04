#!/usr/bin/env python3
"""Run deterministic retrieval evaluation cases."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ojtflow.infrastructure.retrieval.evaluation import (  # noqa: E402
    evaluate_retrieval_repository,
    load_eval_cases,
)
from ojtflow.infrastructure.retrieval.static import StaticRetrievalRepository  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate deterministic healthcare retrieval quality.",
    )
    parser.add_argument(
        "--cases",
        default="tests/fixtures/retrieval_eval_cases.json",
        help="Path to retrieval eval case JSON.",
    )
    parser.add_argument(
        "--knowledge-dir",
        default="knowledge",
        help="Path to trusted healthcare knowledge directory.",
    )
    parser.add_argument(
        "--min-hit-rate",
        default=1.0,
        type=float,
        help="Minimum hit@k rate required to pass.",
    )
    parser.add_argument(
        "--min-mean-recall",
        default=0.8,
        type=float,
        help="Minimum mean recall@k required to pass.",
    )
    parser.add_argument(
        "--min-mrr",
        default=0.8,
        type=float,
        help="Minimum mean reciprocal rank required to pass.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a compact text report.",
    )
    args = parser.parse_args()

    cases_path = _resolve_path(args.cases)
    knowledge_dir = _resolve_path(args.knowledge_dir)
    repository = StaticRetrievalRepository(knowledge_dir)
    summary = evaluate_retrieval_repository(
        repository,
        load_eval_cases(cases_path),
        min_hit_rate_at_k=args.min_hit_rate,
        min_mean_recall_at_k=args.min_mean_recall,
        min_mean_reciprocal_rank=args.min_mrr,
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
        "Retrieval evaluation",
        f"  cases: {summary['case_count']}",
        f"  hit@k: {summary['hit_rate_at_k']:.3f}",
        f"  mean recall@k: {summary['mean_recall_at_k']:.3f}",
        f"  mean precision@k: {summary['mean_precision_at_k']:.3f}",
        f"  MRR: {summary['mean_reciprocal_rank']:.3f}",
        f"  mean selected sources: {summary['mean_selected_source_count']:.3f}",
        f"  missing expected sources: {summary['total_missing_source_ids']}",
        f"  passed: {summary['passed']}",
        "",
        "Cases",
    ]
    for result in summary["results"]:
        status = "PASS" if result["hit_at_k"] and not result["missing_source_ids"] else "WARN"
        lines.append(
            "  "
            f"{status} {result['case_id']}: "
            f"RR={result['reciprocal_rank']:.3f}, "
            f"recall={result['recall_at_k']:.3f}, "
            f"retrieved={', '.join(result['retrieved_source_ids'])}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
