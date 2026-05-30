"""Ports implemented by infrastructure adapters."""

from __future__ import annotations

from typing import Protocol

from ojtflow.core.contracts.events import WorkflowEvent
from ojtflow.core.contracts.evidence import Evidence
from ojtflow.core.contracts.enums import WorkflowStatus
from ojtflow.core.contracts.storage import DatasetRecord
from ojtflow.core.contracts.workflow import WorkflowState


class DatasetStore(Protocol):
    def put_text(
        self,
        text: str,
        workflow_id: str | None = None,
        source_kind: str = "inline",
        declared_format: str | None = None,
        detected_format: str | None = None,
    ) -> DatasetRecord: ...

    def put_bytes(
        self,
        data: bytes,
        workflow_id: str | None = None,
        source_kind: str = "binary",
        filename: str | None = None,
        declared_format: str | None = None,
        detected_format: str | None = None,
    ) -> DatasetRecord: ...

    def get_text(self, storage_ref: str) -> str: ...


class WorkflowRepository(Protocol):
    def save(self, workflow: WorkflowState) -> None: ...

    def get(self, workflow_id: str) -> WorkflowState: ...

    def find_by_review_id(self, review_id: str) -> WorkflowState: ...

    def list(self, status: WorkflowStatus | None = None, limit: int = 50) -> list[WorkflowState]: ...


class EventRepository(Protocol):
    def append(self, event: WorkflowEvent) -> None: ...

    def list_for_workflow(self, workflow_id: str) -> list[WorkflowEvent]: ...


class KnowledgeRepository(Protocol):
    def get_schema(self, schema_id: str | None) -> dict | None: ...

    def list_schemas(self) -> list[dict]: ...

    def search(self, query: str, *, top_k: int = 5) -> list[Evidence]: ...
