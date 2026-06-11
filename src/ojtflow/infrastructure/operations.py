"""Operations and release-readiness catalog loaders."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.contracts.operations import (
    DeploymentSmokePlan,
    LoadSmokePlan,
    ObservabilityDashboardSpec,
    PerformanceBudgetCatalog,
    ReleaseGateCatalog,
)


OPERATIONS_DIR = Path("operations")
PERFORMANCE_BUDGETS_PATH = OPERATIONS_DIR / "performance_budgets.json"
LOAD_SMOKE_PLAN_PATH = OPERATIONS_DIR / "load_smoke_plan.json"
OBSERVABILITY_DASHBOARD_PATH = OPERATIONS_DIR / "observability_dashboard.json"
RELEASE_GATES_PATH = OPERATIONS_DIR / "release_gates.json"
DEPLOYMENT_SMOKE_PLAN_PATH = OPERATIONS_DIR / "deployment_smoke_plan.json"

ModelT = TypeVar("ModelT", bound=ContractModel)


def load_performance_budgets(knowledge_root: Path) -> PerformanceBudgetCatalog:
    catalog = _load_contract(
        knowledge_root / PERFORMANCE_BUDGETS_PATH,
        PerformanceBudgetCatalog,
    )
    _ensure_unique(
        [metric.metric_id for metric in catalog.metrics],
        label="performance metric",
        path=knowledge_root / PERFORMANCE_BUDGETS_PATH,
    )
    return catalog


def load_load_smoke_plan(knowledge_root: Path) -> LoadSmokePlan:
    plan = _load_contract(knowledge_root / LOAD_SMOKE_PLAN_PATH, LoadSmokePlan)
    _ensure_unique(
        [scenario.scenario_id for scenario in plan.scenarios],
        label="load smoke scenario",
        path=knowledge_root / LOAD_SMOKE_PLAN_PATH,
    )
    return plan


def load_observability_dashboard(knowledge_root: Path) -> ObservabilityDashboardSpec:
    dashboard = _load_contract(
        knowledge_root / OBSERVABILITY_DASHBOARD_PATH,
        ObservabilityDashboardSpec,
    )
    _ensure_unique(
        [panel.panel_id for panel in dashboard.panels],
        label="observability panel",
        path=knowledge_root / OBSERVABILITY_DASHBOARD_PATH,
    )
    return dashboard


def load_release_gates(knowledge_root: Path) -> ReleaseGateCatalog:
    catalog = _load_contract(knowledge_root / RELEASE_GATES_PATH, ReleaseGateCatalog)
    _ensure_unique(
        [gate.gate_id for gate in catalog.gates],
        label="release gate",
        path=knowledge_root / RELEASE_GATES_PATH,
    )
    return catalog


def load_deployment_smoke_plan(knowledge_root: Path) -> DeploymentSmokePlan:
    plan = _load_contract(
        knowledge_root / DEPLOYMENT_SMOKE_PLAN_PATH,
        DeploymentSmokePlan,
    )
    _ensure_unique(
        [target.target_id for target in plan.targets],
        label="deployment smoke target",
        path=knowledge_root / DEPLOYMENT_SMOKE_PLAN_PATH,
    )
    return plan


def _load_contract(path: Path, model: type[ModelT]) -> ModelT:
    if not path.exists():
        raise FileNotFoundError(f"Missing operations catalog: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    return model.model_validate(raw)


def _ensure_unique(values: list[str], *, label: str, path: Path) -> None:
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise ValueError(f"Duplicate {label} IDs in {path}: {', '.join(duplicates)}")
