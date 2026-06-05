"""In-memory storage adapters for tests and local scaffolding."""

from __future__ import annotations

from copy import deepcopy

from ojtflow.core.contracts.events import WorkflowEvent
from ojtflow.core.contracts.enums import WorkflowStatus
from ojtflow.core.contracts.retrieval import (
    RetrievalRelevanceJudgment,
    RetrievalRelevanceJudgmentWrite,
)
from ojtflow.core.contracts.storage import DatasetRecord
from ojtflow.core.contracts.summary import WorkflowStats, WorkflowSummaryPage
from ojtflow.core.contracts.workflow import WorkflowState
from ojtflow.core.errors import NotFoundError
from ojtflow.core.ids import new_id
from ojtflow.core.time import utc_now
from ojtflow.data_tools.hashing import sha256_bytes, sha256_text
from ojtflow.infrastructure.storage.summary import filter_sort_page_summaries, workflow_stats


class InMemoryDatasetStore:
    """Stores text by storage ref."""

    def __init__(self) -> None:
        self._text_by_ref: dict[str, str] = {}
        self._bytes_by_ref: dict[str, bytes] = {}
        self._records: dict[str, DatasetRecord] = {}

    def put_text(
        self,
        text: str,
        workflow_id: str | None = None,
        source_kind: str = "inline",
        declared_format: str | None = None,
        detected_format: str | None = None,
    ) -> DatasetRecord:
        digest = sha256_text(text)
        dataset_id = f"ds_{digest[:12]}"
        storage_ref = f"memory://datasets/{dataset_id}"
        record = DatasetRecord(
            dataset_id=dataset_id,
            workflow_id=workflow_id,
            source_kind=source_kind,
            declared_format=declared_format,
            detected_format=detected_format,
            byte_size=len(text.encode("utf-8")),
            sha256=digest,
            storage_ref=storage_ref,
        )
        self._text_by_ref[storage_ref] = text
        self._records[storage_ref] = record
        return record

    def put_bytes(
        self,
        data: bytes,
        workflow_id: str | None = None,
        source_kind: str = "binary",
        filename: str | None = None,
        declared_format: str | None = None,
        detected_format: str | None = None,
    ) -> DatasetRecord:
        digest = sha256_bytes(data)
        dataset_id = f"ds_{digest[:12]}"
        storage_ref = f"memory://datasets/{dataset_id}"
        record = DatasetRecord(
            dataset_id=dataset_id,
            workflow_id=workflow_id,
            source_kind=source_kind,
            declared_format=declared_format,
            detected_format=detected_format,
            byte_size=len(data),
            sha256=digest,
            storage_ref=storage_ref,
        )
        self._bytes_by_ref[storage_ref] = bytes(data)
        self._records[storage_ref] = record
        return record

    def get_text(self, storage_ref: str) -> str:
        try:
            return self._text_by_ref[storage_ref]
        except KeyError as exc:
            raise NotFoundError(f"Dataset not found: {storage_ref}") from exc


