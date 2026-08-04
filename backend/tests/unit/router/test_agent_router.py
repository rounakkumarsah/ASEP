"""
ASEP — Unit Tests for Agent Router Engine
"""

import pytest
from src.multi_agent.router_engine import (
    AgentProfile,
    AgentRouterEngine,
    CapabilityMatcher,
    CostAwareRouter,
    ModelTier,
)


def test_capability_matcher():
    matcher = CapabilityMatcher()
    agent = AgentProfile(name="test_agent", role="Tester", capabilities=["rag", "search"])

    score = matcher.score_agent(agent, required_capabilities=["rag"], task_tags=[])
    assert score > 0.5

    inactive_agent = AgentProfile(name="inactive", role="Tester", capabilities=["rag"], is_active=False)
    assert matcher.score_agent(inactive_agent, ["rag"], []) == 0.0


def test_cost_aware_router():
    router = CostAwareRouter()

    assert router.select_model(urgency="high") == ModelTier.PRO
    assert router.select_model(urgency="normal", max_cost_budget=0.001) == ModelTier.FLASH_LITE
    assert router.select_model(urgency="normal", max_cost_budget=0.01) == ModelTier.FLASH


def test_agent_router_engine():
    engine = AgentRouterEngine()

    # Route RAG task
    agent = engine.route_task("Perform semantic search on knowledge base", required_capabilities=["rag"])
    assert agent is not None
    assert agent.name == "research"

    # Route planning task
    agent = engine.route_task("Decompose project goal into steps", required_capabilities=["planning"])
    assert agent is not None
    assert agent.name == "planner"
