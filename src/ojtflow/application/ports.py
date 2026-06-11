"""Ports implemented by infrastructure adapters."""

from __future__ import annotations

from datetime import datetime
from collections.abc import AsyncIterator
from typing import Any, Protocol

from ojtflow.core.contracts.auth import (
    AuthenticatedSession,
    GoogleIdentityProfile,
    SessionRecord,
    UserRecord,
)
from ojtflow.core.contracts.artifacts import ParsingPipelineTrace, UploadedArtifact
from ojtflow.core.contracts.assistant import (
    AssistantChatMessage,
    AssistantChatSessionDetail,
    AssistantChatSessionSummary,
    AssistantPlan,
    AssistantMessageRole,
    AssistantStreamReplay,
    AssistantToolSpec,
)
from ojtflow.core.contracts.events import WorkflowEvent
from ojtflow.core.contracts.evidence import Evidence
from ojtflow.core.contracts.enums import WorkflowStatus
from ojtflow.core.contracts.jobs import BackgroundJob, JobError, JobType
from ojtflow.core.contracts.retrieval import (
    RetrievalIntegrityReport,
    RetrievalPlan,
    RetrievalPackage,
    RetrievalQuery,
    RetrievalRelevanceJudgment,
    RetrievalRelevanceJudgmentWrite,
    RetrievalSource,
)
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

    def list_records(self, limit: int = 1000) -> list[DatasetRecord]: ...


class UploadedArtifactRepository(Protocol):
    def put_bytes(
        self,
        *,
        owner_user_id: str,
        filename: str,
        mime_type: str,
        data: bytes,
        source: str = "upload",
        metadata: dict[str, Any] | None = None,
    ) -> UploadedArtifact: ...

    def get(self, *, owner_user_id: str, artifact_id: str) -> UploadedArtifact: ...

    def get_bytes(self, *, owner_user_id: str, artifact_id: str) -> bytes: ...

    def list(
        self,
        *,
        owner_user_id: str,
        limit: int = 100,
    ) -> list[UploadedArtifact]: ...

    def append_trace(self, trace: ParsingPipelineTrace) -> ParsingPipelineTrace: ...

    def list_traces(
        self,
        *,
        owner_user_id: str,
        artifact_id: str,
    ) -> list[ParsingPipelineTrace]: ...


class DocumentExtractor(Protocol):
    def extract(
        self,
        *,
        data: bytes,
        filename: str,
        prefer: str = "auto",
    ) -> Any: ...


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
    def plan(self, query: RetrievalQuery) -> RetrievalPlan: ...

    def search(self, query: RetrievalQuery) -> RetrievalPackage: ...

    def list_sources(self) -> list[RetrievalSource]: ...

    def reindex(self, *, include_seeded: bool = True, include_corpus: bool = True) -> dict: ...

    def integrity_report(
        self,
        *,
        include_seeded: bool = True,
        include_corpus: bool = False,
    ) -> RetrievalIntegrityReport: ...


class RetrievalJudgmentRepository(Protocol):
    def upsert(
        self,
        *,
        owner_user_id: str,
        query_hash: str,
        write: RetrievalRelevanceJudgmentWrite,
    ) -> RetrievalRelevanceJudgment: ...

    def list(
        self,
        *,
        owner_user_id: str,
        query_hash: str | None = None,
        run_id: str | None = None,
        evidence_id: str | None = None,
        limit: int = 500,
    ) -> list[RetrievalRelevanceJudgment]: ...

    def delete(self, *, owner_user_id: str, judgment_id: str) -> None: ...


class AssistantSessionRepository(Protocol):
    def create_session(self, *, owner_user_id: str, title: str) -> AssistantChatSessionSummary: ...

    def list_sessions(
        self,
        *,
        owner_user_id: str,
        include_archived: bool = False,
        limit: int = 100,
        q: str | None = None,
    ) -> list[AssistantChatSessionSummary]: ...

    def get_session(
        self,
        *,
        owner_user_id: str,
        session_id: str,
    ) -> AssistantChatSessionDetail: ...

    def rename_session(
        self,
        *,
        owner_user_id: str,
        session_id: str,
        title: str,
    ) -> AssistantChatSessionSummary: ...

    def archive_session(
        self,
        *,
        owner_user_id: str,
        session_id: str,
    ) -> AssistantChatSessionSummary: ...

    def delete_session(self, *, owner_user_id: str, session_id: str) -> None: ...

    def append_message(
        self,
        *,
        owner_user_id: str,
        session_id: str,
        role: AssistantMessageRole,
        content: str,
        payload: dict[str, Any] | None = None,
        workflow_refs: list[str] | None = None,
    ) -> AssistantChatMessage: ...

    def append_stream_replay(
        self,
        *,
        replay: AssistantStreamReplay,
    ) -> AssistantStreamReplay: ...

    def list_stream_replays(
        self,
        *,
        owner_user_id: str,
        session_id: str,
    ) -> list[AssistantStreamReplay]: ...


class BackgroundJobRepository(Protocol):
    def create(
        self,
        *,
        owner_user_id: str,
        job_type: JobType,
        input: dict[str, Any],
        max_attempts: int = 1,
    ) -> BackgroundJob: ...

    def get(self, *, owner_user_id: str, job_id: str) -> BackgroundJob: ...

    def list(
        self,
        *,
        owner_user_id: str,
        status: str | None = None,
        job_type: str | None = None,
        limit: int = 100,
    ) -> list[BackgroundJob]: ...

    def mark_running(self, *, owner_user_id: str, job_id: str) -> BackgroundJob: ...

    def mark_succeeded(
        self,
        *,
        owner_user_id: str,
        job_id: str,
        output: dict[str, Any],
    ) -> BackgroundJob: ...

    def mark_failed(
        self,
        *,
        owner_user_id: str,
        job_id: str,
        error: JobError,
    ) -> BackgroundJob: ...


class AssistantPlanner(Protocol):
    @property
    def model_name(self) -> str: ...

    async def plan(
        self,
        *,
        message: str,
        context: dict,
        tools: list[AssistantToolSpec],
        max_tool_calls: int,
    ) -> AssistantPlan: ...

    def plan_stream(
        self,
        *,
        message: str,
        context: dict,
        tools: list[AssistantToolSpec],
        max_tool_calls: int,
    ) -> AsyncIterator[dict[str, Any]]: ...

    async def synthesize(
        self,
        *,
        message: str,
        context: dict[str, Any],
        plan: AssistantPlan,
        tool_results: list[dict[str, Any]],
        findings: list[dict[str, Any]],
        evidence_summary: list[dict[str, Any]],
    ) -> str: ...

    def synthesize_stream(
        self,
        *,
        message: str,
        context: dict[str, Any],
        plan: AssistantPlan,
        tool_results: list[dict[str, Any]],
        findings: list[dict[str, Any]],
        evidence_summary: list[dict[str, Any]],
    ) -> AsyncIterator[str]: ...
