"""Operations, performance, and release-readiness contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel, NonBlankStr


PerformanceSurface = Literal[
    "workflow_create",
    "retrieval_search",
    "assistant_stream",
    "upload_parse",
    "reindex",
    "runtime_readiness",
]

ReleaseGateCategory = Literal[
    "backend",
    "frontend",
    "security",
    "retrieval",
    "docker",
    "e2e",
    "deployment",
    "repo_hygiene",
]

ReleaseGateStatus = Literal["required", "recommended", "manual"]


class PerformanceBudgetMetric(ContractModel):
    metric_id: NonBlankStr
    surface: PerformanceSurface
    metric_name: NonBlankStr
    percentile: NonBlankStr | None = None
    budget_ms: float | None = Field(default=None, gt=0)
    budget_count: int | None = Field(default=None, ge=0)
    budget_ratio: float | None = Field(default=None, ge=0.0, le=1.0)
    blocking: bool = True
    measurement: NonBlankStr
    notes: list[NonBlankStr] = Field(default_factory=list)


class PerformanceBudgetCatalog(ContractModel):
    catalog_id: NonBlankStr
    version: NonBlankStr
    environment: NonBlankStr
    metrics: list[PerformanceBudgetMetric] = Field(default_factory=list)
    warnings: list[NonBlankStr] = Field(default_factory=list)


class LoadSmokeScenario(ContractModel):
    scenario_id: NonBlankStr
    surface: PerformanceSurface
    method: NonBlankStr
    path: NonBlankStr
    repetitions: int = Field(ge=1)
    warmup_requests: int = Field(default=0, ge=0)
    expected_status: int = Field(default=200, ge=100, le=599)
    max_p95_ms: float = Field(gt=0)
    max_error_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    description: NonBlankStr
    notes: list[NonBlankStr] = Field(default_factory=list)


class LoadSmokeScenarioResult(ContractModel):
    scenario_id: NonBlankStr
    surface: PerformanceSurface
    request_count: int = Field(ge=0)
    error_count: int = Field(ge=0)
    error_ratio: float = Field(ge=0.0, le=1.0)
    min_ms: float = Field(ge=0)
    mean_ms: float = Field(ge=0)
    p50_ms: float = Field(ge=0)
    p95_ms: float = Field(ge=0)
    max_ms: float = Field(ge=0)
    passed: bool
    warnings: list[NonBlankStr] = Field(default_factory=list)


class LoadSmokeReport(ContractModel):
    report_id: NonBlankStr
    started_at: NonBlankStr
    completed_at: NonBlankStr
    base_url: NonBlankStr
    mode: Literal["asgi", "http"]
    scenario_results: list[LoadSmokeScenarioResult] = Field(default_factory=list)
    passed: bool
    warnings: list[NonBlankStr] = Field(default_factory=list)


class LoadSmokePlan(ContractModel):
    plan_id: NonBlankStr
    version: NonBlankStr
    scenarios: list[LoadSmokeScenario] = Field(default_factory=list)
    warnings: list[NonBlankStr] = Field(default_factory=list)


class ObservabilityPanel(ContractModel):
    panel_id: NonBlankStr
    title: NonBlankStr
    signals: list[NonBlankStr] = Field(default_factory=list)
    source: NonBlankStr
    alert_thresholds: list[NonBlankStr] = Field(default_factory=list)
    notes: list[NonBlankStr] = Field(default_factory=list)


class ObservabilityDashboardSpec(ContractModel):
    dashboard_id: NonBlankStr
    version: NonBlankStr
    intended_audience: NonBlankStr
    panels: list[ObservabilityPanel] = Field(default_factory=list)
    missing_instrumentation: list[NonBlankStr] = Field(default_factory=list)
    warnings: list[NonBlankStr] = Field(default_factory=list)


class ReleaseGate(ContractModel):
    gate_id: NonBlankStr
    category: ReleaseGateCategory
    status: ReleaseGateStatus
    command: NonBlankStr
    evidence: NonBlankStr
    owner: NonBlankStr
    blocking: bool = True
    notes: list[NonBlankStr] = Field(default_factory=list)


class ReleaseGateCatalog(ContractModel):
    catalog_id: NonBlankStr
    version: NonBlankStr
    gates: list[ReleaseGate] = Field(default_factory=list)
    warnings: list[NonBlankStr] = Field(default_factory=list)


class DeploymentSmokeTarget(ContractModel):
    target_id: NonBlankStr
    url_env_var: NonBlankStr
    default_url: NonBlankStr
    required_paths: list[NonBlankStr] = Field(default_factory=list)
    optional_paths: list[NonBlankStr] = Field(default_factory=list)
    expected_statuses: list[int] = Field(default_factory=lambda: [200])
    notes: list[NonBlankStr] = Field(default_factory=list)


class DeploymentSmokePlan(ContractModel):
    plan_id: NonBlankStr
    version: NonBlankStr
    targets: list[DeploymentSmokeTarget] = Field(default_factory=list)
    required_env: list[NonBlankStr] = Field(default_factory=list)
    warnings: list[NonBlankStr] = Field(default_factory=list)
