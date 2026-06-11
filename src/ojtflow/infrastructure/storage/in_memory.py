"""In-memory storage adapters for tests and local scaffolding."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from ojtflow.core.audit_hash_chain import audit_chain_scope, link_audit_record
from ojtflow.core.contracts.artifacts import (
    ArtifactAccessEvent,
    ArtifactRetentionPolicy,
    ParsingPipelineTrace,
    UploadedArtifact,
)
from ojtflow.core.contracts.assistant import (
    AssistantChatMessage,
    AssistantChatSessionDetail,
    AssistantChatSessionSummary,
    AssistantMemoryPreference,
    AssistantMessageRole,
    AssistantStreamReplay,
)
from ojtflow.core.contracts.audit import AuditRecord
from ojtflow.core.contracts.events import WorkflowEvent
from ojtflow.core.contracts.enums import WorkflowStatus
from ojtflow.core.contracts.graph import GraphContextRecord
from ojtflow.core.contracts.jobs import BackgroundJob, JobError, JobType
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

    def list_records(self, limit: int = 1000) -> list[DatasetRecord]:
        records = list(self._records.values())
        return [deepcopy(record) for record in records[: max(0, limit)]]


class InMemoryUploadedArtifactRepository:
    """In-memory uploaded artifact metadata and bytes."""

    def __init__(self) -> None:
        self._artifacts: dict[str, UploadedArtifact] = {}
        self._bytes_by_ref: dict[str, bytes] = {}
        self._traces: dict[str, list[ParsingPipelineTrace]] = {}
        self._access_events: dict[str, list[ArtifactAccessEvent]] = {}

    def put_bytes(
        self,
        *,
        owner_user_id: str,
        filename: str,
        mime_type: str,
        data: bytes,
        source: str = "upload",
        retention_policy: ArtifactRetentionPolicy | None = None,
        metadata: dict | None = None,
    ) -> UploadedArtifact:
        digest = sha256_bytes(data)
        duplicate = self._canonical_for_hash(
            owner_user_id=owner_user_id,
            sha256=digest,
            byte_size=len(data),
        )
        extension = Path(filename).suffix.lower()
        storage_ref = (
            duplicate.storage_ref
            if duplicate
            else f"memory://uploads/art_{digest[:12]}{extension or '.bin'}"
        )
        if duplicate is None:
            self._bytes_by_ref[storage_ref] = bytes(data)
        artifact = UploadedArtifact(
            owner_user_id=owner_user_id,
            filename=filename,
            mime_type=mime_type or "application/octet-stream",
            extension=extension,
            byte_size=len(data),
            sha256=digest,
            source=source,
            storage_ref=storage_ref,
            duplicate_of_artifact_id=duplicate.artifact_id if duplicate else None,
            retention_policy=retention_policy or ArtifactRetentionPolicy(),
            metadata=metadata or {},
        )
        self._artifacts[artifact.artifact_id] = deepcopy(artifact)
        return deepcopy(artifact)

    def get(self, *, owner_user_id: str, artifact_id: str) -> UploadedArtifact:
        artifact = self._artifact(owner_user_id=owner_user_id, artifact_id=artifact_id)
        return deepcopy(artifact)

    def get_bytes(self, *, owner_user_id: str, artifact_id: str) -> bytes:
        artifact = self._artifact(owner_user_id=owner_user_id, artifact_id=artifact_id)
        try:
            return bytes(self._bytes_by_ref[artifact.storage_ref])
        except KeyError as exc:
            raise NotFoundError(f"Uploaded artifact bytes not found: {artifact_id}") from exc

    def list(self, *, owner_user_id: str, limit: int = 100) -> list[UploadedArtifact]:
        artifacts = [
            artifact
            for artifact in self._artifacts.values()
            if artifact.owner_user_id == owner_user_id
        ]
        artifacts.sort(key=lambda artifact: artifact.created_at, reverse=True)
        return [deepcopy(artifact) for artifact in artifacts[: max(1, min(limit, 500))]]

    def append_trace(self, trace: ParsingPipelineTrace) -> ParsingPipelineTrace:
        self._artifact(owner_user_id=trace.owner_user_id, artifact_id=trace.artifact_id)
        self._traces.setdefault(trace.artifact_id, []).append(deepcopy(trace))
        return deepcopy(trace)

    def list_traces(
        self,
        *,
        owner_user_id: str,
        artifact_id: str,
    ) -> list[ParsingPipelineTrace]:
        self._artifact(owner_user_id=owner_user_id, artifact_id=artifact_id)
        return [deepcopy(trace) for trace in self._traces.get(artifact_id, [])]

    def append_access_event(self, event: ArtifactAccessEvent) -> ArtifactAccessEvent:
        self._artifact(owner_user_id=event.owner_user_id, artifact_id=event.artifact_id)
        self._access_events.setdefault(event.artifact_id, []).append(deepcopy(event))
        return deepcopy(event)

    def list_access_events(
        self,
        *,
        owner_user_id: str,
        artifact_id: str,
    ) -> list[ArtifactAccessEvent]:
        self._artifact(owner_user_id=owner_user_id, artifact_id=artifact_id)
        return [
            deepcopy(event)
            for event in self._access_events.get(artifact_id, [])
            if event.owner_user_id == owner_user_id
        ]

    def _canonical_for_hash(
        self,
        *,
        owner_user_id: str,
        sha256: str,
        byte_size: int,
    ) -> UploadedArtifact | None:
        candidates = [
            artifact
            for artifact in self._artifacts.values()
            if artifact.owner_user_id == owner_user_id
            and artifact.sha256 == sha256
            and artifact.byte_size == byte_size
            and artifact.duplicate_of_artifact_id is None
        ]
        candidates.sort(key=lambda artifact: artifact.created_at)
        return candidates[0] if candidates else None

    def _artifact(self, *, owner_user_id: str, artifact_id: str) -> UploadedArtifact:
        artifact = self._artifacts.get(artifact_id)
        if not artifact or artifact.owner_user_id != owner_user_id:
            raise NotFoundError(f"Uploaded artifact not found: {artifact_id}")
        return deepcopy(artifact)


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


class InMemoryAuditRepository:
    """Append-only in-memory generic audit record store."""

    def __init__(self) -> None:
        self._records: list[AuditRecord] = []

    def append(self, record: AuditRecord) -> AuditRecord:
        scope = audit_chain_scope(record)
        previous = next(
            (
                candidate
                for candidate in reversed(self._records)
                if (candidate.chain_scope or audit_chain_scope(candidate)) == scope
            ),
            None,
        )
        linked = link_audit_record(record, previous)
        self._records.append(deepcopy(linked))
        return deepcopy(linked)

    def list(
        self,
        *,
        owner_user_id: str | None = None,
        action: str | None = None,
        workflow_id: str | None = None,
        assistant_session_id: str | None = None,
        limit: int = 100,
    ) -> list[AuditRecord]:
        records = [
            record
            for record in self._records
            if (owner_user_id is None or record.owner_user_id == owner_user_id)
            and (action is None or record.action == action)
            and (workflow_id is None or record.workflow_id == workflow_id)
            and (
                assistant_session_id is None
                or record.assistant_session_id == assistant_session_id
            )
        ]
        records.sort(key=lambda record: (record.timestamp, record.audit_id), reverse=True)
        return [deepcopy(record) for record in records[: max(1, min(limit, 1000))]]


class InMemoryGraphRepository:
    """In-memory Graph-NER context repository for tests and demos."""

    def __init__(self) -> None:
        self._records: dict[str, GraphContextRecord] = {}

    def save_context(self, record: GraphContextRecord) -> GraphContextRecord:
        self._records[record.graph_id] = deepcopy(record)
        return deepcopy(record)

    def list_contexts(
        self,
        *,
        owner_user_id: str | None,
        workflow_id: str | None = None,
        limit: int = 100,
    ) -> list[GraphContextRecord]:
        records = list(self._records.values())
        if owner_user_id is not None:
            records = [
                record for record in records
                if record.owner_user_id == owner_user_id
            ]
        if workflow_id is not None:
            records = [record for record in records if record.workflow_id == workflow_id]
        records.sort(key=lambda record: record.created_at, reverse=True)
        return [deepcopy(record) for record in records[: max(1, min(limit, 1000))]]


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


class InMemoryAssistantSessionRepository:
    """User-scoped in-memory Assistant chat sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, AssistantChatSessionSummary] = {}
        self._messages: dict[str, list[AssistantChatMessage]] = {}
        self._stream_replays: dict[str, list[AssistantStreamReplay]] = {}

    def create_session(self, *, owner_user_id: str, title: str) -> AssistantChatSessionSummary:
        now = utc_now().isoformat()
        session = AssistantChatSessionSummary(
            owner_user_id=owner_user_id,
            title=title,
            message_count=0,
            created_at=now,
            updated_at=now,
        )
        self._sessions[session.session_id] = deepcopy(session)
        self._messages[session.session_id] = []
        self._stream_replays[session.session_id] = []
        return deepcopy(session)

    def list_sessions(
        self,
        *,
        owner_user_id: str,
        include_archived: bool = False,
        limit: int = 100,
        q: str | None = None,
    ) -> list[AssistantChatSessionSummary]:
        sessions = [
            session
            for session in self._sessions.values()
            if session.owner_user_id == owner_user_id
            and (include_archived or session.archived_at is None)
        ]
        if q:
            needle = q.casefold()
            sessions = [
                session
                for session in sessions
                if needle in session.title.casefold()
                or any(
                    needle in message.content.casefold()
                    for message in self._messages.get(session.session_id, [])
                )
            ]
        sessions.sort(key=lambda session: session.updated_at, reverse=True)
        return [deepcopy(session) for session in sessions[: max(1, min(limit, 500))]]

    def get_session(
        self,
        *,
        owner_user_id: str,
        session_id: str,
    ) -> AssistantChatSessionDetail:
        session = self._session(owner_user_id=owner_user_id, session_id=session_id)
        return AssistantChatSessionDetail(
            session=deepcopy(session),
            messages=deepcopy(self._messages.get(session_id, [])),
        )

    def rename_session(
        self,
        *,
        owner_user_id: str,
        session_id: str,
        title: str,
    ) -> AssistantChatSessionSummary:
        session = self._session(owner_user_id=owner_user_id, session_id=session_id)
        session.title = title
        session.updated_at = utc_now().isoformat()
        self._sessions[session_id] = deepcopy(session)
        return deepcopy(session)

    def archive_session(
        self,
        *,
        owner_user_id: str,
        session_id: str,
    ) -> AssistantChatSessionSummary:
        session = self._session(owner_user_id=owner_user_id, session_id=session_id)
        now = utc_now().isoformat()
        session.archived_at = now
        session.updated_at = now
        self._sessions[session_id] = deepcopy(session)
        return deepcopy(session)

    def delete_session(self, *, owner_user_id: str, session_id: str) -> None:
        self._session(owner_user_id=owner_user_id, session_id=session_id)
        del self._sessions[session_id]
        self._messages.pop(session_id, None)
        self._stream_replays.pop(session_id, None)

    def append_message(
        self,
        *,
        owner_user_id: str,
        session_id: str,
        role: AssistantMessageRole,
        content: str,
        payload: dict | None = None,
        workflow_refs: list[str] | None = None,
    ) -> AssistantChatMessage:
        session = self._session(owner_user_id=owner_user_id, session_id=session_id)
        message = AssistantChatMessage(
            session_id=session_id,
            owner_user_id=owner_user_id,
            role=role,
            content=content,
            workflow_refs=workflow_refs or [],
            payload=payload or {},
            phi_classification=(payload or {}).get("phi_classification"),
        )
        self._messages.setdefault(session_id, []).append(deepcopy(message))
        session.message_count = len(self._messages[session_id])
        session.updated_at = message.created_at
        self._sessions[session_id] = deepcopy(session)
        return deepcopy(message)

    def append_stream_replay(self, *, replay: AssistantStreamReplay) -> AssistantStreamReplay:
        self._session(owner_user_id=replay.owner_user_id, session_id=replay.session_id)
        self._stream_replays.setdefault(replay.session_id, []).append(deepcopy(replay))
        return deepcopy(replay)

    def list_stream_replays(
        self,
        *,
        owner_user_id: str,
        session_id: str,
    ) -> list[AssistantStreamReplay]:
        self._session(owner_user_id=owner_user_id, session_id=session_id)
        replays = self._stream_replays.get(session_id, [])
        return [deepcopy(replay) for replay in replays]

    def _session(self, *, owner_user_id: str, session_id: str) -> AssistantChatSessionSummary:
        session = self._sessions.get(session_id)
        if not session or session.owner_user_id != owner_user_id:
            raise NotFoundError(f"Assistant chat session not found: {session_id}")
        return deepcopy(session)


