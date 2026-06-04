"""Application service for durable retrieval relevance judgments."""

from __future__ import annotations

import math
from collections.abc import Iterable

from ojtflow.application.ports import RetrievalJudgmentRepository
from ojtflow.application.retrieval_evaluation_policy import (
    RetrievalEvaluationPolicyRule,
    recommendations_from_policy,
)
from ojtflow.core.contracts.enums import EvidenceSourceType
from ojtflow.core.contracts.retrieval import (
    RetrievalJudgmentEvaluationResult,
    RetrievalJudgmentValue,
    RetrievalRelevanceJudgment,
    RetrievalRelevanceJudgmentSummary,
    RetrievalRelevanceJudgmentWrite,
)
from ojtflow.data_tools.hashing import sha256_text


class RetrievalJudgmentService:
    """Coordinates user-scoped relevance judgments for retrieval evaluation."""

    def __init__(
        self,
        repository: RetrievalJudgmentRepository,
        evaluation_policy_rules: Iterable[RetrievalEvaluationPolicyRule] = (),
    ) -> None:
        self.repository = repository
        self.evaluation_policy_rules = tuple(evaluation_policy_rules)

    def upsert(
        self,
        *,
        owner_user_id: str,
        query: str,
        evidence_id: str,
        value: RetrievalJudgmentValue,
        rating: int | None = None,
        source_id: str | None = None,
        source_type: EvidenceSourceType | None = None,
        source_version: str | None = None,
        run_id: str | None = None,
        search_signature: str | None = None,
        metadata: dict | None = None,
    ) -> RetrievalRelevanceJudgment:
        write = RetrievalRelevanceJudgmentWrite(
            query=query,
            evidence_id=evidence_id,
            value=value,
            rating=rating if rating is not None else rating_from_judgment_value(value),
            source_id=source_id,
            source_type=source_type,
            source_version=source_version,
            run_id=run_id,
            search_signature=search_signature,
            metadata=metadata or {},
        )
        return self.repository.upsert(
            owner_user_id=owner_user_id,
            query_hash=query_hash(write.query),
            write=write,
        )

    def list(
        self,
        *,
        owner_user_id: str,
        query: str | None = None,
        run_id: str | None = None,
        evidence_id: str | None = None,
        limit: int = 500,
    ) -> list[RetrievalRelevanceJudgment]:
        return self.repository.list(
            owner_user_id=owner_user_id,
            query_hash=query_hash(query) if query else None,
            run_id=run_id,
            evidence_id=evidence_id,
            limit=limit,
        )

    def summary(
        self,
        *,
        owner_user_id: str,
        query: str | None = None,
        limit: int = 1000,
    ) -> RetrievalRelevanceJudgmentSummary:
        sample_limit = max(1, min(limit, 1000))
        judgments = self.list(
            owner_user_id=owner_user_id,
            query=query,
            limit=sample_limit,
        )
        value_counts = {
            "relevant": sum(1 for judgment in judgments if judgment.value == "relevant"),
            "partial": sum(1 for judgment in judgments if judgment.value == "partial"),
            "not_relevant": sum(
                1 for judgment in judgments if judgment.value == "not_relevant"
            ),
        }
        source_ids = {
            judgment.source_id
            for judgment in judgments
            if judgment.source_id is not None
        }
        latest = max((judgment.updated_at for judgment in judgments), default=None)
        return RetrievalRelevanceJudgmentSummary(
            total_count=len(judgments),
            query_count=len({judgment.query_hash for judgment in judgments}),
            evidence_count=len({judgment.evidence_id for judgment in judgments}),
            source_count=len(source_ids),
            relevant_count=value_counts["relevant"],
            partial_count=value_counts["partial"],
            not_relevant_count=value_counts["not_relevant"],
            average_rating=(
                round(sum(judgment.rating for judgment in judgments) / len(judgments), 6)
                if judgments
                else None
            ),
            latest_updated_at=latest,
            sample_limit=sample_limit,
            value_counts=value_counts,
        )

    def evaluate_ranked_results(
        self,
        *,
        owner_user_id: str,
        query: str,
        ranked_evidence_ids: list[str],
        cutoff: int | None = None,
    ) -> RetrievalJudgmentEvaluationResult:
        normalized_ranked_ids = _ordered_unique(
            evidence_id.strip() for evidence_id in ranked_evidence_ids if evidence_id.strip()
        )
        top_k = max(
            1,
            min(cutoff or len(normalized_ranked_ids) or 1, len(normalized_ranked_ids) or 1, 100),
        )
        top_ids = normalized_ranked_ids[:top_k]
        judgments = self.list(
            owner_user_id=owner_user_id,
            query=query,
            limit=1000,
        )
        judgments_by_evidence = {judgment.evidence_id: judgment for judgment in judgments}
        ranked_judgments = [
            judgments_by_evidence[evidence_id]
            for evidence_id in top_ids
            if evidence_id in judgments_by_evidence
        ]
        ranked_ratings = [
            judgments_by_evidence[evidence_id].rating
            if evidence_id in judgments_by_evidence
            else 0
            for evidence_id in top_ids
        ]
        relevant_count = sum(1 for judgment in ranked_judgments if judgment.value == "relevant")
        partial_count = sum(1 for judgment in ranked_judgments if judgment.value == "partial")
        not_relevant_count = sum(
            1 for judgment in ranked_judgments if judgment.value == "not_relevant"
        )
        positive_count = relevant_count + partial_count
        judged_count = len(ranked_judgments)
        unjudged_ids = [
            evidence_id for evidence_id in top_ids if evidence_id not in judgments_by_evidence
        ]
        positive_judgments_total = sum(1 for judgment in judgments if judgment.rating > 0)
        ideal_ratings = sorted(
            (judgment.rating for judgment in judgments),
            reverse=True,
        )[:top_k]
        ideal_dcg = _discounted_cumulative_gain(ideal_ratings)
        coverage_at_k = round(judged_count / top_k, 6)
        precision_at_k = round(positive_count / top_k, 6)
        judged_precision = (
            round(positive_count / judged_count, 6) if judged_count else None
        )
        average_precision_at_k = round(
            _average_precision_at_k(top_ids, judgments_by_evidence, positive_judgments_total),
            6,
        )
        ndcg_at_k = (
            round(_discounted_cumulative_gain(ranked_ratings) / ideal_dcg, 6)
            if ideal_dcg
            else None
        )
        average_rating = (
            round(sum(judgment.rating for judgment in ranked_judgments) / judged_count, 6)
            if judged_count
            else None
        )
        recommendation_context = {
            "average_precision_at_k": average_precision_at_k,
            "average_rating": average_rating,
            "coverage_at_k": coverage_at_k,
            "cutoff": top_k,
            "judged_count": judged_count,
            "judged_precision": judged_precision,
            "ndcg_at_k": ndcg_at_k,
            "not_relevant_count": not_relevant_count,
            "partial_count": partial_count,
            "positive_count": positive_count,
            "precision_at_k": precision_at_k,
            "relevant_count": relevant_count,
            "unjudged_count": len(unjudged_ids),
        }
        return RetrievalJudgmentEvaluationResult(
            query=query,
            ranked_evidence_ids=top_ids,
            cutoff=top_k,
            judged_count=judged_count,
            unjudged_count=len(unjudged_ids),
            relevant_count=relevant_count,
            partial_count=partial_count,
            not_relevant_count=not_relevant_count,
            coverage_at_k=coverage_at_k,
            precision_at_k=precision_at_k,
            judged_precision=judged_precision,
            average_precision_at_k=average_precision_at_k,
            ndcg_at_k=ndcg_at_k,
            average_rating=average_rating,
            unjudged_evidence_ids=unjudged_ids,
            judgment_ids=[judgment.judgment_id for judgment in ranked_judgments],
            recommendations=recommendations_from_policy(
                rules=self.evaluation_policy_rules,
                context=recommendation_context,
                unjudged_evidence_ids=unjudged_ids,
            ),
        )

    def delete(self, *, owner_user_id: str, judgment_id: str) -> None:
        self.repository.delete(owner_user_id=owner_user_id, judgment_id=judgment_id)


