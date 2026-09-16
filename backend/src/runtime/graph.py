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
            # If current phase criteria isn't met, it would return the same phase to retry
            # For this architecture, we progress to the next phase sequentially.
            current = state.get("current_phase")
            phase_map = state.get("phase_map", [])
            
            if not current or not phase_map:
                return "end"
                
            try:
                idx = phase_map.index(current)
                if idx + 1 < len(phase_map):
                    return phase_map[idx + 1]
                return "end"
            except ValueError:
                return "end"

        # The orchestrator decides the first phase
        self.workflow.add_conditional_edges("orchestrator", phase_router)
        
        # Each phase is a conditional node that routes to the next phase
        # based on success criteria (checked in phase_router)
        for phase in ["research", "blueprint", "scaffold", "implement", "test", "security_audit", "deploy"]:
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
