"""Internal HTTP service for graph-med annotation."""

from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI

from ojtflow.config import get_settings
from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.contracts.knowledge_graph import (
    GraphMedAnnotationRequest,
    GraphMedLinkedEntity,
    GraphMedStatus,
)
from ojtflow.core.errors import DependencyUnavailableError
from ojtflow.infrastructure.graph_med.annotation import GraphMedAnnotationClient
from ojtflow.infrastructure.graph_med.factory import build_direct_graph_med_annotation_client
from ojtflow.interfaces.api.responses import error_response, ok

app = FastAPI(title="OJTFlow graph-med service", version="0.1.0")


class GraphMedStatusEnvelope(ContractModel):
    data: GraphMedStatus
    error: None = None


class GraphMedAnnotationEnvelope(ContractModel):
    data: list[GraphMedLinkedEntity]
    error: None = None


@lru_cache(maxsize=1)
def _annotator() -> GraphMedAnnotationClient:
    return build_direct_graph_med_annotation_client(get_settings())


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "graph-med"}


@app.get("/status", response_model=GraphMedStatusEnvelope)
async def status() -> dict:
    return ok(_annotator().status())


@app.post("/annotate", response_model=GraphMedAnnotationEnvelope)
async def annotate(request: GraphMedAnnotationRequest) -> dict:
    try:
        annotations = _annotator().annotate_text(
            patient_id=request.patient_id,
            encounter_id=request.encounter_id,
            concat_text=request.concat_text,
            narrative_text=request.narrative_text,
        )
    except DependencyUnavailableError as exc:
        return error_response(
            "dependency_unavailable",
            str(exc),
            status_code=503,
            details=exc.details,
            workflow_id=exc.workflow_id,
        )
    return ok(annotations)
