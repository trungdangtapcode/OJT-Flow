"""Ports implemented by infrastructure adapters."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from ojtflow.core.contracts.auth import (
    AuthenticatedSession,
    GoogleIdentityProfile,
    SessionRecord,
    UserRecord,
)
from ojtflow.core.contracts.events import WorkflowEvent
from ojtflow.core.contracts.evidence import Evidence
from ojtflow.core.contracts.enums import WorkflowStatus
from ojtflow.core.contracts.retrieval import RetrievalPackage, RetrievalQuery, RetrievalSource
from ojtflow.core.contracts.storage import DatasetRecord
from ojtflow.core.contracts.summary import WorkflowStats, WorkflowSummaryPage
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

    def list(
        self,
        status: WorkflowStatus | None = None,
        limit: int = 50,
        owner_user_id: str | None = None,
    ) -> list[WorkflowState]: ...

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
    ) -> WorkflowSummaryPage: ...

    def stats(self, owner_user_id: str | None = None) -> WorkflowStats: ...


class EventRepository(Protocol):
    def append(self, event: WorkflowEvent) -> None: ...

    def list_for_workflow(self, workflow_id: str) -> list[WorkflowEvent]: ...


class KnowledgeRepository(Protocol):
    def get_schema(self, schema_id: str | None) -> dict | None: ...

    def list_schemas(self) -> list[dict]: ...

    def search(self, query: str, *, top_k: int = 5) -> list[Evidence]: ...


class IdentityProvider(Protocol):
    @property
    def is_configured(self) -> bool: ...

    def authorization_url(self, redirect_uri: str, state: str) -> str: ...

    async def exchange_code_for_profile(
        self,
        code: str,
        redirect_uri: str,
    ) -> GoogleIdentityProfile: ...


class AuthRepository(Protocol):
    def upsert_google_user(self, profile: GoogleIdentityProfile) -> UserRecord: ...

    def create_session(
        self,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> SessionRecord: ...

    def get_active_session(
        self,
        token_hash: str,
        now: datetime,
    ) -> AuthenticatedSession | None: ...

    def touch_session(self, token_hash: str) -> None: ...

    def revoke_session(self, token_hash: str) -> None: ...


class SessionCache(Protocol):
    def set_session(
        self,
        token_hash: str,
        payload: dict,
        ttl_seconds: int,
    ) -> None: ...

    def get_session(self, token_hash: str) -> dict | None: ...

    def delete_session(self, token_hash: str) -> None: ...

    def set_oauth_state(
        self,
        state: str,
        ttl_seconds: int,
        payload: dict | None = None,
    ) -> None: ...

    def consume_oauth_state(self, state: str) -> dict | None: ...

class RetrievalRepository(Protocol):
    def search(self, query: RetrievalQuery) -> RetrievalPackage: ...

    def list_sources(self) -> list[RetrievalSource]: ...

    def reindex(self, *, include_seeded: bool = True, include_corpus: bool = True) -> dict: ...
