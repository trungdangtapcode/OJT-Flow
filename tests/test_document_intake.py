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
