"""Transformation agent."""

from __future__ import annotations

from ojtflow.agents.base import Agent
from ojtflow.core.contracts.agent import AgentResult
from ojtflow.core.contracts.data import ParsedData, TransformationPlan
from ojtflow.core.contracts.enums import AgentStatus, DataFormat
from ojtflow.data_tools.convert import convert_data


class TransformationAgent(Agent):
    agent_id = "transformation_agent"

    def run(
        self,
        parsed: ParsedData,
        target_format: DataFormat,
        plan: TransformationPlan | None,
    ) -> AgentResult:
        output_text, output = convert_data(parsed, target_format, plan)
        return self.result(
            AgentStatus.SUCCESS,
            f"Converted data to {target_format.value}",
            data={"output_text": output_text, "transformation_output": output},
            next_recommended_action="explanation_agent",
        )

