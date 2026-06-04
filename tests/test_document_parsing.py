from pathlib import Path
from datetime import datetime, timezone

import httpx
import pytest

from ojtflow.application.workflow_service import WorkflowService
from ojtflow.config import clear_settings_cache
from ojtflow.core.contracts.auth import (
    AuthenticatedSession,
    SessionRecord,
    UserRecord,
)
from ojtflow.core.contracts.enums import DataFormat, EventType, WorkflowStatus
from ojtflow.core.contracts.workflow import WorkflowState
from ojtflow.core.errors import ToolExecutionError, UnsupportedUploadError
from ojtflow.data_tools.extract import ExtractionResult, sanitize_upload_filename
from ojtflow.data_tools.parse import parse_data
from ojtflow.interfaces.api.app import create_app
from ojtflow.interfaces.api.deps import (
    clear_workflow_service_cache,
    get_workflow_service,
    require_authentication,
)
from ojtflow.infrastructure.retrieval.static import (
    StaticKnowledgeRepository,
    StaticRetrievalRepository,
)
from ojtflow.infrastructure.storage.in_memory import (
    InMemoryDatasetStore,
    InMemoryEventRepository,
    InMemoryWorkflowRepository,
)


ROOT = Path(__file__).resolve().parents[1]


def make_service() -> WorkflowService:
    return WorkflowService(
        datasets=InMemoryDatasetStore(),
        workflows=InMemoryWorkflowRepository(),
        events=InMemoryEventRepository(),
        knowledge=StaticKnowledgeRepository(ROOT / "knowledge"),
        retrieval=StaticRetrievalRepository(ROOT / "knowledge"),
    )


async def _client() -> httpx.AsyncClient:
    app = create_app()
    app.dependency_overrides[require_authentication] = _authenticated_session
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


def _authenticated_session() -> AuthenticatedSession:
    now = datetime.now(timezone.utc)
    return AuthenticatedSession(
        user=UserRecord(
            user_id="usr_document_parse_test",
            google_sub="google-document-parse-test",
            email="document-parse@example.com",
            email_verified=True,
            display_name="Document Parse Test",
            avatar_url=None,
            created_at=now,
            updated_at=now,
            last_login_at=now,
        ),
        session=SessionRecord(
            session_id="ses_document_parse_test",
            user_id="usr_document_parse_test",
            token_hash="hash",
            created_at=now,
            expires_at=now,
            revoked_at=None,
            last_seen_at=now,
        ),
    )


def test_sanitize_upload_filename_rejects_path_traversal() -> None:
    with pytest.raises(UnsupportedUploadError):
        sanitize_upload_filename("../../lab.pdf")

    with pytest.raises(UnsupportedUploadError):
        sanitize_upload_filename("..\\lab.pdf")


def test_markdown_table_parse_preserves_rows() -> None:
    parsed = parse_data(
        "| lab_name | value | unit |\n| --- | --- | --- |\n| HbA1c | 7.4 | % |\n",
        DataFormat.MARKDOWN,
        source_ref="memory://fixture",
    )

    assert parsed.records == [
        {"lab_name": "HbA1c", "value": "7.4", "unit": "%", "_source_row": 2}
    ]


def test_file_workflow_extraction_failure_is_persisted(monkeypatch) -> None:
    service = make_service()

    def fail_extract(*args, **kwargs):
        raise ToolExecutionError("extractor failed")

    monkeypatch.setattr("ojtflow.data_tools.extract.extract_document", fail_extract)

    workflow = service.start_workflow_from_file(
        instruction="Extract this PDF.",
        file_bytes=b"%PDF-1.4 demo",
        filename="lab_report.pdf",
    )
    persisted = service.get_workflow(workflow.workflow_id)
    events = service.list_events(workflow.workflow_id)

    assert workflow.status == WorkflowStatus.FAILED
    assert persisted.status == WorkflowStatus.FAILED
    assert persisted.input is not None
    assert persisted.handoff_context["raw_upload"]["filename"] == "lab_report.pdf"
    assert any(event.event_type == EventType.WORKFLOW_FAILED for event in events)


