from pathlib import Path

import pytest

from ojtflow.application.assistant_service import AssistantService
from ojtflow.application.assistant_tools import OJTFlowToolExecutor
from ojtflow.application.medical_evidence_service import MedicalEvidenceService
from ojtflow.application.workflow_service import WorkflowService
from ojtflow.infrastructure.assistant.policies import load_assistant_tool_permission_policies
from ojtflow.infrastructure.assistant_evaluations import load_assistant_evaluation_suite
from ojtflow.infrastructure.retrieval.static import (
    StaticKnowledgeRepository,
    StaticRetrievalRepository,
)
from ojtflow.infrastructure.storage.in_memory import (
    InMemoryDatasetStore,
    InMemoryEventRepository,
    InMemoryWorkflowRepository,
)


ROOT = Path(__file__).resolve().parents[1]


def _assistant_service() -> AssistantService:
    knowledge_root = ROOT / "knowledge"
    workflow_service = WorkflowService(
        datasets=InMemoryDatasetStore(),
        workflows=InMemoryWorkflowRepository(),
        events=InMemoryEventRepository(),
        knowledge=StaticKnowledgeRepository(knowledge_root),
        retrieval=StaticRetrievalRepository(knowledge_root),
    )
    return AssistantService(
        OJTFlowToolExecutor(
            workflow_service=workflow_service,
            medical_evidence_service=MedicalEvidenceService(),
            tool_permission_policies=load_assistant_tool_permission_policies(knowledge_root),
        )
    )


def test_assistant_evaluation_suite_is_data_driven() -> None:
    suite = load_assistant_evaluation_suite(ROOT / "knowledge")

    assert suite.version == "assistant_evaluations.v1"
    assert len(suite.cases) >= 4
    assert {case.case_id for case in suite.cases} >= {
        "validate_lab_csv_with_evidence",
        "retrieve_ucum_unit_standard",
        "list_pending_reviews",
        "mapping_draft_is_write_gated",
    }
    assert all("F117" in case.roadmap_refs for case in suite.cases)


@pytest.mark.asyncio
async def test_assistant_evaluation_cases_match_tool_and_faithfulness_contracts() -> None:
    suite = load_assistant_evaluation_suite(ROOT / "knowledge")
    service = _assistant_service()

    for case in suite.cases:
        response = await service.chat(
            message=case.message,
            context=case.context,
            execute_write_actions=case.execute_write_actions,
            owner_user_id="usr_assistant_eval",
            request_id=f"req_{case.case_id}",
        )
        tool_names = [tool.tool_name for tool in response.tool_calls]
        tool_statuses = [tool.status for tool in response.tool_calls]
        answer = response.message.lower()
        evidence_source_ids = {evidence.source_id for evidence in response.evidence_summary}

        assert tool_names == case.expected_tool_names, case.case_id
        assert tool_statuses == case.expected_tool_statuses, case.case_id
        assert len(response.evidence_summary) >= case.min_evidence_summaries, case.case_id
        for term in case.required_answer_terms:
            assert term.lower() in answer, case.case_id
        for term in case.forbidden_answer_terms:
            assert term.lower() not in answer, case.case_id
        for source_id in case.required_evidence_source_ids:
            assert source_id in evidence_source_ids, case.case_id
