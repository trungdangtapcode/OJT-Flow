"""Data-driven Assistant starter examples."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ojtflow.core.contracts.assistant import AssistantExample


DEFAULT_ASSISTANT_EXAMPLES_PATH = Path("assistant/examples.json")


def load_assistant_examples(knowledge_root: Path) -> list[AssistantExample]:
    """Load Assistant starter examples from the trusted knowledge directory."""

    path = knowledge_root / DEFAULT_ASSISTANT_EXAMPLES_PATH
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = raw.get("examples") if isinstance(raw, dict) else None
    if not isinstance(records, list):
        raise ValueError(f"Invalid assistant examples registry at {path}: expected examples list")
    examples = [
        AssistantExample.model_validate(_example_record(record, path=path))
        for record in records
    ]
    _ensure_unique_example_ids(examples, path=path)
    return examples


def _example_record(record: Any, *, path: Path) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError(f"Invalid assistant examples registry at {path}: example must be an object")
    return record


def _ensure_unique_example_ids(examples: list[AssistantExample], *, path: Path) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for example in examples:
        if example.example_id in seen:
            duplicates.add(example.example_id)
        seen.add(example.example_id)
    if duplicates:
        duplicate_text = ", ".join(sorted(duplicates))
        raise ValueError(
            f"Invalid assistant examples registry at {path}: duplicate example_id {duplicate_text}"
        )
