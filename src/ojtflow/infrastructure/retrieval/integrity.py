"""Integrity checks for trusted retrieval knowledge indexes."""

from __future__ import annotations

import json
from collections import defaultdict
from hashlib import sha256
from typing import Iterable

from ojtflow.core.contracts.retrieval import (
    RetrievalIntegrityItem,
    RetrievalIntegrityReport,
)
from ojtflow.infrastructure.retrieval.engine import KnowledgeChunk


def build_integrity_report(
    *,
    repository: str,
    expected_chunks: list[KnowledgeChunk],
    indexed_chunks: list[KnowledgeChunk],
    checked_scope: str,
) -> RetrievalIntegrityReport:
    """Compare expected trusted chunks with currently indexed chunks."""

    expected_by_source = _group_by_source(expected_chunks)
    indexed_by_source = _group_by_source(indexed_chunks)
    source_ids = sorted(set(expected_by_source).union(indexed_by_source))
    checks: list[RetrievalIntegrityItem] = []

    for source_id in source_ids:
        expected = expected_by_source.get(source_id, [])
        indexed = indexed_by_source.get(source_id, [])
        expected_hash = _source_hash(expected) if expected else None
        indexed_hash = _source_hash(indexed) if indexed else None
        if expected and indexed and expected_hash == indexed_hash:
            status = "ok"
            message = "Indexed source matches trusted source content."
        elif expected and not indexed:
            status = "missing"
            message = "Trusted source is missing from the retrieval index."
        elif not expected and indexed:
            status = "extra"
            message = "Indexed source is not part of the selected trusted source scope."
        else:
            status = "stale"
            message = "Indexed source differs from trusted source content."
        checks.append(
            RetrievalIntegrityItem(
                source_id=source_id,
                status=status,
                expected_chunk_count=len(expected),
                indexed_chunk_count=len(indexed),
                expected_hash=expected_hash,
                indexed_hash=indexed_hash,
                message=message,
            )
        )

    stale_count = _status_count(checks, "stale")
    missing_count = _status_count(checks, "missing")
    extra_count = _status_count(checks, "extra")
    warnings = [
        check.message + f" source_id={check.source_id}"
        for check in checks
        if check.status in {"stale", "missing", "extra"}
    ]
    return RetrievalIntegrityReport(
        repository=repository,
        status="ok" if not warnings else "warning",
        checked_scope=checked_scope,
        expected_source_count=len(expected_by_source),
        indexed_source_count=len(indexed_by_source),
        ok_count=_status_count(checks, "ok"),
        stale_count=stale_count,
        missing_count=missing_count,
        extra_count=extra_count,
        checks=checks,
        warnings=warnings,
    )


def _group_by_source(chunks: Iterable[KnowledgeChunk]) -> dict[str, list[KnowledgeChunk]]:
    grouped: dict[str, list[KnowledgeChunk]] = defaultdict(list)
    for chunk in chunks:
        grouped[chunk.source_id].append(chunk)
    return {
        source_id: sorted(source_chunks, key=lambda chunk: chunk.chunk_id)
        for source_id, source_chunks in grouped.items()
    }


def _source_hash(chunks: list[KnowledgeChunk]) -> str:
    payload = [_chunk_payload(chunk) for chunk in chunks]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _chunk_payload(chunk: KnowledgeChunk) -> dict:
    return {
        "chunk_id": chunk.chunk_id,
        "source_id": chunk.source_id,
        "source_type": chunk.source_type.value,
        "title": chunk.title,
        "content": chunk.content,
        "source_version": chunk.source_version,
        "trust_level": chunk.trust_level.value,
        "clinical_domain": chunk.clinical_domain,
        "standard_system": chunk.standard_system,
        "locator": chunk.locator,
        "metadata": chunk.metadata,
    }


def _status_count(checks: list[RetrievalIntegrityItem], status: str) -> int:
    return sum(1 for check in checks if check.status == status)
