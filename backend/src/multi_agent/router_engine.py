"""
ASEP — Agent Router Engine
===========================
Provides intelligent routing of tasks to specialized agents.

Features:
- Capability Matching: Score candidate agents against required task capabilities.
- Cost-Aware Routing: Select model tiers based on urgency, token budget, and pricing.
- Dynamic Model Selection: Automatically pick optimal LLMs (Flash vs Pro vs Gemini).
"""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass, field

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ModelTier(enum.StrEnum):
    FLASH_LITE = "flash_lite"
    FLASH = "flash"
    PRO = "pro"


@dataclass
class AgentCapability:
    name: str
    description: str
    supported_tasks: set[str] = field(default_factory=set)
    supported_tools: set[str] = field(default_factory=set)
    cost_per_1k_tokens: float = 0.001
    latency_score: float = 0.9  # 0.0 (slowest) to 1.0 (fastest)


class AgentProfile(BaseModel):
    name: str
    role: str
    capabilities: list[str] = Field(default_factory=list)
    model_tier: ModelTier = ModelTier.FLASH
    max_tokens: int = 4096
    cost_per_1k_tokens: float = 0.001
    is_active: bool = True


# ---------------------------------------------------------------------------
# Capability Matcher
# ---------------------------------------------------------------------------

class CapabilityMatcher:
    """Scores agent suitability for a given task specification."""

    def score_agent(
        self,
        agent: AgentProfile,
        required_capabilities: list[str],
        task_tags: list[str],
    ) -> float:
        if not agent.is_active:
            return 0.0

        score = 0.0
        agent_caps = set(agent.capabilities)

        # Capability overlap score
        if required_capabilities:
            matched = agent_caps.intersection(set(required_capabilities))
            score += (len(matched) / len(required_capabilities)) * 0.7

        # Tag overlap score
        if task_tags:
            tag_matched = agent_caps.intersection(set(task_tags))
            score += (len(tag_matched) / len(task_tags)) * 0.3

        if not required_capabilities and not task_tags:
            score = 0.5  # Neutral baseline match

        return round(score, 3)


# ---------------------------------------------------------------------------
# Model Selector & Cost Router
# ---------------------------------------------------------------------------

class CostAwareRouter:
    """Selects the best agent and model tier based on cost and SLA priorities."""

    def select_model(
        self,
        urgency: str = "normal",  # low, normal, high
        max_cost_budget: float = 0.05,
        estimated_tokens: int = 2000,
    ) -> ModelTier:
        if urgency == "high":
            return ModelTier.PRO
        elif max_cost_budget < 0.002 or estimated_tokens < 1000:
            return ModelTier.FLASH_LITE
        elif max_cost_budget < 0.02:
            return ModelTier.FLASH
        else:
            return ModelTier.PRO


# ---------------------------------------------------------------------------
# Main Agent Router
# ---------------------------------------------------------------------------

class AgentRouterEngine:
    """Routes tasks to candidate agents using capabilities, cost, and availability."""

    def __init__(self, agents: list[AgentProfile] | None = None) -> None:
        self.matcher = CapabilityMatcher()
        self.cost_router = CostAwareRouter()
        self.registry: dict[str, AgentProfile] = {}

        # Default registered profiles
        default_profiles = agents or [
            AgentProfile(name="supervisor", role="Supervisor", capabilities=["routing", "synthesis", "governance"], model_tier=ModelTier.PRO),
            AgentProfile(name="research", role="Researcher", capabilities=["search", "rag", "retrieval"], model_tier=ModelTier.FLASH),
            AgentProfile(name="planner", role="Planner", capabilities=["planning", "decomposition"], model_tier=ModelTier.PRO),
            AgentProfile(name="executor", role="Executor", capabilities=["execution", "tool_call", "code"], model_tier=ModelTier.FLASH),
        ]
        for a in default_profiles:
            self.register_agent(a)

    def register_agent(self, agent: AgentProfile) -> None:
        self.registry[agent.name] = agent

    def route_task(
        self,
        task_description: str,
        required_capabilities: list[str] | None = None,
        task_tags: list[str] | None = None,
        urgency: str = "normal",
        max_cost_budget: float = 0.05,
    ) -> AgentProfile | None:
        req_caps = required_capabilities or []
        tags = task_tags or []

        # Auto-infer capabilities if none provided
        if not req_caps:
            desc_lower = task_description.lower()
            if "search" in desc_lower or "rag" in desc_lower or "find" in desc_lower:
                req_caps.append("rag")
            elif "plan" in desc_lower or "schedule" in desc_lower:
                req_caps.append("planning")
            else:
                req_caps.append("execution")

        best_agent: AgentProfile | None = None
        best_score = -1.0

        for agent in self.registry.values():
            score = self.matcher.score_agent(agent, req_caps, tags)
            if score > best_score and score > 0.0:
                best_score = score
                best_agent = agent

        if best_agent:
            selected_tier = self.cost_router.select_model(
                urgency=urgency, max_cost_budget=max_cost_budget
            )
            logger.info("Routed task to agent '%s' (Score: %.2f, Tier: %s)", best_agent.name, best_score, selected_tier.value)

        return best_agent
