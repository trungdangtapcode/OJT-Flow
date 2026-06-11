"""Contracts for MCP resource and prompt catalogs."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel, NonBlankStr


class McpResourceSpec(ContractModel):
    """One MCP resource exposed by the local OJTFlow MCP server."""

    resource_id: NonBlankStr
    uri: NonBlankStr
    name: NonBlankStr
    title: NonBlankStr
    description: NonBlankStr
    mime_type: NonBlankStr = "application/json"
    provider_key: NonBlankStr
    permission_scope: NonBlankStr = "data:read"
    tags: list[NonBlankStr] = Field(default_factory=list)
    roadmap_refs: list[NonBlankStr] = Field(default_factory=list)


class McpResourceCatalog(ContractModel):
    """Versioned MCP resource registry loaded from trusted data."""

    version: NonBlankStr
    resources: list[McpResourceSpec] = Field(default_factory=list)


class McpPromptArgument(ContractModel):
    """One argument accepted by a cataloged MCP prompt template."""

    name: NonBlankStr
    description: NonBlankStr
    required: bool = True
    default: str | None = None
    value_hint: str | None = None


class McpPromptSpec(ContractModel):
    """One data-driven MCP prompt template."""

    prompt_id: NonBlankStr
    name: NonBlankStr
    title: NonBlankStr
    description: NonBlankStr
    task_type: NonBlankStr
    template: NonBlankStr
    arguments: list[McpPromptArgument] = Field(default_factory=list)
    recommended_tools: list[NonBlankStr] = Field(default_factory=list)
    evidence_required: bool = False
    write_actions_allowed: bool = False
    tags: list[NonBlankStr] = Field(default_factory=list)
    roadmap_refs: list[NonBlankStr] = Field(default_factory=list)


class McpPromptCatalog(ContractModel):
    """Versioned MCP prompt registry loaded from trusted data."""

    version: NonBlankStr
    prompts: list[McpPromptSpec] = Field(default_factory=list)


class McpRemoteDeploymentControl(ContractModel):
    """One control required before exposing MCP over remote transports."""

    control_id: NonBlankStr
    title: NonBlankStr
    requirement: NonBlankStr
    status: NonBlankStr = "required"
    phase: NonBlankStr = "before_remote"
    verification: NonBlankStr
    blocks_remote: bool = True
    references: list[NonBlankStr] = Field(default_factory=list)


class McpRemoteDeploymentPolicy(ContractModel):
    """Data-driven remote MCP deployment readiness policy."""

    version: NonBlankStr
    status: NonBlankStr = "design_only"
    remote_exposure_allowed: bool = False
    summary: NonBlankStr
    deployment_modes: list[NonBlankStr] = Field(default_factory=list)
    required_controls: list[McpRemoteDeploymentControl] = Field(default_factory=list)
    oauth: dict[str, Any] = Field(default_factory=dict)
    resource_indicators: dict[str, Any] = Field(default_factory=dict)
    per_user_scoping: dict[str, Any] = Field(default_factory=dict)
    rate_limits: dict[str, Any] = Field(default_factory=dict)
    audit: dict[str, Any] = Field(default_factory=dict)
    roadmap_refs: list[NonBlankStr] = Field(default_factory=list)
