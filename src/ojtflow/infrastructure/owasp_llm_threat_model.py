"""OWASP LLM threat model loader."""

from __future__ import annotations

import json
from pathlib import Path

from ojtflow.core.contracts.owasp_llm import (
    OwaspLlmCategoryId,
    OwaspLlmThreatModel,
)


REQUIRED_OWASP_LLM_CATEGORY_IDS: tuple[OwaspLlmCategoryId, ...] = (
    "LLM01",
    "LLM02",
    "LLM03",
    "LLM04",
    "LLM05",
    "LLM06",
    "LLM07",
    "LLM08",
    "LLM09",
    "LLM10",
)


def load_owasp_llm_threat_model(path: Path) -> OwaspLlmThreatModel:
    """Load and validate the OWASP LLM threat model."""

    raw = json.loads(path.read_text(encoding="utf-8"))
    model = OwaspLlmThreatModel.model_validate(raw)
    category_ids = [category.category_id for category in model.categories]
    if len(category_ids) != len(set(category_ids)):
        raise ValueError(f"Duplicate OWASP LLM category IDs in {path}")
    missing = sorted(set(REQUIRED_OWASP_LLM_CATEGORY_IDS) - set(category_ids))
    extra = sorted(set(category_ids) - set(REQUIRED_OWASP_LLM_CATEGORY_IDS))
    if missing or extra:
        raise ValueError(
            f"OWASP LLM threat model must contain exactly {REQUIRED_OWASP_LLM_CATEGORY_IDS}; "
            f"missing={missing}, extra={extra}"
        )
    return model
