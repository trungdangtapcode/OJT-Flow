"""Validation, policy, and data-quality issue contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.contracts.enums import Severity
from ojtflow.core.ids import new_id


class SourceLocation(ContractModel):
    """Human and machine-readable location for an issue."""

    row: int | None = None
    column: str | None = None
    field: str | None = None
    source_ref: str | None = None


class Issue(ContractModel):
    """A precise issue that can drive review, UI, metrics, and audit."""

    issue_id: str = Field(default_factory=lambda: new_id("iss"))
    kind: str
    severity: Severity
    message: str
    location: SourceLocation | None = None
    suggested_action: str | None = None
    requires_review: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

