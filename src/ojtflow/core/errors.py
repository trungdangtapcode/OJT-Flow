"""Domain-specific exceptions."""

from __future__ import annotations


class OJTFlowError(Exception):
    """Base exception for expected OJTFlow failures."""


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
