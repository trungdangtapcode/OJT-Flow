"""Tenant-aware corpus partition policy helpers."""

from __future__ import annotations

from ojtflow.core.contracts.enums import EvidenceSourceType
from ojtflow.core.contracts.retrieval import (
    CorpusPartitionCatalog,
    CorpusPartitionPolicy,
)

GLOBAL_STANDARDS_PARTITION_ID = "global_standards"
GLOBAL_STANDARDS_VISIBILITY = "global"


def resolve_corpus_partition(
    catalog: CorpusPartitionCatalog,
    *,
    source_id: str,
    source_type: EvidenceSourceType,
    local_path: str | None = None,
    metadata: dict | None = None,
) -> CorpusPartitionPolicy | None:
    """Resolve the configured partition for one corpus source."""

    metadata = metadata or {}
    explicit_id = _text(metadata.get("corpus_partition_id"))
    if explicit_id:
        partition = _partition_by_id(catalog, explicit_id)
        if partition is not None:
            return partition

    for partition in catalog.partitions:
        if _matches_partition(
            partition,
            source_id=source_id,
            source_type=source_type,
            local_path=local_path,
        ):
            return partition

    return _partition_by_id(catalog, catalog.default_partition_id) or _default_partition(catalog)


def partition_metadata(
    partition: CorpusPartitionPolicy | None,
    *,
    organization_id: str | None = None,
) -> dict[str, object]:
    """Build source/chunk metadata for a resolved partition."""

    if partition is None:
        return {
            "corpus_partition_id": GLOBAL_STANDARDS_PARTITION_ID,
            "corpus_visibility": GLOBAL_STANDARDS_VISIBILITY,
            "corpus_partition_purpose": "global_standard",
            "external_provider_allowed": True,
            "phi_allowed": False,
            "requires_reviewer_approval": False,
        }
    metadata: dict[str, object] = {
        "corpus_partition_id": partition.partition_id,
        "corpus_partition_label": partition.label,
        "corpus_partition_purpose": partition.purpose,
        "corpus_visibility": partition.visibility,
        "corpus_required_permission_scopes": list(partition.required_permission_scopes),
        "external_provider_allowed": partition.external_provider_allowed,
        "phi_allowed": partition.phi_allowed,
        "requires_reviewer_approval": partition.requires_reviewer_approval,
        "retention_policy_id": partition.retention_policy_id,
    }
    if organization_id:
        metadata["organization_id"] = organization_id
    return metadata


def chunk_visible_for_organization(
    metadata: dict,
    *,
    organization_id: str | None,
) -> bool:
    """Return whether a chunk is visible to the given organization scope."""

    visibility = _text(metadata.get("corpus_visibility")) or GLOBAL_STANDARDS_VISIBILITY
    if visibility == GLOBAL_STANDARDS_VISIBILITY:
        return True
    if not organization_id:
        return False
    return _text(metadata.get("organization_id")) == organization_id


def metadata_partition_id(metadata: dict) -> str:
    return _text(metadata.get("corpus_partition_id")) or GLOBAL_STANDARDS_PARTITION_ID


def metadata_visibility(metadata: dict) -> str:
    return _text(metadata.get("corpus_visibility")) or GLOBAL_STANDARDS_VISIBILITY


def _matches_partition(
    partition: CorpusPartitionPolicy,
    *,
    source_id: str,
    source_type: EvidenceSourceType,
    local_path: str | None,
) -> bool:
    if any(source_id.startswith(prefix) for prefix in partition.source_id_prefixes):
        return True
    if local_path and any(
        local_path.startswith(prefix) for prefix in partition.local_path_prefixes
    ):
        return True
    return source_type in partition.allowed_source_types and partition.default_for_uncataloged


def _partition_by_id(
    catalog: CorpusPartitionCatalog,
    partition_id: str,
) -> CorpusPartitionPolicy | None:
    for partition in catalog.partitions:
        if partition.partition_id == partition_id:
            return partition
    return None


def _default_partition(catalog: CorpusPartitionCatalog) -> CorpusPartitionPolicy | None:
    for partition in catalog.partitions:
        if partition.default_for_uncataloged:
            return partition
    return catalog.partitions[0] if catalog.partitions else None


def _text(value: object) -> str:
    return value if isinstance(value, str) else ""
