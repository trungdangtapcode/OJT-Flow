"""Application service for MedSigLIP medical image classification."""

from __future__ import annotations

from ojtflow.core.contracts.jobs import BackgroundJob
from ojtflow.core.contracts.medsiglip import (
    MedSiglipClassificationRequest,
    MedSiglipClassificationResult,
    MedSiglipServiceStatus,
)
from ojtflow.infrastructure.medsiglip.client import MedSiglipClient


class MedSiglipService:
    """Use case wrapper for local MedSigLIP inference."""

    def __init__(self, client: MedSiglipClient) -> None:
        self.client = client

    def classify(
        self,
        request: MedSiglipClassificationRequest,
    ) -> MedSiglipClassificationResult:
        return self.client.classify(request)

    def classify_from_job(self, job: BackgroundJob) -> dict:
        request = MedSiglipClassificationRequest.model_validate(
            {
                "images": job.input.get("images", []),
                "candidate_labels": job.input.get("candidate_labels", []),
                "include_embeddings": bool(job.input.get("include_embeddings", False)),
            }
        )
        result = self.classify(request)
        return result.model_dump(mode="json")

    def status(self) -> MedSiglipServiceStatus:
        return self.client.status()
