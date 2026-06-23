"""Celery dispatch adapter for durable background jobs."""

from __future__ import annotations

from ojtflow.config import Settings
from ojtflow.core.contracts.jobs import BackgroundJob


class CeleryJobDispatcher:
    """Publish durable jobs to RabbitMQ/Celery workers."""

    queue_backed = True

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def enqueue(self, job: BackgroundJob) -> None:
        from ojtflow.infrastructure.queue.celery_app import celery_app

        celery_app.send_task(
            "ojtflow.run_background_job",
            args=[job.owner_user_id, job.job_id],
            queue=queue_for_job(job, self.settings),
            task_id=job.job_id,
        )


def queue_for_job(job: BackgroundJob, settings: Settings) -> str:
    if job.job_type in {"ocr_extract"}:
        return settings.ocr_queue_name
    if job.job_type == "file_parse":
        source_format = str(job.input.get("source_format") or "").lower()
        extractor = str(job.input.get("prefer_extractor") or "").lower()
        if source_format in {"pdf", "image"} or extractor in {
            "openai_vision",
            "tesseract",
            "mineru",
        }:
            return settings.ocr_queue_name
        return settings.ingestion_queue_name
    if job.job_type in {"retrieval_reindex", "embedding_reindex"}:
        return settings.embedding_queue_name
    if job.job_type == "medsiglip_classification":
        return settings.medsiglip_queue_name
    if job.job_type == "external_ingest":
        return settings.ingestion_queue_name
    if job.job_type == "export_package":
        return settings.export_queue_name
    return settings.default_queue_name
