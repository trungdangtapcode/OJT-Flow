"""Data-driven retrieval search presets."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from ojtflow.core.contracts.retrieval import RetrievalSearchPreset


DEFAULT_PRESET_PATH = Path("retrieval/search_presets.json")


def load_retrieval_search_presets(knowledge_root: Path) -> list[RetrievalSearchPreset]:
    """Load operator retrieval presets from the trusted knowledge directory."""

    return list(_load_retrieval_search_presets(str(knowledge_root / DEFAULT_PRESET_PATH)))


@lru_cache(maxsize=8)
def _load_retrieval_search_presets(path_text: str) -> tuple[RetrievalSearchPreset, ...]:
    path = Path(path_text)
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
