"""AI risk register loader."""

from __future__ import annotations

import json
from pathlib import Path

from ojtflow.core.contracts.ai_risk import AiRiskRegister


def load_ai_risk_register(path: Path) -> AiRiskRegister:
    """Load and validate the AI risk register."""

    raw = json.loads(path.read_text(encoding="utf-8"))
    register = AiRiskRegister.model_validate(raw)
    risk_ids = [risk.risk_id for risk in register.risks]
    if len(risk_ids) != len(set(risk_ids)):
        raise ValueError(f"Duplicate AI risk IDs in {path}")
    return register
