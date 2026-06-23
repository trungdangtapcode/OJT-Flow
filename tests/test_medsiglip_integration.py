from ojtflow.application.medsiglip_service import MedSiglipService
from ojtflow.config import Settings
from ojtflow.core.contracts.jobs import BackgroundJob
from ojtflow.core.contracts.medsiglip import (
    MedSiglipClassificationResult,
    MedSiglipImageClassification,
    MedSiglipPrediction,
)
from ojtflow.infrastructure.queue.dispatcher import queue_for_job


class _FakeMedSiglipClient:
    def __init__(self) -> None:
        self.seen_candidate_labels: list[str] = []

    def classify(self, request):
        self.seen_candidate_labels = list(request.candidate_labels)
        return MedSiglipClassificationResult(
            model="google/medsiglip-448",
            device="cuda",
            classifications=[
                MedSiglipImageClassification(
                    image_index=0,
                    predictions=[MedSiglipPrediction(label="normal", score=0.9)],
                )
            ],
            elapsed_ms=1.0,
        )

    def status(self):
        raise AssertionError("status is not used in this test")


def test_medsiglip_jobs_route_to_dedicated_queue() -> None:
    settings = Settings(
        OJT_EMBEDDING_MODEL="text-embedding-3-small",
        OJT_MEDSIGLIP_QUEUE="vision-gpu",
    )
    job = BackgroundJob(
        owner_user_id="usr_test",
        job_type="medsiglip_classification",
    )

    assert queue_for_job(job, settings) == "vision-gpu"


def test_medsiglip_job_handler_ignores_worker_metadata() -> None:
    client = _FakeMedSiglipClient()
    service = MedSiglipService(client)  # type: ignore[arg-type]
    job = BackgroundJob(
        owner_user_id="usr_test",
        job_type="medsiglip_classification",
        input={
            "images": [{"image_base64": "aW1hZ2U=", "mime_type": "image/png"}],
            "candidate_labels": ["normal", "normal", "abnormal"],
            "include_embeddings": False,
            "request_id": "req_test",
        },
    )

    output = service.classify_from_job(job)

    assert output["model"] == "google/medsiglip-448"
    assert client.seen_candidate_labels == ["normal", "abnormal"]
