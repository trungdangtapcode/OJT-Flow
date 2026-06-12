"""Local trusted corpus ingestion for retrieval."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path

from ojtflow.core.contracts.enums import EvidenceSourceType, TrustLevel
from ojtflow.core.contracts.retrieval import (
    CorpusAdapterCatalog,
    CorpusChunkingProfile,
    CorpusIngestionLedger,
    CorpusIngestionLedgerRecord,
    CorpusIngestionLedgerSummary,
    CorpusIngestionItem,
    CorpusIngestionManifest,
    CorpusLicenseMetadata,
    CorpusPartitionCatalog,
    CorpusSourceAdapter,
)
from ojtflow.infrastructure.retrieval.catalogs import (
    load_corpus_adapter_catalog,
    load_corpus_chunking_profile_catalog,
    load_corpus_partition_catalog,
)
from ojtflow.infrastructure.retrieval.corpus_partitions import (
    partition_metadata,
    resolve_corpus_partition,
)
from ojtflow.infrastructure.retrieval.engine import KnowledgeChunk


SUPPORTED_CORPUS_EXTENSIONS = {".md", ".txt", ".json", ".yaml", ".yml", ".csv"}


@dataclass(frozen=True)
class CorpusIndexResult:
    """Summary of local corpus ingestion."""

    files_seen: int
    files_indexed: int
    chunks_indexed: int
    skipped_files: list[str]
    manifest: CorpusIngestionManifest | None = None
    ledger: CorpusIngestionLedger | None = None

    def to_dict(self) -> dict:
        return {
            "files_seen": self.files_seen,
            "files_indexed": self.files_indexed,
            "chunks_indexed": self.chunks_indexed,
            "skipped_files": list(self.skipped_files),
            "manifest": (
                self.manifest.model_dump(mode="json") if self.manifest is not None else None
            ),
            "ledger": (
                self.ledger.model_dump(mode="json") if self.ledger is not None else None
            ),
        }


@dataclass(frozen=True)
class _ChunkRecord:
    text: str
    section_heading: str | None = None
    start_char: int = 0
    end_char: int = 0


def build_corpus_ingestion_manifest(
    corpus_dirs: tuple[Path, ...],
    *,
    knowledge_root: Path,
    generated_at: datetime | None = None,
) -> CorpusIngestionManifest:
    """Build a governed manifest for local corpus files available to ingestion."""

    catalog = load_corpus_adapter_catalog(knowledge_root)
    partition_catalog = load_corpus_partition_catalog(knowledge_root)
    adapters_by_path = _adapters_by_local_path(catalog, knowledge_root=knowledge_root)
    generated_at_value = _isoformat(generated_at or datetime.now(UTC))
    items: list[CorpusIngestionItem] = []
    for path in _iter_supported_corpus_files(corpus_dirs):
        relative = _display_path(path, knowledge_root)
        adapter = adapters_by_path.get(relative)
        text = _read_text(path)
        items.append(
            _manifest_item_for_file(
                path,
                text,
                knowledge_root=knowledge_root,
                adapter=adapter,
                adapter_catalog_version=catalog.version,
                partition_catalog=partition_catalog,
            )
        )
    return CorpusIngestionManifest(
        version="corpus_ingestion_manifest.v1",
        generated_at=generated_at_value,
        adapter_catalog_version=catalog.version,
        knowledge_root=_display_path(knowledge_root, knowledge_root),
        item_count=len(items),
        enabled_adapter_count=sum(1 for adapter in catalog.adapters if adapter.enabled),
        approved_item_count=sum(1 for item in items if item.reviewer_state == "approved"),
        needs_review_item_count=sum(
            1 for item in items if item.reviewer_state == "needs_review"
        ),
        items=items,
    )


def build_corpus_ingestion_ledger(
    corpus_dirs: tuple[Path, ...],
    *,
    knowledge_root: Path,
    max_chars: int,
    overlap_chars: int,
) -> CorpusIngestionLedger:
    """Build a chunk-level lineage ledger for the configured local corpus."""

    _chunks, result = load_local_corpus_chunks(
        corpus_dirs,
        knowledge_root=knowledge_root,
        max_chars=max_chars,
        overlap_chars=overlap_chars,
    )
    if result.ledger is None:
        manifest = result.manifest or build_corpus_ingestion_manifest(
            corpus_dirs,
            knowledge_root=knowledge_root,
        )
        return _ledger_from_chunks(
            [],
            manifest=manifest,
            knowledge_root=knowledge_root,
            max_chars=max_chars,
            overlap_chars=overlap_chars,
        )
    return result.ledger


def load_local_corpus_chunks(
    corpus_dirs: tuple[Path, ...],
    *,
    knowledge_root: Path,
    max_chars: int,
    overlap_chars: int,
) -> tuple[list[KnowledgeChunk], CorpusIndexResult]:
    """Load operator-provided trusted corpus files into retrieval chunks."""

    chunks: list[KnowledgeChunk] = []
    files_seen = 0
    files_indexed = 0
    skipped_files: list[str] = []
    manifest = build_corpus_ingestion_manifest(corpus_dirs, knowledge_root=knowledge_root)
    chunking_profiles = {
        profile.profile_id: profile
        for profile in load_corpus_chunking_profile_catalog(knowledge_root).profiles
    }
    manifest_by_path = {
        item.path: item
        for item in manifest.items
        if item.path
    }

    for corpus_dir in corpus_dirs:
        if not corpus_dir.exists():
            skipped_files.append(f"{_display_path(corpus_dir, knowledge_root)}:missing")
            continue
        if not corpus_dir.is_dir():
            skipped_files.append(f"{_display_path(corpus_dir, knowledge_root)}:not_directory")
            continue
        for path in sorted(corpus_dir.rglob("*")):
            if not path.is_file() or _has_hidden_part(path):
                continue
            files_seen += 1
            if path.suffix.lower() not in SUPPORTED_CORPUS_EXTENSIONS:
                skipped_files.append(f"{_display_path(path, knowledge_root)}:unsupported_extension")
                continue
            text = _read_text(path)
            if not text.strip():
                skipped_files.append(f"{_display_path(path, knowledge_root)}:blank")
                continue
            manifest_item = manifest_by_path.get(_display_path(path, knowledge_root))
            if manifest_item and (
                not manifest_item.enabled
                or manifest_item.lifecycle_state in {"blocked", "failed"}
            ):
                skipped_files.append(
                    f"{_display_path(path, knowledge_root)}:{manifest_item.lifecycle_state}"
                )
                continue
            files_indexed += 1
            chunks.extend(
                _chunks_for_file(
                    path,
                    text,
                    knowledge_root=knowledge_root,
                    max_chars=max_chars,
                    overlap_chars=overlap_chars,
                    manifest_item=manifest_item,
                    chunking_profiles=chunking_profiles,
                    ingestion_run_id=_ingestion_run_id(manifest),
                    adapter_catalog_version=manifest.adapter_catalog_version,
                )
            )

    ledger = _ledger_from_chunks(
        chunks,
        manifest=manifest,
        knowledge_root=knowledge_root,
        max_chars=max_chars,
        overlap_chars=overlap_chars,
    )
    return chunks, CorpusIndexResult(
        files_seen=files_seen,
        files_indexed=files_indexed,
        chunks_indexed=len(chunks),
        skipped_files=skipped_files[:50],
        manifest=manifest,
        ledger=ledger,
    )


def _chunks_for_file(
    path: Path,
    text: str,
    *,
    knowledge_root: Path,
    max_chars: int,
    overlap_chars: int,
    manifest_item: CorpusIngestionItem | None = None,
    chunking_profiles: dict[str, CorpusChunkingProfile] | None = None,
    ingestion_run_id: str | None = None,
    adapter_catalog_version: str | None = None,
) -> list[KnowledgeChunk]:
    relative = _display_path(path, knowledge_root)
    title = _title_from_text(path, text)
    source_id = f"corpus:{_stable_slug(relative)}"
    source_type = _source_type_for(path, text)
    clinical_domain = _clinical_domain_for(path, text)
    standard_system = _standard_system_for(path, text)
    source_version = "local-unversioned"
    metadata = {
        "origin": "local_corpus",
        "content_hash": sha256(text.encode("utf-8")).hexdigest(),
        "extension": path.suffix.lower(),
    }
    if manifest_item is not None:
        title = manifest_item.title
        source_id = manifest_item.source_id
        source_type = manifest_item.source_type
        clinical_domain = manifest_item.clinical_domain
        standard_system = manifest_item.standard_system
        source_version = manifest_item.release_version
        metadata.update(_metadata_from_manifest_item(manifest_item))
    profile = _chunking_profile_for_item(manifest_item, chunking_profiles or {})
    effective_max_chars = min(max_chars, profile.max_chars) if profile else max_chars
    effective_overlap_chars = (
        min(overlap_chars, profile.overlap_chars) if profile else overlap_chars
    )
    chunk_records = _chunk_records(
        text,
        max_chars=effective_max_chars,
        overlap_chars=effective_overlap_chars,
        profile=profile,
    )
    run_id = ingestion_run_id or "corpus_run:untracked"
    catalog_version = adapter_catalog_version or (
        str(manifest_item.metadata.get("adapter_catalog_version"))
        if manifest_item is not None
        else "unknown"
    )

    chunks: list[KnowledgeChunk] = []
    for index, record in enumerate(chunk_records):
        chunk_text = record.text
        chunk_hash = sha256(f"{relative}:{index}:{chunk_text}".encode("utf-8")).hexdigest()[:16]
        locator = {
            "path": relative,
            "chunk_index": index,
            "start_char": record.start_char,
            "end_char": record.end_char,
        }
        if record.section_heading:
            locator["section_heading"] = record.section_heading
        chunk_metadata = {
            **metadata,
            **_metadata_from_chunk_record(record, profile=profile),
            "ingestion_run_id": run_id,
            "ingestion_ledger_record_id": _ledger_record_id(
                ingestion_run_id=run_id,
                chunk_id=f"chunk_corpus_{chunk_hash}",
                raw_artifact_hash=str(metadata.get("content_hash") or "unknown"),
            ),
            "adapter_version": catalog_version,
            "chunk_content_hash": f"sha256:{sha256(chunk_text.encode('utf-8')).hexdigest()}",
            "index_decision": _index_decision(
                reviewer_state=str(metadata.get("reviewer_state") or "needs_review"),
                lifecycle_state=str(metadata.get("lifecycle_state") or "needs_review"),
            ),
            "approved_for_indexing": (
                metadata.get("reviewer_state") == "approved"
                and metadata.get("lifecycle_state") == "approved"
            ),
        }
        chunks.append(
            KnowledgeChunk(
                chunk_id=f"chunk_corpus_{chunk_hash}",
                source_id=source_id,
                source_type=source_type,
                title=title,
                content=chunk_text,
                source_version=source_version,
                trust_level=TrustLevel.APPROVED,
                clinical_domain=clinical_domain,
                standard_system=standard_system,
                locator=locator,
                metadata=chunk_metadata,
            )
        )
    return chunks


def _manifest_item_for_file(
    path: Path,
    text: str,
    *,
    knowledge_root: Path,
    adapter: CorpusSourceAdapter | None,
    adapter_catalog_version: str,
    partition_catalog: CorpusPartitionCatalog,
) -> CorpusIngestionItem:
    relative = _display_path(path, knowledge_root)
    stat = path.stat()
    content_hash = sha256(path.read_bytes()).hexdigest()
    fallback_license = CorpusLicenseMetadata(
        license_id="operator_provided",
        name="Operator-provided local corpus",
        constraints=[
            "Operator must confirm source rights and reviewer approval before production use"
        ],
    )
    source_id = f"corpus:{_stable_slug(relative)}"
    warnings: list[str] = []
    if adapter is None:
        warnings.append("uncataloged_local_corpus_file")
    elif not adapter.enabled:
        warnings.append("adapter_disabled")
    partition = resolve_corpus_partition(
        partition_catalog,
        source_id=adapter.source_id if adapter else source_id,
        source_type=adapter.source_type if adapter else _source_type_for(path, text),
        local_path=relative,
        metadata=adapter.metadata if adapter else None,
    )
    resolved_partition_metadata = partition_metadata(
        partition,
        organization_id=(
            str(adapter.metadata.get("organization_id"))
            if adapter and adapter.metadata.get("organization_id")
            else None
        ),
    )
    return CorpusIngestionItem(
        item_id=f"corpus_item:{_stable_slug(relative)}",
        source_id=source_id,
        adapter_id=adapter.adapter_id if adapter else None,
        title=adapter.title if adapter else _title_from_text(path, text),
        source_type=adapter.source_type if adapter else _source_type_for(path, text),
        clinical_domain=(
            adapter.clinical_domain if adapter else _clinical_domain_for(path, text)
        ),
        standard_system=(
            adapter.standard_system if adapter else _standard_system_for(path, text)
        ),
        release_version=adapter.release_version if adapter else "local-unversioned",
        fetched_at=_isoformat(datetime.fromtimestamp(stat.st_mtime, UTC)),
        fetch_time_source="filesystem_mtime",
        content_hash=f"sha256:{content_hash}",
        size_bytes=stat.st_size,
        path=relative,
        source_url=_primary_source_url(adapter),
        license=adapter.license if adapter else fallback_license,
        reviewer_state=adapter.reviewer_state if adapter else "needs_review",
        lifecycle_state=adapter.lifecycle_state if adapter else "needs_review",
        enabled=adapter.enabled if adapter else True,
        warnings=warnings,
        metadata={
            "canonical_source_id": adapter.source_id if adapter else None,
            "adapter_catalog_version": adapter_catalog_version,
            "authority": adapter.authority if adapter else None,
            "access_mode": adapter.access_mode if adapter else "local_file",
            "ingestion_mode": adapter.ingestion_mode if adapter else "operator_local_file",
            "chunk_profile": adapter.chunk_profile if adapter else "paragraph_window_v0",
            "parser": adapter.parser if adapter else "plain_text",
            "resource_type": adapter.metadata.get("resource_type") if adapter else None,
            "origin": "local_corpus",
            "extension": path.suffix.lower(),
            **resolved_partition_metadata,
        },
    )


def _metadata_from_manifest_item(item: CorpusIngestionItem) -> dict:
    return {
        "corpus_item_id": item.item_id,
        "adapter_id": item.adapter_id,
        "adapter_catalog_version": item.metadata.get("adapter_catalog_version"),
        "canonical_source_id": item.metadata.get("canonical_source_id"),
        "authority": item.metadata.get("authority"),
        "access_mode": item.metadata.get("access_mode"),
        "ingestion_mode": item.metadata.get("ingestion_mode"),
        "chunk_profile": item.metadata.get("chunk_profile"),
        "parser": item.metadata.get("parser"),
        "resource_type": item.metadata.get("resource_type"),
        "corpus_partition_id": item.metadata.get("corpus_partition_id"),
        "corpus_partition_label": item.metadata.get("corpus_partition_label"),
        "corpus_partition_purpose": item.metadata.get("corpus_partition_purpose"),
        "corpus_visibility": item.metadata.get("corpus_visibility"),
        "corpus_required_permission_scopes": item.metadata.get(
            "corpus_required_permission_scopes"
        ),
        "organization_id": item.metadata.get("organization_id"),
        "external_provider_allowed": item.metadata.get("external_provider_allowed"),
        "phi_allowed": item.metadata.get("phi_allowed"),
        "requires_reviewer_approval": item.metadata.get("requires_reviewer_approval"),
        "retention_policy_id": item.metadata.get("retention_policy_id"),
        "release_version": item.release_version,
        "fetched_at": item.fetched_at,
        "fetch_time_source": item.fetch_time_source,
        "content_hash": item.content_hash,
        "size_bytes": item.size_bytes,
        "license_id": item.license.license_id,
        "license_name": item.license.name,
        "license_constraints": list(item.license.constraints),
        "reviewer_state": item.reviewer_state,
        "lifecycle_state": item.lifecycle_state,
        "source_url": item.source_url,
        "warnings": list(item.warnings),
    }


def _ledger_from_chunks(
    chunks: list[KnowledgeChunk],
    *,
    manifest: CorpusIngestionManifest,
    knowledge_root: Path,
    max_chars: int,
    overlap_chars: int,
) -> CorpusIngestionLedger:
    ingestion_run_id = _ingestion_run_id(manifest)
    items_by_id = {item.item_id: item for item in manifest.items}
    records = [
        _ledger_record_for_chunk(
            chunk,
            manifest=manifest,
            ingestion_run_id=ingestion_run_id,
            item=items_by_id.get(str(chunk.metadata.get("corpus_item_id") or "")),
        )
        for chunk in chunks
    ]
    approved_count = sum(1 for record in records if record.approved_for_indexing)
    needs_review_count = sum(
        1 for record in records if record.reviewer_state == "needs_review"
    )
    deprecated_count = sum(
        1 for record in records if record.lifecycle_state == "deprecated"
    )
    warning_count = sum(len(record.warnings) for record in records)
    return CorpusIngestionLedger(
        version="corpus_ingestion_ledger.v1",
        generated_at=manifest.generated_at,
        ingestion_run_id=ingestion_run_id,
        adapter_catalog_version=manifest.adapter_catalog_version,
        knowledge_root=_display_path(knowledge_root, knowledge_root),
        chunking={
            "max_chars": max_chars,
            "overlap_chars": overlap_chars,
        },
        summary=CorpusIngestionLedgerSummary(
            source_count=len({record.source_id for record in records}),
            chunk_count=len(records),
            approved_chunk_count=approved_count,
            needs_review_chunk_count=needs_review_count,
            deprecated_chunk_count=deprecated_count,
            unapproved_chunk_count=len(records) - approved_count,
            warning_count=warning_count,
        ),
        records=records,
    )


def _ledger_record_for_chunk(
    chunk: KnowledgeChunk,
    *,
    manifest: CorpusIngestionManifest,
    ingestion_run_id: str,
    item: CorpusIngestionItem | None,
) -> CorpusIngestionLedgerRecord:
    metadata = chunk.metadata
    raw_artifact_hash = str(
        (item.content_hash if item is not None else None)
        or metadata.get("content_hash")
        or "sha256:unknown"
    )
    reviewer_state = (
        item.reviewer_state if item is not None else metadata.get("reviewer_state") or "needs_review"
    )
    lifecycle_state = (
        item.lifecycle_state if item is not None else metadata.get("lifecycle_state") or "needs_review"
    )
    chunk_index = _int_metadata(chunk.locator.get("chunk_index"), default=0)
    chunk_start = _int_metadata(
        chunk.locator.get("start_char") or metadata.get("chunk_start_char"),
        default=0,
    )
    chunk_end = _int_metadata(
        chunk.locator.get("end_char") or metadata.get("chunk_end_char"),
        default=chunk_start,
    )
    warning_values = [
        str(value)
        for value in (
            item.warnings if item is not None else metadata.get("warnings", [])
        )
        if str(value)
    ]
    index_decision = _index_decision(
        reviewer_state=str(reviewer_state),
        lifecycle_state=str(lifecycle_state),
    )
    approved = index_decision == "indexed"
    ledger_record_id = _ledger_record_id(
        ingestion_run_id=ingestion_run_id,
        chunk_id=chunk.chunk_id,
        raw_artifact_hash=raw_artifact_hash,
    )
    return CorpusIngestionLedgerRecord(
        ledger_record_id=ledger_record_id,
        ingestion_run_id=ingestion_run_id,
        item_id=str(
            (item.item_id if item is not None else None)
            or metadata.get("corpus_item_id")
            or chunk.source_id
        ),
        chunk_id=chunk.chunk_id,
        source_id=chunk.source_id,
        adapter_id=(
            item.adapter_id if item is not None else _optional_str(metadata.get("adapter_id"))
        ),
        adapter_version=str(
            metadata.get("adapter_version")
            or metadata.get("adapter_catalog_version")
            or manifest.adapter_catalog_version
        ),
        title=chunk.title,
        source_type=chunk.source_type,
        clinical_domain=chunk.clinical_domain or "general",
        standard_system=chunk.standard_system or "local_corpus",
        source_version=chunk.source_version,
        path=_optional_str(item.path if item is not None else chunk.locator.get("path")),
        source_url=item.source_url if item is not None else _optional_str(metadata.get("source_url")),
        raw_artifact_hash=raw_artifact_hash,
        chunk_content_hash=str(
            metadata.get("chunk_content_hash")
            or f"sha256:{sha256(chunk.content.encode('utf-8')).hexdigest()}"
        ),
        chunk_index=chunk_index,
        chunk_start_char=chunk_start,
        chunk_end_char=max(chunk_end, chunk_start),
        chunk_profile=_optional_str(metadata.get("chunk_profile")),
        parser=_optional_str(metadata.get("parser")),
        reviewer_state=reviewer_state,
        lifecycle_state=lifecycle_state,
        reviewer_decision=reviewer_state,
        index_decision=index_decision,
        approved_for_indexing=approved,
        warnings=warning_values,
        metadata={
            "fetch_time_source": metadata.get("fetch_time_source"),
            "fetched_at": metadata.get("fetched_at"),
            "license_id": metadata.get("license_id"),
            "canonical_source_id": metadata.get("canonical_source_id"),
            "ingestion_mode": metadata.get("ingestion_mode"),
        },
    )


def _ingestion_run_id(manifest: CorpusIngestionManifest) -> str:
    payload = {
        "version": manifest.version,
        "adapter_catalog_version": manifest.adapter_catalog_version,
        "knowledge_root": manifest.knowledge_root,
        "items": [
            {
                "item_id": item.item_id,
                "source_id": item.source_id,
                "adapter_id": item.adapter_id,
                "release_version": item.release_version,
                "content_hash": item.content_hash,
                "reviewer_state": item.reviewer_state,
                "lifecycle_state": item.lifecycle_state,
                "enabled": item.enabled,
                "path": item.path,
            }
            for item in sorted(manifest.items, key=lambda entry: entry.item_id)
        ],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"corpus_run:{sha256(encoded.encode('utf-8')).hexdigest()[:16]}"


def _ledger_record_id(
    *,
    ingestion_run_id: str,
    chunk_id: str,
    raw_artifact_hash: str,
) -> str:
    payload = f"{ingestion_run_id}:{chunk_id}:{raw_artifact_hash}"
    return f"corpus_ledger:{sha256(payload.encode('utf-8')).hexdigest()[:16]}"


def _index_decision(*, reviewer_state: str, lifecycle_state: str) -> str:
    if reviewer_state == "approved" and lifecycle_state == "approved":
        return "indexed"
    return "indexed_needs_review"


def _int_metadata(value: object, *, default: int) -> int:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
    return max(parsed, 0)


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _chunking_profile_for_item(
    item: CorpusIngestionItem | None,
    profiles: dict[str, CorpusChunkingProfile],
) -> CorpusChunkingProfile | None:
    profile_id = None
    if item is not None:
        profile_id = item.metadata.get("chunk_profile")
    if not isinstance(profile_id, str) or not profile_id:
        profile_id = "paragraph_window_v0"
    return profiles.get(profile_id)


def _chunk_records(
    text: str,
    *,
    max_chars: int,
    overlap_chars: int,
    profile: CorpusChunkingProfile | None,
) -> list[_ChunkRecord]:
    strategy = profile.boundary_strategy if profile else "paragraph"
    if strategy == "markdown_section":
        return _markdown_section_chunk_records(
            text,
            max_chars=max_chars,
            overlap_chars=overlap_chars,
        )
    return _paragraph_chunk_records(
        text,
        max_chars=max_chars,
        overlap_chars=overlap_chars,
    )


def _paragraph_chunk_records(
    text: str,
    *,
    max_chars: int,
    overlap_chars: int,
) -> list[_ChunkRecord]:
    chunks = _chunk_text(text, max_chars=max_chars, overlap_chars=overlap_chars)
    return [
        _record_for_text_chunk(text, chunk_text, cursor=0)
        for chunk_text in chunks
    ]


def _markdown_section_chunk_records(
    text: str,
    *,
    max_chars: int,
    overlap_chars: int,
) -> list[_ChunkRecord]:
    heading_matches = list(re.finditer(r"(?m)^(#{1,6})\s+(.+?)\s*$", text))
    if not heading_matches:
        return _paragraph_chunk_records(
            text,
            max_chars=max_chars,
            overlap_chars=overlap_chars,
        )
    records: list[_ChunkRecord] = []
    for index, match in enumerate(heading_matches):
        section_start = match.start()
        section_end = (
            heading_matches[index + 1].start()
            if index + 1 < len(heading_matches)
            else len(text)
        )
        heading = match.group(2).strip()
        section_text = text[section_start:section_end].strip()
        for chunk_text in _chunk_text(
            section_text,
            max_chars=max_chars,
            overlap_chars=overlap_chars,
        ):
            start_offset = section_text.find(chunk_text[: min(len(chunk_text), 80)])
            start_char = section_start + max(start_offset, 0)
            records.append(
                _ChunkRecord(
                    text=chunk_text,
                    section_heading=heading,
                    start_char=start_char,
                    end_char=start_char + len(chunk_text),
                )
            )
    return records


def _record_for_text_chunk(text: str, chunk_text: str, *, cursor: int) -> _ChunkRecord:
    start = text.find(chunk_text[: min(len(chunk_text), 80)], cursor)
    if start < 0:
        start = 0
    return _ChunkRecord(
        text=chunk_text,
        start_char=start,
        end_char=start + len(chunk_text),
    )


def _metadata_from_chunk_record(
    record: _ChunkRecord,
    *,
    profile: CorpusChunkingProfile | None,
) -> dict:
    metadata = {
        "chunk_start_char": record.start_char,
        "chunk_end_char": record.end_char,
        "field_names": _field_names_for(record.text),
    }
    if profile is not None:
        metadata["chunk_profile"] = profile.profile_id
        metadata["chunk_boundary_strategy"] = profile.boundary_strategy
    if record.section_heading:
        metadata["section_heading"] = record.section_heading
    return metadata


def _field_names_for(text: str) -> list[str]:
    candidates: set[str] = set()
    for match in re.finditer(r"`([a-zA-Z][a-zA-Z0-9_]{1,60})`", text):
        candidates.add(match.group(1))
    first_line = text.splitlines()[0] if text.splitlines() else ""
    if "," in first_line and len(first_line) < 300:
        for item in first_line.split(","):
            candidate = item.strip()
            if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,60}", candidate):
                candidates.add(candidate)
    for match in re.finditer(r"\b([a-z][a-z0-9]+(?:_[a-z0-9]+)+)\b", text):
        candidates.add(match.group(1))
    return sorted(candidates)[:30]


def _iter_supported_corpus_files(corpus_dirs: tuple[Path, ...]) -> list[Path]:
    paths: list[Path] = []
    for corpus_dir in corpus_dirs:
        if not corpus_dir.exists() or not corpus_dir.is_dir():
            continue
        for path in sorted(corpus_dir.rglob("*")):
            if (
                path.is_file()
                and not _has_hidden_part(path)
                and path.suffix.lower() in SUPPORTED_CORPUS_EXTENSIONS
            ):
                paths.append(path)
    return paths


def _adapters_by_local_path(
    catalog: CorpusAdapterCatalog,
    *,
    knowledge_root: Path,
) -> dict[str, CorpusSourceAdapter]:
    adapters: dict[str, CorpusSourceAdapter] = {}
    for adapter in catalog.adapters:
        for local_path in adapter.local_paths:
            path = Path(local_path)
            relative = str(path) if not path.is_absolute() else _display_path(path, knowledge_root)
            adapters[relative] = adapter
    return adapters


def _primary_source_url(adapter: CorpusSourceAdapter | None) -> str | None:
    if adapter is None or not adapter.source_urls:
        return None
    if "primary" in adapter.source_urls:
        return adapter.source_urls["primary"]
    return next(iter(adapter.source_urls.values()))


def _isoformat(value: datetime) -> str:
    normalized = value.astimezone(UTC).replace(microsecond=0)
    return normalized.isoformat().replace("+00:00", "Z")


def _chunk_text(text: str, *, max_chars: int, overlap_chars: int) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.extend(_sliding_chunks(paragraph, max_chars=max_chars, overlap_chars=overlap_chars))
            continue
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
        else:
            chunks.append(current.strip())
            prefix = current[-overlap_chars:].strip() if overlap_chars else ""
            current = f"{prefix}\n\n{paragraph}".strip() if prefix else paragraph
    if current:
        chunks.append(current.strip())
    return chunks


def _sliding_chunks(text: str, *, max_chars: int, overlap_chars: int) -> list[str]:
    step = max(1, max_chars - overlap_chars)
    chunks: list[str] = []
    for start in range(0, len(text), step):
        chunk = text[start : start + max_chars].strip()
        if chunk:
            chunks.append(chunk)
        if start + max_chars >= len(text):
            break
    return chunks


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").strip()


def _title_from_text(path: Path, text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or path.stem.replace("_", " ").title()
    return path.stem.replace("_", " ").replace("-", " ").title()


def _source_type_for(path: Path, text: str) -> EvidenceSourceType:
    inspected = f"{path} {text[:1000]}".lower()
    if any(
        term in inspected
        for term in ["loinc", "ucum", "rxnorm", "snomed", "mesh", "icd-10"]
    ):
        return EvidenceSourceType.TERMINOLOGY_SYSTEM
    if any(term in inspected for term in ["fhir", "omop", "hl7", "standard", "clinicaltrials.gov"]):
        return EvidenceSourceType.HEALTHCARE_STANDARD
    if "example" in inspected:
        return EvidenceSourceType.TRANSFORMATION_EXAMPLE
    return EvidenceSourceType.DATA_DICTIONARY


def _clinical_domain_for(path: Path, text: str) -> str:
    inspected = f"{path} {text[:1000]}".lower()
    if any(
        term in inspected
        for term in [
            "allergy",
            "allergies",
            "intolerance",
            "allergyintolerance",
            "adverse reaction",
            "reaction manifestation",
            "latex sensitivity",
        ]
    ):
        return "allergy"
    if any(
        term in inspected
        for term in [
            "condition",
            "diagnosis",
            "diagnoses",
            "problem list",
            "problem-list",
            "icd-10",
            "snomed",
        ]
    ):
        return "problem_list"
    if any(
        term in inspected
        for term in [
            "lab",
            "laboratory",
            "observation",
            "hba1c",
            "glucose",
            "creatinine",
            "sodium",
            "potassium",
            "cholesterol",
        ]
    ):
        return "laboratory"
    if any(term in inspected for term in ["medication", "rxnorm", "drug", "openfda", "ndc"]):
        return "medication"
    if any(
        term in inspected
        for term in ["mesh", "pubmed", "medline", "literature", "clinicaltrials", "trial"]
    ):
        return "literature"
    if any(term in inspected for term in ["fhir", "hl7", "interoperability"]):
        return "interoperability"
    if any(term in inspected for term in ["omop", "analytics", "cohort"]):
        return "analytics"
    if any(term in inspected for term in ["imaging", "dicom", "radiology"]):
        return "imaging"
    if any(term in inspected for term in ["governance", "policy", "review"]):
        return "governance"
    return "general"


def _standard_system_for(path: Path, text: str) -> str:
    inspected = f"{path} {text[:1000]}".lower()
    candidates = {
        "FHIR": ["fhir", "hl7"],
        "LOINC": ["loinc"],
        "UCUM": ["ucum"],
        "RxNorm": ["rxnorm"],
        "MeSH": ["mesh", "pubmed", "medline"],
        "OMOP": ["omop"],
        "ClinicalTrials.gov": ["clinicaltrials.gov", "clinicaltrials"],
        "openFDA": ["openfda", "fda adverse", "drug label"],
        "SNOMED CT": ["snomed"],
        "ICD-10-CM": ["icd-10"],
        "MedlinePlus": ["medlineplus"],
    }
    for system, markers in candidates.items():
        if any(marker in inspected for marker in markers):
            return system
    return "local_corpus"


def _display_path(path: Path, knowledge_root: Path) -> str:
    try:
        return str(path.relative_to(knowledge_root.parent))
    except ValueError:
        return str(path)


def _stable_slug(value: str) -> str:
    stem = re.sub(r"[^a-z0-9]+", "_", Path(value).stem.lower()).strip("_") or "document"
    digest = sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"{stem}_{digest}"


def _has_hidden_part(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)
