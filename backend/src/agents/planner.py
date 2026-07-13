"""
ASEP — LangGraph Planner Node (Placeholder)
=============================================
The Planner is the first node in the agent graph.
It receives a high-level goal and decomposes it into
an ordered list of subtasks stored in AgentState.plan.

TODO (Phase 0.2):
    - Implement LLM-based goal decomposition (via Ollama / LangChain)
    - Add structured output parsing with Pydantic
    - Add few-shot examples for engineering tasks
    - Add task dependency graph (DAG) instead of flat list
    - Add replanning capability when execution fails
"""

from __future__ import annotations

import logging

from src.agents.state import AgentState

logger = logging.getLogger(__name__)


async def planner_node(state: AgentState) -> AgentState:
    """
    LangGraph node: Planner.

    Receives:
        state.goal  — The user's high-level task description.

    Produces:
        state.plan  — A list of decomposed subtasks.

    Args:
        state: Current agent state.

    Returns:
        Updated state with plan populated.
    """
    logger.info("Planner node invoked", extra={"run_id": str(state.run_id), "goal": state.goal})

    # TODO (Phase 0.2): call LLM to decompose state.goal into subtasks
    # Example:
    #   response = await llm.ainvoke([HumanMessage(content=PLANNER_PROMPT.format(goal=state.goal))])
    #   plan = parse_plan(response.content)

    stub_plan = [
        f"[STUB] Analyse the goal: {state.goal}",
        "[STUB] Identify required tools",
        "[STUB] Execute tasks sequentially",
        "[STUB] Produce final output",
    ]

    return state.model_copy(update={"plan": stub_plan})
