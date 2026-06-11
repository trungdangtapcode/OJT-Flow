"""Load data-driven governance defaults."""

from __future__ import annotations

import json
from pathlib import Path

from ojtflow.core.contracts.governance import WorkspaceDefaults


DEFAULT_WORKSPACE_DEFAULTS_PATH = Path("governance/workspace_defaults.json")


def load_workspace_defaults(knowledge_root: Path) -> WorkspaceDefaults:
    """Load initial workspace role/group/settings defaults."""

    path = knowledge_root / DEFAULT_WORKSPACE_DEFAULTS_PATH
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid workspace defaults at {path}: expected object")
    return WorkspaceDefaults.model_validate(raw)
