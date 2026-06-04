from pathlib import Path
from datetime import datetime, timedelta, timezone

import pytest

from ojtflow.application.workflow_service import WorkflowService
from ojtflow.core.contracts.auth import GoogleIdentityProfile
from ojtflow.core.contracts.enums import DataFormat, ReviewDecision, WorkflowStatus
from ojtflow.core.errors import NotFoundError
from ojtflow.infrastructure.retrieval.static import (
    StaticKnowledgeRepository,
    StaticRetrievalRepository,
)
from ojtflow.infrastructure.storage.auth_sqlite import SQLiteAuthRepository
from ojtflow.infrastructure.storage.sqlite import (
    SQLiteBackboneStore,
    SQLiteDatasetStore,
    SQLiteEventRepository,
    SQLiteWorkflowRepository,
)


ROOT = Path(__file__).resolve().parents[1]


def make_service(tmp_path: Path) -> WorkflowService:
    backbone = SQLiteBackboneStore(tmp_path / "ojtflow.db", tmp_path / "var")
    return WorkflowService(
        datasets=SQLiteDatasetStore(backbone),
        workflows=SQLiteWorkflowRepository(backbone),
        events=SQLiteEventRepository(backbone),
        knowledge=StaticKnowledgeRepository(ROOT / "knowledge"),
        retrieval=StaticRetrievalRepository(ROOT / "knowledge"),
    )


def test_sqlite_workflow_restart_resume_preserves_events(tmp_path: Path) -> None:
    text = (ROOT / "data/fixtures/structured/lab_results_messy.csv").read_text()
    service = make_service(tmp_path)
    workflow = service.start_workflow(
        instruction="Clean this CSV, convert it to JSON, and explain anomalies.",
        data=text,
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
        schema_id="lab_result_v1",
        require_human_review=True,
        owner_user_id="usr_sqlite_owner",
    )

    assert workflow.status == WorkflowStatus.NEEDS_HUMAN_REVIEW
    assert workflow.review is not None
    assert workflow.steps
    event_count_before = len(service.list_events(workflow.workflow_id))

    restarted = make_service(tmp_path)
    completed = restarted.submit_review(
        workflow.review.review_id,
        ReviewDecision.APPROVE,
        decided_by="usr_sqlite_restart_test",
        owner_user_id="usr_sqlite_owner",
    )
    events_after = restarted.list_events(completed.workflow_id)

    assert completed.status == WorkflowStatus.COMPLETED
    assert completed.owner_user_id == "usr_sqlite_owner"
    assert restarted.workflow_stats(owner_user_id="usr_sqlite_owner").total == 1
    assert restarted.workflow_stats(owner_user_id="usr_other").total == 0
    assert completed.output is not None
    assert completed.output.transformation is not None
    assert completed.output.transformation.output_ref is not None
    assert len(events_after) > event_count_before
    assert any(step.name == "workflow_completed" for step in completed.steps)


def test_sqlite_dataset_store_rejects_file_refs_outside_artifact_roots(
    tmp_path: Path,
) -> None:
    backbone = SQLiteBackboneStore(tmp_path / "ojtflow.db", tmp_path / "var")
    store = SQLiteDatasetStore(backbone)
    safe_dataset = store.put_text("safe dataset")
    safe_output = store.put_text("safe output", source_kind="generated")
    outside = tmp_path / "outside.txt"
    outside.write_text("outside data", encoding="utf-8")
    symlink = backbone.datasets_dir / "outside-link.txt"
    symlink.symlink_to(outside)

    assert store.get_text(safe_dataset.storage_ref) == "safe dataset"
    assert store.get_text(safe_output.storage_ref) == "safe output"
    with pytest.raises(NotFoundError, match="outside the configured artifact directory"):
        store.get_text(outside.resolve().as_uri())
    with pytest.raises(NotFoundError, match="outside the configured artifact directory"):
        store.get_text(symlink.absolute().as_uri())
    with pytest.raises(NotFoundError, match="Dataset file not found"):
        store.get_text(backbone.datasets_dir.resolve().as_uri())
    with pytest.raises(NotFoundError, match="local file URI"):
        store.get_text(f"file://evil-host{safe_dataset.storage_ref.removeprefix('file://')}")
    with pytest.raises(NotFoundError, match="absolute file URI"):
        store.get_text("file:var/datasets/relative.txt")


def test_sqlite_auth_repository_persists_and_revokes_sessions(tmp_path: Path) -> None:
    backbone = SQLiteBackboneStore(tmp_path / "ojtflow.db", tmp_path / "var")
    repository = SQLiteAuthRepository(backbone)
    user = repository.upsert_google_user(
        GoogleIdentityProfile(
            google_sub="google-sub-1",
            email="user@example.com",
            email_verified=True,
            display_name="Example User",
            avatar_url=None,
        )
    )
    token_hash = "a" * 64
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    session = repository.create_session(
        user_id=user.user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        user_agent="pytest",
        ip_address="127.0.0.1",
    )

    restarted = SQLiteAuthRepository(
        SQLiteBackboneStore(tmp_path / "ojtflow.db", tmp_path / "var")
    )
    authenticated = restarted.get_active_session(token_hash, datetime.now(timezone.utc))

    assert authenticated is not None
    assert authenticated.user.email == "user@example.com"
    assert authenticated.session.session_id == session.session_id

    restarted.revoke_session(token_hash)
    assert restarted.get_active_session(token_hash, datetime.now(timezone.utc)) is None
