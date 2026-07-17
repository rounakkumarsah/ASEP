from __future__ import annotations
import logging
from typing import Dict, List, Optional
from src.multi_agent.contracts import AgentRole
from src.multi_agent.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class AgentRegistry:
    """Dynamic, thread-safe central registry for Agent registrations, health indicators, and discovery."""

    def __init__(self) -> None:
        self._agents: Dict[AgentRole, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        """Register a new agent instance."""
        logger.info(f"Registering agent: {agent.role.value} (v{agent.metadata().version})")
        self._agents[agent.role] = agent

    def unregister(self, role: AgentRole) -> None:
        """Unregister an agent from active registry pool."""
        if role in self._agents:
            logger.info(f"Unregistering agent: {role.value}")
            del self._agents[role]

    def lookup(self, role: AgentRole) -> Optional[BaseAgent]:
        """Lookup agent by its Role."""
        return self._agents.get(role)

    def discover(self, capability: str) -> List[BaseAgent]:
        """Find all agents supporting a given capability string."""
        matches = []
        for agent in self._agents.values():
            if capability in agent.capabilities():
                matches.append(agent)
        return matches

    def enable(self, role: AgentRole) -> None:
        """Enable the agent."""
        agent = self.lookup(role)
        if agent:
            agent.enable()

    def disable(self, role: AgentRole) -> None:
        """Disable the agent."""
        agent = self.lookup(role)
        if agent:
            agent.disable()

    def health(self) -> Dict[str, bool]:
        """Check status health of all registered agents."""
        return {role.value: agent.health() for role, agent in self._agents.items()}

# Global Registry instance
_registry = AgentRegistry()

def get_agent_registry() -> AgentRegistry:
    return _registry
