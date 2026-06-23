"""Persistent corpus knowledge-graph routes (search / neighborhood / nodes / import)."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

from ojtflow.application.graph_med_service import GraphMedService
from ojtflow.application.governance_service import GovernanceService
from ojtflow.application.knowledge_graph_service import KnowledgeGraphService
from ojtflow.config import Settings
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.contracts.governance import WorkspaceDetail
from ojtflow.core.contracts.knowledge_graph import (
    GraphMedStatus,
    KnowledgeGraphImportRequest,
    KnowledgeGraphImportResult,
    KnowledgeGraphNode,
    KnowledgeGraphStats,
    KnowledgeGraphView,
)
from ojtflow.core.errors import UnsupportedUploadError, UploadTooLargeError
from ojtflow.interfaces.api.deps import (
    get_api_settings,
    get_graph_med_service,
    get_governance_service,
    get_knowledge_graph_service,
    require_authentication,
)
from ojtflow.interfaces.api.responses import ok

router = APIRouter(tags=["knowledge-graph"])


class KnowledgeGraphViewEnvelope(ContractModel):
    data: KnowledgeGraphView
    error: None = None


class KnowledgeGraphNodesEnvelope(ContractModel):
    data: list[KnowledgeGraphNode]
    error: None = None


class KnowledgeGraphNodeEnvelope(ContractModel):
    data: KnowledgeGraphNode | None
    error: None = None


class KnowledgeGraphStatsEnvelope(ContractModel):
    data: KnowledgeGraphStats
    error: None = None


class GraphMedStatusEnvelope(ContractModel):
    data: GraphMedStatus
    error: None = None


class KnowledgeGraphImportEnvelope(ContractModel):
    data: KnowledgeGraphImportResult
    error: None = None


TEXT_GRAPH_IMPORT_EXTENSIONS = {".txt", ".csv", ".md", ".json"}


def _organization_id(workspace: WorkspaceDetail | None) -> str | None:
    if workspace is None:
        return None
    return workspace.organization.organization_id or None


def _optional(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


async def _read_graph_import_upload(file: UploadFile, settings: Settings) -> str:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix and suffix not in TEXT_GRAPH_IMPORT_EXTENSIONS:
        raise UnsupportedUploadError(
            "Knowledge graph import accepts UTF-8 text, CSV, Markdown, or JSON files. "
            "Parse PDFs/DOCX first, then import the extracted text."
        )
    data = bytearray()
    while True:
        chunk = await file.read(settings.upload_read_chunk_bytes)
        if not chunk:
            break
        data.extend(chunk)
        if len(data) > settings.max_upload_bytes:
            raise UploadTooLargeError(
                f"Uploaded file exceeds the {settings.max_upload_bytes} byte limit."
            )
    if not data:
        raise UnsupportedUploadError("Uploaded file is empty.")
    try:
        return bytes(data).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UnsupportedUploadError(
            "Knowledge graph import file must be UTF-8 text."
        ) from exc


@router.get("/knowledge-graph/search", response_model=KnowledgeGraphNodesEnvelope)
async def search_concepts(
    q: str = Query(default="", max_length=200),
    limit: int = Query(default=50, ge=1, le=1000),
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
) -> dict:
    workspace = governance.require_permission(
        user=authenticated.user, permission_scope="retrieval:read"
    )
    return ok(
        service.search(q=q, organization_id=_organization_id(workspace), limit=limit)
    )


@router.get("/knowledge-graph/neighborhood", response_model=KnowledgeGraphViewEnvelope)
async def get_neighborhood(
    node_id: str | None = None,
    q: str | None = None,
    depth: int = Query(default=1, ge=0, le=2),
    limit: int = Query(default=100, ge=1, le=1000),
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
) -> dict:
    workspace = governance.require_permission(
        user=authenticated.user, permission_scope="retrieval:read"
    )
    return ok(
        service.neighborhood(
            node_id=_optional(node_id),
            q=_optional(q),
            depth=depth,
            limit=limit,
            organization_id=_organization_id(workspace),
        )
    )


@router.get("/knowledge-graph/nodes/{node_id}", response_model=KnowledgeGraphNodeEnvelope)
async def get_node(
    node_id: str,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
) -> dict:
    workspace = governance.require_permission(
        user=authenticated.user, permission_scope="retrieval:read"
    )
    return ok(
        service.get_node(node_id=node_id, organization_id=_organization_id(workspace))
    )


@router.get("/knowledge-graph/stats", response_model=KnowledgeGraphStatsEnvelope)
async def get_stats(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
) -> dict:
    workspace = governance.require_permission(
        user=authenticated.user, permission_scope="retrieval:read"
    )
    return ok(service.stats(organization_id=_organization_id(workspace)))


@router.get("/knowledge-graph/graph-med/status", response_model=GraphMedStatusEnvelope)
async def get_graph_med_status(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    service: GraphMedService = Depends(get_graph_med_service),
) -> dict:
    governance.require_permission(user=authenticated.user, permission_scope="retrieval:read")
    return ok(service.status())


@router.post("/knowledge-graph/import", response_model=KnowledgeGraphImportEnvelope)
async def import_knowledge(
    request: KnowledgeGraphImportRequest,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    service: GraphMedService = Depends(get_graph_med_service),
) -> dict:
    workspace = governance.require_permission(
        user=authenticated.user, permission_scope="data:profile"
    )
    organization_id = _organization_id(workspace) or authenticated.user.user_id
    result = service.import_text(
        text=request.text or "",
        organization_id=organization_id,
        scope="organization",
        document_id=request.document_id,
        source_id=request.source_id,
        patient_id=request.patient_id,
        encounter_id=request.encounter_id,
        concat_text=request.concat_text,
        narrative_text=request.narrative_text,
    )
    return ok(result)


@router.post("/knowledge-graph/import-file", response_model=KnowledgeGraphImportEnvelope)
async def import_knowledge_file(
    file: UploadFile = File(...),
    document_id: str | None = Form(default=None),
    source_id: str | None = Form(default=None),
    patient_id: str | None = Form(default=None),
    encounter_id: str | None = Form(default=None),
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    service: GraphMedService = Depends(get_graph_med_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    workspace = governance.require_permission(
        user=authenticated.user, permission_scope="data:profile"
    )
    organization_id = _organization_id(workspace) or authenticated.user.user_id
    text = await _read_graph_import_upload(file, settings)
    result = service.import_text(
        text=text,
        organization_id=organization_id,
        scope="organization",
        document_id=_optional(document_id) or file.filename or None,
        source_id=_optional(source_id),
        patient_id=_optional(patient_id),
        encounter_id=_optional(encounter_id),
    )
    return ok(result)
