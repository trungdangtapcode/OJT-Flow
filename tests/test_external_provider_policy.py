import httpx
import pytest

from ojtflow.application.retrieval_service import RetrievalService
from ojtflow.config import clear_settings_cache, get_settings, save_runtime_assistant_settings
from ojtflow.core.contracts.assistant import AssistantToolSpec
from ojtflow.core.contracts.external_provider import (
    ExternalProviderPolicy,
    ExternalProviderRule,
)
from ojtflow.core.contracts.retrieval import (
    RetrievalPlan,
    RetrievalPlanCoverageSummary,
    RetrievalPlanTaskSummary,
    RetrievalPackage,
    RetrievalQuery,
    RetrievalQueryAnalysis,
    RetrievalSource,
    RetrievalSearchHint,
    RetrievalSearchTask,
    RetrievalTrace,
)
from ojtflow.core.errors import PolicyBlockedError, ToolExecutionError
from ojtflow.core.policy.external_provider_policy import (
    decide_external_provider_handoff,
    external_provider_policy_from_settings,
)
from ojtflow.data_tools.extract import Extractor, extract_document
from ojtflow.infrastructure.retrieval.embeddings import OpenAIEmbeddingProvider
from ojtflow.infrastructure.llm.openai import OpenAIResponsesPlanner


def _policy(
    surface: str,
    *,
    enabled: bool = True,
    allow_phi: bool = False,
    allow_unknown_sensitivity: bool = True,
) -> ExternalProviderPolicy:
    return ExternalProviderPolicy(
        rules=[
            ExternalProviderRule(
                surface=surface,  # type: ignore[arg-type]
                enabled=enabled,
                allow_phi=allow_phi,
                allow_unknown_sensitivity=allow_unknown_sensitivity,
                reason=f"Test rule for {surface}.",
            )
        ]
    )


def test_external_provider_policy_blocks_phi_by_default() -> None:
    policy = _policy("openai_llm", allow_phi=False)

    decision = decide_external_provider_handoff(
        policy,
        surface="openai_llm",
        text="patient_id=P001 ssn=123-45-6789 diagnosis=diabetes",
    )

    assert decision.allowed is False
    assert decision.phi_classification is not None
    assert decision.phi_classification.risk_level == "high"


def test_external_provider_policy_can_allow_phi_explicitly() -> None:
    policy = _policy("openai_llm", allow_phi=True)

    decision = decide_external_provider_handoff(
        policy,
        surface="openai_llm",
        text="patient_id=P001 ssn=123-45-6789 diagnosis=diabetes",
    )

    assert decision.allowed is True
    assert decision.phi_classification is not None


def test_external_provider_settings_are_runtime_reloadable(monkeypatch, tmp_path) -> None:
    runtime_path = tmp_path / "runtime_settings.json"
    monkeypatch.setenv("OJT_RUNTIME_SETTINGS_PATH", str(runtime_path))
    clear_settings_cache()

    try:
        settings = get_settings()
        updated = save_runtime_assistant_settings(
            settings,
            {
                "external_openai_llm_allow_phi": True,
                "external_openai_embeddings_enabled": False,
                "external_medical_search_allow_phi": True,
            },
        )
        clear_settings_cache()
        reloaded = get_settings()
    finally:
        clear_settings_cache()

    assert updated.external_openai_llm_allow_phi is True
    assert reloaded.external_openai_llm_allow_phi is True
    assert reloaded.external_openai_embeddings_enabled is False
    assert reloaded.external_medical_search_allow_phi is True