class InMemoryAssistantMemoryRepository:
    """User-scoped in-memory Assistant preference memory."""

    def __init__(self) -> None:
        self._preferences: dict[tuple[str, str], AssistantMemoryPreference] = {}

    def list_preferences(
        self,
        *,
        owner_user_id: str,
    ) -> list[AssistantMemoryPreference]:
        preferences = [
            preference
            for (owner, _), preference in self._preferences.items()
            if owner == owner_user_id
        ]
        preferences.sort(key=lambda preference: preference.key)
        return [deepcopy(preference) for preference in preferences]

    def upsert_preference(
        self,
        *,
        preference: AssistantMemoryPreference,
    ) -> AssistantMemoryPreference:
        self._preferences[(preference.owner_user_id, preference.key)] = deepcopy(
            preference
        )
        return deepcopy(preference)

    def delete_preference(self, *, owner_user_id: str, key: str) -> None:
        self._preferences.pop((owner_user_id, key), None)


class InMemoryBackgroundJobRepository:
    """In-memory background jobs for tests and local scaffolding."""

    def __init__(self) -> None:
        self._jobs: dict[str, BackgroundJob] = {}

    def create(
        self,
        *,
        owner_user_id: str,
        job_type: JobType,
        input: dict,
        max_attempts: int = 1,
    ) -> BackgroundJob:
        now = utc_now().isoformat()
        job = BackgroundJob(
            owner_user_id=owner_user_id,
            job_type=job_type,
            input=input,
            max_attempts=max_attempts,
            created_at=now,
            updated_at=now,
        )
        self._jobs[job.job_id] = deepcopy(job)
        return deepcopy(job)

    def get(self, *, owner_user_id: str, job_id: str) -> BackgroundJob:
        return deepcopy(self._job(owner_user_id=owner_user_id, job_id=job_id))

    def list(
        self,
        *,
        owner_user_id: str,
        status: str | None = None,
        job_type: str | None = None,
        limit: int = 100,
    ) -> list[BackgroundJob]:
        jobs = [
            job
            for job in self._jobs.values()
            if job.owner_user_id == owner_user_id
            and (status is None or job.status == status)
            and (job_type is None or job.job_type == job_type)
        ]
        jobs.sort(key=lambda job: job.updated_at, reverse=True)
        return [deepcopy(job) for job in jobs[: max(1, min(limit, 500))]]

    def mark_running(self, *, owner_user_id: str, job_id: str) -> BackgroundJob:
        job = self._job(owner_user_id=owner_user_id, job_id=job_id)
        now = utc_now().isoformat()
        job.status = "running"
        job.attempts += 1
        job.started_at = job.started_at or now
        job.updated_at = now
        self._jobs[job_id] = deepcopy(job)
        return deepcopy(job)

    def mark_succeeded(
        self,
        *,
        owner_user_id: str,
        job_id: str,
        output: dict,
    ) -> BackgroundJob:
        job = self._job(owner_user_id=owner_user_id, job_id=job_id)
        now = utc_now().isoformat()
        job.status = "succeeded"
        job.output = output
        job.error = None
        job.progress.current = job.progress.total or 1
        job.progress.total = job.progress.total or 1
        job.progress.message = "Completed."
        job.completed_at = now
        job.updated_at = now
        self._jobs[job_id] = deepcopy(job)
        return deepcopy(job)

    def mark_failed(
        self,
        *,
        owner_user_id: str,
        job_id: str,
        error: JobError,
    ) -> BackgroundJob:
        job = self._job(owner_user_id=owner_user_id, job_id=job_id)
        now = utc_now().isoformat()
        job.status = "failed"
        job.error = error
        job.progress.message = error.message
        job.completed_at = now
        job.updated_at = now
        self._jobs[job_id] = deepcopy(job)
        return deepcopy(job)

    def mark_cancelled(
        self,
        *,
        owner_user_id: str,
        job_id: str,
        error: JobError,
    ) -> BackgroundJob:
        job = self._job(owner_user_id=owner_user_id, job_id=job_id)
        now = utc_now().isoformat()
        job.status = "cancelled"
        job.error = error
        job.progress.message = error.message
        job.completed_at = now
        job.updated_at = now
        self._jobs[job_id] = deepcopy(job)
        return deepcopy(job)

    def _job(self, *, owner_user_id: str, job_id: str) -> BackgroundJob:
        job = self._jobs.get(job_id)
        if not job or job.owner_user_id != owner_user_id:
            raise NotFoundError(f"Background job not found: {job_id}")
        return deepcopy(job)
