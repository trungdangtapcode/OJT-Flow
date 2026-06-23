"""Agent base helpers."""

from __future__ import annotations

from ojtflow.core.contracts.agent import AgentResult
from ojtflow.core.contracts.enums import AgentStatus


class Agent:
    """Small role wrapper around rule-based services."""

    agent_id: str = "agent"

    def result(
        self,
        status: AgentStatus,
        summary: str,
        **kwargs: object,
    ) -> AgentResult:
        """Build a typed agent result."""

        return AgentResult(status=status, summary=summary, **kwargs)

