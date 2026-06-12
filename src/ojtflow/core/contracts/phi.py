"""PHI and sensitive-data classification contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.contracts.issue import SourceLocation
from ojtflow.core.ids import new_id


PhiTargetType = Literal[
    "field",
    "row",
    "document",
    "chunk",
    "chat_message",
    "generated_output",
]
PhiRiskLevel = Literal["none", "low", "medium", "high"]
PhiCategory = Literal[
    "direct_identifier",
    "contact",
    "clinical_context",
    "demographic",
    "free_text_sensitive",
    "unknown_sensitive",
]


class PhiFieldRule(ContractModel):
    """Data-driven field-name rule for PHI classification."""

    rule_id: str
    tokens: list[str] = Field(default_factory=list)
    category: PhiCategory
    kind: str
    confidence: float = Field(default=0.85, ge=0, le=1)
    reason: str


class PhiPatternRule(ContractModel):
    """Data-driven value/text pattern rule for PHI classification."""

    rule_id: str
    pattern: str
    category: PhiCategory
    kind: str
    confidence: float = Field(default=0.9, ge=0, le=1)
    reason: str


class PhiClassificationPolicy(ContractModel):
    """Versioned PHI classification rules and risk behavior."""

    policy_id: str
    version: str
    field_rules: list[PhiFieldRule] = Field(default_factory=list)
    pattern_rules: list[PhiPatternRule] = Field(default_factory=list)
    high_risk_categories: list[PhiCategory] = Field(default_factory=list)
    medium_risk_categories: list[PhiCategory] = Field(default_factory=list)
    review_risk_levels: list[PhiRiskLevel] = Field(default_factory=list)
    external_provider_block_risk_levels: list[PhiRiskLevel] = Field(default_factory=list)


class PhiFinding(ContractModel):
    """One PHI or sensitive-data signal found in a data surface."""

    finding_id: str = Field(default_factory=lambda: new_id("phi"))
    target_type: PhiTargetType
    category: PhiCategory
    kind: str
    confidence: float = Field(default=0.85, ge=0, le=1)
    reason: str
    field: str | None = None
    value_preview: str | None = None
    source_ref: str | None = None
    location: SourceLocation | None = None
    requires_review: bool = True


class PhiClassification(ContractModel):
    """Summary plus findings for one classified surface."""

    classification_id: str = Field(default_factory=lambda: new_id("phic"))
    target_type: PhiTargetType
    source_ref: str | None = None
    risk_level: PhiRiskLevel = "none"
    finding_count: int = 0
    categories: list[PhiCategory] = Field(default_factory=list)
    findings: list[PhiFinding] = Field(default_factory=list)
    requires_review: bool = False
    external_provider_block_recommended: bool = False
