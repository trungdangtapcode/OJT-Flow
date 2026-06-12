"""Data-driven Assistant memory policy loader."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from ojtflow.core.contracts.assistant import AssistantMemoryPolicy

DEFAULT_ASSISTANT_MEMORY_POLICY_PATH = Path("assistant/memory_policy.json")


def load_assistant_memory_policy(knowledge_root: Path) -> AssistantMemoryPolicy:
    """Load the allowlist and safety denial rules for Assistant memory."""

    path = knowledge_root / DEFAULT_ASSISTANT_MEMORY_POLICY_PATH
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Assistant memory policy file is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid assistant memory policy JSON at {path}: {exc}") from exc
    try:
        policy = AssistantMemoryPolicy.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"Invalid assistant memory policy at {path}: {exc}") from exc
    _validate_policy(policy=policy, path=path)
    return policy


def _validate_policy(*, policy: AssistantMemoryPolicy, path: Path) -> None:
    keys = [preference.key for preference in policy.preferences]
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    if duplicates:
        duplicate_text = ", ".join(duplicates)
        raise ValueError(
            f"Invalid assistant memory policy at {path}: duplicate keys {duplicate_text}"
        )
    for preference in policy.preferences:
        if preference.value_type == "enum" and not preference.allowed_values:
            raise ValueError(
                f"Invalid assistant memory policy at {path}: "
                f"{preference.key} must define allowed_values"
            )
