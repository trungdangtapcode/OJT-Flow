import base64
from datetime import datetime, timezone

import httpx
import pytest

from ojtflow.application.background_job_service import BackgroundJobService
from ojtflow.application.document_intake_service import DocumentIntakeService
from ojtflow.core.contracts.auth import AuthenticatedSession, SessionRecord, UserRecord
from ojtflow.data_tools.extract import ExtractionResult, Extractor, validate_extractor_choice
from ojtflow.infrastructure.storage.in_memory import (
    InMemoryBackgroundJobRepository,
    InMemoryDatasetStore,
    InMemoryUploadedArtifactRepository,
)
from ojtflow.interfaces.api.app import create_app
from ojtflow.interfaces.api.deps import get_document_intake_service, require_authentication


class FakeDocumentExtractor:
    def extract(self, *, data: bytes, filename: str, prefer: str = "auto") -> ExtractionResult:
        del data, filename, prefer
        return ExtractionResult(
            text="patient_id,value,unit\nP001,7.4,%\n",
            extractor_used="markitdown",
            source_format="csv",
            filename="lab.csv",
            warnings=["Header row detected automatically."],
            metadata={"provider": "local", "model": "fake-test-extractor"},
        )


def _service() -> DocumentIntakeService:
    return DocumentIntakeService(
        artifacts=InMemoryUploadedArtifactRepository(),
        datasets=InMemoryDatasetStore(),
        jobs=BackgroundJobService(InMemoryBackgroundJobRepository()),
        extractor=FakeDocumentExtractor(),
    )


def _service_with_retention_rules() -> DocumentIntakeService:
    return DocumentIntakeService(
        artifacts=InMemoryUploadedArtifactRepository(),
        datasets=InMemoryDatasetStore(),
        jobs=BackgroundJobService(InMemoryBackgroundJobRepository()),
        extractor=FakeDocumentExtractor(),
        product_mode="production",
        retention_rules=(
            {
                "rule_id": "prod_clipboard_phi_delete_7",
                "mode": "production",
                "source": "clipboard",
                "sensitivity_class": "potential_phi",
                "action": "delete_after_expiry",
                "retain_days": 7,
                "reason": "Production clipboard images expire quickly.",
            },
        ),
    )


async def _authenticated_dependency() -> AuthenticatedSession:
    now = datetime.now(timezone.utc)
    user = UserRecord(
        user_id="usr_1",
        google_sub="google-usr_1",
        email="reviewer@example.com",
        email_verified=True,
        display_name="Reviewer",
        avatar_url=None,
        created_at=now,
        updated_at=now,
        last_login_at=now,
    )
    return AuthenticatedSession(
        user=user,
        session=SessionRecord(
            session_id="ses_1",
            user_id=user.user_id,
            token_hash="hash",
            created_at=now,
            expires_at=now,
            revoked_at=None,
            last_seen_at=now,
        ),
    )


def test_upload_artifact_dedupes_bytes_and_preserves_upload_record() -> None:
    service = _service()
    first = service.register_upload(
        owner_user_id="usr_1",
        filename="lab.csv",
        mime_type="text/csv",
        data=b"patient_id,value\nP001,7.4\n",
    )
    second = service.register_upload(
        owner_user_id="usr_1",
        filename="copy.csv",
        mime_type="text/csv",
        data=b"patient_id,value\nP001,7.4\n",
    )

    assert first.duplicate_of_artifact_id is None
    assert second.duplicate_of_artifact_id == first.artifact_id
    assert second.storage_ref == first.storage_ref
    assert len(service.list_artifacts(owner_user_id="usr_1")) == 2


