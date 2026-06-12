"""Data-driven Assistant answer templates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ojtflow.core.contracts.assistant import AssistantAnswerTemplate


DEFAULT_ASSISTANT_TEMPLATES_PATH = Path("assistant/answer_templates.json")


def load_assistant_answer_templates(knowledge_root: Path) -> list[AssistantAnswerTemplate]:
    """Load governed Assistant answer templates from trusted knowledge data."""

    path = knowledge_root / DEFAULT_ASSISTANT_TEMPLATES_PATH
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = raw.get("templates") if isinstance(raw, dict) else None
    if not isinstance(records, list):
        raise ValueError(
            f"Invalid assistant answer template registry at {path}: expected templates list"
        )
    templates = [
        AssistantAnswerTemplate.model_validate(_template_record(record, path=path))
        for record in records
    ]
    _ensure_unique_template_ids(templates, path=path)
    return templates


def _template_record(record: Any, *, path: Path) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError(
            f"Invalid assistant answer template registry at {path}: template must be an object"
        )
    return record


def _ensure_unique_template_ids(
    templates: list[AssistantAnswerTemplate],
    *,
    path: Path,
) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for template in templates:
        if template.template_id in seen:
            duplicates.add(template.template_id)
        seen.add(template.template_id)
    if duplicates:
        duplicate_text = ", ".join(sorted(duplicates))
        raise ValueError(
            f"Invalid assistant answer template registry at {path}: "
            f"duplicate template_id {duplicate_text}"
        )
