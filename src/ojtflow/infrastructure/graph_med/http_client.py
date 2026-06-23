"""HTTP client for the internal graph-med annotation service."""

from __future__ import annotations

from typing import Any

import httpx

from ojtflow.core.contracts.knowledge_graph import (
    GraphMedAnnotationRequest,
    GraphMedLinkedEntity,
    GraphMedStatus,
)
from ojtflow.core.errors import DependencyUnavailableError


class GraphMedHttpAnnotationClient:
    """Call graph-med as a separate service through the application port."""

    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float,
        icd_vector_index: str,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._icd_vector_index = icd_vector_index

    def status(self) -> GraphMedStatus:
        try:
            response = httpx.get(
                f"{self._base_url}/status",
                timeout=min(self._timeout_seconds, 10.0),
            )
            response.raise_for_status()
            payload = response.json()
            return GraphMedStatus.model_validate(payload.get("data", payload))
        except Exception as exc:
            return GraphMedStatus(
                enabled=True,
                available=False,
                ontology_loaded=False,
                gpu_required=False,
                gpu_available=False,
                gnn_endpoint_configured=False,
                gnn_endpoint_reachable=False,
                embedding_endpoint_configured=False,
                llm_endpoint_configured=False,
                embedding_endpoint_reachable=False,
                llm_endpoint_reachable=False,
                icd_vector_index=self._icd_vector_index,
                icd_disease_count=0,
                hpo_phenotype_count=0,
                umls_count=0,
                message=f"graph-med service unavailable: {exc}",
            )

    def annotate_text(
        self,
        *,
        patient_id: str,
        encounter_id: str,
        concat_text: str,
        narrative_text: str,
    ) -> list[GraphMedLinkedEntity]:
        request = GraphMedAnnotationRequest(
            patient_id=patient_id,
            encounter_id=encounter_id,
            concat_text=concat_text,
            narrative_text=narrative_text,
        )
        try:
            response = httpx.post(
                f"{self._base_url}/annotate",
                json=request.model_dump(),
                timeout=self._timeout_seconds,
            )
        except Exception as exc:
            raise DependencyUnavailableError(f"graph-med service unavailable: {exc}") from exc
        if response.status_code >= 400:
            raise DependencyUnavailableError(
                _error_message(response),
                details={"graph_med_service_status": response.status_code},
            )
        payload = response.json()
        data = payload.get("data", payload)
        if not isinstance(data, list):
            raise DependencyUnavailableError("graph-med service returned invalid annotations.")
        return [GraphMedLinkedEntity.model_validate(item) for item in data]


def _error_message(response: httpx.Response) -> str:
    try:
        payload: Any = response.json()
    except ValueError:
        return response.text or f"graph-med service returned HTTP {response.status_code}"
    error = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(error, dict) and error.get("message"):
        return str(error["message"])
    detail = payload.get("detail") if isinstance(payload, dict) else None
    if detail:
        return str(detail)
    return f"graph-med service returned HTTP {response.status_code}"
