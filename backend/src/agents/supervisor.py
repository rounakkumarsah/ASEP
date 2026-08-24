"""
ASEP — LangGraph Supervisor (Placeholder)
==========================================
The Supervisor orchestrates multiple specialised agents.
It decides which sub-agent to invoke next based on the
current plan step and execution context.

Architecture pattern: Supervisor → Worker Agents
Reference: LangGraph multi-agent supervisor pattern

TODO (Phase 0.2):
    - Implement LangGraph StateGraph with conditional edges
    - Add worker agent registry lookup
    - Add error recovery logic (retry / skip / abort)
    - Add token budget enforcement
    - Add parallel sub-agent invocation for independent tasks
    - Integrate with LangGraph checkpointer for state persistence
"""

from __future__ import annotations

import logging

from src.agents.state import AgentState

logger = logging.getLogger(__name__)

# Names of registered worker agents (populated from registry in Phase 0.2)
WORKER_AGENTS: list[str] = [
    # TODO (Phase 0.2): "code_writer"
    # TODO (Phase 0.2): "code_reviewer"
    # TODO (Phase 0.2): "test_runner"
    # TODO (Phase 0.2): "file_system"
    # TODO (Phase 0.2): "web_search"
    # TODO (Phase 0.2): "memory_retriever"
]


from typing import Any


async def executor_node(state: AgentState) -> dict[str, Any]:
    """Mock executor node until full agent runtime is implemented."""
    current = state.get("current_step", 0)
    logger.info("Executor node: executing step %d", current)
    return {"current_step": current + 1}

async def supervisor_node(state: AgentState) -> dict[str, Any]:
    """
    LangGraph node: Supervisor.

    Decides the next worker agent to invoke, or terminates the graph
    if all plan steps are complete.
    """
    run_id = str(state.get("run_id"))
    current_step = state.get("current_step", 0)
    plan = state.get("plan", [])

    logger.info(
        "Supervisor node invoked",
        extra={
            "run_id": run_id,
            "current_step": current_step,
            "plan_length": len(plan),
        },
    )

    if current_step >= len(plan):
        logger.info("Supervisor: all plan steps complete", extra={"run_id": run_id})
        return {"is_complete": True}

    next_step = plan[current_step]
    logger.info(
        "Supervisor: dispatching step",
        extra={"run_id": run_id, "step": next_step},
    )

    # For now, we rely on the executor_node to increment the step.
    return {"is_complete": False}


def build_supervisor_graph() -> Any:
    """
    Constructs and compiles the LangGraph StateGraph.
    """
    from langgraph.graph import END, StateGraph

    from src.agents.planner import planner_node

    graph = StateGraph(AgentState)
    graph.add_node("planner", planner_node)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("executor", executor_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "supervisor")

    def supervisor_condition(state: AgentState) -> str:
        if state.get("is_complete"):
            return END
        return "executor"

    graph.add_conditional_edges("supervisor", supervisor_condition)
    graph.add_edge("executor", "supervisor")

    return graph.compile()