def test_upload_artifact_stamps_configurable_retention_policy() -> None:
    service = _service_with_retention_rules()
    artifact = service.register_upload(
        owner_user_id="usr_1",
        filename="clipboard.png",
        mime_type="image/png",
        data=b"fake-image",
        source="clipboard",
    )

    assert artifact.retention_policy.policy_id == "prod_clipboard_phi_delete_7"
    assert artifact.retention_policy.action == "delete_after_expiry"
    assert artifact.retention_policy.sensitivity_class == "potential_phi"
    assert artifact.retention_policy.retain_until


def test_file_parse_job_persists_trace_and_extracted_text_ref() -> None:
    service = _service()
    artifact = service.register_upload(
        owner_user_id="usr_1",
        filename="lab.csv",
        mime_type="text/csv",
        data=b"patient_id,value\nP001,7.4\n",
    )

    job = service.create_parse_job(
        owner_user_id="usr_1",
        artifact_id=artifact.artifact_id,
        prefer_extractor="markitdown",
        execute_now=True,
        request_id="req_test",
    )
    traces = service.list_traces(
        owner_user_id="usr_1",
        artifact_id=artifact.artifact_id,
    )

    assert job.status == "succeeded"
    assert job.output["trace"]["artifact_id"] == artifact.artifact_id
    assert traces[0].extractor_chosen == "markitdown"
    assert traces[0].char_count > 0
    assert traces[0].text_storage_ref
    assert traces[0].warnings == ["Header row detected automatically."]
    assert traces[0].metadata["extraction"]["model"] == "fake-test-extractor"
    intelligence = traces[0].metadata["document_intelligence"]
    assert intelligence["quality"]["score"] <= 1
    assert intelligence["quality"]["requires_review"] is True
    assert intelligence["explanation"]["read"]
    redaction = traces[0].metadata["redaction_preview"]
    assert redaction["match_count"] == 1
    assert redaction["external_provider_block_recommended"] is True


def test_openai_vision_is_valid_extractor_choice() -> None:
    assert validate_extractor_choice(Extractor.OPENAI_VISION) == "openai_vision"


def test_tesseract_is_valid_extractor_choice() -> None:
    assert validate_extractor_choice(Extractor.TESSERACT) == "tesseract"


@pytest.mark.asyncio
async def test_upload_parse_job_endpoint_creates_queued_artifact_job() -> None:
    service = _service()

    async def _intake_dependency() -> DocumentIntakeService:
        return service

    app = create_app()
    app.dependency_overrides[require_authentication] = _authenticated_dependency
    app.dependency_overrides[get_document_intake_service] = _intake_dependency
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/parse/upload/jobs",
            data={"extractor": "auto", "execute_now": "false"},
            files={"file": ("lab.csv", b"patient_id,value\nP001,7.4\n", "text/csv")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["data"]["job"]["status"] == "queued"
    assert body["data"]["job"]["job_type"] == "file_parse"
    assert body["data"]["artifact"]["filename"] == "lab.csv"
    assert body["data"]["artifact"]["sha256"]
    assert body["data"]["trace"] is None


@pytest.mark.asyncio
async def test_batch_upload_parse_job_endpoint_preserves_shared_metadata() -> None:
    service = _service()

    async def _intake_dependency() -> DocumentIntakeService:
        return service

    app = create_app()
    app.dependency_overrides[require_authentication] = _authenticated_dependency
    app.dependency_overrides[get_document_intake_service] = _intake_dependency
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/parse/upload/batch/jobs",
            data={
                "extractor": "auto",
                "execute_now": "false",
                "case_id": "case-123",
                "project_id": "project-alpha",
            },
            files=[
                ("files", ("lab-a.csv", b"patient_id,value\nP001,7.4\n", "text/csv")),
                ("files", ("lab-b.csv", b"patient_id,value\nP002,8.1\n", "text/csv")),
            ],
        )

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["data"]["case_id"] == "case-123"
    assert body["data"]["project_id"] == "project-alpha"
    assert len(body["data"]["items"]) == 2
    assert all(item["job"]["status"] == "queued" for item in body["data"]["items"])
    assert {item["artifact"]["metadata"]["batch_id"] for item in body["data"]["items"]} == {
        body["data"]["batch_id"]
    }
    assert all(
        item["artifact"]["metadata"]["case_id"] == "case-123"
        for item in body["data"]["items"]
    )


