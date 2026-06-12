"""Data-driven Assistant adversarial safety fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from ojtflow.core.contracts.assistant import (
    AssistantSafetyCase,
    AssistantSafetySuite,
)


DEFAULT_ASSISTANT_SAFETY_PATH = Path("assistant/safety_cases.json")


def load_assistant_safety_suite(knowledge_root: Path) -> AssistantSafetySuite:
    """Load Assistant prompt-injection safety cases from trusted knowledge."""

    path = knowledge_root / DEFAULT_ASSISTANT_SAFETY_PATH
    if not path.exists():
        return AssistantSafetySuite(version="assistant_safety.empty", cases=[])
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid assistant safety suite at {path}: expected object")
    suite = AssistantSafetySuite.model_validate(raw)
    _ensure_unique_case_ids(suite.cases, path=path)
    return suite


def _ensure_unique_case_ids(cases: list[AssistantSafetyCase], *, path: Path) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for case in cases:
        if case.case_id in seen:
            duplicates.add(case.case_id)
        seen.add(case.case_id)
    if duplicates:
        duplicate_text = ", ".join(sorted(duplicates))
        raise ValueError(
            f"Invalid assistant safety suite at {path}: duplicate case_id "
            f"{duplicate_text}"
        )
