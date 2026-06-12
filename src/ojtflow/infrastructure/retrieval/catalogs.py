"""Data-driven retrieval governance catalogs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from ojtflow.core.contracts.retrieval import (
    CorpusAdapterCatalog,
    CorpusChunkingProfile,
    CorpusChunkingProfileCatalog,
    CorpusPartitionCatalog,
    CorpusPartitionPolicy,
    CorpusSourceAdapter,
    MedicalSourceQualityPolicyCatalog,
    MedicalSourceQualityRule,
    RetrievalSourceTrustPolicy,
    RetrievalSourceTrustPolicyCatalog,
    RetrievalStrategyCatalog,
    RetrievalStrategyProfile,
)


DEFAULT_CORPUS_ADAPTER_CATALOG_PATH = Path("source_catalog/corpus_adapters.json")
DEFAULT_CORPUS_CHUNKING_PROFILE_CATALOG_PATH = Path("retrieval/chunking_profiles.json")
DEFAULT_CORPUS_PARTITION_CATALOG_PATH = Path("source_catalog/corpus_partitions.json")
DEFAULT_SOURCE_POLICY_PATH = Path("source_catalog/source_trust_policies.json")
DEFAULT_SOURCE_QUALITY_POLICY_PATH = Path("retrieval/source_quality_policy.json")
DEFAULT_STRATEGY_CATALOG_PATH = Path("retrieval/strategy_catalog.json")


class _HasId(Protocol):
    @property
    def key(self) -> str: ...


def load_source_trust_policy_catalog(knowledge_root: Path) -> RetrievalSourceTrustPolicyCatalog:
    """Load source-level governance policy from trusted knowledge data."""

    path = knowledge_root / DEFAULT_SOURCE_POLICY_PATH
    if not path.exists():
        return RetrievalSourceTrustPolicyCatalog(
            version="source_trust_policies.empty",
            policies=[],
        )
    raw = _read_json_object(path)
    catalog = RetrievalSourceTrustPolicyCatalog.model_validate(raw)
    _ensure_unique(
        [_PolicyKey(policy) for policy in catalog.policies],
        path=path,
        field="source_id",
    )
    return catalog


def load_medical_source_quality_policy_catalog(
    knowledge_root: Path,
) -> MedicalSourceQualityPolicyCatalog:
    """Load source-level medical quality scoring policy from trusted data."""

    path = knowledge_root / DEFAULT_SOURCE_QUALITY_POLICY_PATH
    if not path.exists():
        return MedicalSourceQualityPolicyCatalog(
            version="medical_source_quality_policy.empty",
            base_score=50,
            status_thresholds={
                "ready_min": 85,
                "watch_min": 70,
                "needs_review_min": 45,
            },
            rules=[],
        )
    raw = _read_json_object(path)
    catalog = MedicalSourceQualityPolicyCatalog.model_validate(raw)
    _ensure_unique(
        [_SourceQualityRuleKey(rule) for rule in catalog.rules],
        path=path,
        field="rule_id",
    )
    return catalog


def load_corpus_adapter_catalog(knowledge_root: Path) -> CorpusAdapterCatalog:
    """Load governed corpus adapter specs from trusted knowledge data."""

    path = knowledge_root / DEFAULT_CORPUS_ADAPTER_CATALOG_PATH
    if not path.exists():
        return CorpusAdapterCatalog(
            version="corpus_adapters.empty",
            adapters=[],
        )
    raw = _read_json_object(path)
    catalog = CorpusAdapterCatalog.model_validate(raw)
    _ensure_unique(
        [_AdapterKey(adapter) for adapter in catalog.adapters],
        path=path,
        field="adapter_id",
    )
    _ensure_unique(
        [_AdapterSourceKey(adapter) for adapter in catalog.adapters],
        path=path,
        field="source_id",
    )
    return catalog


def load_corpus_partition_catalog(knowledge_root: Path) -> CorpusPartitionCatalog:
    """Load tenant-aware corpus partition policy from trusted knowledge data."""

    path = knowledge_root / DEFAULT_CORPUS_PARTITION_CATALOG_PATH
    if not path.exists():
        return CorpusPartitionCatalog(
            version="corpus_partitions.empty",
            default_partition_id="global_standards",
            partitions=[],
        )
    raw = _read_json_object(path)
    catalog = CorpusPartitionCatalog.model_validate(raw)
    _ensure_unique(
        [_PartitionKey(partition) for partition in catalog.partitions],
        path=path,
        field="partition_id",
    )
    if catalog.partitions and catalog.default_partition_id not in {
        partition.partition_id for partition in catalog.partitions
    }:
        raise ValueError(
            f"Invalid corpus partition catalog at {path}: default_partition_id "
            f"{catalog.default_partition_id!r} is not defined"
        )
    return catalog


def load_corpus_chunking_profile_catalog(knowledge_root: Path) -> CorpusChunkingProfileCatalog:
    """Load data-driven corpus chunking profiles from trusted knowledge data."""

    path = knowledge_root / DEFAULT_CORPUS_CHUNKING_PROFILE_CATALOG_PATH
    if not path.exists():
        return CorpusChunkingProfileCatalog(
            version="corpus_chunking_profiles.empty",
            profiles=[],
        )
    raw = _read_json_object(path)
    catalog = CorpusChunkingProfileCatalog.model_validate(raw)
    _ensure_unique(
        [_ChunkingProfileKey(profile) for profile in catalog.profiles],
        path=path,
        field="profile_id",
    )
    return catalog


def load_retrieval_strategy_catalog(knowledge_root: Path) -> RetrievalStrategyCatalog:
    """Load operator-facing retrieval strategy profiles from trusted knowledge data."""

    path = knowledge_root / DEFAULT_STRATEGY_CATALOG_PATH
    if not path.exists():
        return RetrievalStrategyCatalog(
            version="retrieval_strategy_catalog.empty",
            strategies=[],
        )
    raw = _read_json_object(path)
    catalog = RetrievalStrategyCatalog.model_validate(raw)
    _ensure_unique(
        [_StrategyKey(strategy) for strategy in catalog.strategies],
        path=path,
        field="strategy_id",
    )
    return catalog


def _read_json_object(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid retrieval catalog at {path}: expected object")
    return raw


def _ensure_unique(items: list[_HasId], *, path: Path, field: str) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for item in items:
        if item.key in seen:
            duplicates.add(item.key)
        seen.add(item.key)
    if duplicates:
        duplicate_text = ", ".join(sorted(duplicates))
        raise ValueError(
            f"Invalid retrieval catalog at {path}: duplicate {field} {duplicate_text}"
        )


class _PolicyKey:
    def __init__(self, policy: RetrievalSourceTrustPolicy) -> None:
        self.key = policy.source_id


class _SourceQualityRuleKey:
    def __init__(self, rule: MedicalSourceQualityRule) -> None:
        self.key = rule.rule_id


class _AdapterKey:
    def __init__(self, adapter: CorpusSourceAdapter) -> None:
        self.key = adapter.adapter_id


class _AdapterSourceKey:
    def __init__(self, adapter: CorpusSourceAdapter) -> None:
        self.key = adapter.source_id


class _PartitionKey:
    def __init__(self, partition: CorpusPartitionPolicy) -> None:
        self.key = partition.partition_id


class _ChunkingProfileKey:
    def __init__(self, profile: CorpusChunkingProfile) -> None:
        self.key = profile.profile_id


class _StrategyKey:
    def __init__(self, strategy: RetrievalStrategyProfile) -> None:
        self.key = strategy.strategy_id
