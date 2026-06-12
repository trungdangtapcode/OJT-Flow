"""Active-learning queue for retrieval benchmark curation."""

from __future__ import annotations

import json
from typing import Any

from ojtflow.application.ports import RetrievalActiveLearningRepository
from ojtflow.core.contracts.retrieval import (
    RetrievalActiveLearningCandidate,
    RetrievalActiveLearningCandidateUpdate,
    RetrievalActiveLearningCandidateWrite,
    RetrievalActiveLearningPriority,
    RetrievalActiveLearningSourceKind,
    RetrievalActiveLearningStatus,
    RetrievalActiveLearningSummary,
    RetrievalJudgmentEvaluationResult,
    RetrievalRelevanceJudgment,
)
from ojtflow.data_tools.hashing import sha256_text


ACTIVE_LEARNING_SOURCE_KINDS: tuple[RetrievalActiveLearningSourceKind, ...] = (
    "low_confidence_retrieval",
    "unsupported_claim",
    "reviewer_correction",
    "weak_support",
    "negative_judgment",
)
ACTIVE_LEARNING_STATUSES: tuple[RetrievalActiveLearningStatus, ...] = (
    "open",
    "accepted",
    "rejected",
    "promoted",
    "archived",
)
ACTIVE_LEARNING_PRIORITIES: tuple[RetrievalActiveLearningPriority, ...] = (
    "low",
    "normal",
    "high",
    "critical",
)
NEGATIVE_JUDGMENT_VALUES = {
    "irrelevant",
    "not_relevant",
    "unsafe",
    "stale",
    "source_policy_blocked",
}


