"""Workspace artifact/file browser routes."""

from __future__ import annotations

import io
from typing import Literal
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse

from ojtflow.application.document_intake_service import DocumentIntakeService
from ojtflow.application.governance_service import GovernanceService
from ojtflow.config import Settings
from ojtflow.core.contracts.artifacts import (
    ArtifactAccessEvent,
    ParsingPipelineTrace,
    UploadedArtifact,
)
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.core.contracts.base import ContractModel, NonBlankStr
from ojtflow.core.errors import NotFoundError
from ojtflow.data_tools.extract import sanitize_upload_filename
from ojtflow.interfaces.api.deps import (
    get_api_settings,
    get_document_intake_service,
    get_governance_service,
    require_authentication,
)
from ojtflow.interfaces.api.responses import ok

router = APIRouter(tags=["artifacts"])
ArtifactScope = Literal["workspace", "mine"]


class ArtifactListResponse(ContractModel):
    items: list[UploadedArtifact]
    scope: ArtifactScope
    organization_id: str
    storage_backend: str
    object_storage_backend: str


class ArtifactListEnvelope(ContractModel):
    data: ArtifactListResponse
    error: None = None


class ArtifactDetailResponse(ContractModel):
    artifact: UploadedArtifact
    traces: list[ParsingPipelineTrace]
    access_events: list[ArtifactAccessEvent]


class ArtifactDetailEnvelope(ContractModel):
    data: ArtifactDetailResponse
    error: None = None


@router.get("/artifacts", response_model=ArtifactListEnvelope)
def list_workspace_artifacts(
    scope: ArtifactScope = Query(default="workspace"),
    limit: int = Query(default=100, ge=1, le=500),
    q: str | None = Query(default=None),
    mime_type: str | None = Query(default=None),
    source: str | None = Query(default=None),
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    settings: Settings = Depends(get_api_settings),
    intake: DocumentIntakeService = Depends(get_document_intake_service),
) -> dict:
    """List files uploaded in the current workspace or by the current user."""

    workspace = governance.require_permission(
        user=authenticated.user,
        permission_scope="data:read",
    )
    organization_id = workspace.organization.organization_id
    if scope == "mine":
        items = _filter_artifacts(
            intake.list_artifacts(owner_user_id=authenticated.user.user_id, limit=limit),
            q=q,
            mime_type=mime_type,
            source=source,
        )
    else:
        items = intake.list_workspace_artifacts(
            organization_id=organization_id,
            limit=limit,
            q=q,
            mime_type=mime_type,
            source=source,
        )
    return ok(
        ArtifactListResponse(
            items=items,
            scope=scope,
            organization_id=organization_id,
            storage_backend=settings.storage_backend,
            object_storage_backend=settings.object_storage_backend,
        )
    )


@router.get("/artifacts/{artifact_id}", response_model=ArtifactDetailEnvelope)
def get_workspace_artifact(
    http_request: Request,
    artifact_id: NonBlankStr,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    intake: DocumentIntakeService = Depends(get_document_intake_service),
) -> dict:
    """Return workspace artifact metadata, extraction traces, and access events."""

    workspace = governance.require_permission(
        user=authenticated.user,
        permission_scope="data:read",
    )
    artifact, _via_workspace = _get_accessible_artifact(
        intake=intake,
        organization_id=workspace.organization.organization_id,
        owner_user_id=authenticated.user.user_id,
        artifact_id=artifact_id,
    )
    intake.record_artifact_access(
        owner_user_id=artifact.owner_user_id,
        artifact_id=artifact.artifact_id,
        actor_user_id=authenticated.user.user_id,
        action="view_metadata",
        request_id=getattr(http_request.state, "request_id", None),
        metadata={"route": "get_workspace_artifact"},
    )
    return ok(
        ArtifactDetailResponse(
            artifact=artifact,
            traces=intake.list_traces(
                owner_user_id=artifact.owner_user_id,
                artifact_id=artifact.artifact_id,
            ),
            access_events=intake.list_artifact_access_events(
                owner_user_id=artifact.owner_user_id,
                artifact_id=artifact.artifact_id,
            ),
        )
    )


@router.get("/artifacts/{artifact_id}/download")
def download_workspace_artifact(
    http_request: Request,
    artifact_id: NonBlankStr,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    intake: DocumentIntakeService = Depends(get_document_intake_service),
):
    """Download raw artifact bytes for a file in the current workspace."""

    workspace = governance.require_permission(
        user=authenticated.user,
        permission_scope="data:export",
    )
    organization_id = workspace.organization.organization_id
    artifact, via_workspace = _get_accessible_artifact(
        intake=intake,
        organization_id=organization_id,
        owner_user_id=authenticated.user.user_id,
        artifact_id=artifact_id,
    )
    if via_workspace:
        data = intake.get_workspace_artifact_bytes(
            organization_id=organization_id,
            artifact_id=artifact.artifact_id,
        )
    else:
        data = intake.get_artifact_bytes(
            owner_user_id=authenticated.user.user_id,
            artifact_id=artifact.artifact_id,
        )
    intake.record_artifact_access(
        owner_user_id=artifact.owner_user_id,
        artifact_id=artifact.artifact_id,
        actor_user_id=authenticated.user.user_id,
        action="download",
        request_id=getattr(http_request.state, "request_id", None),
        metadata={"route": "download_workspace_artifact", "byte_size": len(data)},
    )
    return StreamingResponse(
        io.BytesIO(data),
        media_type=artifact.mime_type,
        headers={
            "Content-Disposition": _content_disposition_filename(artifact.filename),
            "X-OJT-Artifact-ID": artifact.artifact_id,
        },
    )


def _filter_artifacts(
    artifacts: list[UploadedArtifact],
    *,
    q: str | None,
    mime_type: str | None,
    source: str | None,
) -> list[UploadedArtifact]:
    needle = (q or "").strip().lower()
    return [
        artifact
        for artifact in artifacts
        if (not needle or needle in artifact.filename.lower())
        and (not mime_type or artifact.mime_type == mime_type)
        and (not source or artifact.source == source)
    ]


def _get_accessible_artifact(
    *,
    intake: DocumentIntakeService,
    organization_id: str,
    owner_user_id: str,
    artifact_id: str,
) -> tuple[UploadedArtifact, bool]:
    try:
        return (
            intake.get_workspace_artifact(
                organization_id=organization_id,
                artifact_id=artifact_id,
            ),
            True,
        )
    except NotFoundError:
        return (
            intake.get_artifact(owner_user_id=owner_user_id, artifact_id=artifact_id),
            False,
        )


def _content_disposition_filename(filename: str) -> str:
    safe = sanitize_upload_filename(filename)
    return f"attachment; filename*=UTF-8''{quote(safe)}"
