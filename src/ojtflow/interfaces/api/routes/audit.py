"""Generic audit routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ojtflow.application.audit_export_service import build_audit_export_package
from ojtflow.application.governance_service import GovernanceService
from ojtflow.application.ports import AuditRepository
from ojtflow.application.workflow_service import WorkflowService
from ojtflow.core.contracts.audit import AuditExportFilters
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.core.errors import OJTFlowError
from ojtflow.interfaces.api.deps import (
    get_audit_repository,
    get_governance_service,
    get_workflow_service,
    require_authentication,
)
from ojtflow.interfaces.api.responses import ok

router = APIRouter(tags=["audit"])


@router.get("/audit/records")
async def list_audit_records(
    action: str | None = None,
    workflow_id: str | None = None,
    assistant_session_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    repository: AuditRepository = Depends(get_audit_repository),
) -> dict:
    governance.require_permission(user=authenticated.user, permission_scope="audit:read")
    return ok(
        repository.list(
            owner_user_id=authenticated.user.user_id,
            action=action,
            workflow_id=workflow_id,
            assistant_session_id=assistant_session_id,
            limit=limit,
        )
    )


@router.get("/audit/export")
async def export_audit_package(
    action: str | None = None,
    workflow_id: str | None = None,
    assistant_session_id: str | None = None,
    include_workflow_events: bool = Query(default=True),
    limit: int = Query(default=100, ge=1, le=500),
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    repository: AuditRepository = Depends(get_audit_repository),
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    """Export an owner-scoped audit package for compliance review."""

    governance.require_permission(user=authenticated.user, permission_scope="audit:read")
    filters = AuditExportFilters(
        action=action,
        workflow_id=workflow_id,
        assistant_session_id=assistant_session_id,
        limit=limit,
        include_workflow_events=include_workflow_events,
    )
    records = repository.list(
        owner_user_id=authenticated.user.user_id,
        action=action,
        workflow_id=workflow_id,
        assistant_session_id=assistant_session_id,
        limit=limit,
    )
    workflow_events = []
    workflow_event_limitations: list[str] = []
    if workflow_id and include_workflow_events:
        try:
            workflow_events = workflow_service.list_events(
                workflow_id,
                owner_user_id=authenticated.user.user_id,
            )
        except OJTFlowError as exc:
            workflow_event_limitations.append(str(exc))

    return ok(
        build_audit_export_package(
            owner_user_id=authenticated.user.user_id,
            filters=filters,
            records=records,
            workflow_events=workflow_events,
            workflow_event_limitations=workflow_event_limitations,
        )
    )
