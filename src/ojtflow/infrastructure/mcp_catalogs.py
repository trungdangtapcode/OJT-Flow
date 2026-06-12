"""Data-driven MCP resource and prompt catalog loaders."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from ojtflow.core.contracts.mcp import (
    McpPromptCatalog,
    McpPromptSpec,
    McpRemoteDeploymentPolicy,
    McpResourceCatalog,
    McpResourceSpec,
)


DEFAULT_MCP_RESOURCE_CATALOG_PATH = Path("assistant/mcp_resources.json")
DEFAULT_MCP_PROMPT_CATALOG_PATH = Path("assistant/mcp_prompts.json")
DEFAULT_MCP_REMOTE_POLICY_PATH = Path("assistant/remote_mcp_deployment_policy.json")


class _HasKey(Protocol):
    @property
    def key(self) -> str: ...


def load_mcp_resource_catalog(knowledge_root: Path) -> McpResourceCatalog:
    """Load the MCP resource catalog from trusted knowledge data."""

    path = knowledge_root / DEFAULT_MCP_RESOURCE_CATALOG_PATH
    if not path.exists():
        return McpResourceCatalog(version="mcp_resources.empty", resources=[])
    catalog = McpResourceCatalog.model_validate(_read_json_object(path))
    _ensure_unique(
        [_ResourceKey(resource) for resource in catalog.resources],
        path=path,
        field="resource_id",
    )
    _ensure_unique(
        [_ResourceUriKey(resource) for resource in catalog.resources],
        path=path,
        field="uri",
    )
    return catalog


def load_mcp_prompt_catalog(knowledge_root: Path) -> McpPromptCatalog:
    """Load the MCP prompt catalog from trusted knowledge data."""

    path = knowledge_root / DEFAULT_MCP_PROMPT_CATALOG_PATH
    if not path.exists():
        return McpPromptCatalog(version="mcp_prompts.empty", prompts=[])
    catalog = McpPromptCatalog.model_validate(_read_json_object(path))
    _ensure_unique(
        [_PromptKey(prompt) for prompt in catalog.prompts],
        path=path,
        field="prompt_id",
    )
    _ensure_unique(
        [_PromptNameKey(prompt) for prompt in catalog.prompts],
        path=path,
        field="name",
    )
    return catalog


def load_mcp_remote_deployment_policy(knowledge_root: Path) -> McpRemoteDeploymentPolicy:
    """Load the remote MCP deployment readiness policy from trusted knowledge data."""

    path = knowledge_root / DEFAULT_MCP_REMOTE_POLICY_PATH
    if not path.exists():
        return McpRemoteDeploymentPolicy(
            version="remote_mcp_policy.empty",
            status="missing",
            remote_exposure_allowed=False,
            summary="Remote MCP deployment policy is not configured.",
        )
    policy = McpRemoteDeploymentPolicy.model_validate(_read_json_object(path))
    _ensure_unique(
        [_RemoteControlKey(control) for control in policy.required_controls],
        path=path,
        field="control_id",
    )
    return policy


def render_mcp_prompt(prompt: McpPromptSpec, variables: dict[str, str]) -> str:
    """Render a cataloged prompt with simple explicit placeholder substitution."""

    rendered = prompt.template
    for argument in prompt.arguments:
        value = variables.get(argument.name)
        if value is None or value == "":
            value = argument.default or ""
        rendered = rendered.replace("{{" + argument.name + "}}", value)

    missing = [
        argument.name
        for argument in prompt.arguments
        if argument.required and not (variables.get(argument.name) or argument.default)
    ]
    if missing:
        rendered += "\n\nMissing required input: " + ", ".join(missing) + "."
    return rendered


def _read_json_object(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid MCP catalog at {path}: expected object")
    return raw


def _ensure_unique(items: list[_HasKey], *, path: Path, field: str) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for item in items:
        if item.key in seen:
            duplicates.add(item.key)
        seen.add(item.key)
    if duplicates:
        duplicate_text = ", ".join(sorted(duplicates))
        raise ValueError(f"Invalid MCP catalog at {path}: duplicate {field} {duplicate_text}")


class _ResourceKey:
    def __init__(self, resource: McpResourceSpec) -> None:
        self.key = resource.resource_id


class _ResourceUriKey:
    def __init__(self, resource: McpResourceSpec) -> None:
        self.key = resource.uri


class _PromptKey:
    def __init__(self, prompt: McpPromptSpec) -> None:
        self.key = prompt.prompt_id


class _PromptNameKey:
    def __init__(self, prompt: McpPromptSpec) -> None:
        self.key = prompt.name


class _RemoteControlKey:
    def __init__(self, control) -> None:
        self.key = control.control_id
