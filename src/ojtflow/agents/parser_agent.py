"""Parser agent."""

from __future__ import annotations

from ojtflow.agents.base import Agent
from ojtflow.core.contracts.agent import AgentResult
from ojtflow.core.contracts.enums import AgentStatus, DataFormat
from ojtflow.data_tools.detect import detect_format
from ojtflow.data_tools.parse import parse_data
from ojtflow.data_tools.profile import profile_data


class ParserAgent(Agent):
    agent_id = "parser_agent"

    def run(
        self,
        text: str,
        declared_format: DataFormat | None,
        source_ref: str,
    ) -> AgentResult:
        detection = detect_format(text, declared_format)
        parsed = parse_data(text, detection.format, source_ref=source_ref)
        profile = profile_data(parsed)
        return self.result(
            AgentStatus.SUCCESS,
            f"Parsed {detection.format.value} input with {profile.row_count} rows",
            confidence=detection.confidence,
            data={"detection": detection, "parsed": parsed, "profile": profile},
            next_recommended_action="retrieval_agent",
        )

