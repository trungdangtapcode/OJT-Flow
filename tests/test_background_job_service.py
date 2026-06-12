from ojtflow.application.background_job_service import BackgroundJobService
from ojtflow.infrastructure.storage.in_memory import InMemoryBackgroundJobRepository


def test_cancelled_background_job_is_not_run_by_sync_runner() -> None:
    service = BackgroundJobService(InMemoryBackgroundJobRepository())
    job = service.create_job(owner_user_id="usr_test", job_type="retrieval_reindex")
    cancelled = service.cancel_job(owner_user_id="usr_test", job_id=job.job_id)

    def handler(_job):
        raise AssertionError("Cancelled job should not execute")

    result = service.run_sync(
        owner_user_id="usr_test",
        job_id=job.job_id,
        handler=handler,
    )

    assert cancelled.status == "cancelled"
    assert result.status == "cancelled"
    assert result.error is not None
    assert result.error.code == "job_cancelled"
