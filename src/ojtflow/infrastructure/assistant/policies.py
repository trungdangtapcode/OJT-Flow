"""Data-driven Assistant tool permission policy loader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_TOOL_PERMISSION_POLICY_PATH = Path("assistant/tool_permission_policies.json")


def load_assistant_tool_permission_policies(
    knowledge_root: Path,
) -> dict[str, dict[str, Any]]:
    """Load per-tool permission metadata from trusted knowledge data."""

    path = knowledge_root / DEFAULT_TOOL_PERMISSION_POLICY_PATH
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid Assistant tool permission registry at {path}: expected object")
    records = raw.get("policies")
    if not isinstance(records, list):
        raise ValueError(
            f"Invalid Assistant tool permission registry at {path}: expected policies list"
        )
    policies: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError(
                f"Invalid Assistant tool permission registry at {path}: policy must be object"
            )
        tool_name = record.get("tool_name")
        if not isinstance(tool_name, str) or not tool_name.strip():
            raise ValueError(
                f"Invalid Assistant tool permission registry at {path}: tool_name is required"
            )
        normalized_name = tool_name.strip()
        if normalized_name in policies:
            raise ValueError(
                f"Invalid Assistant tool permission registry at {path}: "
                f"duplicate tool_name {normalized_name}"
            )
        policies[normalized_name] = _policy_payload(record, path=path)
    return policies


def _policy_payload(record: dict[str, Any], *, path: Path) -> dict[str, Any]:
    tags = record.get("permission_tags", [])
    if not isinstance(tags, list) or any(not isinstance(tag, str) or not tag.strip() for tag in tags):
        raise ValueError(
            f"Invalid Assistant tool permission registry at {path}: "
            "permission_tags must be a list of non-empty strings"
        )
    risk_level = record.get("risk_level", "low")
    if not isinstance(risk_level, str) or not risk_level.strip():
        raise ValueError(
            f"Invalid Assistant tool permission registry at {path}: risk_level is required"
        )
    requires_approval = record.get("requires_approval")
    if not isinstance(requires_approval, bool):
        raise ValueError(
            f"Invalid Assistant tool permission registry at {path}: "
            "requires_approval must be boolean"
        )
    approval_reason = record.get("approval_reason")
    if approval_reason is not None and not isinstance(approval_reason, str):
        raise ValueError(
            f"Invalid Assistant tool permission registry at {path}: "
            "approval_reason must be string or null"
        )
    return {
        "permission_tags": [tag.strip() for tag in tags],
        "risk_level": risk_level.strip(),
        "requires_approval": requires_approval,
        "approval_reason": approval_reason.strip() if isinstance(approval_reason, str) else None,
    }
