"""Data-driven Assistant tool progress policy loader."""

from __future__ import annotations

import json
from pathlib import Path

from ojtflow.core.contracts.assistant import (
    AssistantToolProgressCatalog,
    AssistantToolProgressStage,
)


DEFAULT_TOOL_PROGRESS_POLICY_PATH = Path("assistant/tool_progress_policies.json")


def load_assistant_tool_progress_policies(
    knowledge_root: Path,
) -> dict[str, list[AssistantToolProgressStage]]:
    """Load per-tool stream progress stages from trusted knowledge data."""

    path = knowledge_root / DEFAULT_TOOL_PROGRESS_POLICY_PATH
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid Assistant tool progress registry at {path}: expected object")
    catalog = AssistantToolProgressCatalog.model_validate(raw)
    policies: dict[str, list[AssistantToolProgressStage]] = {}
    for policy in catalog.policies:
        if policy.tool_name in policies:
            raise ValueError(
                f"Invalid Assistant tool progress registry at {path}: "
                f"duplicate tool_name {policy.tool_name}"
            )
        stage_ids: set[str] = set()
        for stage in policy.stages:
            if stage.stage_id in stage_ids:
                raise ValueError(
                    f"Invalid Assistant tool progress registry at {path}: "
                    f"duplicate stage_id {stage.stage_id} for {policy.tool_name}"
                )
            stage_ids.add(stage.stage_id)
        policies[policy.tool_name] = list(policy.stages)
    return policies
