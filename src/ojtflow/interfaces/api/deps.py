"""API dependency assembly."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ojtflow.application.workflow_service import WorkflowService
from ojtflow.config import get_settings
from ojtflow.infrastructure.retrieval.static import StaticKnowledgeRepository
from ojtflow.infrastructure.storage.in_memory import (
    InMemoryDatasetStore,
    InMemoryEventRepository,
    InMemoryWorkflowRepository,
)
from ojtflow.infrastructure.storage.postgres import (
    PostgresBackboneStore,
    PostgresDatasetStore,
    PostgresEventRepository,
    PostgresWorkflowRepository,
)
from ojtflow.infrastructure.storage.sqlite import (
    SQLiteBackboneStore,
    SQLiteDatasetStore,
    SQLiteEventRepository,
    SQLiteWorkflowRepository,
)


@lru_cache(maxsize=1)
def _build_workflow_service() -> WorkflowService:
    """Build the default local service graph."""

    repo_root = Path(__file__).resolve().parents[4]
    settings = get_settings()
    if settings.storage_backend == "memory":
        datasets = InMemoryDatasetStore()
        workflows = InMemoryWorkflowRepository()
        events = InMemoryEventRepository()
    elif settings.storage_backend == "sqlite":
        backbone = SQLiteBackboneStore(
            settings.resolved_database_path,
            settings.resolved_data_dir,
        )
        datasets = SQLiteDatasetStore(backbone)
        workflows = SQLiteWorkflowRepository(backbone)
        events = SQLiteEventRepository(backbone)
    elif settings.storage_backend == "postgres":
        backbone = PostgresBackboneStore(
            settings.postgres_dsn,
            settings.resolved_data_dir,
        )
        datasets = PostgresDatasetStore(backbone)
        workflows = PostgresWorkflowRepository(backbone)
        events = PostgresEventRepository(backbone)
    else:
        raise ValueError(f"Unsupported storage backend: {settings.storage_backend}")

    return WorkflowService(
        datasets=datasets,
        workflows=workflows,
        events=events,
        knowledge=StaticKnowledgeRepository(repo_root / "knowledge"),
    )


async def get_workflow_service() -> WorkflowService:
    """Return the cached workflow service without FastAPI threadpool dispatch."""

    return _build_workflow_service()


def clear_workflow_service_cache() -> None:
    """Clear cached service graph in tests."""

    _build_workflow_service.cache_clear()