def query_hash(query: str) -> str:
    """Stable query hash for lookup without making query text the storage key."""

    return sha256_text(query.strip())


def rating_from_judgment_value(value: RetrievalJudgmentValue) -> int:
    """Default graded relevance rating for the operator judgment controls."""

    if value == "relevant":
        return 3
    if value == "partial":
        return 1
    return 0


def _average_precision_at_k(
    ranked_evidence_ids: list[str],
    judgments_by_evidence: dict[str, RetrievalRelevanceJudgment],
    positive_judgment_count: int,
) -> float:
    if positive_judgment_count == 0:
        return 0.0
    seen_relevant = 0
    precision_sum = 0.0
    for rank, evidence_id in enumerate(ranked_evidence_ids, start=1):
        judgment = judgments_by_evidence.get(evidence_id)
        if not judgment or judgment.rating <= 0:
            continue
        seen_relevant += 1
        precision_sum += seen_relevant / rank
    return precision_sum / positive_judgment_count


def _discounted_cumulative_gain(ratings: list[int]) -> float:
    total = 0.0
    for index, rating in enumerate(ratings, start=1):
        if rating <= 0:
            continue
        total += (2**rating - 1) / math.log2(index + 1)
    return total


def _ordered_unique(values) -> list[str]:
    return list(dict.fromkeys(values))
