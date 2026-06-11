"""Generic audit routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ojtflow.application.governance_service import GovernanceService
from ojtflow.application.ports import AuditRepository
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.interfaces.api.deps import (
    get_audit_repository,
    get_governance_service,
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