@pytest.mark.asyncio
async def test_openai_planner_blocks_phi_before_http(monkeypatch) -> None:
    def fail_client(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("OpenAI HTTP client should not be created")

    monkeypatch.setattr("ojtflow.infrastructure.llm.openai.httpx.AsyncClient", fail_client)
    planner = OpenAIResponsesPlanner(
        api_key="test-key",
        model="chat-latest",
        planning_model="gpt-4.1-mini",
        synthesis_model="gpt-4.1-mini",
        base_url="https://api.openai.test/v1",
        timeout_seconds=1,
        external_provider_policy=_policy("openai_llm", allow_phi=False),
    )

    with pytest.raises(PolicyBlockedError, match="cannot receive PHI"):
        await planner.plan(
            message="Validate patient_id=P001 ssn=123-45-6789",
            context={},
            tools=[
                AssistantToolSpec(
                    name="validate_with_evidence",
                    description="Validate data.",
                    permission_scope="read",
                    input_schema={"type": "object"},
                )
            ],
            max_tool_calls=1,
        )


def test_openai_embedding_provider_blocks_phi_before_http() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise AssertionError("OpenAI embedding HTTP call should not run")

    provider = OpenAIEmbeddingProvider(
        api_key="test-key",
        model="text-embedding-3-small",
        dimensions=3,
        base_url="https://api.openai.test/v1",
        timeout_seconds=1,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        external_provider_policy=_policy("openai_embeddings", allow_phi=False),
    )

    with pytest.raises(PolicyBlockedError, match="cannot receive PHI"):
        provider.embed_query("patient_id=P001 ssn=123-45-6789")


def test_openai_vision_ocr_blocks_unknown_sensitivity_before_http(monkeypatch) -> None:
    monkeypatch.setenv("OJT_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OJT_EXTERNAL_OPENAI_OCR_ALLOW_UNKNOWN", "false")
    clear_settings_cache()

    try:
        with pytest.raises(ToolExecutionError, match="blocked by external-provider policy"):
            extract_document(
                b"not-real-image-bytes",
                "scan.png",
                prefer=Extractor.OPENAI_VISION,
            )
    finally:
        clear_settings_cache()


def test_retrieval_service_suppresses_external_search_handoff_when_policy_blocks_phi() -> None:
    class FakeRepository:
        def search(self, _query: RetrievalQuery) -> RetrievalPackage:
            return RetrievalPackage(
                trace=RetrievalTrace(strategy="fake"),
                handoff_context={
                    "query_analysis": {
                        "search_hints": [
                            {
                                "target": "pubmed",
                                "query": "patient P001 SSN 123-45-6789",
                            }
                        ],
                        "retrieval_tasks": [
                            {
                                "target": "local_corpus",
                                "query": "FHIR Observation",
                            },
                            {
                                "target": "external_medical_index",
                                "query": "patient P001 SSN 123-45-6789",
                            },
                        ],
                    }
                },
            )

        def plan(self, _query: RetrievalQuery):  # pragma: no cover - not used here
            raise NotImplementedError

        def list_sources(self) -> list[RetrievalSource]:  # pragma: no cover
            return []

        def reindex(self, *, include_seeded=True, include_corpus=True):  # pragma: no cover
            return {}

        def integrity_report(
            self,
            *,
            include_seeded=True,
            include_corpus=False,
        ):  # pragma: no cover
            raise NotImplementedError

    service = RetrievalService(
        FakeRepository(),  # type: ignore[arg-type]
        external_provider_policy=_policy("external_medical_search", allow_phi=False),
    )

    package = service.search(
        RetrievalQuery(query="patient_id=P001 ssn=123-45-6789 FHIR Observation")
    )

    query_analysis = package.handoff_context["query_analysis"]
    assert query_analysis["search_hints"] == []
    assert query_analysis["retrieval_tasks"] == [
        {"target": "local_corpus", "query": "FHIR Observation"}
    ]
    assert query_analysis["external_search_suppressed"] is True
    assert "external_medical_search_policy_blocked" in package.trace.safety_flags
    assert package.handoff_context["external_provider_policy"]["external_medical_search"][
        "allowed"
    ] is False


def test_retrieval_plan_suppression_updates_counts_when_policy_blocks_phi() -> None:
    query = RetrievalQuery(query="patient_id=P001 ssn=123-45-6789 FHIR Observation")

    class FakeRepository:
        def search(self, _query: RetrievalQuery):  # pragma: no cover - not used here
            raise NotImplementedError

        def plan(self, _query: RetrievalQuery) -> RetrievalPlan:
            return RetrievalPlan(
                query=query,
                query_analysis=RetrievalQueryAnalysis(
                    search_hints=[
                        RetrievalSearchHint(
                            target="fhir",
                            query="patient P001 SSN 123-45-6789",
                            rationale="External standard follow-up.",
                        )
                    ],
                    retrieval_tasks=[
                        RetrievalSearchTask(
                            task_id="local:primary",
                            label="Primary evidence search",
                            target="local_corpus",
                            action_type="run_local_search",
                            query="FHIR Observation",
                            rationale="Search local trusted corpus.",
                            priority=1,
                            required=True,
                        ),
                        RetrievalSearchTask(
                            task_id="external:fhir:1",
                            label="FHIR follow-up",
                            target="external_medical_index",
                            action_type="open_external_url",
                            query="patient P001 SSN 123-45-6789",
                            rationale="Review external FHIR docs.",
                            priority=2,
                        ),
                    ],
                ),
                coverage_summary=RetrievalPlanCoverageSummary(
                    ready=True,
                    local_task_count=1,
                    required_local_task_count=1,
                    external_task_count=1,
                    standard_count=1,
                    filter_count=0,
                    standards=["FHIR"],
                    next_action="Run local and external tasks.",
                    summary="Plan includes external follow-up.",
                ),
                task_summary=RetrievalPlanTaskSummary(
                    total_task_count=2,
                    runnable_local_count=1,
                    required_runnable_local_count=1,
                    external_open_count=1,
                    external_copy_count=0,
                    manual_followup_count=1,
                    blocked_task_count=0,
                    primary_action="Run local and external tasks.",
                    summary="1 local and 1 external task.",
                ),
                search_signature="pending",
                summary="Plan includes external search.",
            )

        def list_sources(self) -> list[RetrievalSource]:  # pragma: no cover
            return []

        def reindex(self, *, include_seeded=True, include_corpus=True):  # pragma: no cover
            return {}

        def integrity_report(
            self,
            *,
            include_seeded=True,
            include_corpus=False,
        ):  # pragma: no cover
            raise NotImplementedError

    service = RetrievalService(
        FakeRepository(),  # type: ignore[arg-type]
        external_provider_policy=_policy("external_medical_search", allow_phi=False),
    )

    plan = service.plan(query)

    assert plan.query_analysis.search_hints == []
    assert [task.target for task in plan.query_analysis.retrieval_tasks] == ["local_corpus"]
    assert plan.coverage_summary.external_task_count == 0
    assert plan.task_summary.external_open_count == 0
    assert plan.task_summary.manual_followup_count == 0
    assert plan.task_summary.blocked_task_count == 1
    assert plan.query_analysis.diagnostics[-1].code == "external_medical_search_policy_blocked"


def test_settings_build_external_provider_policy(monkeypatch) -> None:
    monkeypatch.setenv("OJT_EXTERNAL_OPENAI_LLM_ALLOW_PHI", "true")
    monkeypatch.setenv("OJT_EXTERNAL_MEDICAL_SEARCH_ENABLED", "false")
    clear_settings_cache()

    try:
        policy = external_provider_policy_from_settings(get_settings())
    finally:
        clear_settings_cache()

    rules = {rule.surface: rule for rule in policy.rules}
    assert rules["openai_llm"].allow_phi is True
    assert rules["external_medical_search"].enabled is False
