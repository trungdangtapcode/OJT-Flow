from ojtflow.core.contracts.enums import DataFormat, WorkflowStatus
from ojtflow.core.contracts.workflow import WorkflowIntent, WorkflowState
from ojtflow.infrastructure.storage.summary import filter_sort_page_summaries, workflow_stats


def _workflow(
    workflow_id: str,
    *,
    owner_user_id: str | None = None,
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    updated_at: str = "2026-01-01T00:00:00+00:00",
    schema_id: str | None = "lab_result_v1",
) -> WorkflowState:
    return WorkflowState(
        workflow_id=workflow_id,
        owner_user_id=owner_user_id,
        created_at="2026-01-01T00:00:00+00:00",
        updated_at=updated_at,
        status=status,
        user_instruction=f"Workflow {workflow_id}",
        intent=WorkflowIntent(
            target_format=DataFormat.JSON,
            options={"schema_id": schema_id},
        ),
    )


def test_summary_sort_uses_workflow_id_tie_breaker() -> None:
    workflows = [
        _workflow("wf_c"),
        _workflow("wf_a"),
        _workflow("wf_b"),
    ]

    page = filter_sort_page_summaries(
        workflows,
        sort="updated_at",
        direction="desc",
    )

    assert [item.workflow_id for item in page.items] == ["wf_a", "wf_b", "wf_c"]


def test_summary_sort_direction_only_applies_to_primary_field() -> None:
    workflows = [
        _workflow("wf_b", status=WorkflowStatus.COMPLETED),
        _workflow("wf_c", status=WorkflowStatus.NEEDS_HUMAN_REVIEW),
        _workflow("wf_a", status=WorkflowStatus.COMPLETED),
    ]

    page = filter_sort_page_summaries(
        workflows,
        sort="status",
        direction="asc",
    )

    assert [item.workflow_id for item in page.items] == ["wf_a", "wf_b", "wf_c"]


def test_summary_filter_page_and_stats_contract() -> None:
    workflows = [
        _workflow("wf_a", status=WorkflowStatus.COMPLETED, schema_id="lab_result_v1"),
        _workflow("wf_b", status=WorkflowStatus.FAILED, schema_id="patient_v1"),
        _workflow("wf_c", status=WorkflowStatus.COMPLETED, schema_id="lab_result_v1"),
    ]

    page = filter_sort_page_summaries(
        workflows,
        q="lab_result",
        page=1,
        page_size=1,
        sort="workflow_id",
        direction="asc",
    )
    stats = workflow_stats(workflows)

    assert page.total == 2
    assert page.page == 1
    assert page.page_size == 1
    assert [item.workflow_id for item in page.items] == ["wf_a"]
    assert stats.total == 3
    assert stats.completed == 2
    assert stats.failed == 1


def test_summary_and_stats_can_filter_by_owner() -> None:
    workflows = [
        _workflow("wf_a", owner_user_id="usr_a", status=WorkflowStatus.COMPLETED),
        _workflow("wf_b", owner_user_id="usr_b", status=WorkflowStatus.FAILED),
        _workflow("wf_c", owner_user_id=None, status=WorkflowStatus.COMPLETED),
    ]

    page = filter_sort_page_summaries(
        workflows,
        owner_user_id="usr_a",
    )
    stats = workflow_stats(workflows, owner_user_id="usr_a")

    assert page.total == 1
    assert page.items[0].workflow_id == "wf_a"
    assert page.items[0].owner_user_id == "usr_a"
    assert stats.total == 1
    assert stats.completed == 1
    assert stats.failed == 0
