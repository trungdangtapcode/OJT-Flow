"""Load data-driven Assistant prompt-injection policy."""

from __future__ import annotations

import json
from pathlib import Path

from ojtflow.core.contracts.prompt_injection import PromptInjectionPolicy


DEFAULT_PROMPT_INJECTION_POLICY_PATH = Path("assistant/prompt_injection_policy.json")


def load_prompt_injection_policy(knowledge_root: Path) -> PromptInjectionPolicy:
    """Load prompt-injection policy from trusted knowledge data."""

    path = knowledge_root / DEFAULT_PROMPT_INJECTION_POLICY_PATH
    if not path.exists():
        return PromptInjectionPolicy()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid prompt-injection policy at {path}: expected object")
    policy = PromptInjectionPolicy.model_validate(raw)
    _validate_unique_rule_ids(policy, path=path)
    return policy


def _validate_unique_rule_ids(policy: PromptInjectionPolicy, *, path: Path) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for rule in policy.rules:
        if rule.rule_id in seen:
            duplicates.add(rule.rule_id)
        seen.add(rule.rule_id)
    if duplicates:
        duplicate_text = ", ".join(sorted(duplicates))
        raise ValueError(
            f"Invalid prompt-injection policy at {path}: duplicate rule_id "
            f"{duplicate_text}"
        )
