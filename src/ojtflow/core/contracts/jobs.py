"""Background job contracts."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.ids import new_id
from ojtflow.core.time import utc_now


JobType = Literal[
    "retrieval_reindex",
    "file_parse",
    "ocr_extract",
    "embedding_reindex",
    "external_ingest",
    "export_package",
]
JobStatus = Literal["queued", "running", "succeeded", "failed", "cancelled"]


class JobError(ContractModel):
    """Structured job failure without exposing secrets or raw tracebacks."""

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class JobProgress(ContractModel):
    """Operator-readable job progress."""

    current: int = Field(default=0, ge=0)
    total: int | None = Field(default=None, ge=0)
    message: str = ""


class BackgroundJob(ContractModel):
    """Durable background job state."""

    job_id: str = Field(default_factory=lambda: new_id("job"))
    owner_user_id: str
    job_type: JobType
    status: JobStatus = "queued"
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    error: JobError | None = None
    progress: JobProgress = Field(default_factory=JobProgress)
    attempts: int = Field(default=0, ge=0)
    max_attempts: int = Field(default=1, ge=1)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())
    updated_at: str = Field(default_factory=lambda: utc_now().isoformat())
    started_at: str | None = None
    completed_at: str | None = None