class RetrievalActiveLearningService:
    """Coordinates durable retrieval cases that should become benchmark fixtures."""

    def __init__(self, repository: RetrievalActiveLearningRepository) -> None:
        self.repository = repository

    def enqueue(
        self,
        *,
        owner_user_id: str,
        write: RetrievalActiveLearningCandidateWrite,
    ) -> RetrievalActiveLearningCandidate:
        query_hash = sha256_text(write.query)
        candidate_key = candidate_key_for_write(query_hash=query_hash, write=write)
        return self.repository.upsert(
            owner_user_id=owner_user_id,
            query_hash=query_hash,
            candidate_key=candidate_key,
            write=write,
        )

    def list(
        self,
        *,
        owner_user_id: str,
        status: RetrievalActiveLearningStatus | None = None,
        source_kind: RetrievalActiveLearningSourceKind | None = None,
        priority: RetrievalActiveLearningPriority | None = None,
        query: str | None = None,
        limit: int = 500,
    ) -> list[RetrievalActiveLearningCandidate]:
        return self.repository.list(
            owner_user_id=owner_user_id,
            status=status,
            source_kind=source_kind,
            priority=priority,
            query_hash=sha256_text(query) if query else None,
            limit=limit,
        )

    def summary(
        self,
        *,
        owner_user_id: str,
        limit: int = 1000,
    ) -> RetrievalActiveLearningSummary:
        candidates = self.repository.list(
            owner_user_id=owner_user_id,
            limit=limit,
        )
        status_counts = {
            status: sum(1 for candidate in candidates if candidate.status == status)
            for status in ACTIVE_LEARNING_STATUSES
        }
        source_kind_counts = {
            source_kind: sum(
                1 for candidate in candidates if candidate.source_kind == source_kind
            )
            for source_kind in ACTIVE_LEARNING_SOURCE_KINDS
        }
        return RetrievalActiveLearningSummary(
            total_count=len(candidates),
            open_count=status_counts["open"],
            accepted_count=status_counts["accepted"],
            rejected_count=status_counts["rejected"],
            promoted_count=status_counts["promoted"],
            archived_count=status_counts["archived"],
            critical_count=sum(1 for candidate in candidates if candidate.priority == "critical"),
            high_count=sum(1 for candidate in candidates if candidate.priority == "high"),
            source_kind_counts=source_kind_counts,
            latest_updated_at=max(
                (candidate.updated_at for candidate in candidates),
                default=None,
            ),
            sample_limit=max(1, min(limit, 1000)),
        )

    def update(
        self,
        *,
        owner_user_id: str,
        candidate_id: str,
        reviewer_user_id: str | None,
        update: RetrievalActiveLearningCandidateUpdate,
    ) -> RetrievalActiveLearningCandidate:
        return self.repository.update(
            owner_user_id=owner_user_id,
            candidate_id=candidate_id,
            reviewer_user_id=reviewer_user_id,
            update=update,
        )

    def enqueue_from_judgment(
        self,
        *,
        owner_user_id: str,
        judgment: RetrievalRelevanceJudgment,
    ) -> RetrievalActiveLearningCandidate | None:
        if judgment.value == "relevant":
            return None
        source_kind: RetrievalActiveLearningSourceKind = (
            "negative_judgment"
            if judgment.value in NEGATIVE_JUDGMENT_VALUES
            else "reviewer_correction"
        )
        priority = priority_for_judgment_value(judgment.value)
        return self.enqueue(
            owner_user_id=owner_user_id,
            write=RetrievalActiveLearningCandidateWrite(
                source_kind=source_kind,
                query=judgment.query,
                trigger_reason=f"Reviewer labeled evidence {judgment.value}.",
                priority=priority,
                evidence_id=judgment.evidence_id,
                source_id=judgment.source_id,
                source_type=judgment.source_type,
                source_version=judgment.source_version,
                run_id=judgment.run_id,
                judgment_id=judgment.judgment_id,
                suggested_expected_evidence_ids=(
                    [judgment.evidence_id] if judgment.value == "partial" else []
                ),
                metadata={
                    "judgment_value": judgment.value,
                    "rating": judgment.rating,
                    "search_signature": judgment.search_signature,
                },
            ),
        )

    def enqueue_from_evaluation(
        self,
        *,
        owner_user_id: str,
        evaluation: RetrievalJudgmentEvaluationResult,
    ) -> list[RetrievalActiveLearningCandidate]:
        candidates: list[RetrievalActiveLearningCandidate] = []
        if (
            evaluation.coverage_at_k >= evaluation.evaluation_readiness.min_coverage_at_k
            and evaluation.hit_rate_at_k > 0
            and evaluation.not_relevant_count == 0
        ):
            return candidates
        priority: RetrievalActiveLearningPriority = (
            "high" if evaluation.hit_rate_at_k == 0 and evaluation.judged_count else "normal"
        )
        evidence_ids = evaluation.unjudged_evidence_ids[:10] or evaluation.ranked_evidence_ids[:10]
        for evidence_id in evidence_ids:
            candidates.append(
                self.enqueue(
                    owner_user_id=owner_user_id,
                    write=RetrievalActiveLearningCandidateWrite(
                        source_kind="low_confidence_retrieval",
                        query=evaluation.query,
                        trigger_reason="Retrieval evaluation had weak judgment coverage or no positive hit.",
                        priority=priority,
                        evidence_id=evidence_id,
                        benchmark_metadata={
                            "cutoff": evaluation.cutoff,
                            "coverage_at_k": evaluation.coverage_at_k,
                            "hit_rate_at_k": evaluation.hit_rate_at_k,
                            "precision_at_k": evaluation.precision_at_k,
                        },
                        metadata={
                            "evaluation_readiness": evaluation.evaluation_readiness.model_dump(),
                            "judgment_ids": evaluation.judgment_ids,
                            "unjudged_count": evaluation.unjudged_count,
                            "not_relevant_count": evaluation.not_relevant_count,
                        },
                    ),
                )
            )
        return candidates


def priority_for_judgment_value(value: str) -> RetrievalActiveLearningPriority:
    if value in {"unsafe", "source_policy_blocked"}:
        return "critical"
    if value == "stale":
        return "high"
    if value == "partial":
        return "low"
    return "normal"


def candidate_key_for_write(
    *,
    query_hash: str,
    write: RetrievalActiveLearningCandidateWrite,
) -> str:
    identity: dict[str, Any] = {
        "claim_id": write.claim_id,
        "evidence_id": write.evidence_id,
        "judgment_id": write.judgment_id,
        "query_hash": query_hash,
        "run_id": write.run_id,
        "source_id": write.source_id,
        "source_kind": write.source_kind,
        "support_status": write.support_status,
        "workflow_id": write.workflow_id,
    }
    if not any(
        value
        for key, value in identity.items()
        if key not in {"query_hash", "source_kind"}
    ):
        identity["trigger_reason_hash"] = sha256_text(write.trigger_reason)
    payload = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    return sha256_text(payload)
