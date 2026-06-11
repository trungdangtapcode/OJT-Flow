"""Data-driven retrieval governance catalogs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from ojtflow.core.contracts.retrieval import (
    CorpusAdapterCatalog,
    CorpusSourceAdapter,
    RetrievalSourceTrustPolicy,
    RetrievalSourceTrustPolicyCatalog,
    RetrievalStrategyCatalog,
    RetrievalStrategyProfile,
)


DEFAULT_CORPUS_ADAPTER_CATALOG_PATH = Path("source_catalog/corpus_adapters.json")
DEFAULT_SOURCE_POLICY_PATH = Path("source_catalog/source_trust_policies.json")
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


class _AdapterKey:
    def __init__(self, adapter: CorpusSourceAdapter) -> None:
        self.key = adapter.adapter_id


class _AdapterSourceKey:
    def __init__(self, adapter: CorpusSourceAdapter) -> None:
        self.key = adapter.source_id


class _StrategyKey:
    def __init__(self, strategy: RetrievalStrategyProfile) -> None:
        self.key = strategy.strategy_id
