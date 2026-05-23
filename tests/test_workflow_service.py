from pathlib import Path

from ojtflow.application.workflow_service import WorkflowService
from ojtflow.core.contracts.enums import DataFormat, ReviewDecision, WorkflowStatus
from ojtflow.infrastructure.retrieval.static import StaticKnowledgeRepository
from ojtflow.infrastructure.storage.in_memory import (
    InMemoryDatasetStore,
    InMemoryEventRepository,
    InMemoryWorkflowRepository,
)


ROOT = Path(__file__).resolve().parents[1]


def make_service() -> WorkflowService:
    return WorkflowService(
        datasets=InMemoryDatasetStore(),
        workflows=InMemoryWorkflowRepository(),
        events=InMemoryEventRepository(),
        knowledge=StaticKnowledgeRepository(ROOT / "knowledge"),
    )


def test_workflow_pauses_for_review_then_completes_after_approval() -> None:
    service = make_service()
    text = (ROOT / "data/fixtures/structured/lab_results_messy.csv").read_text()

    workflow = service.start_workflow(
        instruction="Clean this CSV, convert it to JSON, and explain anomalies.",
        data=text,
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
        schema_id="lab_result_v1",
        require_human_review=True,
    )

    assert workflow.status == WorkflowStatus.NEEDS_HUMAN_REVIEW
    assert workflow.review is not None
    assert workflow.transformation_plan is not None
    assert workflow.validation_report is not None
    assert workflow.retrieved_context

    completed = service.submit_review(workflow.review.review_id, ReviewDecision.APPROVE)

    assert completed.status == WorkflowStatus.COMPLETED
    assert completed.output is not None
    assert completed.output.transformation is not None
    assert completed.explanation is not None
    assert completed.explanation.intended_use.startswith("Support data validation")


def test_review_rejection_cancels_workflow() -> None:
    service = make_service()
    text = (ROOT / "data/fixtures/structured/lab_results_messy.csv").read_text()

    workflow = service.start_workflow(
        instruction="Clean this CSV.",
        data=text,
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
    )

    cancelled = service.submit_review(workflow.review.review_id, ReviewDecision.REJECT)
    assert cancelled.status == WorkflowStatus.CANCELLED

