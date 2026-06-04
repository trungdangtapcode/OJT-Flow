"""Data-driven retrieval search presets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ojtflow.core.contracts.retrieval import (
    RetrievalSearchOption,
    RetrievalSearchOptions,
    RetrievalSearchPreset,
)


DEFAULT_PRESET_PATH = Path("retrieval/search_presets.json")
DEFAULT_OPTIONS_PATH = Path("retrieval/search_options.json")


def load_retrieval_search_presets(knowledge_root: Path) -> list[RetrievalSearchPreset]:
    """Load operator retrieval presets from the trusted knowledge directory."""

    return list(_load_retrieval_search_presets(knowledge_root / DEFAULT_PRESET_PATH))


def load_retrieval_search_options(knowledge_root: Path) -> RetrievalSearchOptions:
    """Load retrieval query-builder options from the trusted knowledge directory."""

    return _load_retrieval_search_options(knowledge_root / DEFAULT_OPTIONS_PATH)


def _load_retrieval_search_presets(path: Path) -> tuple[RetrievalSearchPreset, ...]:
    if not path.exists():
        return ()

    raw = json.loads(path.read_text(encoding="utf-8"))
    records = raw.get("presets") if isinstance(raw, dict) else None
    if not isinstance(records, list):
        raise ValueError(f"Invalid retrieval preset registry at {path}: expected presets list")

    presets = tuple(
        RetrievalSearchPreset.model_validate(_preset_record(record, path=path))
        for record in records
    )
    _ensure_unique_ids(presets, path=path)
    return presets


def _load_retrieval_search_options(path: Path) -> RetrievalSearchOptions:
    if not path.exists():
        return RetrievalSearchOptions()

    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid retrieval search options registry at {path}: expected object")

    options = RetrievalSearchOptions.model_validate(raw)
    _ensure_unique_option_values(options.detected_formats, field="detected_formats", path=path)
    _ensure_valid_top_k_values(options.top_k_values, path=path)
    return options


def _preset_record(record: Any, *, path: Path) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError(f"Invalid retrieval preset registry at {path}: preset must be an object")
    return record


def _ensure_unique_ids(presets: tuple[RetrievalSearchPreset, ...], *, path: Path) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for preset in presets:
        if preset.preset_id in seen:
            duplicates.add(preset.preset_id)
        seen.add(preset.preset_id)
    if duplicates:
        duplicate_text = ", ".join(sorted(duplicates))
        raise ValueError(
            f"Invalid retrieval preset registry at {path}: duplicate preset_id {duplicate_text}"
        )


def _ensure_unique_option_values(
    options: list[RetrievalSearchOption],
    *,
    field: str,
    path: Path,
) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for option in options:
        if option.value in seen:
            duplicates.add(option.value)
        seen.add(option.value)
    if duplicates:
        duplicate_text = ", ".join(sorted(duplicates))
        raise ValueError(
            f"Invalid retrieval search options registry at {path}: "
            f"duplicate {field} value {duplicate_text}"
        )


def _ensure_valid_top_k_values(values: list[int], *, path: Path) -> None:
    invalid = [value for value in values if value < 1 or value > 20]
    if invalid:
        invalid_text = ", ".join(str(value) for value in invalid)
        raise ValueError(
            f"Invalid retrieval search options registry at {path}: "
            f"top_k_values must be between 1 and 20, got {invalid_text}"
        )
    if len(set(values)) != len(values):
        raise ValueError(
            f"Invalid retrieval search options registry at {path}: duplicate top_k_values"
        )
