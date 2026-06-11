"""Contracts for MCP resource and prompt catalogs."""

from __future__ import annotations

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
