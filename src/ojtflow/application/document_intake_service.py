"""Use cases for uploaded document intake and extraction."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ojtflow.application.background_job_service import BackgroundJobService
from ojtflow.application.ports import DatasetStore, DocumentExtractor, UploadedArtifactRepository
from ojtflow.core.contracts.artifacts import (
    ExtractionStepTrace,
    ParsingPipelineTrace,
    UploadedArtifact,
)
from ojtflow.core.contracts.jobs import BackgroundJob
from ojtflow.core.time import utc_now
from ojtflow.data_tools.extract import source_format_for_filename
from ojtflow.data_tools.hashing import sha256_text


class DocumentIntakeService:
    """Register uploaded artifacts and run traceable document extraction."""

    def __init__(
        self,
        *,
        artifacts: UploadedArtifactRepository,
        datasets: DatasetStore,
        jobs: BackgroundJobService,
        extractor: DocumentExtractor,
    ) -> None:
        self.artifacts = artifacts
        self.datasets = datasets
        self.jobs = jobs
        self.extractor = extractor

    def register_upload(
        self,
        *,
        owner_user_id: str,
        filename: str,
        mime_type: str,
        data: bytes,
        source: str = "upload",
        request_id: str | None = None,
    ) -> UploadedArtifact:
        """Persist raw upload bytes and return artifact metadata."""

        return self.artifacts.put_bytes(
            owner_user_id=owner_user_id,
            filename=filename,
            mime_type=mime_type,
            data=data,
            source=source,
            metadata={
                "request_id": request_id,
                "source_format": source_format_for_filename(filename),
            },
        )

    def create_parse_job(
        self,
        *,
        owner_user_id: str,
        artifact_id: str,
        prefer_extractor: str = "auto",
        execute_now: bool = True,
        request_id: str | None = None,
    ) -> BackgroundJob:
        """Create a durable parse job; optionally execute it in sync local mode."""

        job = self.jobs.create_job(
            owner_user_id=owner_user_id,
            job_type="file_parse",
            input={
                "artifact_id": artifact_id,
                "prefer_extractor": prefer_extractor,
                "request_id": request_id,
            },
        )
        if not execute_now:
            return job
        return self.jobs.run_sync(
            owner_user_id=owner_user_id,
            job_id=job.job_id,
            handler=self._run_parse_job,
        )

    def list_artifacts(self, *, owner_user_id: str, limit: int = 100) -> list[UploadedArtifact]:
        return self.artifacts.list(owner_user_id=owner_user_id, limit=limit)

    def get_artifact(self, *, owner_user_id: str, artifact_id: str) -> UploadedArtifact:
        return self.artifacts.get(owner_user_id=owner_user_id, artifact_id=artifact_id)

    def list_traces(
        self,
        *,
        owner_user_id: str,
        artifact_id: str,
    ) -> list[ParsingPipelineTrace]:
        return self.artifacts.list_traces(owner_user_id=owner_user_id, artifact_id=artifact_id)

    def _run_parse_job(self, job: BackgroundJob) -> dict[str, Any]:
        artifact_id = str(job.input.get("artifact_id") or "")
        prefer_extractor = str(job.input.get("prefer_extractor") or "auto")
        artifact = self.artifacts.get(
            owner_user_id=job.owner_user_id,
            artifact_id=artifact_id,
        )
        data = self.artifacts.get_bytes(
            owner_user_id=job.owner_user_id,
            artifact_id=artifact.artifact_id,
        )
        trace = self.extract_artifact(
            owner_user_id=job.owner_user_id,
            artifact=artifact,
            data=data,
            prefer_extractor=prefer_extractor,
            job_id=job.job_id,
        )
        return {
            "artifact": artifact.model_dump(mode="json"),
            "trace": trace.model_dump(mode="json"),
        }

    def extract_artifact(
        self,
        *,
        owner_user_id: str,
        artifact: UploadedArtifact,
        data: bytes,
        prefer_extractor: str = "auto",
        job_id: str | None = None,
    ) -> ParsingPipelineTrace:
        """Extract text from a stored artifact and persist a trace record."""

        started_at = utc_now().isoformat()
        result = self.extractor.extract(
            data=data,
            filename=artifact.filename,
            prefer=prefer_extractor,
        )
        completed_at = utc_now().isoformat()
        text = result.text or ""
        dataset = self.datasets.put_text(
            text,
            source_kind="extracted_text",
            declared_format="text",
            detected_format=result.source_format,
        )
        confidence = _extraction_confidence(
            text=text,
            warnings=result.warnings,
            extractor_used=result.extractor_used,
        )
        fallback_path = _fallback_path(prefer_extractor, result.extractor_used)
        step = ExtractionStepTrace(
            extractor=result.extractor_used,
            status="succeeded",
            started_at=started_at,
            completed_at=completed_at,
            summary=_step_summary(result.extractor_used, text),
            warnings=list(result.warnings),
            input_ref=artifact.storage_ref,
            output_ref=dataset.storage_ref,
            confidence=confidence,
            metadata={
                "filename": artifact.filename,
                "mime_type": artifact.mime_type,
                "extension": artifact.extension,
            },
        )
        trace = ParsingPipelineTrace(
            artifact_id=artifact.artifact_id,
            owner_user_id=owner_user_id,
            job_id=job_id,
            source_format=result.source_format,
            requested_extractor=prefer_extractor,
            extractor_chosen=result.extractor_used,
            fallback_path=fallback_path,
            warnings=list(result.warnings),
            char_count=len(text),
            token_count_estimate=_estimate_tokens(text),
            confidence=confidence,
            text_sha256=sha256_text(text) if text else None,
            text_storage_ref=dataset.storage_ref,
            text_dataset_id=dataset.dataset_id,
            page_count=result.page_count,
            steps=[step],
            metadata={
                "original_filename": artifact.filename,
                "source": artifact.source,
                "duplicate_of_artifact_id": artifact.duplicate_of_artifact_id,
            },
            started_at=started_at,
            completed_at=completed_at,
        )
        return self.artifacts.append_trace(trace)


def _fallback_path(prefer_extractor: str, extractor_used: str) -> list[str]:
    if prefer_extractor == "auto":
        return [extractor_used]
    if prefer_extractor == extractor_used:
        return [extractor_used]
    return [prefer_extractor, extractor_used]


def _estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


def _extraction_confidence(*, text: str, warnings: list[str], extractor_used: str) -> float:
    confidence = 0.95
    if not text.strip():
        confidence = 0.2
    if extractor_used in {"openai_vision", "mineru"}:
        confidence -= 0.05
    confidence -= min(0.35, 0.08 * len(warnings))
    return round(max(0.0, min(1.0, confidence)), 3)


def _step_summary(extractor_used: str, text: str) -> str:
    stem = Path(extractor_used).name
    if text.strip():
        return f"{stem} extracted {len(text)} characters."
    return f"{stem} completed but produced no text."
