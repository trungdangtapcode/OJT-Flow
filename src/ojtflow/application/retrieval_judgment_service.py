"""Application service for durable retrieval relevance judgments."""

from __future__ import annotations

from ojtflow.application.ports import RetrievalJudgmentRepository
from ojtflow.core.contracts.enums import EvidenceSourceType
from ojtflow.core.contracts.retrieval import (
    RetrievalJudgmentValue,
    RetrievalRelevanceJudgment,
    RetrievalRelevanceJudgmentSummary,
    RetrievalRelevanceJudgmentWrite,
)
from ojtflow.data_tools.hashing import sha256_text


class RetrievalJudgmentService:
    """Coordinates user-scoped relevance judgments for retrieval evaluation."""

    def __init__(self, repository: RetrievalJudgmentRepository) -> None:
        self.repository = repository

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
