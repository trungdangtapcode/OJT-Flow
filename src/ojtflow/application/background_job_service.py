"""Use cases for durable background jobs."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol

from ojtflow.application.ports import BackgroundJobRepository
from ojtflow.core.contracts.jobs import BackgroundJob, JobError, JobType


JobHandler = Callable[[BackgroundJob], dict[str, Any]]


class JobDispatcher(Protocol):
    """Dispatch durable jobs to an external worker queue."""

    queue_backed: bool

    def enqueue(self, job: BackgroundJob) -> None: ...


class SyncJobRunner:
    """Synchronous local runner used before queue-backed workers exist."""

    def run(self, job: BackgroundJob, handler: JobHandler) -> dict[str, Any]:
        return handler(job)


class BackgroundJobService:
    """Create, inspect, and execute user-owned jobs."""

    def __init__(
        self,
        repository: BackgroundJobRepository,
        runner: SyncJobRunner | None = None,
        dispatcher: JobDispatcher | None = None,
    ) -> None:
        self.repository = repository
        self.runner = runner or SyncJobRunner()
        self.dispatcher = dispatcher

    @property
    def queue_backed(self) -> bool:
        return bool(self.dispatcher and self.dispatcher.queue_backed)

    def create_job(
        self,
        *,
        owner_user_id: str,
        job_type: JobType,
        input: dict[str, Any] | None = None,
        max_attempts: int = 1,
    ) -> BackgroundJob:
        return self.repository.create(
            owner_user_id=owner_user_id,
            job_type=job_type,
            input=input or {},
            max_attempts=max_attempts,
        )

    def get_job(self, *, owner_user_id: str, job_id: str) -> BackgroundJob:
        return self.repository.get(owner_user_id=owner_user_id, job_id=job_id)

    def list_jobs(
        self,
        *,
        owner_user_id: str,
        status: str | None = None,
        job_type: str | None = None,
        limit: int = 100,
    ) -> list[BackgroundJob]:
        return self.repository.list(
            owner_user_id=owner_user_id,
            status=status,
            job_type=job_type,
            limit=limit,
        )

    def cancel_job(self, *, owner_user_id: str, job_id: str) -> BackgroundJob:
        job = self.repository.get(owner_user_id=owner_user_id, job_id=job_id)
        if job.status in {"succeeded", "failed", "cancelled"}:
            return job
        return self.repository.mark_cancelled(
            owner_user_id=owner_user_id,
            job_id=job_id,
            error=JobError(
                code="job_cancelled",
                message="Job was cancelled by the user.",
            ),
        )

    def enqueue(self, *, owner_user_id: str, job_id: str) -> BackgroundJob:
        job = self.repository.get(owner_user_id=owner_user_id, job_id=job_id)
        if job.status in {"succeeded", "failed", "cancelled", "running"}:
            return job
        if self.dispatcher is None:
            return job
        self.dispatcher.enqueue(job)
        return self.repository.get(owner_user_id=owner_user_id, job_id=job_id)

    def run_sync(self, *, owner_user_id: str, job_id: str, handler: JobHandler) -> BackgroundJob:
        current = self.repository.get(owner_user_id=owner_user_id, job_id=job_id)
        if current.status in {"succeeded", "failed", "cancelled"}:
            return current
        job = self.repository.mark_running(owner_user_id=owner_user_id, job_id=job_id)
        try:
            output = self.runner.run(job, handler)
        except Exception as exc:
            return self.repository.mark_failed(
                owner_user_id=owner_user_id,
                job_id=job_id,
                error=JobError(
                    code="job_execution_failed",
                    message="Job execution failed.",
                    details={"error_type": type(exc).__name__},
                ),
            )
        return self.repository.mark_succeeded(
            owner_user_id=owner_user_id,
            job_id=job_id,
            output=output,
        )
