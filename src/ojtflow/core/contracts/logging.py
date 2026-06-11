"""Logging safety contracts."""

from __future__ import annotations

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel


class LogPhiFinding(ContractModel):
    """One raw-PHI-like signal found in log text."""

    source_ref: str
    line_number: int
    kind: str
    value_preview: str | None = None
    reason: str


class LogPhiScanResult(ContractModel):
    """Scan result for one log source."""

    source_ref: str
    finding_count: int = 0
    findings: list[LogPhiFinding] = Field(default_factory=list)
