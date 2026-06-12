"""Use cases for uploaded document intake and extraction."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ojtflow.application.artifact_retention import resolve_artifact_retention_policy
from ojtflow.application.background_job_service import BackgroundJobService
from ojtflow.application.ports import DatasetStore, DocumentExtractor, UploadedArtifactRepository
from ojtflow.core.contracts.artifacts import (
    ArtifactAccessEvent,
    ExtractionStepTrace,
    ParsingPipelineTrace,
    UploadedArtifact,
)
from ojtflow.core.contracts.enums import DataFormat
from ojtflow.core.contracts.jobs import BackgroundJob
from ojtflow.core.time import utc_now
from ojtflow.data_tools.document_analysis import build_document_intelligence_profile
from ojtflow.data_tools.extract import source_format_for_filename
from ojtflow.data_tools.hashing import sha256_text
from ojtflow.data_tools.redaction import build_redaction_preview


class DocumentIntakeService:
    """Register uploaded artifacts and run traceable document extraction."""

    def __init__(
        self,
        *,
        artifacts: UploadedArtifactRepository,
        datasets: DatasetStore,
        jobs: BackgroundJobService,
        extractor: DocumentExtractor,
        product_mode: str = "local_dev",
        retention_rules: tuple[dict[str, object], ...] = (),
    ) -> None:
        self.artifacts = artifacts
        self.datasets = datasets
        self.jobs = jobs
        self.extractor = extractor
        self.product_mode = product_mode
        self.retention_rules = retention_rules

    def register_upload(
        self,
        *,
        owner_user_id: str,
        filename: str,
        mime_type: str,
        data: bytes,
        source: str = "upload",
        request_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> UploadedArtifact:
        """Persist raw upload bytes and return artifact metadata."""

        artifact_metadata = {
            "request_id": request_id,
            "source_format": source_format_for_filename(filename),
        }
        artifact_metadata.update(metadata or {})
        retention_policy = resolve_artifact_retention_policy(
            product_mode=self.product_mode,
            owner_user_id=owner_user_id,
            source=source,
            mime_type=mime_type,
            filename=filename,
            rules=self.retention_rules,
        )
        return self.artifacts.put_bytes(
            owner_user_id=owner_user_id,
            filename=filename,
            mime_type=mime_type,
            data=data,
            source=source,
            retention_policy=retention_policy,
            metadata=artifact_metadata,
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

    def get_artifact_bytes(self, *, owner_user_id: str, artifact_id: str) -> bytes:
        return self.artifacts.get_bytes(owner_user_id=owner_user_id, artifact_id=artifact_id)

    def record_artifact_access(
        self,
        *,
        owner_user_id: str,
        artifact_id: str,
        actor_user_id: str,
        action: str,
        request_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> ArtifactAccessEvent:
        artifact = self.artifacts.get(owner_user_id=owner_user_id, artifact_id=artifact_id)
        event = ArtifactAccessEvent(
            artifact_id=artifact.artifact_id,
            owner_user_id=artifact.owner_user_id,
            actor_user_id=actor_user_id,
            action=action,
            request_id=request_id,
            metadata=metadata or {},
        )
        return self.artifacts.append_access_event(event)

    def list_artifact_access_events(
        self,
        *,
        owner_user_id: str,
        artifact_id: str,
    ) -> list[ArtifactAccessEvent]:
        return self.artifacts.list_access_events(
            owner_user_id=owner_user_id,
            artifact_id=artifact_id,
        )

    def list_traces(
        self,
        *,
        owner_user_id: str,
        artifact_id: str,
    ) -> list[ParsingPipelineTrace]:
        return self.artifacts.list_traces(owner_user_id=owner_user_id, artifact_id=artifact_id)

    def extracted_document_from_trace(
        self,
        *,
        artifact: UploadedArtifact,
        trace: ParsingPipelineTrace | None,
    ) -> dict[str, Any] | None:
        """Build caller-facing extracted text metadata from a completed trace."""

        if trace is None or not trace.text_storage_ref:
            return None
        text = self.datasets.get_text(trace.text_storage_ref)
        return {
            "filename": artifact.filename,
            "source_format": trace.source_format,
            "extractor_used": trace.extractor_chosen,
            "page_count": trace.page_count,
            "char_count": len(text),
            "word_count": len(text.split()),
            "text": text,
            "warnings": trace.warnings,
            "artifact_id": artifact.artifact_id,
            "job_id": trace.job_id,
            "trace_id": trace.trace_id,
            "text_dataset_id": trace.text_dataset_id,
            "text_storage_ref": trace.text_storage_ref,
            "source": artifact.source,
        }

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
        extractor_confidence = _extraction_confidence(
            text=text,
            warnings=result.warnings,
            extractor_used=result.extractor_used,
        )
        intelligence = build_document_intelligence_profile(
            data=data,
            filename=artifact.filename,
            source_format=result.source_format,
            extracted_text=text,
            extractor_used=result.extractor_used,
            extraction_confidence=extractor_confidence,
            extraction_warnings=list(result.warnings),
        )
        redaction_preview = build_redaction_preview(
            text,
            data_format=_redaction_data_format(result.source_format),
        )
        overall_confidence = min(extractor_confidence, intelligence.quality.score)
        trace_warnings = _dedupe_warnings(
            [*result.warnings, *intelligence.quality.warnings]
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
            confidence=extractor_confidence,
            metadata={
                "filename": artifact.filename,
                "mime_type": artifact.mime_type,
                "extension": artifact.extension,
                "extraction": dict(result.metadata),
                "quality_score": intelligence.quality.score,
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
            warnings=trace_warnings,
            char_count=len(text),
            token_count_estimate=_estimate_tokens(text),
            confidence=overall_confidence,
            text_sha256=sha256_text(text) if text else None,
            text_storage_ref=dataset.storage_ref,
            text_dataset_id=dataset.dataset_id,
            page_count=result.page_count,
            steps=[step],
            metadata={
                "original_filename": artifact.filename,
                "source": artifact.source,
                "duplicate_of_artifact_id": artifact.duplicate_of_artifact_id,
                "extraction": dict(result.metadata),
                "document_intelligence": intelligence.model_dump(mode="json"),
                "redaction_preview": _redaction_summary(redaction_preview),
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


def _dedupe_warnings(warnings: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for warning in warnings:
        if warning and warning not in seen:
            seen.add(warning)
            result.append(warning)
    return result


def _redaction_data_format(source_format: str) -> DataFormat | None:
    if source_format == "csv":
        return DataFormat.CSV
    if source_format == "json":
        return DataFormat.JSON
    if source_format == "yaml":
        return DataFormat.YAML
    if source_format == "markdown":
        return DataFormat.MARKDOWN
    return None


def _redaction_summary(preview) -> dict[str, object]:
    return {
        "match_count": len(preview.matches),
        "external_provider_block_recommended": preview.external_provider_block_recommended,
        "warnings": list(preview.warnings),
        "matches": [match.model_dump(mode="json") for match in preview.matches[:50]],
        "truncated": len(preview.matches) > 50,
    }
