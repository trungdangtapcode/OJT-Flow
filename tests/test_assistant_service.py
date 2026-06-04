import pytest

from ojtflow.application.assistant_service import AssistantService
from ojtflow.application.assistant_tools import ASSISTANT_TOOL_SPECS
from ojtflow.core.contracts.assistant import AssistantPlan, AssistantToolPlan
from ojtflow.infrastructure.llm.openai import OpenAIResponsesPlanner


class _FakeToolExecutor:
    @property
    def tool_specs(self):
        return []

    def execute(self, plan, *, execute_write_actions=False, owner_user_id=None):
        del execute_write_actions, owner_user_id
        from ojtflow.core.contracts.assistant import AssistantToolResult

        return AssistantToolResult(
            tool_name=plan.tool_name,
            status="completed",
            arguments=plan.arguments,
            output={"ok": True},
            summary=f"{plan.tool_name} completed.",
        )


class _FakePlanner:
    model_name = "fake-model"

    async def plan(self, *, message, context, tools, max_tool_calls):
        del message, context, tools, max_tool_calls
        return AssistantPlan(
            message="planned",
            tool_calls=[
                AssistantToolPlan(
                    tool_name="retrieval_search",
                    arguments={"query": "HbA1c"},
                    rationale="search",
                )
            ],
        )


@pytest.mark.asyncio
async def test_assistant_service_uses_planner_but_backend_executor_owns_tools() -> None:
    service = AssistantService(
        _FakeToolExecutor(),  # type: ignore[arg-type]
        planner=_FakePlanner(),
        max_tool_calls=2,
    )

    response = await service.chat(message="search HbA1c", owner_user_id="usr_test")

    assert response.mode == "llm"
    assert response.model == "fake-model"
    assert response.tool_calls[0].tool_name == "retrieval_search"
    assert response.tool_calls[0].status == "completed"
    assert response.findings[0].title == "Trusted evidence retrieved"


@pytest.mark.asyncio
async def test_openai_responses_planner_builds_structured_plan_request(monkeypatch) -> None:
    captured = {}

    class FakeResponse:
        status_code = 200

        @property
        def text(self):
            return "ok"

        def json(self):
            return {
                "output_text": (
                    '{"message":"ok","tool_calls":[{"tool_name":"retrieval_search",'
                    '"arguments":{"query":"HbA1c"},"rationale":"search"}],"warnings":[]}'
                )
            }

    class FakeAsyncClient:
        def __init__(self, *, timeout):
            captured["timeout"] = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, *, headers, json):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return FakeResponse()

    monkeypatch.setattr(
        "ojtflow.infrastructure.llm.openai.httpx.AsyncClient",
        FakeAsyncClient,
    )
    planner = OpenAIResponsesPlanner(
        api_key="test-key",
        model="chat-latest",
        base_url="https://api.openai.com/v1",
        timeout_seconds=9.0,
    )

    plan = await planner.plan(
        message="Search HbA1c evidence",
        context={},
        tools=list(ASSISTANT_TOOL_SPECS.values()),
        max_tool_calls=1,
    )

    assert plan.tool_calls[0].tool_name == "retrieval_search"
    assert captured["url"] == "https://api.openai.com/v1/responses"
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["json"]["model"] == "chat-latest"
    assert captured["json"]["text"]["format"]["type"] == "json_schema"
