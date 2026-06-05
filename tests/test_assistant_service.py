import asyncio

import pytest

from ojtflow.application.assistant_service import AssistantService
from ojtflow.application.assistant_tools import ASSISTANT_TOOL_SPECS, OJTFlowToolExecutor
from ojtflow.core.contracts.assistant import AssistantPlan, AssistantToolPlan
from ojtflow.core.errors import ToolExecutionError
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

    async def synthesize(
        self,
        *,
        message,
        context,
        plan,
        tool_results,
        findings,
        evidence_summary,
    ):
        del message, context, plan, tool_results, findings, evidence_summary
        return "LLM synthesized answer with cited evidence."


class _SlowPlanner(_FakePlanner):
    async def plan(self, *, message, context, tools, max_tool_calls):
        await asyncio.sleep(0.03)
        return await super().plan(
            message=message,
            context=context,
            tools=tools,
            max_tool_calls=max_tool_calls,
        )


class _StreamingPlanner(_FakePlanner):
    async def plan_stream(self, *, message, context, tools, max_tool_calls):
        del message, context, tools, max_tool_calls
        yield {
            "type": "planning_step",
            "label": "Planner request sent",
            "message": "Planning through the fake stream.",
        }
        yield {"type": "planning_delta", "delta": '{"message":"planned",'}
        yield {"type": "planning_delta", "delta": '"tool_calls":[],"warnings":[]}'}
        yield {
            "type": "plan",
            "plan": AssistantPlan(message="planned", tool_calls=[]),
        }


class _FailingPlanner:
    model_name = "fake-model"

    async def plan(self, *, message, context, tools, max_tool_calls):
        del message, context, tools, max_tool_calls
        raise ToolExecutionError("Planner unavailable.")


class _FailingSynthesizer(_FakePlanner):
    async def synthesize(
        self,
        *,
        message,
        context,
        plan,
        tool_results,
        findings,
        evidence_summary,
    ):
        del message, context, plan, tool_results, findings, evidence_summary
        raise ToolExecutionError("Synthesis unavailable.")


class _FakeRetrievalToolExecutor:
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
            output={
                "evidence": [
                    {
                        "evidence_id": "ev_schema",
                        "source_id": "schema:lab_result_v1",
                        "source_type": "schema",
                        "claim": "Lab schema evidence.",
                        "trust_level": "approved",
                    }
                ],
                "trace": {"strategy": "test_strategy", "warnings": [], "safety_flags": []},
                "coverage": {"warnings": []},
                "evidence_buckets": [
                    {
                        "bucket_id": "schema",
                        "label": "Schema",
                        "description": "Schema support.",
                        "evidence_ids": ["ev_schema"],
                        "source_ids": ["schema:lab_result_v1"],
                        "hit_count": 1,
                        "required": True,
                        "status": "available",
                        "warnings": [],
                    },
                    {
                        "bucket_id": "policy",
                        "label": "Policy",
                        "description": "Policy support.",
                        "evidence_ids": [],
                        "source_ids": [],
                        "hit_count": 0,
                        "required": True,
                        "status": "missing",
                        "warnings": ["missing_policy_evidence"],
                    },
                ],
                "remediation_summary": (
                    "Recover Policy evidence (P20; apply filter 1)"
                ),
                "interpretation": {
                    "status": "support_gaps",
                    "summary": (
                        "The top result is schema:lab_result_v1, but required "
                        "evidence support is missing for Policy."
                    ),
                    "top_evidence_id": "ev_schema",
                    "top_source_id": "schema:lab_result_v1",
                    "top_score_driver": "Schema match +0.20",
                    "support_status": "partial",
                    "matched_terms": ["hba1c", "unit"],
                    "concept_labels": ["LOINC laboratory test"],
                    "aspect_labels": ["Lab unit evidence"],
                    "required_bucket_count": 2,
                    "covered_required_bucket_count": 1,
                    "missing_required_buckets": ["Policy"],
                    "warning_count": 1,
                    "next_action_title": "Recover Policy evidence",
                    "next_action_detail": "Run a targeted policy evidence search.",
                    "metadata": {"quality_status": "review"},
                },
                "recommended_actions": [
                    {
                        "action_id": "retrieval_action:policy",
                        "priority": 20,
                        "severity": "warning",
                        "action_type": "apply_filter",
                        "title": "Recover Policy evidence",
                        "description": "Run a targeted policy evidence search.",
                        "suggested_filter": {"standard_system": "ojtflow_policy"},
                        "source_signal_codes": ["missing_required_evidence_buckets"],
                        "evidence_ids": ["ev_schema"],
                        "metadata": {"corrective_rule_id": "missing_required_bucket_recovery"},
                    }
                ],
            },
            summary="Retrieved evidence.",
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
    assert response.synthesis_mode == "llm"
    assert response.model == "fake-model"
    assert response.message == "LLM synthesized answer with cited evidence."
    assert response.tool_calls[0].tool_name == "retrieval_search"
    assert response.tool_calls[0].status == "completed"
    assert response.findings[0].title == "Trusted evidence retrieved"


