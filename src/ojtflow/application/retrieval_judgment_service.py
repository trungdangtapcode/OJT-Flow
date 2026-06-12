"""Application service for durable retrieval relevance judgments."""

from __future__ import annotations

import math
from collections.abc import Iterable

from ojtflow.application.ports import RetrievalJudgmentRepository
from ojtflow.application.retrieval_active_learning_service import (
    RetrievalActiveLearningService,
)
from ojtflow.application.retrieval_evaluation_policy import (
    RetrievalEvaluationPolicyRule,
    recommendations_from_policy,
)
from ojtflow.core.contracts.enums import EvidenceSourceType
from ojtflow.core.contracts.retrieval import (
    RetrievalEvaluationReadiness,
    RetrievalJudgmentEvaluationResult,
    RetrievalJudgmentValue,
    RetrievalRelevanceJudgment,
    RetrievalRelevanceJudgmentSummary,
    RetrievalRelevanceJudgmentWrite,
)
from ojtflow.data_tools.hashing import sha256_text


NON_RELEVANT_JUDGMENT_VALUES = {
    "irrelevant",
    "not_relevant",
    "unsafe",
    "stale",
    "source_policy_blocked",
}
RETRIEVAL_JUDGMENT_VALUES = (
    "relevant",
    "partial",
    "irrelevant",
    "not_relevant",
    "unsafe",
    "stale",
    "source_policy_blocked",
)


