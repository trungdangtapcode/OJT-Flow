"""External provider policy contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.contracts.phi import PhiClassification


ExternalProviderSurface = Literal[
    "openai_llm",
    "openai_vision_ocr",
    "openai_embeddings",
    "huggingface_embeddings",
    "external_medical_search",
]


class ExternalProviderRule(ContractModel):
    """One external provider boundary rule."""

    surface: ExternalProviderSurface
    enabled: bool = True
    allow_phi: bool = False
    allow_unknown_sensitivity: bool = True
    reason: str


class ExternalProviderPolicy(ContractModel):
    """Versioned policy controlling external provider handoffs."""

    policy_id: str = "external_provider_policy_v0"
    version: str = "2026-06-11"
    rules: list[ExternalProviderRule] = Field(default_factory=list)


class ExternalProviderDecision(ContractModel):
    """Decision for one provider handoff attempt."""

    surface: ExternalProviderSurface
    allowed: bool
    reason: str
    phi_classification: PhiClassification | None = None
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
