"""Deterministic retrieval evaluation helpers."""

from __future__ import annotations

import json
import math
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic import Field, model_validator

from ojtflow.core.contracts.base import ContractModel, NonBlankStr
from ojtflow.core.contracts.retrieval import RetrievalQuery


class RetrievalEvalJudgment(ContractModel):
    """One source-level relevance judgment for retrieval evaluation."""

    source_id: NonBlankStr
    rating: int = Field(ge=0, le=3)
    reason: NonBlankStr | None = None


class RetrievalEvalCase(ContractModel):
    """One labeled retrieval quality case."""

    case_id: NonBlankStr
    description: NonBlankStr
    query: NonBlankStr
    expected_source_ids: list[NonBlankStr] = Field(default_factory=list)
    judgments: list[RetrievalEvalJudgment] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=20)
    fields: list[str] = Field(default_factory=list)
    schema_id: str | None = None
    detected_format: str | None = None
    resource_type: str | None = None
    filters: dict[str, Any] = Field(default_factory=lambda: {"trust_level": "approved"})

    @model_validator(mode="after")
    def _has_relevant_sources(self) -> "RetrievalEvalCase":
        if not self.positive_source_ids():
            raise ValueError(
                "Retrieval eval cases require expected_source_ids or positive judgments."
            )
        return self

    def to_query(self) -> RetrievalQuery:
        return RetrievalQuery(
            query=self.query,
            fields=self.fields,
            schema_id=self.schema_id,
            detected_format=self.detected_format,
            resource_type=self.resource_type,
            top_k=self.top_k,
            filters=self.filters,
        )

    def relevance_ratings(self) -> dict[str, int]:
        ratings = {judgment.source_id: judgment.rating for judgment in self.judgments}
        for source_id in self.expected_source_ids:
            ratings.setdefault(source_id, 1)
        return ratings

    def positive_source_ids(self) -> list[str]:
        ratings = self.relevance_ratings()
        return [
            source_id
            for source_id in _ordered_unique(
                [
                    *self.expected_source_ids,
                    *(judgment.source_id for judgment in self.judgments),
                ]
            )
            if ratings.get(source_id, 0) > 0
        ]


class RetrievalEvalCaseResult(ContractModel):
    """Rank-aware metrics for one retrieval eval case."""

    case_id: str
    description: str
    expected_source_ids: list[str]
    retrieved_source_ids: list[str]
    hit_at_k: bool
    coverage_at_k: float
    recall_at_k: float
    precision_at_k: float
    average_precision_at_k: float
    ndcg_at_k: float
    reciprocal_rank: float
    first_relevant_rank: int | None = None
    missing_source_ids: list[str] = Field(default_factory=list)
    judged_source_count: int = 0
    judged_retrieved_source_count: int = 0
    relevance_ratings: dict[str, int] = Field(default_factory=dict)
    selected_source_count: int = 0
    duplicate_selected_source_count: int = 0


class RetrievalEvalSummary(ContractModel):
    """Aggregate retrieval quality metrics for a fixture set."""

    case_count: int
    hit_rate_at_k: float
    mean_coverage_at_k: float
    mean_recall_at_k: float
    mean_precision_at_k: float
    mean_average_precision_at_k: float
    mean_ndcg_at_k: float
    mean_reciprocal_rank: float
    mean_selected_source_count: float
    total_missing_source_ids: int
    passed: bool
    thresholds: dict[str, float]
    results: list[RetrievalEvalCaseResult]


def load_eval_cases(path: Path) -> list[RetrievalEvalCase]:
    """Load retrieval evaluation cases from JSON."""

    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("Retrieval evaluation fixture must be a JSON list.")
    return [RetrievalEvalCase.model_validate(item) for item in raw]


def evaluate_retrieval_repository(
    repository: Any,
    cases: list[RetrievalEvalCase],
    *,
    min_hit_rate_at_k: float = 1.0,
    min_mean_recall_at_k: float = 0.8,
    min_mean_reciprocal_rank: float = 0.8,
    min_mean_ndcg_at_k: float = 0.8,
) -> RetrievalEvalSummary:
    """Evaluate a repository against labeled retrieval cases."""

    results = [_evaluate_case(repository, case) for case in cases]
    case_count = len(results)
    if case_count == 0:
        raise ValueError("At least one retrieval evaluation case is required.")

    hit_rate = sum(1 for result in results if result.hit_at_k) / case_count
    mean_coverage = _mean(result.coverage_at_k for result in results)
    mean_recall = _mean(result.recall_at_k for result in results)
    mean_precision = _mean(result.precision_at_k for result in results)
    mean_ap = _mean(result.average_precision_at_k for result in results)
    mean_ndcg = _mean(result.ndcg_at_k for result in results)
    mean_rr = _mean(result.reciprocal_rank for result in results)
    mean_sources = _mean(result.selected_source_count for result in results)
    thresholds = {
        "min_hit_rate_at_k": min_hit_rate_at_k,
        "min_mean_recall_at_k": min_mean_recall_at_k,
        "min_mean_reciprocal_rank": min_mean_reciprocal_rank,
        "min_mean_ndcg_at_k": min_mean_ndcg_at_k,
    }
    return RetrievalEvalSummary(
        case_count=case_count,
        hit_rate_at_k=round(hit_rate, 6),
        mean_coverage_at_k=round(mean_coverage, 6),
        mean_recall_at_k=round(mean_recall, 6),
        mean_precision_at_k=round(mean_precision, 6),
        mean_average_precision_at_k=round(mean_ap, 6),
        mean_ndcg_at_k=round(mean_ndcg, 6),
        mean_reciprocal_rank=round(mean_rr, 6),
        mean_selected_source_count=round(mean_sources, 6),
        total_missing_source_ids=sum(len(result.missing_source_ids) for result in results),
        passed=(
            hit_rate >= min_hit_rate_at_k
            and mean_recall >= min_mean_recall_at_k
            and mean_rr >= min_mean_reciprocal_rank
            and mean_ndcg >= min_mean_ndcg_at_k
        ),
        thresholds=thresholds,
        results=results,
    )


