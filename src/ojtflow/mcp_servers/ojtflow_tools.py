"""MCP tools for OJTFlow healthcare data operations.

Run locally with:

    PYTHONPATH=src python -m ojtflow.mcp_servers.ojtflow_tools

Install the optional dependency first:

    pip install -e '.[mcp]'
"""

from __future__ import annotations

from typing import Any

from ojtflow.application.assistant_tools import OJTFlowToolExecutor
from ojtflow.application.tool_audit import append_tool_audit_record
from ojtflow.config import get_settings
from ojtflow.core.contracts.mcp import McpPromptSpec, McpResourceSpec
from ojtflow.core.errors import DependencyUnavailableError
from ojtflow.infrastructure.assistant.memory import load_assistant_memory_policy
from ojtflow.infrastructure.assistant.policies import load_assistant_tool_permission_policies
from ojtflow.infrastructure.assistant.progress import load_assistant_tool_progress_policies
from ojtflow.infrastructure.assistant_examples import load_assistant_examples
from ojtflow.infrastructure.assistant_templates import load_assistant_answer_templates
from ojtflow.infrastructure.mcp_catalogs import (
    load_mcp_prompt_catalog,
    load_mcp_resource_catalog,
    render_mcp_prompt,
)
from ojtflow.infrastructure.retrieval.catalogs import (
    load_retrieval_strategy_catalog,
    load_source_trust_policy_catalog,
)
from ojtflow.infrastructure.retrieval.presets import (
    load_retrieval_search_options,
    load_retrieval_search_presets,
)
from ojtflow.interfaces.api.deps import (
    _build_audit_repository,
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
    settings = get_settings()
    knowledge_root = settings.resolved_knowledge_dir
    workflow_service = _build_workflow_service()
    medical_evidence_service = _build_medical_evidence_service()
    executor = OJTFlowToolExecutor(
        workflow_service=workflow_service,
        medical_evidence_service=medical_evidence_service,
        tool_permission_policies=load_assistant_tool_permission_policies(knowledge_root),
    )
    audit_repository = _build_audit_repository()
    assistant = _build_assistant_service()
    _register_catalog_resources(
        mcp,
        load_mcp_resource_catalog(knowledge_root).resources,
        providers={
            "assistant_tool_catalog": lambda: [
                tool.model_dump(mode="json") for tool in executor.tool_specs
            ],
            "assistant_answer_templates": lambda: [
                template.model_dump(mode="json")
                for template in load_assistant_answer_templates(knowledge_root)
            ],
            "assistant_examples": lambda: [
                example.model_dump(mode="json")
                for example in load_assistant_examples(knowledge_root)
            ],
            "assistant_tool_progress_policies": lambda: {
                tool_name: [stage.model_dump(mode="json") for stage in stages]
                for tool_name, stages in load_assistant_tool_progress_policies(
                    knowledge_root
                ).items()
            },
            "assistant_memory_policy": lambda: load_assistant_memory_policy(
                knowledge_root
            ).model_dump(mode="json"),
            "retrieval_strategies": lambda: load_retrieval_strategy_catalog(
                knowledge_root
            ).model_dump(mode="json"),
            "source_trust_policies": lambda: load_source_trust_policy_catalog(
                knowledge_root
            ).model_dump(mode="json"),
            "retrieval_search_presets": lambda: [
                preset.model_dump(mode="json")
                for preset in load_retrieval_search_presets(knowledge_root)
            ],
            "retrieval_search_options": lambda: load_retrieval_search_options(
                knowledge_root
            ).model_dump(mode="json"),
            "workflow_queue": lambda: [
                workflow.model_dump(mode="json")
                for workflow in workflow_service.list_workflows(limit=50)
            ],
            "review_queue": lambda: [
                workflow.model_dump(mode="json")
                for workflow in workflow_service.list_reviews(status="pending", limit=50)
            ],
            "schema_catalog": lambda: workflow_service.list_schemas(),
            "knowledge_source_inventory": lambda: [
                source.model_dump(mode="json")
                for source in workflow_service.list_retrieval_sources()
            ],
        },
    )
    _register_catalog_prompts(mcp, load_mcp_prompt_catalog(knowledge_root).prompts)

    @mcp.tool()
    async def assistant_chat(
        message: str,
        context: dict[str, Any] | None = None,
        execute_write_actions: bool = False,
        owner_user_id: str | None = None,
        request_id: str | None = None,
        assistant_session_id: str | None = None,
    ) -> dict[str, Any]:
        """Run one natural-language OJTFlow assistant command over allowlisted tools."""

        arguments = {
            "message": message,
            "context": context or {},
            "execute_write_actions": execute_write_actions,
        }
        try:
            response = await assistant.chat(
                message=message,
                context=context or {},
                execute_write_actions=execute_write_actions,
                owner_user_id=owner_user_id,
                request_id=request_id,
                assistant_session_id=assistant_session_id,
            )
            payload = response.model_dump(mode="json")
            append_tool_audit_record(
                audit_repository,
                action_prefix="mcp",
                tool_name="assistant_chat",
                arguments=arguments,
                output=payload,
                owner_user_id=owner_user_id,
                request_id=request_id,
                assistant_session_id=assistant_session_id,
                actor_type="mcp",
                actor_id=owner_user_id or "mcp_client",
            )
            return payload
        except Exception as exc:
            append_tool_audit_record(
                audit_repository,
                action_prefix="mcp",
                tool_name="assistant_chat",
                arguments=arguments,
                output={"status": "failed", "error": exc.__class__.__name__},
                owner_user_id=owner_user_id,
                request_id=request_id,
                assistant_session_id=assistant_session_id,
                actor_type="mcp",
                actor_id=owner_user_id or "mcp_client",
            )
            raise

    @mcp.tool()
    def retrieval_search(
        query: str,
        top_k: int = 5,
        schema_id: str | None = None,
        clinical_domain: str | None = None,
        standard_system: str | None = None,
        trust_level: str | None = "approved",
        owner_user_id: str | None = None,
        request_id: str | None = None,
        assistant_session_id: str | None = None,
    ) -> dict[str, Any]:
        """Search trusted OJTFlow healthcare evidence."""

        return _execute_mcp_tool(
            executor,
            audit_repository,
            "retrieval_search",
            {
                "query": query,
                "top_k": top_k,
                "schema_id": schema_id,
                "clinical_domain": clinical_domain,
                "standard_system": standard_system,
                "trust_level": trust_level,
            },
            owner_user_id=owner_user_id,
            request_id=request_id,
            assistant_session_id=assistant_session_id,
        )

    @mcp.tool()
    def validate_data(
        data: str,
        input_format: str | None = None,
        schema_id: str | None = "lab_result_v1",
        owner_user_id: str | None = None,
        request_id: str | None = None,
        assistant_session_id: str | None = None,
    ) -> dict[str, Any]:
        """Parse and validate JSON, YAML, CSV, or extracted markdown text."""

        return _execute_mcp_tool(
            executor,
            audit_repository,
            "validate_data",
            {"data": data, "input_format": input_format, "schema_id": schema_id},
            owner_user_id=owner_user_id,
            request_id=request_id,
            assistant_session_id=assistant_session_id,
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
        owner_user_id: str | None = None,
        request_id: str | None = None,
        assistant_session_id: str | None = None,
    ) -> dict[str, Any]:
        """Validate healthcare data and retrieve standards evidence explaining issues."""

        return _execute_mcp_tool(
            executor,
            audit_repository,
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
            owner_user_id=owner_user_id,
            request_id=request_id,
            assistant_session_id=assistant_session_id,
        )

    @mcp.tool()
    def convert_data(
        data: str,
        target_format: str = "json",
        input_format: str | None = None,
        owner_user_id: str | None = None,
        request_id: str | None = None,
        assistant_session_id: str | None = None,
    ) -> dict[str, Any]:
        """Convert JSON, YAML, CSV, or extracted markdown text."""

        return _execute_mcp_tool(
            executor,
            audit_repository,
            "convert_data",
            {
                "data": data,
                "input_format": input_format,
                "target_format": target_format,
            },
            owner_user_id=owner_user_id,
            request_id=request_id,
            assistant_session_id=assistant_session_id,
        )

    @mcp.tool()
    def fhir_profile(
        data: str,
        owner_user_id: str | None = None,
        request_id: str | None = None,
        assistant_session_id: str | None = None,
    ) -> dict[str, Any]:
        """Profile FHIR-like JSON and produce schema evidence."""

        return _execute_mcp_tool(
            executor,
            audit_repository,
            "fhir_profile",
            {"data": data},
            owner_user_id=owner_user_id,
            request_id=request_id,
            assistant_session_id=assistant_session_id,
        )

    @mcp.tool()
    def list_workflows(
        status: str | None = None,
        limit: int = 10,
        owner_user_id: str | None = None,
        request_id: str | None = None,
        assistant_session_id: str | None = None,
    ) -> dict[str, Any]:
        """List workflows in the configured OJTFlow backend."""

        return _execute_mcp_tool(
            executor,
            audit_repository,
            "list_workflows",
            {"status": status, "limit": limit},
            owner_user_id=owner_user_id,
            request_id=request_id,
            assistant_session_id=assistant_session_id,
        )

    @mcp.tool()
    def list_reviews(
        status: str | None = "pending",
        limit: int = 10,
        owner_user_id: str | None = None,
        request_id: str | None = None,
        assistant_session_id: str | None = None,
    ) -> dict[str, Any]:
        """List human-review-gated workflows."""

        return _execute_mcp_tool(
            executor,
            audit_repository,
            "list_reviews",
            {"status": status, "limit": limit},
            owner_user_id=owner_user_id,
            request_id=request_id,
            assistant_session_id=assistant_session_id,
        )

    @mcp.tool()
    def get_workflow(
        workflow_id: str,
        owner_user_id: str | None = None,
        request_id: str | None = None,
        assistant_session_id: str | None = None,
    ) -> dict[str, Any]:
        """Inspect one workflow by ID."""

        return _execute_mcp_tool(
            executor,
            audit_repository,
            "get_workflow",
            {"workflow_id": workflow_id},
            owner_user_id=owner_user_id,
            request_id=request_id,
            assistant_session_id=assistant_session_id,
        )

    @mcp.tool()
    def workflow_summary(
        workflow_id: str,
        owner_user_id: str | None = None,
        request_id: str | None = None,
        assistant_session_id: str | None = None,
    ) -> dict[str, Any]:
        """Summarize one workflow for operator review and next action."""

        return _execute_mcp_tool(
            executor,
            audit_repository,
            "workflow_summary",
            {"workflow_id": workflow_id},
            owner_user_id=owner_user_id,
            request_id=request_id,
            assistant_session_id=assistant_session_id,
        )

    @mcp.tool()
    def start_workflow(
        instruction: str,
        data: str,
        input_format: str | None = None,
        target_format: str = "json",
        schema_id: str | None = "lab_result_v1",
        require_human_review: bool = True,
        execute_write_actions: bool = False,
        owner_user_id: str | None = None,
        request_id: str | None = None,
        assistant_session_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a workflow only when execute_write_actions is explicitly true."""

        return _execute_mcp_tool(
            executor,
            audit_repository,
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
            owner_user_id=owner_user_id,
            request_id=request_id,
            assistant_session_id=assistant_session_id,
        )

    @mcp.tool()
    def generate_mapping_draft(
        instruction: str,
        data: str,
        input_format: str | None = None,
        target_format: str = "json",
        schema_id: str | None = "lab_result_v1",
        mapping_goal: str | None = None,
        source_fields: list[str] | None = None,
        target_fields: list[str] | None = None,
        evidence_ids: list[str] | None = None,
        execute_write_actions: bool = False,
        owner_user_id: str | None = None,
        request_id: str | None = None,
        assistant_session_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a review-gated mapping draft without executing conversion."""

        return _execute_mcp_tool(
            executor,
            audit_repository,
            "generate_mapping_draft",
            {
                "instruction": instruction,
                "data": data,
                "input_format": input_format,
                "target_format": target_format,
                "schema_id": schema_id,
                "mapping_goal": mapping_goal,
                "source_fields": source_fields or [],
                "target_fields": target_fields or [],
                "evidence_ids": evidence_ids or [],
            },
            execute_write_actions=execute_write_actions,
            owner_user_id=owner_user_id,
            request_id=request_id,
            assistant_session_id=assistant_session_id,
        )

    @mcp.tool()
    def create_review_task(
        question: str,
        data: str | None = None,
        input_format: str | None = None,
        schema_id: str | None = "lab_result_v1",
        review_focus: str | None = None,
        source_workflow_id: str | None = None,
        source_turn_id: str | None = None,
        issue_kinds: list[str] | None = None,
        evidence_ids: list[str] | None = None,
        execute_write_actions: bool = False,
        owner_user_id: str | None = None,
        request_id: str | None = None,
        assistant_session_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a durable human-review task only when writes are explicit."""

        return _execute_mcp_tool(
            executor,
            audit_repository,
            "create_review_task",
            {
                "question": question,
                "data": data,
                "input_format": input_format,
                "schema_id": schema_id,
                "review_focus": review_focus,
                "source_workflow_id": source_workflow_id,
                "source_turn_id": source_turn_id,
                "issue_kinds": issue_kinds or [],
                "evidence_ids": evidence_ids or [],
            },
            execute_write_actions=execute_write_actions,
            owner_user_id=owner_user_id,
            request_id=request_id,
            assistant_session_id=assistant_session_id,
        )

    return mcp


def _execute_mcp_tool(
    executor: OJTFlowToolExecutor,
    audit_repository: Any,
    tool_name: str,
    arguments: dict[str, Any],
    *,
    execute_write_actions: bool = False,
    owner_user_id: str | None = None,
    request_id: str | None = None,
    assistant_session_id: str | None = None,
) -> dict[str, Any]:
    output = executor.execute_tool(
        tool_name,
        arguments,
        execute_write_actions=execute_write_actions,
        owner_user_id=owner_user_id,
        request_id=request_id,
    )
    append_tool_audit_record(
        audit_repository,
        action_prefix="mcp",
        tool_name=tool_name,
        arguments={
            **arguments,
            "execute_write_actions": execute_write_actions,
        },
        output=output,
        owner_user_id=owner_user_id,
        request_id=request_id,
        assistant_session_id=assistant_session_id,
        actor_type="mcp",
        actor_id=owner_user_id or "mcp_client",
    )
    return output


def _register_catalog_resources(
    mcp: Any,
    resources: list[McpResourceSpec],
    *,
    providers: dict[str, Any],
) -> None:
    for resource in resources:
        provider = providers.get(resource.provider_key)
        if provider is None:
            raise DependencyUnavailableError(
                f"MCP resource {resource.resource_id} uses unknown provider "
                f"{resource.provider_key}."
            )
        reader = _resource_reader(resource, provider)
        mcp.resource(
            resource.uri,
            name=resource.name,
            title=resource.title,
            description=resource.description,
            mime_type=resource.mime_type,
        )(reader)


def _resource_reader(resource: McpResourceSpec, provider):
    def read_resource() -> str:
        payload = {
            "resource": resource.model_dump(mode="json"),
            "data": provider(),
        }
        return json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True)

    read_resource.__name__ = f"read_{resource.name}"
    read_resource.__doc__ = resource.description
    return read_resource


def _register_catalog_prompts(mcp: Any, prompts: list[McpPromptSpec]) -> None:
    for prompt in prompts:
        renderer = _prompt_renderer(prompt)
        mcp.prompt(
            name=prompt.name,
            title=prompt.title,
            description=prompt.description,
        )(renderer)


def _prompt_renderer(prompt: McpPromptSpec):
    def render_prompt(
        data: str = "",
        workflow_id: str = "",
        schema_id: str = "",
        query: str = "",
        unit: str = "",
        review_status: str = "",
    ) -> str:
        return render_mcp_prompt(
            prompt,
            {
                "data": data,
                "workflow_id": workflow_id,
                "schema_id": schema_id,
                "query": query,
                "unit": unit,
                "review_status": review_status,
            },
        )

    render_prompt.__name__ = f"prompt_{prompt.name}"
    render_prompt.__doc__ = prompt.description
    return render_prompt


def main() -> None:
    create_server().run()


if __name__ == "__main__":  # pragma: no cover
    main()
