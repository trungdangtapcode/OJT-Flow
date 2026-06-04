"""Deterministic retrieval evaluation helpers."""

from __future__ import annotations

import json
from pathlib import Path
from collections.abc import Iterable
from typing import Any

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel, NonBlankStr
from ojtflow.core.contracts.retrieval import RetrievalQuery


class RetrievalEvalCase(ContractModel):
    """One labeled retrieval quality case."""

    case_id: NonBlankStr
    description: NonBlankStr
    query: NonBlankStr
    expected_source_ids: list[NonBlankStr] = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    fields: list[str] = Field(default_factory=list)
    schema_id: str | None = None
    detected_format: str | None = None
    resource_type: str | None = None
    filters: dict[str, Any] = Field(default_factory=lambda: {"trust_level": "approved"})

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


class RetrievalEvalCaseResult(ContractModel):
    """Rank-aware metrics for one retrieval eval case."""

    case_id: str
    description: str
    expected_source_ids: list[str]
    retrieved_source_ids: list[str]
    hit_at_k: bool
    recall_at_k: float
    precision_at_k: float
    reciprocal_rank: float
    first_relevant_rank: int | None = None
    missing_source_ids: list[str] = Field(default_factory=list)
    selected_source_count: int = 0
    duplicate_selected_source_count: int = 0


class RetrievalEvalSummary(ContractModel):
    """Aggregate retrieval quality metrics for a fixture set."""

    case_count: int
    hit_rate_at_k: float
    mean_recall_at_k: float
    mean_precision_at_k: float
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
) -> RetrievalEvalSummary:
    """Evaluate a repository against labeled retrieval cases."""

    results = [_evaluate_case(repository, case) for case in cases]
    case_count = len(results)
    if case_count == 0:
        raise ValueError("At least one retrieval evaluation case is required.")

    hit_rate = sum(1 for result in results if result.hit_at_k) / case_count
    mean_recall = _mean(result.recall_at_k for result in results)
    mean_precision = _mean(result.precision_at_k for result in results)
    mean_rr = _mean(result.reciprocal_rank for result in results)
    mean_sources = _mean(result.selected_source_count for result in results)
    thresholds = {
        "min_hit_rate_at_k": min_hit_rate_at_k,
        "min_mean_recall_at_k": min_mean_recall_at_k,
        "min_mean_reciprocal_rank": min_mean_reciprocal_rank,
    }
    return RetrievalEvalSummary(
        case_count=case_count,
        hit_rate_at_k=round(hit_rate, 6),
        mean_recall_at_k=round(mean_recall, 6),
        mean_precision_at_k=round(mean_precision, 6),
        mean_reciprocal_rank=round(mean_rr, 6),
        mean_selected_source_count=round(mean_sources, 6),
        total_missing_source_ids=sum(len(result.missing_source_ids) for result in results),
        passed=(
            hit_rate >= min_hit_rate_at_k
            and mean_recall >= min_mean_recall_at_k
            and mean_rr >= min_mean_reciprocal_rank
        ),
        thresholds=thresholds,
        results=results,
    )


def _evaluate_case(repository: Any, case: RetrievalEvalCase) -> RetrievalEvalCaseResult:
    package = repository.search(case.to_query())
    retrieved = [hit.evidence.source_id for hit in package.hits]
    expected = set(case.expected_source_ids)
    relevant_ranks = [
        index
        for index, source_id in enumerate(retrieved, start=1)
        if source_id in expected
    ]
    relevant_retrieved = {source_id for source_id in retrieved if source_id in expected}
    first_rank = min(relevant_ranks) if relevant_ranks else None
    raw_diversity = package.handoff_context.get("diversity", {})
    diversity = raw_diversity if isinstance(raw_diversity, dict) else {}
    return RetrievalEvalCaseResult(
        case_id=case.case_id,
        description=case.description,
        expected_source_ids=list(case.expected_source_ids),
        retrieved_source_ids=retrieved,
        hit_at_k=first_rank is not None,
        recall_at_k=round(len(relevant_retrieved) / len(expected), 6),
        precision_at_k=round(len(relevant_ranks) / max(1, len(retrieved)), 6),
        reciprocal_rank=round(1.0 / first_rank, 6) if first_rank else 0.0,
        first_relevant_rank=first_rank,
        missing_source_ids=sorted(expected.difference(relevant_retrieved)),
        selected_source_count=int(diversity.get("selected_source_count", len(set(retrieved)))),
        duplicate_selected_source_count=int(
            diversity.get("duplicate_selected_source_count", len(retrieved) - len(set(retrieved)))
        ),
    )


def _mean(values: Iterable[float]) -> float:
    collected = list(values)
    return sum(collected) / len(collected)
