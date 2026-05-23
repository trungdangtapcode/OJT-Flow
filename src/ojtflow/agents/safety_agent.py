"""Safety and policy agent."""

from __future__ import annotations

from ojtflow.agents.base import Agent
from ojtflow.core.contracts.agent import AgentResult
from ojtflow.core.contracts.data import TransformationPlan, ValidationReport
from ojtflow.core.contracts.enums import AgentStatus
from ojtflow.core.policy.risk_rules import review_required


class SafetyAgent(Agent):
    agent_id = "safety_agent"

    def run(self, report: ValidationReport, plan: TransformationPlan | None) -> AgentResult:
        if review_required(report, plan):
            return self.result(
                AgentStatus.NEEDS_HUMAN_REVIEW,
                "Human review is required before transformation",
                data={"requires_review": True},
                issues=report.issues,
                next_recommended_action="review_agent",
            )
        return self.result(
            AgentStatus.SUCCESS,
            "No human review required by current policy",
            data={"requires_review": False},
            next_recommended_action="transformation_agent",
        )

