"""Sanitized marker artifacts for retrieval reindex operations."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

from ojtflow.application.retrieval_reindex_safety import retrieval_manifest_hash
from ojtflow.core.contracts.retrieval import (
    EmbeddingReindexRollbackMarker,
    EmbeddingReindexSafetyReport,
    RetrievalIndexManifest,
)


def write_embedding_reindex_rollback_marker(
    *,
    data_dir: Path,
    before_manifest: RetrievalIndexManifest,
    safety_report: EmbeddingReindexSafetyReport,
    job_id: str | None = None,
    request_id: str | None = None,
) -> EmbeddingReindexRollbackMarker:
    """Persist a sanitized pre-reindex marker without storing raw corpus text."""

    marker = EmbeddingReindexRollbackMarker(
        job_id=job_id,
        request_id=request_id,
        approval_token_hash=safety_report.approval_token_hash,
        before_manifest_hash=retrieval_manifest_hash(before_manifest),
        before_lexical_generation_id=before_manifest.lexical_generation_id,
        before_embedding_generation_id=before_manifest.embedding_generation_id,
        before_graph_generation_id=before_manifest.graph_generation_id,
        corpus_ingestion_run_ids=list(before_manifest.corpus_ingestion_run_ids),
        rollback_note=(
            "This marker records the pre-reindex manifest. Use it to compare the "
            "active index after reindexing, then restore from database/file backups "
            "or rerun the previous corpus/embedding configuration if rollback is required."
        ),
    )
    marker_dir = data_dir / "repair_markers" / "embedding_reindex"
    marker_dir.mkdir(parents=True, exist_ok=True)
    marker_path = marker_dir / f"{marker.marker_id}.json"
    marker.marker_ref_hash = _ref_hash(marker_path.resolve().as_uri())
    payload = {
        "marker": marker.model_dump(mode="json"),
        "before_manifest": before_manifest.model_dump(mode="json"),
        "safety_report": safety_report.model_dump(
            mode="json",
            exclude={"approval_token"},
        ),
    }
    marker_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return marker


def _ref_hash(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"
