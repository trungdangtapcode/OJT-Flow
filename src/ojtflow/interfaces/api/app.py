"""FastAPI application factory."""

from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from ojtflow.core.errors import OJTFlowError
from ojtflow.interfaces.api.responses import (
    http_exception_handler,
    ojtflow_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from ojtflow.interfaces.api.deps import require_authentication
from ojtflow.interfaces.api.routes import (
    auth,
    convert,
    fhir,
    health,
    ocr,
    parse,
    retrieval,
    review,
    validate,
    workflows,
)


def create_app() -> FastAPI:
    """Create the local OJTFlow API app."""

    app = FastAPI(
        title="OJTFlow",
        version="0.1.0",
        description="Governed healthcare data workflow scaffold",
    )
    app.add_exception_handler(OJTFlowError, ojtflow_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    protected = [Depends(require_authentication)]
    app.include_router(health.router)
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(workflows.router, prefix="/api/v1", dependencies=protected)
    app.include_router(review.router, prefix="/api/v1", dependencies=protected)
    app.include_router(convert.router, prefix="/api/v1", dependencies=protected)
    app.include_router(validate.router, prefix="/api/v1", dependencies=protected)
    app.include_router(fhir.router, prefix="/api/v1", dependencies=protected)
    app.include_router(ocr.router, prefix="/api/v1", dependencies=protected)
    app.include_router(parse.router, prefix="/api/v1", dependencies=protected)
    app.include_router(retrieval.router, prefix="/api/v1", dependencies=protected)
    return app


app = create_app()