def _evaluate_case(repository: Any, case: RetrievalEvalCase) -> RetrievalEvalCaseResult:
    package = repository.search(case.to_query())
    retrieved = [hit.evidence.source_id for hit in package.hits]
    ratings = case.relevance_ratings()
    expected = set(case.positive_source_ids())
    relevant_ranks = [
        index
        for index, source_id in enumerate(retrieved, start=1)
        if ratings.get(source_id, 0) > 0
    ]
    retrieved_judged_count = sum(1 for source_id in retrieved if source_id in ratings)
    relevant_retrieved = {
        source_id for source_id in retrieved if ratings.get(source_id, 0) > 0
    }
    first_rank = min(relevant_ranks) if relevant_ranks else None
    diversity = _package_diversity_summary(package, retrieved)
    return RetrievalEvalCaseResult(
        case_id=case.case_id,
        description=case.description,
        expected_source_ids=case.positive_source_ids(),
        retrieved_source_ids=retrieved,
        hit_at_k=first_rank is not None,
        coverage_at_k=round(retrieved_judged_count / max(1, len(retrieved)), 6),
        recall_at_k=round(len(relevant_retrieved) / len(expected), 6),
        precision_at_k=round(len(relevant_ranks) / max(1, len(retrieved)), 6),
        average_precision_at_k=round(_average_precision_at_k(retrieved, ratings, expected), 6),
        ndcg_at_k=round(_ndcg_at_k(retrieved, ratings), 6),
        reciprocal_rank=round(1.0 / first_rank, 6) if first_rank else 0.0,
        first_relevant_rank=first_rank,
        missing_source_ids=sorted(expected.difference(relevant_retrieved)),
        judged_source_count=len(ratings),
        judged_retrieved_source_count=retrieved_judged_count,
        relevance_ratings=ratings,
        selected_source_count=diversity["selected_source_count"],
        duplicate_selected_source_count=diversity["duplicate_selected_source_count"],
    )


def _package_diversity_summary(package: Any, retrieved: list[str]) -> dict[str, int]:
    diversity_contract = getattr(package, "diversity", None)
    if diversity_contract is not None:
        selected_source_count = getattr(diversity_contract, "selected_source_count", None)
        duplicate_selected_source_count = getattr(
            diversity_contract,
            "duplicate_selected_source_count",
            None,
        )
        if isinstance(selected_source_count, int) and isinstance(
            duplicate_selected_source_count,
            int,
        ):
            return {
                "selected_source_count": selected_source_count,
                "duplicate_selected_source_count": duplicate_selected_source_count,
            }

    handoff_context = getattr(package, "handoff_context", {})
    raw_diversity = (
        handoff_context.get("diversity", {})
        if isinstance(handoff_context, dict)
        else {}
    )
    diversity = raw_diversity if isinstance(raw_diversity, dict) else {}
    return {
        "selected_source_count": int(
            diversity.get("selected_source_count", len(set(retrieved)))
        ),
        "duplicate_selected_source_count": int(
            diversity.get(
                "duplicate_selected_source_count",
                len(retrieved) - len(set(retrieved)),
            )
        ),
    }


def _average_precision_at_k(
    retrieved: list[str],
    ratings: dict[str, int],
    expected: set[str],
) -> float:
    if not expected:
        return 0.0
    seen_relevant: set[str] = set()
    precision_sum = 0.0
    for index, source_id in enumerate(retrieved, start=1):
        if ratings.get(source_id, 0) <= 0 or source_id in seen_relevant:
            continue
        seen_relevant.add(source_id)
        precision_sum += len(seen_relevant) / index
    return precision_sum / len(expected)


def _ndcg_at_k(retrieved: list[str], ratings: dict[str, int]) -> float:
    ranked_ratings = [ratings.get(source_id, 0) for source_id in retrieved]
    ideal_ratings = sorted(ratings.values(), reverse=True)[: len(retrieved)]
    ideal_dcg = _discounted_cumulative_gain(ideal_ratings)
    if ideal_dcg <= 0:
        return 0.0
    return _discounted_cumulative_gain(ranked_ratings) / ideal_dcg


def _discounted_cumulative_gain(ratings: list[int]) -> float:
    total = 0.0
    for index, rating in enumerate(ratings, start=1):
        if rating <= 0:
            continue
        total += (2**rating - 1) / math.log2(index + 1)
    return total


def _mean(values: Iterable[float]) -> float:
    collected = list(values)
    return sum(collected) / len(collected)


def _ordered_unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(values))
