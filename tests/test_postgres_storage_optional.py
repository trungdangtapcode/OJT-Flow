import os
from pathlib import Path

import pytest

from ojtflow.application.workflow_service import WorkflowService
from ojtflow.core.contracts.enums import DataFormat, ReviewDecision, WorkflowStatus
from ojtflow.infrastructure.retrieval.static import StaticKnowledgeRepository
from ojtflow.infrastructure.storage.postgres import (
    PostgresBackboneStore,
    PostgresDatasetStore,
    PostgresEventRepository,
    PostgresWorkflowRepository,
)


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(
    not os.getenv("OJT_TEST_POSTGRES_DSN"),
    reason="set OJT_TEST_POSTGRES_DSN to run Postgres integration test",
)
def test_postgres_workflow_restart_resume(tmp_path: Path) -> None:
    backbone = PostgresBackboneStore(os.environ["OJT_TEST_POSTGRES_DSN"], tmp_path / "var")
    service = WorkflowService(
        datasets=PostgresDatasetStore(backbone),
        workflows=PostgresWorkflowRepository(backbone),
        events=PostgresEventRepository(backbone),
        knowledge=StaticKnowledgeRepository(ROOT / "knowledge"),
    )
    text = (ROOT / "data/fixtures/structured/lab_results_messy.csv").read_text()
    workflow = service.start_workflow(
        instruction="Clean this CSV, convert it to JSON, and explain anomalies.",
        data=text,
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
        schema_id="lab_result_v1",
        require_human_review=True,
    )

    restarted = WorkflowService(
        datasets=PostgresDatasetStore(backbone),
        workflows=PostgresWorkflowRepository(backbone),
        events=PostgresEventRepository(backbone),
        knowledge=StaticKnowledgeRepository(ROOT / "knowledge"),
    )
    completed = restarted.submit_review(workflow.review.review_id, ReviewDecision.APPROVE)

    assert completed.status == WorkflowStatus.COMPLETED
    assert restarted.list_events(completed.workflow_id)