@pytest.mark.asyncio
async def test_assistant_stream_emits_planning_progress_while_llm_plan_is_pending() -> None:
    service = AssistantService(
        _FakeToolExecutor(),  # type: ignore[arg-type]
        planner=_SlowPlanner(),
        max_tool_calls=2,
        planning_progress_interval_seconds=0.01,
    )

    events = [
        event
        async for event in service.chat_stream(
            message="search HbA1c",
            owner_user_id="usr_test",
        )
    ]

    event_types = [event["type"] for event in events]
    assert "planning_progress" in event_types
    assert event_types.index("planning_started") < event_types.index("planning_progress")
    assert event_types.index("planning_progress") < event_types.index("plan_ready")
    started = next(event for event in events if event["type"] == "planning_started")
    assert started["available_tool_count"] == 0
    assert started["max_tool_calls"] == 2
    progress = next(event for event in events if event["type"] == "planning_progress")
    assert progress["elapsed_seconds"] > 0
    assert "still running" in progress["message"]


@pytest.mark.asyncio
async def test_assistant_stream_emits_streamed_planner_steps_and_deltas() -> None:
    service = AssistantService(
        _FakeToolExecutor(),  # type: ignore[arg-type]
        planner=_StreamingPlanner(),
        max_tool_calls=2,
    )

    events = [
        event
        async for event in service.chat_stream(
            message="search HbA1c",
            owner_user_id="usr_test",
        )
    ]

    event_types = [event["type"] for event in events]
    assert "planning_step" in event_types
    assert "planning_delta" in event_types
    assert event_types.index("planning_delta") < event_types.index("plan_ready")
    assert event_types.index("plan_ready") < event_types.index("final")


@pytest.mark.asyncio
async def test_assistant_service_flags_missing_required_evidence_buckets() -> None:
    service = AssistantService(_FakeRetrievalToolExecutor())  # type: ignore[arg-type]

    response = await service.chat(
        message="Find trusted evidence for HbA1c units",
        context={"schema_id": "lab_result_v1"},
        owner_user_id="usr_test",
    )

    assert response.tool_calls[0].tool_name == "retrieval_search"
    assert response.message == (
        "The top result is schema:lab_result_v1, but required evidence support "
        "is missing for Policy."
    )
    assert response.findings[0].title == "Trusted evidence retrieved"
    assert response.findings[1].title == "Retrieval interpretation"
    assert "required evidence support is missing for Policy" in response.findings[1].detail
    assert response.findings[2].title == "Retrieval remediation"
    assert response.findings[2].detail == "Recover Policy evidence (P20; apply filter 1)"
    assert response.findings[3].title == "Evidence pack needs attention"
    assert "Policy" in response.findings[3].detail
    assert response.findings[4].title == "Recommended search action"
    assert "Recover Policy evidence" in response.findings[4].detail
    assert response.suggestions[0] == "Recover Policy evidence: Run a targeted policy evidence search."
    assert response.suggestions[1] == (
        "Next retrieval step: Recover Policy evidence (P20; apply filter 1)"
    )


@pytest.mark.asyncio
async def test_assistant_service_falls_back_when_llm_planning_fails() -> None:
    service = AssistantService(
        _FakeRetrievalToolExecutor(),  # type: ignore[arg-type]
        planner=_FailingPlanner(),
    )

    response = await service.chat(
        message="Find trusted evidence for HbA1c units",
        context={"schema_id": "lab_result_v1"},
        owner_user_id="usr_test",
    )

    assert response.mode == "deterministic"
    assert response.tool_calls[0].status == "completed"
    assert response.warnings == ["LLM planning failed: Planner unavailable."]


