import os
from pathlib import Path

import pytest

from ojtflow.application.workflow_service import WorkflowService
from ojtflow.core.contracts.enums import DataFormat, ReviewDecision, WorkflowStatus
from ojtflow.core.contracts.retrieval import RetrievalQuery
from ojtflow.core.errors import NotFoundError
from ojtflow.infrastructure.retrieval.postgres import PostgresRetrievalRepository
from ojtflow.infrastructure.retrieval.static import StaticKnowledgeRepository
from ojtflow.infrastructure.storage.postgres import (
    PostgresBackboneStore,
    PostgresDatasetStore,
    PostgresEventRepository,
    PostgresWorkflowRepository,
)


ROOT = Path(__file__).resolve().parents[1]


class _FakePostgresBackbone:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.datasets_dir = data_dir / "datasets"
        self.outputs_dir = data_dir / "outputs"
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)


class _FakeRetrievalCursor:
    def __init__(self) -> None:
        self.executed: list[tuple[str, tuple[object, ...]]] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def execute(self, sql: str, params: tuple[object, ...] = ()) -> None:
        self.executed.append((sql, params))

    def fetchall(self) -> list[dict]:
        return []


class _FakeRetrievalConnection:
    def __init__(self, cursor: _FakeRetrievalCursor) -> None:
        self._cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def cursor(self) -> _FakeRetrievalCursor:
        return self._cursor


class _FakeRetrievalBackbone(_FakePostgresBackbone):
    def __init__(self, data_dir: Path) -> None:
        super().__init__(data_dir)
        self.cursor = _FakeRetrievalCursor()

    def connect(self) -> _FakeRetrievalConnection:
        return _FakeRetrievalConnection(self.cursor)


def test_postgres_dataset_store_rejects_file_refs_outside_artifact_roots(
    tmp_path: Path,
) -> None:
    store = PostgresDatasetStore(_FakePostgresBackbone(tmp_path / "var"))
    safe_file = store.backbone.outputs_dir / "safe.txt"
    safe_file.write_text("safe", encoding="utf-8")
    outside = tmp_path / "outside.txt"
    outside.write_text("outside data", encoding="utf-8")
    symlink = store.backbone.outputs_dir / "outside-link.txt"
    symlink.symlink_to(outside)

    assert store.get_text(safe_file.resolve().as_uri()) == "safe"
    with pytest.raises(NotFoundError, match="outside the configured artifact directory"):
        store.get_text(outside.resolve().as_uri())
    with pytest.raises(NotFoundError, match="outside the configured artifact directory"):
        store.get_text(symlink.absolute().as_uri())
    with pytest.raises(NotFoundError, match="Dataset file not found"):
        store.get_text(store.backbone.outputs_dir.resolve().as_uri())
    with pytest.raises(NotFoundError, match="local file URI"):
        store.get_text(f"file://evil-host{safe_file.resolve().as_uri().removeprefix('file://')}")
    with pytest.raises(NotFoundError, match="absolute file URI"):
        store.get_text("file:var/outputs/relative.txt")


def test_postgres_retrieval_sets_hnsw_ef_search_for_vector_queries(tmp_path: Path) -> None:
    backbone = _FakeRetrievalBackbone(tmp_path / "var")
    repository = PostgresRetrievalRepository(
        backbone,
        ROOT / "knowledge",
        hnsw_ef_search=175,
        seed_defaults=False,
    )
    repository._vector_column_dimensions = lambda: 64

    chunks, warnings = repository._load_candidate_chunks(
        RetrievalQuery(query="FHIR Observation lab evidence", top_k=3)
    )

    assert chunks == []
    assert warnings == []
    assert backbone.cursor.executed[0] == (
        "select set_config('hnsw.ef_search', %s, true)",
        ("175",),
    )
    assert "from ojtflow.knowledge_chunks" in backbone.cursor.executed[1][0]


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
        retrieval=PostgresRetrievalRepository(backbone, ROOT / "knowledge"),
    )
    text = (ROOT / "data/fixtures/structured/lab_results_messy.csv").read_text()
    workflow = service.start_workflow(
        instruction="Clean this CSV, convert it to JSON, and explain anomalies.",
        data=text,
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
        schema_id="lab_result_v1",
        require_human_review=True,
        owner_user_id="usr_postgres_owner",
    )

    restarted = WorkflowService(
        datasets=PostgresDatasetStore(backbone),
        workflows=PostgresWorkflowRepository(backbone),
        events=PostgresEventRepository(backbone),
        knowledge=StaticKnowledgeRepository(ROOT / "knowledge"),
        retrieval=PostgresRetrievalRepository(backbone, ROOT / "knowledge"),
    )
    completed = restarted.submit_review(
        workflow.review.review_id,
        ReviewDecision.APPROVE,
        decided_by="usr_postgres_restart_test",
        owner_user_id="usr_postgres_owner",
    )

    assert completed.status == WorkflowStatus.COMPLETED
    assert completed.owner_user_id == "usr_postgres_owner"
    assert restarted.list_events(completed.workflow_id, owner_user_id="usr_postgres_owner")
    assert restarted.workflow_stats(owner_user_id="usr_postgres_owner").total >= 1
    assert restarted.workflow_stats(owner_user_id="usr_missing_owner").total == 0
