"""API response envelopes and error helpers."""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import Field

from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.errors import NotFoundError, OJTFlowError, PolicyBlockedError, ToolExecutionError


class ApiError(ContractModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    workflow_id: str | None = None


class ApiEnvelope(ContractModel):
    data: Any = None
    error: ApiError | None = None


def ok(data: Any, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {"data": jsonable_encoder(data), "error": None}
    if meta is not None:
        payload["meta"] = jsonable_encoder(meta)
    return payload


def error_response(
    code: str,
    message: str,
    status_code: int = 400,
    details: dict[str, Any] | None = None,
    workflow_id: str | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "data": None,
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
                "workflow_id": workflow_id,
            },
        },
    )


async def ojtflow_exception_handler(request: Request, exc: OJTFlowError) -> JSONResponse:
    if isinstance(exc, NotFoundError):
        return error_response("not_found", str(exc), status_code=404)
    if isinstance(exc, PolicyBlockedError):
        return error_response("policy_blocked", str(exc), status_code=403)
    if isinstance(exc, ToolExecutionError):
        return error_response("tool_execution_error", str(exc), status_code=422)
    return error_response("ojtflow_error", str(exc), status_code=400)


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return error_response(
        "request_validation_error",
        "Request validation failed",
        status_code=422,
        details={"errors": jsonable_encoder(exc.errors())},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return error_response(
        "internal_error",
        "Internal server error",
        status_code=500,
        details={"error_type": type(exc).__name__},
    )