@pytest.mark.asyncio
async def test_assistant_service_falls_back_when_llm_synthesis_fails() -> None:
    service = AssistantService(
        _FakeToolExecutor(),  # type: ignore[arg-type]
        planner=_FailingSynthesizer(),
    )

    response = await service.chat(message="search HbA1c", owner_user_id="usr_test")

    assert response.mode == "llm"
    assert response.synthesis_mode == "deterministic"
    assert response.message == (
        "Retrieved 0 trusted evidence item(s) with the configured retrieval strategy."
    )
    assert response.warnings == ["LLM answer synthesis failed: Synthesis unavailable."]


def test_assistant_tool_executor_skips_missing_required_arguments() -> None:
    executor = OJTFlowToolExecutor(None, None)  # type: ignore[arg-type]

    result = executor.execute(
        AssistantToolPlan(
            tool_name="validate_with_evidence",
            arguments={"schema_id": "lab_result_v1"},
        )
    )

    assert result.status == "skipped"
    assert result.error == "missing_required_arguments"
    assert "data" in result.summary


def test_assistant_retrieval_tool_forwards_exact_source_filters() -> None:
    class FakeWorkflowService:
        def __init__(self) -> None:
            self.query = None

        def search_retrieval(self, query, owner_user_id=None):
            self.query = query
            return type(
                "Package",
                (),
                {"model_dump": lambda _self, mode="json": {"evidence": [], "hits": []}},
            )()

    workflow_service = FakeWorkflowService()
    executor = OJTFlowToolExecutor(workflow_service, None)  # type: ignore[arg-type]

    result = executor.execute(
        AssistantToolPlan(
            tool_name="retrieval_search",
            arguments={
                "query": "FHIR Observation unit source scope",
                "source_id": "standard:fhir_observation_r4",
                "source_type": "healthcare_standard",
                "trust_level": "approved",
            },
        ),
        owner_user_id="usr_test",
    )

    assert result.status == "completed"
    assert workflow_service.query is not None
    assert workflow_service.query.filters["source_id"] == "standard:fhir_observation_r4"
    assert workflow_service.query.filters["source_type"] == "healthcare_standard"
    assert workflow_service.query.filters["trust_level"] == "approved"


@pytest.mark.asyncio
async def test_deterministic_assistant_skips_unsupported_chat() -> None:
    service = AssistantService(_FakeToolExecutor())  # type: ignore[arg-type]

    response = await service.chat(message="hello there", owner_user_id="usr_test")

    assert response.mode == "deterministic"
    assert response.tool_calls == []
    assert response.findings == []
    assert response.warnings == ["No supported OJTFlow operation was detected."]
    assert "validate data" in response.message


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
    tool_call_schema = captured["json"]["text"]["format"]["schema"]["properties"][
        "tool_calls"
    ]["items"]
    assert "arguments_json" in tool_call_schema["properties"]
    assert "arguments" not in tool_call_schema["properties"]
    assert tool_call_schema["additionalProperties"] is False


@pytest.mark.asyncio
async def test_openai_responses_planner_synthesizes_answer_from_tool_results(
    monkeypatch,
) -> None:
    captured = {}

    class FakeResponse:
        status_code = 200

        @property
        def text(self):
            return "ok"

        def json(self):
            return {"output_text": "Use UCUM evidence for missing units [terminology:ucum]."}

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
        model="gpt-5-mini",
        base_url="https://api.openai.com/v1",
        timeout_seconds=9.0,
    )

    answer = await planner.synthesize(
        message="Explain missing units",
        context={"data": "<redacted 100 characters>", "schema_id": "lab_result_v1"},
        plan=AssistantPlan(message="planned"),
        tool_results=[
            {
                "tool_name": "retrieval_search",
                "status": "completed",
                "evidence": [{"source_id": "terminology:ucum", "claim": "UCUM units."}],
            }
        ],
        findings=[],
        evidence_summary=[
            {
                "source_id": "terminology:ucum",
                "claim": "UCUM units.",
                "trust_level": "approved",
            }
        ],
    )

    assert answer == "Use UCUM evidence for missing units [terminology:ucum]."
    assert captured["json"]["model"] == "gpt-5-mini"
    assert "text" not in captured["json"]
    assert "tool_results" in captured["json"]["input"][1]["content"][0]["text"]
