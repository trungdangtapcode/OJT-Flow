"""PHI/sensitive text redaction preview contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.contracts.issue import SourceLocation
from ojtflow.core.ids import new_id


RedactionKind = Literal[
    "ssn",
    "email",
    "phone",
    "sensitive_field",
    "patient_identifier",
]


class RedactionMatch(ContractModel):
    """One potential sensitive span or structured field value."""

    match_id: str = Field(default_factory=lambda: new_id("red"))
    kind: RedactionKind
    value_preview: str
    replacement: str
    confidence: float = Field(default=0.9, ge=0, le=1)
    reason: str
    start: int | None = Field(default=None, ge=0)
    end: int | None = Field(default=None, ge=0)
    location: SourceLocation | None = None


class RedactionPreview(ContractModel):
    """Preview of redactions before text leaves the controlled boundary."""

    original_length: int = Field(ge=0)
    redacted_text: str
    matches: list[RedactionMatch] = Field(default_factory=list)
    external_provider_block_recommended: bool = False
    warnings: list[str] = Field(default_factory=list)
