"""
ASEP — Agent Registry
"""

from typing import Any

from src.multi_agent.contracts import AgentRole


class AgentRegistry:
    """In-memory directory mapping roles to agent instances."""

    def __init__(self) -> None:
        self._agents: dict[AgentRole, Any] = {}

    def register(self, role: AgentRole, agent: Any) -> None:
        self._agents[role] = agent

    def get(self, role: AgentRole) -> Any:
        return self._agents.get(role)

    def registered_roles(self) -> list[AgentRole]:
        return list(self._agents.keys())
