"""Data-driven Assistant evaluation fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from ojtflow.core.contracts.assistant import (
    AssistantEvaluationCase,
    AssistantEvaluationSuite,
)


DEFAULT_ASSISTANT_EVALUATIONS_PATH = Path("assistant/evaluation_cases.json")


def load_assistant_evaluation_suite(knowledge_root: Path) -> AssistantEvaluationSuite:
    """Load Assistant evaluation cases from the trusted knowledge directory."""

    path = knowledge_root / DEFAULT_ASSISTANT_EVALUATIONS_PATH
    if not path.exists():
        return AssistantEvaluationSuite(version="assistant_evaluations.empty", cases=[])
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid assistant evaluation suite at {path}: expected object")
    suite = AssistantEvaluationSuite.model_validate(raw)
    _ensure_unique_case_ids(suite.cases, path=path)
    return suite


def _ensure_unique_case_ids(cases: list[AssistantEvaluationCase], *, path: Path) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for case in cases:
        if case.case_id in seen:
            duplicates.add(case.case_id)
        seen.add(case.case_id)
    if duplicates:
        duplicate_text = ", ".join(sorted(duplicates))
        raise ValueError(
            f"Invalid assistant evaluation suite at {path}: duplicate case_id "
            f"{duplicate_text}"
        )
