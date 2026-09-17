"""
ASEP — StateGraph Wrapper & Compilation
"""

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.runtime.edges import EdgeRegistry
from src.runtime.nodes import NodeRegistry
from src.runtime.state import AgentState


class StateGraphWrapper:
    """Orchestrates building, routing, and compiling the StateGraph using registered handlers."""

    def __init__(
        self,
        node_registry: NodeRegistry,
        edge_registry: EdgeRegistry,
        checkpointer: BaseCheckpointSaver,
    ) -> None:
        self.nodes = node_registry
        self.edges = edge_registry
        self.checkpointer = checkpointer

        # Construct graph with Typed State
        self.workflow = StateGraph(AgentState)

    def assemble_default_flow(self) -> None:
        """Assembles the new agent flow:
        start -> supervisor -> planner -> research -> rag -> coding -> validate -> end
        """
        # 1. Register all nodes from the registry
        for node_name, handler in self.nodes.get_all().items():
            self.workflow.add_node(node_name, handler)

        # 2. Add static transitions
        self.workflow.add_edge(START, "start")
        self.workflow.add_edge("start", "orchestrator")
        
        def phase_router(state: AgentState) -> str:
            # The node advances to the next phase in the phase_map
            # Only if current phase criteria is met
            current = state.get("current_phase")
            phase_map = state.get("phase_map", [])
            status = state.get("status")
            
            if not current or not phase_map:
                return "end"

            # Self-healing loop dynamic routing: critic -> debugger -> critic
            if current == "critic":
                if status == "healing":
                    return "debugger"
                if status == "escalated":
                    return "end"
            elif current == "debugger":
                return "critic"

            # host_failed is non-blocking: treat same as verified, let pipeline continue
            if status == "host_failed":
                try:
                    idx = phase_map.index(current)
                    if idx + 1 < len(phase_map):
                        return phase_map[idx + 1]
                    return "end"
                except ValueError:
                    return "end"

            if status != "verified":
                # Strict enforcement: if status is not verified, it is a hard error.
                # In real execution, we would log it and pause or retry.
                # For this implementation, we loop back to current to retry.
                return current

            try:
                idx = phase_map.index(current)
                if idx + 1 < len(phase_map):
                    return phase_map[idx + 1]
                return "end"
            except ValueError:
                return "end"

        # The orchestrator decides the first phase
        self.workflow.add_conditional_edges("orchestrator", phase_router)

        # Register all possible phases in conditional edges
        all_phases = [
            "research", "blueprint", "scaffold", "implement", "critic", "debugger", "test", "security_audit", "deploy",
            "host_manager",
            "capability_blueprint", "tool_design", "agent_loop_implementation", "memory_state_design",
            "sandbox_tests", "evaluation_runs", "goal_decomposition_design", "planner_executor_critic_architecture",
            "tool_integration", "multi_step_test_scenarios", "failure_recovery_tests", "workflow_mapping",
            "trigger_action_design", "integration_points", "end_to_end_automation_tests", "error_handling_paths"
        ]

        for phase in all_phases:
            if phase in self.nodes.get_all():
                self.workflow.add_conditional_edges(phase, phase_router)

        self.workflow.add_edge("end", END)


    def compile(self) -> CompiledStateGraph:
        """Compile the assembled StateGraph with checkpointing.

        Execution enters the ``validate`` node which pauses execution using
        LangGraph's native ``interrupt()``, enqueuing the session into HITLEngine.
        Resumption is driven by ``astream(Command(resume=…))``.
        """
        return self.workflow.compile(
            checkpointer=self.checkpointer,
        )
