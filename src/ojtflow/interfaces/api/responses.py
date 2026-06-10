"""API response envelopes and error helpers."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.contracts.enums import WorkflowStatus
from ojtflow.core.contracts.workflow import WorkflowState
from ojtflow.core.errors import (
    AuthenticationError,
    ArtifactIntegrityError,
    DependencyUnavailableError,
    NotFoundError,
    OJTFlowError,
    PolicyBlockedError,
    ToolExecutionError,
    UnsupportedUploadError,
    UploadTooLargeError,
)

logger = logging.getLogger(__name__)


class ApiError(ContractModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    workflow_id: str | None = None
    request_id: str | None = None


class ApiEnvelope(ContractModel):
    data: Any = None
    error: ApiError | None = None


def ok(data: Any, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {"data": public_jsonable(data), "error": None}
    if meta is not None:
        payload["meta"] = public_jsonable(meta)
    return payload


_ARTIFACT_REF_KEYS = {
    "dataset_ref",
    "input_refs",
    "output_ref",
    "output_refs",
    "source_ref",
    "storage_ref",
}


def public_jsonable(data: Any) -> Any:
    """Encode API payloads without exposing local filesystem artifact paths."""

    return _redact_local_artifact_refs(jsonable_encoder(data))


def _redact_local_artifact_refs(value: Any, *, key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {
            item_key: _redact_local_artifact_refs(item_value, key=item_key)
            for item_key, item_value in value.items()
        }
    if isinstance(value, list):
        return [_redact_local_artifact_refs(item, key=key) for item in value]
    if isinstance(value, str) and key in _ARTIFACT_REF_KEYS:
        return _public_artifact_ref(value)
    return value


def _public_artifact_ref(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "file":
        return value
    filename = Path(unquote(parsed.path)).name
    if not filename:
        return "artifact://local/redacted"
    return f"artifact://local/{filename}"


def raise_for_failed_workflow(workflow: WorkflowState) -> None:
    """Return failed workflow state as an API error while preserving persistence."""

    if workflow.status != WorkflowStatus.FAILED:
        return

    failure = workflow.failure
    message = failure.message if failure else "Workflow failed during startup"
    details = {
        "status": workflow.status.value,
        "risk_flags": workflow.risk_flags,
    }
    if failure:
        details.update(failure.details)
        details["error_type"] = failure.error_type
        details["failure_code"] = failure.code

    workflow_id = workflow.workflow_id
    failure_code = failure.code if failure else "workflow_failed"
    if failure_code == "artifact_integrity_error":
        raise ArtifactIntegrityError(message, workflow_id=workflow_id, details=details)
    if failure_code == "not_found":
        raise NotFoundError(message, workflow_id=workflow_id, details=details)
    if failure_code == "policy_blocked":
        raise PolicyBlockedError(message, workflow_id=workflow_id, details=details)
    if failure_code == "upload_too_large":
        raise UploadTooLargeError(message, workflow_id=workflow_id, details=details)
    if failure_code == "unsupported_upload":
        raise UnsupportedUploadError(message, workflow_id=workflow_id, details=details)
    raise ToolExecutionError(message, workflow_id=workflow_id, details=details)


def error_response(
    code: str,
    message: str,
    status_code: int = 400,
    details: dict[str, Any] | None = None,
    workflow_id: str | None = None,
    request_id: str | None = None,
) -> JSONResponse:
    public_details = public_jsonable(details or {})
    if request_id and isinstance(public_details, dict):
        public_details = {**public_details, "request_id": request_id}
    headers = {"X-Request-ID": request_id} if request_id else None
    return JSONResponse(
        status_code=status_code,
        headers=headers,
        content={
            "data": None,
            "error": {
                "code": code,
                "message": message,
                "details": public_details,
                "workflow_id": workflow_id,
                "request_id": request_id,
            },
        },
    )


def request_id_from_state(request: Request) -> str | None:
    value = getattr(request.state, "request_id", None)
    return value if isinstance(value, str) and value else None


async def ojtflow_exception_handler(request: Request, exc: OJTFlowError) -> JSONResponse:
    workflow_id = exc.workflow_id
    details = exc.details
    request_id = request_id_from_state(request)
    if isinstance(exc, AuthenticationError):
        return error_response(
            "unauthorized",
            str(exc),
            status_code=401,
            details=details,
            workflow_id=workflow_id,
            request_id=request_id,
        )
    if isinstance(exc, ArtifactIntegrityError):
        return error_response(
            "artifact_integrity_error",
            str(exc),
            status_code=409,
            details=details,
            workflow_id=workflow_id,
            request_id=request_id,
        )
    if isinstance(exc, DependencyUnavailableError):
        return error_response(
            "dependency_unavailable",
            str(exc),
            status_code=503,
            details=details,
            workflow_id=workflow_id,
            request_id=request_id,
        )
    if isinstance(exc, NotFoundError):
        return error_response(
            "not_found",
            str(exc),
            status_code=404,
            details=details,
            workflow_id=workflow_id,
            request_id=request_id,
        )
    if isinstance(exc, PolicyBlockedError):
        return error_response(
            "policy_blocked",
            str(exc),
            status_code=403,
            details=details,
            workflow_id=workflow_id,
            request_id=request_id,
        )
    if isinstance(exc, UploadTooLargeError):
        return error_response(
            "upload_too_large",
            str(exc),
            status_code=413,
            details=details,
            workflow_id=workflow_id,
            request_id=request_id,
        )
    if isinstance(exc, UnsupportedUploadError):
        return error_response(
            "unsupported_upload",
            str(exc),
            status_code=415,
            details=details,
            workflow_id=workflow_id,
            request_id=request_id,
        )
    if isinstance(exc, ToolExecutionError):
        return error_response(
            "tool_execution_error",
            str(exc),
            status_code=422,
            details=details,
            workflow_id=workflow_id,
            request_id=request_id,
        )
    return error_response(
        "ojtflow_error",
        str(exc),
        status_code=400,
        details=details,
        workflow_id=workflow_id,
        request_id=request_id,
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else "HTTP request failed"
    return error_response(
        _http_error_code(exc.status_code),
        detail,
        status_code=exc.status_code,
        details={} if isinstance(exc.detail, str) else {"detail": jsonable_encoder(exc.detail)},
        request_id=request_id_from_state(request),
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return error_response(
        "request_validation_error",
        "Request validation failed",
        status_code=422,
        details={"errors": _public_validation_errors(exc.errors())},
        request_id=request_id_from_state(request),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "Unhandled API exception",
        extra={
            "path": request.url.path,
            "method": request.method,
            "request_id": request_id_from_state(request),
        },
    )
    return error_response(
        "internal_error",
        "Internal server error",
        status_code=500,
        details={},
        request_id=request_id_from_state(request),
    )


def _http_error_code(status_code: int) -> str:
    if status_code == 401:
        return "unauthorized"
    if status_code == 403:
        return "forbidden"
    if status_code == 404:
        return "not_found"
    if status_code == 405:
        return "method_not_allowed"
    return "http_error"


def _public_validation_errors(errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_redact_validation_error(jsonable_encoder(error)) for error in errors]


def _redact_validation_error(value: Any, *, key: str | None = None) -> Any:
    if key == "input":
        return "<redacted>"
    if isinstance(value, dict):
        return {
            item_key: _redact_validation_error(item_value, key=item_key)
            for item_key, item_value in value.items()
        }
    if isinstance(value, list):
        return [_redact_validation_error(item) for item in value]
    return value
