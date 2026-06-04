"""MCP tools for OJTFlow healthcare data operations.

Run locally with:

    PYTHONPATH=src python -m ojtflow.mcp_servers.ojtflow_tools

Install the optional dependency first:

    pip install -e '.[mcp]'
"""

from __future__ import annotations

from typing import Any

from ojtflow.application.assistant_tools import OJTFlowToolExecutor
from ojtflow.core.errors import DependencyUnavailableError
from ojtflow.interfaces.api.deps import (
    _build_assistant_service,
    _build_medical_evidence_service,
    _build_workflow_service,
)

try:  # pragma: no cover - optional dependency path is verified by import tests.
    from mcp.server.fastmcp import FastMCP
except ModuleNotFoundError:  # pragma: no cover
    FastMCP = None  # type: ignore[assignment]


def create_server():
    """Create the OJTFlow MCP server."""

    if FastMCP is None:
        raise DependencyUnavailableError(
            "OJTFlow MCP server requires the optional dependency: pip install -e '.[mcp]'"
        )

    mcp = FastMCP("OJTFlow Healthcare Data Ops", json_response=True)
    executor = OJTFlowToolExecutor(
        workflow_service=_build_workflow_service(),
        medical_evidence_service=_build_medical_evidence_service(),
    )
    assistant = _build_assistant_service()

    @mcp.tool()
    async def assistant_chat(
        message: str,
        context: dict[str, Any] | None = None,
        execute_write_actions: bool = False,
    ) -> dict[str, Any]:
        """Run one natural-language OJTFlow assistant command over allowlisted tools."""

        response = await assistant.chat(
            message=message,
            context=context or {},
            execute_write_actions=execute_write_actions,
        )
        return response.model_dump(mode="json")

    @mcp.tool()
    def retrieval_search(
        query: str,
        top_k: int = 5,
        schema_id: str | None = None,
        clinical_domain: str | None = None,
        standard_system: str | None = None,
        trust_level: str | None = "approved",
    ) -> dict[str, Any]:
        """Search trusted OJTFlow healthcare evidence."""

        return executor.execute_tool(
            "retrieval_search",
            {
                "query": query,
                "top_k": top_k,
                "schema_id": schema_id,
                "clinical_domain": clinical_domain,
                "standard_system": standard_system,
                "trust_level": trust_level,
            },
        )

    @mcp.tool()
    def validate_data(
        data: str,
        input_format: str | None = None,
        schema_id: str | None = "lab_result_v1",
    ) -> dict[str, Any]:
        """Parse and validate JSON, YAML, CSV, or extracted markdown text."""

        return executor.execute_tool(
            "validate_data",
            {"data": data, "input_format": input_format, "schema_id": schema_id},
        )

    @mcp.tool()
    def validate_with_evidence(
        data: str,
        input_format: str | None = None,
        schema_id: str | None = "lab_result_v1",
        fields: list[str] | None = None,
        clinical_domain: str | None = "laboratory",
        standard_system: str | None = None,
        query: str | None = None,
        top_k: int = 5,
    ) -> dict[str, Any]:
        """Validate healthcare data and retrieve standards evidence explaining issues."""

        return executor.execute_tool(
            "validate_with_evidence",
            {
                "data": data,
                "input_format": input_format,
                "schema_id": schema_id,
                "fields": fields or [],
                "clinical_domain": clinical_domain,
                "standard_system": standard_system,
                "query": query,
                "top_k": top_k,
            },
        )

    @mcp.tool()
    def convert_data(
        data: str,
        target_format: str = "json",
        input_format: str | None = None,
    ) -> dict[str, Any]:
        """Convert JSON, YAML, CSV, or extracted markdown text."""

        return executor.execute_tool(
            "convert_data",
            {
                "data": data,
                "input_format": input_format,
                "target_format": target_format,
            },
        )

    @mcp.tool()
    def fhir_profile(data: str) -> dict[str, Any]:
        """Profile FHIR-like JSON and produce schema evidence."""

        return executor.execute_tool("fhir_profile", {"data": data})

    @mcp.tool()
    def list_workflows(status: str | None = None, limit: int = 10) -> dict[str, Any]:
        """List workflows in the configured OJTFlow backend."""

        return executor.execute_tool(
            "list_workflows",
            {"status": status, "limit": limit},
        )

    @mcp.tool()
    def list_reviews(status: str | None = "pending", limit: int = 10) -> dict[str, Any]:
        """List human-review-gated workflows."""

        return executor.execute_tool(
            "list_reviews",
            {"status": status, "limit": limit},
        )

    @mcp.tool()
    def get_workflow(workflow_id: str) -> dict[str, Any]:
        """Inspect one workflow by ID."""

        return executor.execute_tool("get_workflow", {"workflow_id": workflow_id})

    @mcp.tool()
    def workflow_summary(workflow_id: str) -> dict[str, Any]:
        """Summarize one workflow for operator review and next action."""

        return executor.execute_tool("workflow_summary", {"workflow_id": workflow_id})

    @mcp.tool()
    def start_workflow(
        instruction: str,
        data: str,
        input_format: str | None = None,
        target_format: str = "json",
        schema_id: str | None = "lab_result_v1",
        require_human_review: bool = True,
        execute_write_actions: bool = False,
    ) -> dict[str, Any]:
        """Create a workflow only when execute_write_actions is explicitly true."""

        return executor.execute_tool(
            "start_workflow",
            {
                "instruction": instruction,
                "data": data,
                "input_format": input_format,
                "target_format": target_format,
                "schema_id": schema_id,
                "require_human_review": require_human_review,
            },
            execute_write_actions=execute_write_actions,
        )

    return mcp


def main() -> None:
    create_server().run()


if __name__ == "__main__":  # pragma: no cover
    main()
