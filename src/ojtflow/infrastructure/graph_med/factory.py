"""Factories for graph-med annotation adapters."""

from __future__ import annotations

from ojtflow.application.ports import GraphMedAnnotationPort
from ojtflow.config import Settings
from ojtflow.infrastructure.graph_med.annotation import (
    GraphMedAnnotationClient,
    GraphMedAnnotationConfig,
)
from ojtflow.infrastructure.graph_med.http_client import GraphMedHttpAnnotationClient


def build_graph_med_annotation_port(settings: Settings) -> GraphMedAnnotationPort | None:
    """Return the graph-med service port used by the main API."""

    if not settings.graph_med_annotation_enabled:
        return None
    if settings.graph_med_service_base_url:
        return GraphMedHttpAnnotationClient(
            base_url=settings.graph_med_service_base_url,
            timeout_seconds=settings.graph_med_timeout_seconds,
            icd_vector_index=settings.graph_med_icd_vector_index,
        )
    return build_direct_graph_med_annotation_client(settings)


def build_direct_graph_med_annotation_client(settings: Settings) -> GraphMedAnnotationClient:
    """Return the direct graph-med runtime used inside the graph-med service."""

    return GraphMedAnnotationClient(graph_med_annotation_config_from_settings(settings))


def graph_med_annotation_config_from_settings(
    settings: Settings,
) -> GraphMedAnnotationConfig:
    return GraphMedAnnotationConfig(
        enabled=settings.graph_med_annotation_enabled,
        neo4j_uri=settings.neo4j_uri,
        neo4j_user=settings.neo4j_user,
        neo4j_password=settings.neo4j_password,
        neo4j_database=settings.neo4j_database,
        embedding_base_url=settings.graph_med_embedding_base_url,
        embedding_model=settings.graph_med_embedding_model,
        embedding_fallback_base_url=settings.openai_embedding_base_url
        if settings.embedding_provider == "openai"
        else "",
        embedding_fallback_model=settings.embedding_model
        if settings.embedding_provider == "openai"
        else "",
        embedding_fallback_api_key=settings.openai_api_key
        if settings.embedding_provider == "openai"
        else "",
        embedding_fallback_dimensions=settings.embedding_dimensions
        if settings.embedding_provider == "openai"
        else None,
        llm_base_url=settings.graph_med_llm_base_url,
        llm_model=settings.graph_med_llm_model,
        llm_fallback_base_url=settings.llm_base_url
        if settings.llm_provider == "openai"
        else "",
        llm_fallback_model=settings.llm_model if settings.llm_provider == "openai" else "",
        llm_fallback_api_key=settings.openai_api_key
        if settings.llm_provider == "openai"
        else "",
        gnn_base_url=settings.graph_med_gnn_base_url,
        device=settings.graph_med_device,
        require_gpu=settings.graph_med_require_gpu,
        icd_vector_index=settings.graph_med_icd_vector_index,
        candidate_k=settings.graph_med_candidate_k,
        timeout_seconds=settings.graph_med_timeout_seconds,
    )
