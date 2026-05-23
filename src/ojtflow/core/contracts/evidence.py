"""Evidence contracts for retrieval, validation, human review, and multimodal artifacts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.contracts.enums import EvidenceSourceType, TrustLevel
from ojtflow.core.ids import new_id


class Evidence(ContractModel):
    """Traceable support for a claim, issue, action, or explanation sentence."""

    evidence_id: str = Field(default_factory=lambda: new_id("ev"))
    source_type: EvidenceSourceType
    source_id: str
    claim: str
    source_version: str | None = None
    locator: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = None
    trust_level: TrustLevel = TrustLevel.APPROVED

