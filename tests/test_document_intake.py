from ojtflow.application.background_job_service import BackgroundJobService
from ojtflow.application.document_intake_service import DocumentIntakeService
from ojtflow.data_tools.extract import Extractor, validate_extractor_choice
from ojtflow.infrastructure.extraction.document import LocalDocumentExtractor
from ojtflow.infrastructure.storage.in_memory import (
    InMemoryBackgroundJobRepository,
    InMemoryDatasetStore,
    InMemoryUploadedArtifactRepository,
)


_ONE_PIXEL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x04\x00\x00\x00\xb5\x1c\x0c\x02"
    b"\x00\x00\x00\x0bIDATx\xdacd\xf8\xff\x1f\x00\x03\x03"
    b"\x02\x00\xef\xbf\xa7\xdb\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _service() -> DocumentIntakeService:
    return DocumentIntakeService(
        artifacts=InMemoryUploadedArtifactRepository(),
        datasets=InMemoryDatasetStore(),
        jobs=BackgroundJobService(InMemoryBackgroundJobRepository()),
        extractor=LocalDocumentExtractor(),
    )


def _service_with_retention_rules() -> DocumentIntakeService:
    return DocumentIntakeService(
        artifacts=InMemoryUploadedArtifactRepository(),
        datasets=InMemoryDatasetStore(),
        jobs=BackgroundJobService(InMemoryBackgroundJobRepository()),
        extractor=LocalDocumentExtractor(),
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
        data=_ONE_PIXEL_PNG,
        source="clipboard",
    )

    assert artifact.retention_policy.policy_id == "prod_clipboard_phi_delete_7"
    assert artifact.retention_policy.action == "delete_after_expiry"
    assert artifact.retention_policy.sensitivity_class == "potential_phi"
    assert artifact.retention_policy.retain_until


def test_openai_vision_is_valid_extractor_choice() -> None:
    assert validate_extractor_choice(Extractor.OPENAI_VISION) == "openai_vision"


def test_tesseract_is_valid_extractor_choice() -> None:
    assert validate_extractor_choice(Extractor.TESSERACT) == "tesseract"