class RetrievalJudgmentService:
    """Coordinates user-scoped relevance judgments for retrieval evaluation."""

    MIN_EVALUATION_JUDGED_COUNT = 3
    MIN_EVALUATION_COVERAGE_AT_K = 0.6

    def __init__(
        self,
        repository: RetrievalJudgmentRepository,
        active_learning_service: RetrievalActiveLearningService | None = None,
        evaluation_policy_rules: Iterable[RetrievalEvaluationPolicyRule] = (),
    ) -> None:
        self.repository = repository
        self.active_learning_service = active_learning_service
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
        judgment = self.repository.upsert(
            owner_user_id=owner_user_id,
            query_hash=query_hash(write.query),
            write=write,
        )
        if self.active_learning_service is not None:
            self.active_learning_service.enqueue_from_judgment(
                owner_user_id=owner_user_id,
                judgment=judgment,
            )
        return judgment

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
            value: sum(1 for judgment in judgments if judgment.value == value)
            for value in RETRIEVAL_JUDGMENT_VALUES
        }
        not_relevant_count = sum(
            count
            for value, count in value_counts.items()
            if value in NON_RELEVANT_JUDGMENT_VALUES
        )
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
            not_relevant_count=not_relevant_count,
            unsafe_count=value_counts["unsafe"],
            stale_count=value_counts["stale"],
            source_policy_blocked_count=value_counts["source_policy_blocked"],
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
            1
            for judgment in ranked_judgments
            if judgment.value in NON_RELEVANT_JUDGMENT_VALUES
        )
        unsafe_count = sum(1 for judgment in ranked_judgments if judgment.value == "unsafe")
        stale_count = sum(1 for judgment in ranked_judgments if judgment.value == "stale")
        source_policy_blocked_count = sum(
            1
            for judgment in ranked_judgments
            if judgment.value == "source_policy_blocked"
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
        hit_rate_at_k = 1.0 if positive_count else 0.0
        precision_at_k = round(positive_count / top_k, 6)
        judged_precision = (
            round(positive_count / judged_count, 6) if judged_count else None
        )
        average_precision_at_k = round(
            _average_precision_at_k(top_ids, judgments_by_evidence, positive_judgments_total),
            6,
        )
        mrr_at_k = round(_mean_reciprocal_rank_at_k(top_ids, judgments_by_evidence), 6)
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
            "hit_rate_at_k": hit_rate_at_k,
            "judged_count": judged_count,
            "judged_precision": judged_precision,
            "mrr_at_k": mrr_at_k,
            "ndcg_at_k": ndcg_at_k,
            "not_relevant_count": not_relevant_count,
            "partial_count": partial_count,
            "positive_count": positive_count,
            "precision_at_k": precision_at_k,
            "relevant_count": relevant_count,
            "source_policy_blocked_count": source_policy_blocked_count,
            "stale_count": stale_count,
            "unsafe_count": unsafe_count,
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
            unsafe_count=unsafe_count,
            stale_count=stale_count,
            source_policy_blocked_count=source_policy_blocked_count,
            coverage_at_k=coverage_at_k,
            hit_rate_at_k=hit_rate_at_k,
            precision_at_k=precision_at_k,
            judged_precision=judged_precision,
            average_precision_at_k=average_precision_at_k,
            mrr_at_k=mrr_at_k,
            ndcg_at_k=ndcg_at_k,
            average_rating=average_rating,
            unjudged_evidence_ids=unjudged_ids,
            judgment_ids=[judgment.judgment_id for judgment in ranked_judgments],
            evaluation_readiness=evaluation_readiness(
                judged_count=judged_count,
                coverage_at_k=coverage_at_k,
                min_judged_count=self.MIN_EVALUATION_JUDGED_COUNT,
                min_coverage_at_k=self.MIN_EVALUATION_COVERAGE_AT_K,
                unjudged_count=len(unjudged_ids),
            ),
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


def evaluation_readiness(
    *,
    coverage_at_k: float,
    judged_count: int,
    min_coverage_at_k: float,
    min_judged_count: int,
    unjudged_count: int,
) -> RetrievalEvaluationReadiness:
    if judged_count == 0:
        return RetrievalEvaluationReadiness(
            status="unlabeled",
            label="No judgments yet",
            message="Label ranked evidence before using retrieval metrics for tuning.",
            min_judged_count=min_judged_count,
            min_coverage_at_k=min_coverage_at_k,
        )
    if judged_count < min_judged_count or coverage_at_k < min_coverage_at_k:
        return RetrievalEvaluationReadiness(
            status="low_confidence",
            label="Low-confidence metrics",
            message=(
                f"Metrics need at least {min_judged_count} judged hits and "
                f"{int(min_coverage_at_k * 100)}% Coverage@k before ranking quality is reliable. "
                f"{unjudged_count} ranked hit(s) remain unjudged."
            ),
            min_judged_count=min_judged_count,
            min_coverage_at_k=min_coverage_at_k,
        )
    if unjudged_count:
        return RetrievalEvaluationReadiness(
            status="usable_with_gaps",
            label="Usable with gaps",
            message=(
                "Enough labels exist for directional tuning, but unjudged hits can still "
                "change rank-aware metrics."
            ),
            min_judged_count=min_judged_count,
            min_coverage_at_k=min_coverage_at_k,
        )
    return RetrievalEvaluationReadiness(
        status="ready",
        label="Ready for tuning",
        message="The ranked set is fully judged for the current cutoff.",
        min_judged_count=min_judged_count,
        min_coverage_at_k=min_coverage_at_k,
    )


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


def _mean_reciprocal_rank_at_k(
    ranked_evidence_ids: list[str],
    judgments_by_evidence: dict[str, RetrievalRelevanceJudgment],
) -> float:
    for rank, evidence_id in enumerate(ranked_evidence_ids, start=1):
        judgment = judgments_by_evidence.get(evidence_id)
        if judgment and judgment.rating > 0:
            return 1.0 / rank
    return 0.0


def _discounted_cumulative_gain(ratings: list[int]) -> float:
    total = 0.0
    for index, rating in enumerate(ratings, start=1):
        if rating <= 0:
            continue
        total += (2**rating - 1) / math.log2(index + 1)
    return total


def _ordered_unique(values) -> list[str]:
    return list(dict.fromkeys(values))
