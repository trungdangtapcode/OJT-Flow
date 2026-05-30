from pathlib import Path

import httpx
import pytest

from ojtflow.application.workflow_service import WorkflowService
from ojtflow.config import clear_settings_cache
from ojtflow.core.contracts.enums import DataFormat, EventType, WorkflowStatus
from ojtflow.core.errors import ToolExecutionError, UnsupportedUploadError
from ojtflow.data_tools.extract import ExtractionResult, sanitize_upload_filename
from ojtflow.data_tools.parse import parse_data
from ojtflow.interfaces.api.app import create_app
from ojtflow.interfaces.api.deps import clear_workflow_service_cache, require_authentication
from ojtflow.infrastructure.retrieval.static import StaticKnowledgeRepository
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
    )


async def _client() -> httpx.AsyncClient:
    app = create_app()
    app.dependency_overrides[require_authentication] = lambda: None
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


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
