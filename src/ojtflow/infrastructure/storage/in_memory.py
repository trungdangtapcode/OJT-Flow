"""In-memory storage adapters for tests and local scaffolding."""

from __future__ import annotations

from copy import deepcopy

from ojtflow.core.contracts.events import WorkflowEvent
from ojtflow.core.contracts.storage import DatasetRecord
from ojtflow.core.contracts.workflow import WorkflowState
from ojtflow.core.errors import NotFoundError
from ojtflow.data_tools.hashing import sha256_text


class InMemoryDatasetStore:
    """Stores text by storage ref."""

    def __init__(self) -> None:
        self._text_by_ref: dict[str, str] = {}
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


class InMemoryEventRepository:
    """Append-only in-memory workflow event store."""

    def __init__(self) -> None:
        self._events: list[WorkflowEvent] = []

    def append(self, event: WorkflowEvent) -> None:
        self._events.append(deepcopy(event))

    def list_for_workflow(self, workflow_id: str) -> list[WorkflowEvent]:
        return [deepcopy(event) for event in self._events if event.workflow_id == workflow_id]

