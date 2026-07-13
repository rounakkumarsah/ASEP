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


async def supervisor_node(state: AgentState) -> AgentState:
    """
    LangGraph node: Supervisor.

    Decides the next worker agent to invoke, or terminates the graph
    if all plan steps are complete.

    Args:
        state: Current agent state.

    Returns:
        Updated state indicating next action or completion.
    """
    logger.info(
        "Supervisor node invoked",
        extra={
            "run_id": str(state.run_id),
            "current_step": state.current_step,
            "plan_length": len(state.plan),
        },
    )

    if state.current_step >= len(state.plan):
        logger.info("Supervisor: all plan steps complete", extra={"run_id": str(state.run_id)})
        return state.model_copy(update={"is_complete": True})

    # TODO (Phase 0.2): LLM-based routing to appropriate worker agent
    next_step = state.plan[state.current_step]
    logger.info(
        "Supervisor: dispatching step",
        extra={"run_id": str(state.run_id), "step": next_step},
    )

    # Stub: just advance to the next step
    return state.model_copy(update={"current_step": state.current_step + 1})


def build_supervisor_graph():  # type: ignore[return]
    """
    Constructs and compiles the LangGraph StateGraph.

    TODO (Phase 0.2):
        from langgraph.graph import StateGraph, END
        graph = StateGraph(AgentState)
        graph.add_node("planner", planner_node)
        graph.add_node("supervisor", supervisor_node)
        graph.add_node("executor", executor_node)
        graph.set_entry_point("planner")
        graph.add_edge("planner", "supervisor")
        graph.add_conditional_edges(
            "supervisor",
            lambda s: "executor" if not s.is_complete else END,
        )
        graph.add_edge("executor", "supervisor")
        return graph.compile()
    """
    # TODO (Phase 0.2): implement full graph
    raise NotImplementedError("Supervisor graph not yet implemented — Phase 0.2")