class InMemoryWorkflowRepository:
    """Workflow repository for local tests and API demos."""

    def __init__(self) -> None:
        self._workflows: dict[str, WorkflowState] = {}

    def save(self, workflow: WorkflowState) -> None:
        self._workflows[workflow.workflow_id] = deepcopy(workflow)

    def get(self, workflow_id: str) -> WorkflowState:
        try:
            return deepcopy(self._workflows[workflow_id])
        except KeyError as exc:
            raise NotFoundError(f"Workflow not found: {workflow_id}") from exc

    def find_by_review_id(self, review_id: str) -> WorkflowState:
        for workflow in self._workflows.values():
            if workflow.review and workflow.review.review_id == review_id:
                return deepcopy(workflow)
        raise NotFoundError(f"Review not found: {review_id}")

    def list(
        self,
        status: WorkflowStatus | None = None,
        limit: int = 50,
        owner_user_id: str | None = None,
    ) -> list[WorkflowState]:
        workflows = list(self._workflows.values())
        if owner_user_id is not None:
            workflows = [
                workflow for workflow in workflows
                if workflow.owner_user_id == owner_user_id
            ]
        if status:
            workflows = [workflow for workflow in workflows if workflow.status == status]
        workflows.sort(key=lambda workflow: workflow.updated_at, reverse=True)
        return [deepcopy(workflow) for workflow in workflows[:limit]]

    def list_summary(
        self,
        status: WorkflowStatus | None = None,
        q: str | None = None,
        page: int = 1,
        page_size: int = 25,
        sort: str = "updated_at",
        direction: str = "desc",
        reviews_only: bool = False,
        review_status: str | None = None,
        owner_user_id: str | None = None,
    ) -> WorkflowSummaryPage:
        return filter_sort_page_summaries(
            [deepcopy(workflow) for workflow in self._workflows.values()],
            status=status,
            q=q,
            page=page,
            page_size=page_size,
            sort=sort,
            direction=direction,
            reviews_only=reviews_only,
            review_status=review_status,
            owner_user_id=owner_user_id,
        )

    def stats(self, owner_user_id: str | None = None) -> WorkflowStats:
        return workflow_stats(
            [deepcopy(workflow) for workflow in self._workflows.values()],
            owner_user_id=owner_user_id,
        )


class InMemoryEventRepository:
    """Append-only in-memory workflow event store."""

    def __init__(self) -> None:
        self._events: list[WorkflowEvent] = []

    def append(self, event: WorkflowEvent) -> None:
        self._events.append(deepcopy(event))

    def list_for_workflow(self, workflow_id: str) -> list[WorkflowEvent]:
        return [deepcopy(event) for event in self._events if event.workflow_id == workflow_id]


class InMemoryRetrievalJudgmentRepository:
    """User-scoped in-memory retrieval relevance judgments."""

    def __init__(self) -> None:
        self._judgments: dict[str, RetrievalRelevanceJudgment] = {}

    def upsert(
        self,
        *,
        owner_user_id: str,
        query_hash: str,
        write: RetrievalRelevanceJudgmentWrite,
    ) -> RetrievalRelevanceJudgment:
        existing = next(
            (
                judgment
                for judgment in self._judgments.values()
                if judgment.owner_user_id == owner_user_id
                and judgment.query_hash == query_hash
                and judgment.evidence_id == write.evidence_id
            ),
            None,
        )
        now = utc_now().isoformat()
        judgment = RetrievalRelevanceJudgment(
            **write.model_dump(),
            judgment_id=existing.judgment_id if existing else new_id("rj"),
            owner_user_id=owner_user_id,
            query_hash=query_hash,
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )
        self._judgments[judgment.judgment_id] = deepcopy(judgment)
        return deepcopy(judgment)

    def list(
        self,
        *,
        owner_user_id: str,
        query_hash: str | None = None,
        run_id: str | None = None,
        evidence_id: str | None = None,
        limit: int = 500,
    ) -> list[RetrievalRelevanceJudgment]:
        judgments = [
            judgment
            for judgment in self._judgments.values()
            if judgment.owner_user_id == owner_user_id
            and (query_hash is None or judgment.query_hash == query_hash)
            and (run_id is None or judgment.run_id == run_id)
            and (evidence_id is None or judgment.evidence_id == evidence_id)
        ]
        judgments.sort(key=lambda judgment: judgment.updated_at, reverse=True)
        return [deepcopy(judgment) for judgment in judgments[: max(1, min(limit, 1000))]]

    def delete(self, *, owner_user_id: str, judgment_id: str) -> None:
        judgment = self._judgments.get(judgment_id)
        if not judgment or judgment.owner_user_id != owner_user_id:
            raise NotFoundError(f"Retrieval judgment not found: {judgment_id}")
        del self._judgments[judgment_id]
