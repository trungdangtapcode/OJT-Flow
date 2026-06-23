"""Celery application for OJTFlow workers."""

from __future__ import annotations

from ojtflow.config import get_settings
from ojtflow.observability.sentry import configure_sentry

try:
    from celery import Celery
except ImportError as exc:  # pragma: no cover - exercised in deployment images
    raise RuntimeError(
        "Celery is required when OJT_QUEUE_BACKEND=rabbitmq. "
        "Install the queue runtime dependencies before starting workers."
    ) from exc


def build_celery_app() -> Celery:
    settings = get_settings()
    configure_sentry(settings, runtime="celery-worker")
    app = Celery("ojtflow", broker=settings.rabbitmq_url)
    app.conf.update(
        task_default_queue=settings.default_queue_name,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        worker_prefetch_multiplier=1,
        task_time_limit=settings.celery_task_time_limit_seconds,
        task_soft_time_limit=settings.celery_task_soft_time_limit_seconds,
        task_routes={
            "ojtflow.run_background_job": {"queue": settings.default_queue_name},
        },
    )
    return app


celery_app = build_celery_app()


@celery_app.task(name="ojtflow.run_background_job", bind=True)
def run_background_job_task(_task, owner_user_id: str, job_id: str) -> dict:
    from ojtflow.infrastructure.queue.worker_jobs import run_background_job

    return run_background_job(owner_user_id=owner_user_id, job_id=job_id)

