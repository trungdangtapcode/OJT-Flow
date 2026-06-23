"""Tool registry and execution contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.contracts.enums import ToolPermission
from ojtflow.core.contracts.issue import Issue


class ToolSpec(ContractModel):
    """Declarative metadata for rule-based tool access."""

    name: str
    version: str = "0.1.0"
    input_model: str
    output_model: str
    permission_scope: ToolPermission
    allowed_agents: list[str] = Field(default_factory=list)
    requires_approval: bool = False
    idempotent: bool = True
    logs_sensitive_raw_data: bool = False


class ToolResult(ContractModel):
    """Generic rule-based tool result wrapper."""

    tool_name: str
    status: str
    output: dict[str, Any] = Field(default_factory=dict)
    issues: list[Issue] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

