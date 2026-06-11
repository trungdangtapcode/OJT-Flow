"""PHI/sensitive text redaction preview contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.contracts.issue import SourceLocation
from ojtflow.core.contracts.phi import PhiCategory, PhiClassification, PhiRiskLevel
from ojtflow.core.ids import new_id


RedactionKind = str
RedactionActionType = Literal[
    "mask",
    "suppress",
    "tokenize_placeholder",
    "review_gated_reveal",
]
RedactionMatchStatus = Literal["applied", "requires_review", "revealed"]


class RedactionPolicyRule(ContractModel):
    """Action policy for PHI categories, kinds, and risk levels."""

    rule_id: str
    action: RedactionActionType
    kinds: list[RedactionKind] = Field(default_factory=list)
    categories: list[PhiCategory] = Field(default_factory=list)
    risk_levels: list[PhiRiskLevel] = Field(default_factory=list)
    replacement_template: str | None = None
    review_required: bool = False
    reveal_requires_review: bool = False
    reason: str


class RedactionPolicy(ContractModel):
    """Versioned redaction behavior independent from PHI detection."""

    policy_id: str
    version: str
    default_action: RedactionActionType = "mask"
    token_namespace: str = "local_placeholder"
    rules: list[RedactionPolicyRule] = Field(default_factory=list)
    external_provider_block_actions: list[RedactionActionType] = Field(default_factory=list)


class RedactionMatch(ContractModel):
    """One potential sensitive span or structured field value."""

    match_id: str = Field(default_factory=lambda: new_id("red"))
    kind: RedactionKind
    value_preview: str
    replacement: str
    action: RedactionActionType = "mask"
    status: RedactionMatchStatus = "applied"
    rule_id: str | None = None
    token: str | None = None
    confidence: float = Field(default=0.9, ge=0, le=1)
    reason: str
    start: int | None = Field(default=None, ge=0)
    end: int | None = Field(default=None, ge=0)
    location: SourceLocation | None = None
    reveal_requires_review: bool = False


class RedactionPreview(ContractModel):
    """Preview of redactions before text leaves the controlled boundary."""

    policy_id: str | None = None
    policy_version: str | None = None
    original_length: int = Field(ge=0)
    redacted_text: str
    matches: list[RedactionMatch] = Field(default_factory=list)
    phi_classification: PhiClassification | None = None
    action_summary: dict[RedactionActionType, int] = Field(default_factory=dict)
    requires_review: bool = False
    reveal_required: bool = False
    reveal_approved: bool = False
    external_provider_block_recommended: bool = False
    warnings: list[str] = Field(default_factory=list)
