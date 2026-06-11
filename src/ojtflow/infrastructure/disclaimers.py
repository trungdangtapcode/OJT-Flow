"""Disclaimer policy loader."""

from __future__ import annotations

import json
from pathlib import Path

from ojtflow.core.contracts.disclaimer import DisclaimerPolicy, DisclaimerSurface


REQUIRED_DISCLAIMER_SURFACES: tuple[DisclaimerSurface, ...] = (
    "global",
    "assistant",
    "workbench",
    "workflows",
    "workflow_detail",
    "reviews",
    "retrieval",
    "audit",
    "schemas",
    "settings",
    "help",
)


def load_disclaimer_policy(path: Path) -> DisclaimerPolicy:
    """Load and validate the user-facing disclaimer policy."""

    raw = json.loads(path.read_text(encoding="utf-8"))
    policy = DisclaimerPolicy.model_validate(raw)
    surface_ids = [surface.surface_id for surface in policy.surfaces]
    if len(surface_ids) != len(set(surface_ids)):
        raise ValueError(f"Duplicate disclaimer surfaces in {path}")
    missing = sorted(set(REQUIRED_DISCLAIMER_SURFACES) - set(surface_ids))
    if missing:
        raise ValueError(f"Missing disclaimer surfaces in {path}: {missing}")
    return policy
