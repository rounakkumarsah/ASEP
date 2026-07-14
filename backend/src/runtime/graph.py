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
        """Assembles a default processing loop featuring validation and loop-backs:
        
        START -> start -> process -> validate -(conditional)-> end / process -> END
        """
        # 1. Register all nodes from the registry
        for node_name, handler in self.nodes.get_all().items():
            self.workflow.add_node(node_name, handler)
            
        # 2. Add static transitions
        self.workflow.add_edge(START, "start")
        self.workflow.add_edge("start", "process")
        self.workflow.add_edge("process", "validate")
        
        # 3. Add conditional edge routing for the human validation step
        validation_router = self.edges.get_router("human_validation_router")
        self.workflow.add_conditional_edges(
            "validate",
            validation_router,
            {
                "end": "end",
                "process": "process"
            }
        )
        self.workflow.add_edge("end", END)

    def compile(self) -> CompiledStateGraph:
        """Compile the assembled StateGraph with checkpointing."""
        return self.workflow.compile(checkpointer=self.checkpointer)
