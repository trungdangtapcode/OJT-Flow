"""Validation agent."""

from __future__ import annotations

from ojtflow.agents.base import Agent
from ojtflow.core.contracts.agent import AgentResult
from ojtflow.core.contracts.data import DataProfile, ParsedData
from ojtflow.core.contracts.enums import AgentStatus
from ojtflow.core.text import format_count
from ojtflow.data_tools.validate import validate_against_schema


class ValidationAgent(Agent):
    agent_id = "validation_agent"

    def run(self, parsed: ParsedData, profile: DataProfile, schema: dict | None) -> AgentResult:
        report = validate_against_schema(parsed, profile, schema)
        status = AgentStatus.NEEDS_HUMAN_REVIEW if report.requires_review else AgentStatus.SUCCESS
        return self.result(
            status,
            f"Validation produced {format_count(len(report.issues), 'issue')}",
            confidence=report.schema_confidence,
            data={"validation_report": report},
            issues=report.issues,
            next_recommended_action="safety_agent" if report.requires_review else "transformation_agent",
        )
