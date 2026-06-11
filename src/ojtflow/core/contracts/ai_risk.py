"""AI risk register contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel, NonBlankStr


AiRmfFunction = Literal["GOVERN", "MAP", "MEASURE", "MANAGE"]
RiskLevel = Literal["low", "medium", "high", "critical"]


class AiRiskControl(ContractModel):
    control_id: NonBlankStr
    title: NonBlankStr
    implementation_ref: NonBlankStr
    status: Literal["implemented", "partial", "planned"]


class AiRiskRegisterItem(ContractModel):
    risk_id: NonBlankStr
    title: NonBlankStr
    intended_use: NonBlankStr
    limitation: NonBlankStr
    nist_ai_rmf_functions: list[AiRmfFunction] = Field(min_length=1)
    genai_profile_risk_areas: list[NonBlankStr] = Field(default_factory=list)
    severity: RiskLevel
    likelihood: RiskLevel
    residual_risk: RiskLevel
    owner_role: NonBlankStr
    monitoring_signals: list[NonBlankStr] = Field(default_factory=list)
    human_oversight: NonBlankStr
    controls: list[AiRiskControl] = Field(default_factory=list)
    evidence_refs: list[NonBlankStr] = Field(default_factory=list)


class AiRiskRegister(ContractModel):
    version: NonBlankStr = "ai_risk_register.v1"
    standard_refs: list[NonBlankStr] = Field(default_factory=list)
    intended_system_use: NonBlankStr
    prohibited_uses: list[NonBlankStr] = Field(default_factory=list)
    risks: list[AiRiskRegisterItem] = Field(default_factory=list)
