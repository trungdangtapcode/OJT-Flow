"""FastAPI application factory."""

from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from uuid import uuid4

from ojtflow.core.errors import OJTFlowError
from ojtflow.config import get_settings
from ojtflow.observability.logging_guard import install_no_raw_phi_filter
from ojtflow.interfaces.api.rate_limit import build_rate_limiter, rate_limited_response
from ojtflow.interfaces.api.responses import (
    http_exception_handler,
    ojtflow_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from ojtflow.interfaces.api.deps import require_authentication
from ojtflow.interfaces.api.routes import (
    assistant,
    audit,
    auth,
    convert,
    fhir,
    governance,
    health,
    jobs,
    ocr,
    parse,
    retrieval,
    review,
    runtime,
    validate,
    workflows,
)


def create_app() -> FastAPI:
    """Create the local OJTFlow API app."""

    install_no_raw_phi_filter()
    app = FastAPI(
        title="OJTFlow",
        version="0.1.0",
        description="Governed healthcare data workflow scaffold",
    )
    app.add_exception_handler(OJTFlowError, ojtflow_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    rate_limiter = build_rate_limiter(get_settings())

    @app.middleware("http")
    async def request_id_responses(request, call_next):
        request_id = _request_id(request.headers.get("x-request-id"))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.middleware("http")
    async def rate_limit_requests(request, call_next):
        request_id = getattr(request.state, "request_id", None)
        if not isinstance(request_id, str) or not request_id:
            request_id = _request_id(request.headers.get("x-request-id"))
            request.state.request_id = request_id
        decision = rate_limiter.check(request, settings=get_settings())
        if decision is not None and not decision.allowed:
            return rate_limited_response(decision, request_id=request_id)
        response = await call_next(request)
        if decision is not None:
            response.headers["X-RateLimit-Limit"] = str(decision.limit)
            response.headers["X-RateLimit-Remaining"] = str(decision.remaining)
            response.headers["X-RateLimit-Reset"] = str(decision.reset_seconds)
        return response

    @app.middleware("http")
    async def no_store_auth_responses(request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/api/v1/auth/"):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Pragma"] = "no-cache"
        return response

    protected = [Depends(require_authentication)]
    app.include_router(health.router)
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(assistant.router, prefix="/api/v1")
    app.include_router(audit.router, prefix="/api/v1")
    app.include_router(workflows.router, prefix="/api/v1")
    app.include_router(review.router, prefix="/api/v1")
    app.include_router(convert.router, prefix="/api/v1", dependencies=protected)
    app.include_router(validate.router, prefix="/api/v1", dependencies=protected)
    app.include_router(fhir.router, prefix="/api/v1", dependencies=protected)
    app.include_router(governance.router, prefix="/api/v1")
    app.include_router(ocr.router, prefix="/api/v1", dependencies=protected)
    app.include_router(parse.router, prefix="/api/v1")
    app.include_router(retrieval.router, prefix="/api/v1")
    app.include_router(jobs.router, prefix="/api/v1")
    app.include_router(runtime.router, prefix="/api/v1")
    return app


def _request_id(value: str | None) -> str:
    if value:
        clean = value.strip()
        if 1 <= len(clean) <= 128 and all(
            character.isalnum() or character in {"-", "_", ".", ":"}
            for character in clean
        ):
            return clean
    return f"req_{uuid4().hex}"


app = create_app()
