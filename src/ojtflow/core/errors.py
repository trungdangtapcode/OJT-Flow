"""Domain-specific exceptions."""

from __future__ import annotations

from typing import Any


class OJTFlowError(Exception):
    """Base exception for expected OJTFlow failures."""

    def __init__(
        self,
        message: str,
        *,
        workflow_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.workflow_id = workflow_id
        self.details = details or {}


class AuthenticationError(OJTFlowError):
    """Raised when a request does not include a valid authenticated session."""


class ArtifactIntegrityError(OJTFlowError):
    """Raised when a persisted artifact fails an integrity check."""


class DependencyUnavailableError(OJTFlowError):
    """Raised when a required runtime dependency cannot be reached."""


class NotFoundError(OJTFlowError):
    """Raised when an expected workflow, dataset, review, or schema is missing."""


class PolicyBlockedError(OJTFlowError):
    """Raised when a policy rule blocks an operation."""


class ToolExecutionError(OJTFlowError):
    """Raised when a deterministic tool fails with a known cause."""


class UploadTooLargeError(OJTFlowError):
    """Raised when an uploaded file exceeds the configured size limit."""


class UnsupportedUploadError(OJTFlowError):
    """Raised when an uploaded file fails server-side upload policy."""
