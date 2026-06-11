from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from ojtflow.application.tool_audit import append_tool_audit_record
from ojtflow.core.contracts.audit import AuditRecord
from ojtflow.core.contracts.auth import AuthenticatedSession, SessionRecord, UserRecord
from ojtflow.infrastructure.storage.in_memory import InMemoryAuditRepository
from ojtflow.infrastructure.storage.sqlite import SQLiteAuditRepository, SQLiteBackboneStore
from ojtflow.interfaces.api.app import create_app
from ojtflow.interfaces.api.deps import get_audit_repository, require_authentication


def test_tool_audit_redacts_payload_and_links_workflow_refs() -> None:
    repository = InMemoryAuditRepository()

    record = append_tool_audit_record(
        repository,
        action_prefix="assistant",
        tool_name="validate_with_evidence",
        arguments={
            "data": "patient_id,ssn\nP001,123-45-6789\n",
            "query": "does SSN count as PHI",
            "schema_id": "lab_result_v1",
        },
        output={
            "status": "completed",
            "output": {
                "workflow_id": "wf_audit_demo",
                "audit_event_refs": ["evt_parser", "evt_validation"],
            },
        },
        owner_user_id="usr_audit",
        request_id="req_audit",
        assistant_session_id="ses_audit",
        actor_type="assistant",
    )

    assert record is not None
    assert record.action == "assistant.tool.validate_with_evidence"
    assert record.owner_user_id == "usr_audit"
    assert record.workflow_id == "wf_audit_demo"
    assert record.workflow_event_refs == ["evt_parser", "evt_validation"]
    assert record.assistant_session_id == "ses_audit"
    assert len(record.input_hash or "") == 64
    assert len(record.output_hash or "") == 64
    assert record.metadata["data_char_count"] == 32

    public_record = record.model_dump_json()
    assert "123-45-6789" not in public_record
    assert "patient_id,ssn" not in public_record
    assert "does SSN count as PHI" not in public_record


def test_sqlite_audit_repository_persists_across_restart(tmp_path: Path) -> None:
    backbone = SQLiteBackboneStore(tmp_path / "ojtflow.db", tmp_path / "var")
    repository = SQLiteAuditRepository(backbone)
    repository.append(
        AuditRecord(
            owner_user_id="usr_sqlite_audit",
            workflow_id="wf_sqlite_audit",
            assistant_session_id="ses_sqlite_audit",
            request_id="req_sqlite_audit",
            action="mcp.tool.start_workflow",
            actor_id="usr_sqlite_audit",
            actor_type="mcp",
            status="completed",
            workflow_event_refs=["evt_created"],
            input_hash="a" * 64,
            output_hash="b" * 64,
            metadata={"tool_name": "start_workflow"},
        )
    )

    restarted = SQLiteAuditRepository(
        SQLiteBackboneStore(tmp_path / "ojtflow.db", tmp_path / "var")
    )
    records = restarted.list(
        owner_user_id="usr_sqlite_audit",
        workflow_id="wf_sqlite_audit",
        assistant_session_id="ses_sqlite_audit",
    )

    assert len(records) == 1
    assert records[0].action == "mcp.tool.start_workflow"
    assert records[0].workflow_event_refs == ["evt_created"]
    assert records[0].metadata["tool_name"] == "start_workflow"
    assert restarted.list(owner_user_id="usr_other") == []


@pytest.mark.asyncio
async def test_audit_records_api_is_owner_scoped() -> None:
    repository = InMemoryAuditRepository()
    repository.append(
        AuditRecord(
            owner_user_id="usr_api_audit",
            action="assistant.tool.validate_data",
            actor_id="usr_api_audit",
            actor_type="assistant",
            status="completed",
        )
    )
    repository.append(
        AuditRecord(
            owner_user_id="usr_other",
            action="assistant.tool.validate_data",
            actor_id="usr_other",
            actor_type="assistant",
            status="completed",
        )
    )

    async def authenticated() -> AuthenticatedSession:
        now = datetime.now(timezone.utc)
        return AuthenticatedSession(
            user=UserRecord(
                user_id="usr_api_audit",
                google_sub="google-usr-api-audit",
                email="audit@example.com",
                email_verified=True,
                display_name="Audit Tester",
                avatar_url=None,
                created_at=now,
                updated_at=now,
                last_login_at=now,
            ),
            session=SessionRecord(
                session_id="ses_api_audit",
                user_id="usr_api_audit",
                token_hash="hash",
                created_at=now,
                expires_at=now,
                revoked_at=None,
                last_seen_at=now,
            ),
        )

    async def audit_repository() -> InMemoryAuditRepository:
        return repository

    app = create_app()
    app.dependency_overrides[require_authentication] = authenticated
    app.dependency_overrides[get_audit_repository] = audit_repository

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/api/v1/audit/records",
            params={"action": "assistant.tool.validate_data"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert [record["owner_user_id"] for record in body["data"]] == ["usr_api_audit"]
