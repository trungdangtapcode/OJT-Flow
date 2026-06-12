from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from ojtflow.application.tool_audit import append_tool_audit_record
from ojtflow.config import clear_settings_cache
from ojtflow.core.contracts.audit import AuditRecord
from ojtflow.core.contracts.auth import AuthenticatedSession, SessionRecord, UserRecord
from ojtflow.core.contracts.enums import ActorType, EventType, Severity
from ojtflow.core.contracts.events import WorkflowEvent
from ojtflow.infrastructure.storage.in_memory import InMemoryAuditRepository
from ojtflow.infrastructure.storage.sqlite import SQLiteAuditRepository, SQLiteBackboneStore
from ojtflow.interfaces.api.app import create_app
from ojtflow.interfaces.api.deps import (
    get_audit_repository,
    get_workflow_service,
    require_authentication,
)


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
    assert record.chain_scope == "owner_user:usr_audit"
    assert record.chain_sequence == 1
    assert record.previous_record_hash is None
    assert len(record.record_hash or "") == 64
    assert record.hash_algorithm == "sha256"
    assert record.chain_status == "linked"
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
            timestamp="2026-06-11T00:00:00+00:00",
            metadata={"tool_name": "start_workflow"},
        )
    )
    second = repository.append(
        AuditRecord(
            owner_user_id="usr_sqlite_audit",
            workflow_id="wf_sqlite_audit",
            assistant_session_id="ses_sqlite_audit",
            request_id="req_sqlite_audit_2",
            action="assistant.tool.validate_data",
            actor_id="usr_sqlite_audit",
            actor_type="assistant",
            status="completed",
            workflow_event_refs=["evt_validation"],
            input_hash="c" * 64,
            output_hash="d" * 64,
            timestamp="2026-06-11T00:00:01+00:00",
            metadata={"tool_name": "validate_data"},
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

    assert len(records) == 2
    latest, first = records
    assert first.action == "mcp.tool.start_workflow"
    assert first.workflow_event_refs == ["evt_created"]
    assert first.metadata["tool_name"] == "start_workflow"
    assert first.chain_scope == "owner_user:usr_sqlite_audit"
    assert first.chain_sequence == 1
    assert len(first.record_hash or "") == 64
    assert latest.action == "assistant.tool.validate_data"
    assert latest.chain_sequence == 2
    assert latest.previous_record_hash == first.record_hash
    assert latest.record_hash == second.record_hash
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


@pytest.mark.asyncio
async def test_audit_export_api_packages_records_events_and_coverage(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    repository = InMemoryAuditRepository()
    repository.append(
        AuditRecord(
            owner_user_id="usr_audit_export",
            workflow_id="wf_audit_export",
            workflow_event_refs=["evt_review_decided"],
            assistant_session_id="chat_audit_export",
            action="assistant.tool.validate_with_evidence",
            actor_id="usr_audit_export",
            actor_type="assistant",
            status="completed",
            input_hash="a" * 64,
            output_hash="b" * 64,
            metadata={"tool_name": "validate_with_evidence"},
        )
    )
    repository.append(
        AuditRecord(
            owner_user_id="usr_audit_export",
            workflow_id="wf_audit_export",
            action="auth.login",
            actor_id="usr_audit_export",
            actor_type="user",
            status="completed",
            request_id="req_auth_audit_export",
            metadata={"provider": "google"},
        )
    )
    repository.append(
        AuditRecord(
            owner_user_id="usr_other",
            workflow_id="wf_audit_export",
            action="assistant.tool.validate_with_evidence",
            actor_id="usr_other",
            actor_type="assistant",
            status="completed",
        )
    )
    created_event = WorkflowEvent(
        event_id="evt_workflow_created",
        workflow_id="wf_audit_export",
        actor_type=ActorType.SYSTEM,
        actor_id="workflow_service",
        event_type=EventType.WORKFLOW_CREATED,
        severity=Severity.INFO,
        summary="Workflow created",
    )
    review_event = WorkflowEvent(
        event_id="evt_review_decided",
        workflow_id="wf_audit_export",
        actor_type=ActorType.USER,
        actor_id="usr_audit_export",
        event_type=EventType.REVIEW_DECIDED,
        severity=Severity.INFO,
        summary="Review decision recorded: approve",
        metadata={"review_id": "rev_audit_export"},
    )

    class FakeWorkflowService:
        def list_events(
            self,
            workflow_id: str,
            owner_user_id: str | None = None,
        ) -> list[WorkflowEvent]:
            assert workflow_id == "wf_audit_export"
            assert owner_user_id == "usr_audit_export"
            return [created_event, review_event]

    async def authenticated() -> AuthenticatedSession:
        now = datetime.now(timezone.utc)
        return AuthenticatedSession(
            user=UserRecord(
                user_id="usr_audit_export",
                google_sub="google-usr-audit-export",
                email="audit-export@example.com",
                email_verified=True,
                display_name="Audit Export Tester",
                avatar_url=None,
                created_at=now,
                updated_at=now,
                last_login_at=now,
            ),
            session=SessionRecord(
                session_id="ses_audit_export",
                user_id="usr_audit_export",
                token_hash="hash",
                created_at=now,
                expires_at=now,
                revoked_at=None,
                last_seen_at=now,
            ),
        )

    async def audit_repository() -> InMemoryAuditRepository:
        return repository

    async def workflow_service() -> FakeWorkflowService:
        return FakeWorkflowService()

    app = create_app()
    app.dependency_overrides[require_authentication] = authenticated
    app.dependency_overrides[get_audit_repository] = audit_repository
    app.dependency_overrides[get_workflow_service] = workflow_service

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/api/v1/audit/export",
            params={"workflow_id": "wf_audit_export"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    package = body["data"]
    assert package["owner_user_id"] == "usr_audit_export"
    assert package["export_format"] == "json"
    assert package["summary"]["record_count"] == 2
    assert package["summary"]["workflow_event_count"] == 2
    assert package["summary"]["audit_event_like_count"] == 4
    assert package["summary"]["includes_raw_payloads"] is False
    assert package["records"][0]["owner_user_id"] == "usr_audit_export"
    assert [event["event_type"] for event in package["workflow_events"]] == [
        "workflow.created",
        "review.decided",
    ]
    audit_events_like = package["audit_events_like"]
    categories = {item["category"] for item in audit_events_like}
    assert {"workflow_event", "review_event", "auth_event", "tool_execution"}.issubset(
        categories
    )
    workflow_audit_event = next(
        item for item in audit_events_like if item["category"] == "workflow_event"
    )
    assert workflow_audit_event["source_event_ref"] == "evt_workflow_created"
    assert workflow_audit_event["action"] == "C"
    review_audit_event = next(
        item for item in audit_events_like if item["category"] == "review_event"
    )
    assert review_audit_event["resourceType"] == "AuditEvent"
    assert review_audit_event["source_event_ref"] == "evt_review_decided"
    assert review_audit_event["workflow_id"] == "wf_audit_export"
    assert review_audit_event["action"] == "U"
    assert any(
        entity["what"] == "rev_audit_export" and entity["type"] == "review"
        for entity in review_audit_event["entity"]
    )
    tool_record = next(
        record
        for record in package["records"]
        if record["action"] == "assistant.tool.validate_with_evidence"
    )
    tool_audit_event = next(
        item for item in audit_events_like if item["category"] == "tool_execution"
    )
    assert tool_audit_event["source_record_ref"] == tool_record["audit_id"]
    assert tool_audit_event["agent"][0]["type"] == "assistant"
    assert any(entity["role"] == "input_hash" for entity in tool_audit_event["entity"])
    assert "validate_with_evidence" in str(tool_audit_event["metadata"])
    auth_audit_event = next(
        item for item in audit_events_like if item["category"] == "auth_event"
    )
    assert auth_audit_event["request_id"] == "req_auth_audit_export"
    assert auth_audit_event["action"] == "C"
    exported_json = str(package)
    assert "patient_id,ssn" not in exported_json
    assert "123-45-6789" not in exported_json

    coverage = {item["scope"]: item for item in package["coverage"]}
    assert coverage["assistant_tool_calls"]["status"] == "covered"
    assert coverage["assistant_tool_calls"]["record_count"] == 1
    assert coverage["workflows"]["status"] == "partial"
    assert coverage["workflows"]["event_count"] == 2
    assert coverage["reviews"]["event_count"] == 1
    assert coverage["auth_events"]["status"] == "covered"
    assert coverage["auth_events"]["record_count"] == 1
    assert coverage["setting_changes"]["status"] == "not_available"
    assert coverage["source_ingestion"]["status"] == "not_available"
    clear_settings_cache()