@pytest.mark.asyncio
async def test_api_upload_rejects_unsupported_extension(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    async with await _client() as client:
        response = await client.post(
            "/api/v1/parse/extract",
            files={"file": ("blocked.exe", b"demo", "application/octet-stream")},
            data={"extractor": "auto"},
        )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_upload"


@pytest.mark.asyncio
async def test_api_upload_enforces_size_limit(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("OJT_MAX_UPLOAD_BYTES", "4")
    clear_settings_cache()
    clear_workflow_service_cache()

    async with await _client() as client:
        response = await client.post(
            "/api/v1/parse/extract",
            files={"file": ("small.txt", b"12345", "text/plain")},
            data={"extractor": "auto"},
        )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "upload_too_large"


@pytest.mark.asyncio
async def test_api_upload_honors_configured_extension_allowlist(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("OJT_ALLOWED_UPLOAD_EXTENSIONS", ".txt")
    clear_settings_cache()
    clear_workflow_service_cache()

    async with await _client() as client:
        response = await client.post(
            "/api/v1/parse/extract",
            files={"file": ("blocked.pdf", b"%PDF-1.4 demo", "application/pdf")},
            data={"extractor": "auto"},
        )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_upload"


@pytest.mark.asyncio
async def test_api_upload_workflow_rejects_blank_instruction(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    async with await _client() as client:
        response = await client.post(
            "/api/v1/parse/upload/workflow",
            files={"file": ("report.txt", b"hello", "text/plain")},
            data={
                "instruction": "   ",
                "target_format": "json",
                "schema_id": "",
                "require_human_review": "true",
                "extractor": "auto",
            },
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "request_validation_error"


@pytest.mark.asyncio
async def test_api_upload_workflow_rejects_missing_instruction(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    async with await _client() as client:
        response = await client.post(
            "/api/v1/parse/upload/workflow",
            files={"file": ("report.txt", b"hello", "text/plain")},
            data={
                "target_format": "json",
                "schema_id": "",
                "require_human_review": "true",
                "extractor": "auto",
            },
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "request_validation_error"


@pytest.mark.asyncio
async def test_api_upload_workflow_normalizes_form_text(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    class FakeWorkflowService:
        def __init__(self) -> None:
            self.calls: list[dict] = []

        def start_workflow_from_file(
            self,
            *,
            instruction,
            file_bytes,
            filename,
            target_format,
            schema_id,
            require_human_review,
            prefer_extractor,
            owner_user_id,
        ):
            self.calls.append(
                {
                    "instruction": instruction,
                    "file_bytes": file_bytes,
                    "filename": filename,
                    "target_format": target_format,
                    "schema_id": schema_id,
                    "require_human_review": require_human_review,
                    "prefer_extractor": prefer_extractor,
                    "owner_user_id": owner_user_id,
                }
            )
            return WorkflowState(
                owner_user_id=owner_user_id,
                user_instruction=instruction,
                status=WorkflowStatus.COMPLETED,
            )

    fake_service = FakeWorkflowService()
    app = create_app()
    app.dependency_overrides[require_authentication] = _authenticated_session
    app.dependency_overrides[get_workflow_service] = lambda: fake_service
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/parse/upload/workflow",
            files={"file": ("report.txt", b"hello", "text/plain")},
            data={
                "instruction": "  Extract and explain this document.  ",
                "target_format": "json",
                "schema_id": "   ",
                "require_human_review": "true",
                "extractor": " AUTO ",
            },
        )

    assert response.status_code == 200
    assert fake_service.calls == [
        {
            "instruction": "Extract and explain this document.",
            "file_bytes": b"hello",
            "filename": "report.txt",
            "target_format": DataFormat.JSON,
            "schema_id": None,
            "require_human_review": True,
            "prefer_extractor": "auto",
            "owner_user_id": "usr_document_parse_test",
        }
    ]


@pytest.mark.asyncio
async def test_api_extract_only_uses_standard_envelope(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    def fake_extract(data: bytes, filename: str, prefer: str = "auto") -> ExtractionResult:
        return ExtractionResult(
            text="extracted text",
            extractor_used="fake",
            source_format="text",
            filename=filename,
        )

    monkeypatch.setattr("ojtflow.data_tools.extract.extract_document", fake_extract)

    async with await _client() as client:
        response = await client.post(
            "/api/v1/parse/extract",
            files={"file": ("report.txt", b"hello", "text/plain")},
            data={"extractor": "auto"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["data"]["text"] == "extracted text"


@pytest.mark.asyncio
async def test_api_upload_csv_workflow_bypasses_optional_extractors(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()
    csv_text = (ROOT / "data/fixtures/structured/lab_results_messy.csv").read_text()

    async with await _client() as client:
        response = await client.post(
            "/api/v1/parse/upload/workflow",
            files={"file": ("lab_results_messy.csv", csv_text.encode("utf-8"), "text/csv")},
            data={
                "instruction": "Clean this CSV, convert it to JSON, and explain anomalies.",
                "target_format": "json",
                "schema_id": "lab_result_v1",
                "require_human_review": "true",
                "extractor": "auto",
            },
        )

    assert response.status_code == 200
    workflow = response.json()["data"]
    assert workflow["status"] == WorkflowStatus.NEEDS_HUMAN_REVIEW.value
    assert workflow["input"]["declared_format"] == DataFormat.CSV.value
    assert workflow["handoff_context"]["extraction"]["extractor_used"] == "direct_text_upload"
    assert workflow["validation_report"]["issues"]


@pytest.mark.asyncio
async def test_api_upload_csv_workflow_returns_structured_error_for_decode_failure(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    async with await _client() as client:
        response = await client.post(
            "/api/v1/parse/upload/workflow",
            files={"file": ("bad.csv", b"\xff\xfe\x00", "text/csv")},
            data={
                "instruction": "Clean this CSV, convert it to JSON, and explain anomalies.",
                "target_format": "json",
                "schema_id": "lab_result_v1",
                "require_human_review": "true",
                "extractor": "auto",
            },
        )

        assert response.status_code == 422
        body = response.json()
        assert body["data"] is None
        assert body["error"]["code"] == "tool_execution_error"
        workflow_id = body["error"]["workflow_id"]
        assert workflow_id
        assert body["error"]["details"]["status"] == "failed"

        persisted = await client.get(f"/api/v1/workflows/{workflow_id}")
        assert persisted.status_code == 200
        workflow = persisted.json()["data"]
        assert workflow["status"] == WorkflowStatus.FAILED.value
        assert workflow["failure"]["code"] == "tool_execution_error"
        assert workflow["output"] is None