@pytest.mark.asyncio
async def test_clipboard_image_parse_job_endpoint_creates_artifact() -> None:
    service = _service()

    async def _intake_dependency() -> DocumentIntakeService:
        return service

    app = create_app()
    app.dependency_overrides[require_authentication] = _authenticated_dependency
    app.dependency_overrides[get_document_intake_service] = _intake_dependency
    transport = httpx.ASGITransport(app=app)
    payload = {
        "data_base64": base64.b64encode(b"fake-png-bytes").decode("ascii"),
        "mime_type": "image/png",
        "filename": "clipboard.png",
        "extractor": "auto",
        "execute_now": False,
    }

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/v1/parse/clipboard/images/jobs", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["data"]["job"]["status"] == "queued"
    assert body["data"]["artifact"]["source"] == "clipboard"
    assert body["data"]["artifact"]["mime_type"] == "image/png"
    assert body["data"]["artifact"]["filename"] == "clipboard.png"
    assert body["data"]["extracted_document"] is None


@pytest.mark.asyncio
async def test_clipboard_image_parse_job_endpoint_returns_extracted_document_when_run_now() -> None:
    service = _service()

    async def _intake_dependency() -> DocumentIntakeService:
        return service

    app = create_app()
    app.dependency_overrides[require_authentication] = _authenticated_dependency
    app.dependency_overrides[get_document_intake_service] = _intake_dependency
    transport = httpx.ASGITransport(app=app)
    payload = {
        "data_base64": base64.b64encode(b"fake-png-bytes").decode("ascii"),
        "mime_type": "image/png",
        "filename": "clipboard.png",
        "extractor": "auto",
        "execute_now": True,
    }

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/v1/parse/clipboard/images/jobs", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["data"]["job"]["status"] == "succeeded"
    extracted = body["data"]["extracted_document"]
    assert extracted["text"] == "patient_id,value,unit\nP001,7.4,%\n"
    assert extracted["artifact_id"] == body["data"]["artifact"]["artifact_id"]
    assert extracted["trace_id"] == body["data"]["trace"]["trace_id"]
    assert extracted["source"] == "clipboard"


@pytest.mark.asyncio
async def test_artifact_download_export_and_access_events_are_audited() -> None:
    service = _service()

    async def _intake_dependency() -> DocumentIntakeService:
        return service

    app = create_app()
    app.dependency_overrides[require_authentication] = _authenticated_dependency
    app.dependency_overrides[get_document_intake_service] = _intake_dependency
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        upload = await client.post(
            "/api/v1/parse/upload/jobs",
            data={"extractor": "auto", "execute_now": "false"},
            files={"file": ("lab.csv", b"patient_id,value\nP001,7.4\n", "text/csv")},
        )
        artifact_id = upload.json()["data"]["artifact"]["artifact_id"]
        download = await client.get(f"/api/v1/parse/artifacts/{artifact_id}/download")
        export = await client.get(f"/api/v1/parse/artifacts/{artifact_id}/export")
        access = await client.get(f"/api/v1/parse/artifacts/{artifact_id}/access-events")

    assert download.status_code == 200
    assert download.content == b"patient_id,value\nP001,7.4\n"
    assert download.headers["x-ojt-artifact-id"] == artifact_id
    assert "attachment" in download.headers["content-disposition"]
    assert export.status_code == 200
    export_actions = [event["action"] for event in export.json()["data"]["access_events"]]
    assert "download" in export_actions
    assert "export_metadata" in export_actions
    assert access.status_code == 200
    access_actions = [event["action"] for event in access.json()["data"]]
    assert "download" in access_actions
    assert "export_metadata" in access_actions
