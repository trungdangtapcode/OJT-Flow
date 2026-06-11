"""OWASP LLM threat model contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel, NonBlankStr


OwaspLlmCategoryId = Literal[
    "LLM01",
    "LLM02",
    "LLM03",
    "LLM04",
    "LLM05",
    "LLM06",
    "LLM07",
    "LLM08",
    "LLM09",
    "LLM10",
]
OwaspMitigationStatus = Literal["implemented", "partial", "planned"]
ThreatRiskLevel = Literal["low", "medium", "high", "critical"]


class OwaspLlmMitigation(ContractModel):
    mitigation_id: NonBlankStr
    title: NonBlankStr
    status: OwaspMitigationStatus
    owner_role: NonBlankStr
    implementation_refs: list[NonBlankStr] = Field(min_length=1)
    test_refs: list[NonBlankStr] = Field(min_length=1)
    notes: NonBlankStr


class OwaspLlmThreatCategory(ContractModel):
    category_id: OwaspLlmCategoryId
    category_name: NonBlankStr
    owasp_ref: NonBlankStr
    risk_statement: NonBlankStr
    applicable_surfaces: list[NonBlankStr] = Field(min_length=1)
    mitigations: list[OwaspLlmMitigation] = Field(min_length=1)
    monitoring_signals: list[NonBlankStr] = Field(min_length=1)
    residual_risk: ThreatRiskLevel
    residual_risk_note: NonBlankStr
    roadmap_refs: list[NonBlankStr] = Field(default_factory=list)
    evidence_refs: list[NonBlankStr] = Field(default_factory=list)


class OwaspLlmThreatModel(ContractModel):
    version: NonBlankStr = "owasp_llm_threat_model.v1"
    standard_ref: NonBlankStr
    source_url: NonBlankStr
    categories: list[OwaspLlmThreatCategory] = Field(min_length=10, max_length=10)
