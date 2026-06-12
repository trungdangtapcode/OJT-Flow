"""Safety workflow helpers for embedding reindex operations."""

from __future__ import annotations

import json
from hashlib import sha256

from ojtflow.core.contracts.retrieval import (
    EmbeddingReindexImpactSummary,
    EmbeddingReindexQualityComparison,
    EmbeddingReindexSafetyReport,
    RetrievalIndexComponent,
    RetrievalIndexManifest,
)
from ojtflow.core.time import utc_now


def build_embedding_reindex_safety_report(
    *,
    current_manifest: RetrievalIndexManifest,
    include_seeded: bool = True,
    include_corpus: bool = True,
) -> EmbeddingReindexSafetyReport:
    """Build a deterministic dry-run report for an approval-gated reindex."""

    payload = _approval_payload(
        current_manifest=current_manifest,
        include_seeded=include_seeded,
        include_corpus=include_corpus,
    )
    payload_hash = _hash_payload(payload)
    approval_token = f"approve_embedding_reindex_{payload_hash.removeprefix('sha256:')[:20]}"
    vector = _component(current_manifest, "vector")
    warnings = []
    if current_manifest.summary.chunk_count == 0:
        warnings.append("No active retrieval chunks are available to reindex.")
    if vector and vector.stale_chunk_count:
        warnings.append(
            f"{vector.stale_chunk_count} chunk(s) have stale embedding generation metadata."
        )
    return EmbeddingReindexSafetyReport(
        version="embedding_reindex_safety_report.v1",
        generated_at=utc_now().isoformat(),
        approval_token=approval_token,
        approval_token_hash=_hash_text(approval_token),
        approval_payload_hash=payload_hash,
        impact=EmbeddingReindexImpactSummary(
            include_seeded=include_seeded,
            include_corpus=include_corpus,
            chunk_count=current_manifest.summary.chunk_count,
            source_count=current_manifest.summary.source_count,
            stale_chunk_count=current_manifest.summary.stale_chunk_count,
            current_embedding_generation_id=(
                vector.generation_id if vector else current_manifest.embedding_generation_id
            ),
            target_embedding_generation_id=current_manifest.embedding_generation_id,
            embedding_generation_changed=bool(
                vector
                and vector.generation_id
                and current_manifest.embedding_generation_id
                and vector.generation_id != current_manifest.embedding_generation_id
            ),
        ),
        current_manifest=current_manifest,
        warnings=warnings,
        required_operator_action=(
            "Submit approval_token unchanged to create an embedding_reindex job. "
            "The token is bound to the current index manifest and reindex scope."
        ),
        metadata={
            "approval_scope": "current_index_manifest",
            "job_type": "embedding_reindex",
        },
    )


def approval_token_matches_report(
    *,
    report: EmbeddingReindexSafetyReport,
    approval_token: str,
) -> bool:
    """Return whether a submitted token approves exactly this dry-run report."""

    return approval_token.strip() == report.approval_token


def retrieval_manifest_hash(manifest: RetrievalIndexManifest) -> str:
    """Hash a manifest without exposing raw source payloads."""

    return _hash_payload(manifest.model_dump(mode="json"))


def compare_embedding_reindex_manifests(
    *,
    before: RetrievalIndexManifest,
    after: RetrievalIndexManifest,
) -> EmbeddingReindexQualityComparison:
    """Compare preflight and post-run manifests for operator review."""

    before_runs = set(before.corpus_ingestion_run_ids)
    after_runs = set(after.corpus_ingestion_run_ids)
    warnings = []
    if after.summary.chunk_count < before.summary.chunk_count:
        warnings.append("Post-run chunk count is lower than the preflight manifest.")
    if after.summary.stale_chunk_count > before.summary.stale_chunk_count:
        warnings.append("Post-run stale chunk count increased.")
    status = "completed"
    if warnings:
        status = "warning"
    elif after.summary.stale_chunk_count < before.summary.stale_chunk_count:
        status = "improved"
    return EmbeddingReindexQualityComparison(
        status=status,
        before_manifest_hash=retrieval_manifest_hash(before),
        after_manifest_hash=retrieval_manifest_hash(after),
        chunk_count_before=before.summary.chunk_count,
        chunk_count_after=after.summary.chunk_count,
        chunk_count_delta=after.summary.chunk_count - before.summary.chunk_count,
        source_count_before=before.summary.source_count,
        source_count_after=after.summary.source_count,
        source_count_delta=after.summary.source_count - before.summary.source_count,
        stale_chunk_count_before=before.summary.stale_chunk_count,
        stale_chunk_count_after=after.summary.stale_chunk_count,
        stale_chunk_count_delta=(
            after.summary.stale_chunk_count - before.summary.stale_chunk_count
        ),
        embedding_generation_changed=(
            before.embedding_generation_id != after.embedding_generation_id
        ),
        corpus_ingestion_run_ids_added=sorted(after_runs - before_runs),
        corpus_ingestion_run_ids_removed=sorted(before_runs - after_runs),
        warnings=warnings,
    )


def _approval_payload(
    *,
    current_manifest: RetrievalIndexManifest,
    include_seeded: bool,
    include_corpus: bool,
) -> dict:
    vector = _component(current_manifest, "vector")
    return {
        "version": "embedding_reindex_approval_payload.v1",
        "repository": current_manifest.repository,
        "retrieval_framework": current_manifest.retrieval_framework,
        "lexical_generation_id": current_manifest.lexical_generation_id,
        "embedding_generation_id": current_manifest.embedding_generation_id,
        "graph_generation_id": current_manifest.graph_generation_id,
        "corpus_ingestion_run_ids": list(current_manifest.corpus_ingestion_run_ids),
        "include_seeded": include_seeded,
        "include_corpus": include_corpus,
        "chunk_count": current_manifest.summary.chunk_count,
        "source_count": current_manifest.summary.source_count,
        "stale_chunk_count": current_manifest.summary.stale_chunk_count,
        "vector_status": vector.status if vector else None,
        "vector_stale_chunk_count": vector.stale_chunk_count if vector else 0,
    }


def _component(
    manifest: RetrievalIndexManifest,
    component_id: str,
) -> RetrievalIndexComponent | None:
    return next(
        (component for component in manifest.components if component.component_id == component_id),
        None,
    )


def _hash_payload(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return _hash_text(encoded)


def _hash_text(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"
