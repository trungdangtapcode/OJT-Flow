"""Worker-side durable job execution."""

from __future__ import annotations

from typing import Any

from ojtflow.core.contracts.jobs import JobError


def run_background_job(*, owner_user_id: str, job_id: str) -> dict[str, Any]:
    """Load one durable job and execute the handler for its job type."""

    from ojtflow.interfaces.api.deps import (
        _build_background_job_service,
        _build_document_intake_service,
        _build_medsiglip_service,
        _build_workflow_service,
    )
    from ojtflow.config import get_settings

    jobs = _build_background_job_service()
    job = jobs.get_job(owner_user_id=owner_user_id, job_id=job_id)
    if job.status in {"succeeded", "failed", "cancelled"}:
        return job.model_dump(mode="json")

    if job.job_type == "file_parse":
        intake = _build_document_intake_service()
        return jobs.run_sync(
            owner_user_id=owner_user_id,
            job_id=job_id,
            handler=intake._run_parse_job,
        ).model_dump(mode="json")

    if job.job_type == "retrieval_reindex":
        workflow = _build_workflow_service()
        return jobs.run_sync(
            owner_user_id=owner_user_id,
            job_id=job_id,
            handler=lambda running_job: workflow.reindex_retrieval(
                include_seeded=bool(running_job.input.get("include_seeded", True)),
                include_corpus=bool(running_job.input.get("include_corpus", True)),
            ),
        ).model_dump(mode="json")

    if job.job_type == "embedding_reindex":
        workflow = _build_workflow_service()
        settings = get_settings()

        def _run_embedding_reindex(running_job):
            from ojtflow.application.retrieval_reindex_safety import (
                build_embedding_reindex_safety_report,
                compare_embedding_reindex_manifests,
                retrieval_manifest_hash,
            )
            from ojtflow.infrastructure.retrieval.reindex_markers import (
                write_embedding_reindex_rollback_marker,
            )

            before_manifest = workflow.retrieval_index_manifest(
                owner_user_id=running_job.owner_user_id,
            )
            safety_report = build_embedding_reindex_safety_report(
                current_manifest=before_manifest,
                include_seeded=bool(running_job.input.get("include_seeded", True)),
                include_corpus=bool(running_job.input.get("include_corpus", True)),
            )
            if retrieval_manifest_hash(before_manifest) != running_job.input.get(
                "before_manifest_hash"
            ):
                raise RuntimeError("Embedding reindex manifest changed before worker execution.")
            rollback_marker = write_embedding_reindex_rollback_marker(
                data_dir=settings.resolved_data_dir,
                before_manifest=before_manifest,
                safety_report=safety_report,
                job_id=running_job.job_id,
                request_id=str(running_job.input.get("request_id") or "") or None,
            )
            reindex_output = workflow.reindex_retrieval(
                include_seeded=bool(running_job.input.get("include_seeded", True)),
                include_corpus=bool(running_job.input.get("include_corpus", True)),
            )
            after_manifest = workflow.retrieval_index_manifest(
                owner_user_id=running_job.owner_user_id,
            )
            comparison = compare_embedding_reindex_manifests(
                before=before_manifest,
                after=after_manifest,
            )
            return {
                "safety_report": safety_report.model_dump(
                    mode="json",
                    exclude={"approval_token"},
                ),
                "rollback_marker": rollback_marker.model_dump(mode="json"),
                "reindex_output": reindex_output,
                "after_manifest": after_manifest.model_dump(mode="json"),
                "quality_comparison": comparison.model_dump(mode="json"),
            }

        return jobs.run_sync(
            owner_user_id=owner_user_id,
            job_id=job_id,
            handler=_run_embedding_reindex,
        ).model_dump(mode="json")

    if job.job_type == "medsiglip_classification":
        medsiglip = _build_medsiglip_service()
        return jobs.run_sync(
            owner_user_id=owner_user_id,
            job_id=job_id,
            handler=medsiglip.classify_from_job,
        ).model_dump(mode="json")

    failed = jobs.repository.mark_failed(
        owner_user_id=owner_user_id,
        job_id=job_id,
        error=JobError(
            code="job_type_not_supported_by_worker",
            message=f"Worker does not support job type: {job.job_type}",
            details={"job_type": job.job_type},
        ),
    )
    return failed.model_dump(mode="json")
