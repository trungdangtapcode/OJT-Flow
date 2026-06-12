"""PHI-safe private corpus ingestion helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from hashlib import sha256

from ojtflow.core.contracts.artifacts import ArtifactRetentionPolicy
from ojtflow.core.contracts.enums import EvidenceSourceType, TrustLevel
from ojtflow.core.contracts.redaction import RedactionPreview
from ojtflow.core.contracts.retrieval import (
    PrivateCorpusIngestionResult,
    RetrievalSource,
)
from ojtflow.infrastructure.retrieval.engine import KnowledgeChunk, sources_from_chunks

PRIVATE_DOCUMENTS_PARTITION_ID = "private_documents"
PRIVATE_DOCUMENTS_PARTITION_LABEL = "Private Documents"
PRIVATE_DOCUMENTS_PURPOSE = "private_document"
PRIVATE_DOCUMENTS_VISIBILITY = "private"


@dataclass(frozen=True)
class PrivateCorpusBuild:
    """Prepared private corpus chunks plus source inventory metadata."""

    chunks: list[KnowledgeChunk]
    source: RetrievalSource


def build_private_corpus_chunks(
    *,
    owner_user_id: str,
    organization_id: str,
    title: str,
    text: str,
    redaction_preview: RedactionPreview,
    retention_policy: ArtifactRetentionPolicy,
    source_ref: str | None = None,
    artifact_id: str | None = None,
    request_id: str | None = None,
    max_chars: int = 1200,
    overlap_chars: int = 160,
) -> PrivateCorpusBuild:
    """Build private-document retrieval chunks from already-redacted text."""

    indexed_text = redaction_preview.redacted_text
    source_id = _source_id(
        organization_id=organization_id,
        artifact_id=artifact_id,
        source_ref=source_ref,
        title=title,
        indexed_text=indexed_text,
    )
    source_version = f"private-redacted:{_short_hash(indexed_text)}"
    chunks: list[KnowledgeChunk] = []
    for index, chunk_text in enumerate(
        _chunk_text(indexed_text, max_chars=max_chars, overlap_chars=overlap_chars)
    ):
        chunk_id = f"chunk_private_{_short_hash(f'{source_id}:{index}:{chunk_text}')}"
        locator = {
            "source_ref": source_ref,
            "artifact_id": artifact_id,
            "chunk_index": index,
        }
        metadata = _metadata(
            owner_user_id=owner_user_id,
            organization_id=organization_id,
            title=title,
            source_ref=source_ref,
            artifact_id=artifact_id,
            request_id=request_id,
            redaction_preview=redaction_preview,
            retention_policy=retention_policy,
            original_text=text,
            indexed_text=indexed_text,
            chunk_text=chunk_text,
        )
        chunks.append(
            KnowledgeChunk(
                chunk_id=chunk_id,
                source_id=source_id,
                source_type=EvidenceSourceType.INPUT_DATA,
                title=title,
                content=chunk_text,
                source_version=source_version,
                trust_level=TrustLevel.USER_PROVIDED,
                clinical_domain="private_document",
                locator=locator,
                metadata=metadata,
            )
        )
    source = sources_from_chunks(chunks)[0]
    return PrivateCorpusBuild(chunks=chunks, source=source)


def private_corpus_ingestion_result(
    *,
    build: PrivateCorpusBuild,
    owner_user_id: str,
    organization_id: str,
    title: str,
    original_text: str,
    redaction_preview: RedactionPreview,
    retention_policy: ArtifactRetentionPolicy,
    source_ref: str | None = None,
    artifact_id: str | None = None,
) -> PrivateCorpusIngestionResult:
    """Build the API-facing result for a completed private corpus ingestion."""

    warnings: list[str] = []
    if redaction_preview.matches:
        warnings.append("indexed_redacted_text_only")
    if redaction_preview.requires_review:
        warnings.append("redaction_review_required")
    if redaction_preview.external_provider_block_recommended:
        warnings.append("external_provider_blocked_for_private_corpus")
    return PrivateCorpusIngestionResult(
        source_id=build.source.source_id,
        source=build.source,
        chunk_count=len(build.chunks),
        organization_id=organization_id,
        owner_user_id=owner_user_id,
        title=title,
        source_ref=source_ref,
        artifact_id=artifact_id,
        original_text_sha256=f"sha256:{sha256(original_text.encode('utf-8')).hexdigest()}",
        indexed_text_sha256=(
            f"sha256:{sha256(redaction_preview.redacted_text.encode('utf-8')).hexdigest()}"
        ),
        redaction_preview=redaction_preview,
        retention_policy=retention_policy,
        external_provider_allowed=False,
        requires_review=redaction_preview.requires_review,
        warnings=warnings,
        metadata={
            "corpus_partition_id": PRIVATE_DOCUMENTS_PARTITION_ID,
            "corpus_visibility": PRIVATE_DOCUMENTS_VISIBILITY,
            "redaction_match_count": len(redaction_preview.matches),
            "indexed_text": "redacted",
        },
    )


def _metadata(
    *,
    owner_user_id: str,
    organization_id: str,
    title: str,
    source_ref: str | None,
    artifact_id: str | None,
    request_id: str | None,
    redaction_preview: RedactionPreview,
    retention_policy: ArtifactRetentionPolicy,
    original_text: str,
    indexed_text: str,
    chunk_text: str,
) -> dict[str, object]:
    return {
        "origin": "private_corpus",
        "owner_user_id": owner_user_id,
        "organization_id": organization_id,
        "title": title,
        "source_ref": source_ref,
        "artifact_id": artifact_id,
        "request_id": request_id,
        "corpus_partition_id": PRIVATE_DOCUMENTS_PARTITION_ID,
        "corpus_partition_label": PRIVATE_DOCUMENTS_PARTITION_LABEL,
        "corpus_partition_purpose": PRIVATE_DOCUMENTS_PURPOSE,
        "corpus_visibility": PRIVATE_DOCUMENTS_VISIBILITY,
        "external_provider_allowed": False,
        "phi_allowed": True,
        "requires_reviewer_approval": True,
        "retention_policy_id": retention_policy.policy_id,
        "retention_policy": retention_policy.model_dump(mode="json"),
        "redaction_policy_id": redaction_preview.policy_id,
        "redaction_policy_version": redaction_preview.policy_version,
        "redaction_match_count": len(redaction_preview.matches),
        "redaction_requires_review": redaction_preview.requires_review,
        "external_provider_block_recommended": (
            redaction_preview.external_provider_block_recommended
        ),
        "original_text_sha256": f"sha256:{sha256(original_text.encode('utf-8')).hexdigest()}",
        "indexed_text_sha256": f"sha256:{sha256(indexed_text.encode('utf-8')).hexdigest()}",
        "chunk_content_hash": f"sha256:{sha256(chunk_text.encode('utf-8')).hexdigest()}",
        "index_decision": "redacted_private_text_indexed",
        "approved_for_indexing": not redaction_preview.reveal_required,
    }


def _source_id(
    *,
    organization_id: str,
    artifact_id: str | None,
    source_ref: str | None,
    title: str,
    indexed_text: str,
) -> str:
    stable_input = artifact_id or source_ref or f"{title}:{_short_hash(indexed_text)}"
    return f"private_document:{_slug(organization_id)}:{_slug(stable_input)}"


def _chunk_text(text: str, *, max_chars: int, overlap_chars: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    chunks: list[str] = []
    cursor = 0
    step = max(1, max_chars - overlap_chars)
    while cursor < len(text):
        chunks.append(text[cursor : cursor + max_chars].strip())
        cursor += step
    return [chunk for chunk in chunks if chunk]


def _short_hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()[:16]


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value.strip()).strip("_")[:80] or "private"
