"""
ASEP — Unified LangGraph Runtime Orchestrator
"""

import logging
from typing import Any, AsyncGenerator

from langgraph.types import Command

from src.memory.memory_manager import MemoryManager
from src.runtime.checkpoints import CheckpointManager
from src.runtime.edges import EdgeRegistry, human_validation_router_default
from src.runtime.graph import StateGraphWrapper
from src.runtime.nodes import (
    NodeRegistry,
    end_node_default,
    human_validation_node_default,
    process_node_default,
    start_node_default,
)

logger = logging.getLogger(__name__)


class LangGraphRuntime:
    """Core runtime engine driving the StateGraph execution loop, streaming, and pauses."""

    def __init__(self, memory_manager: MemoryManager) -> None:
        self.memory = memory_manager
        
        # 1. Instantiate Registries & Checkpointers
        self.nodes = NodeRegistry()
        self.edges = EdgeRegistry()
        self.checkpoints = CheckpointManager()

        # 2. Register default generic node behaviors (No AI/Planner calls)
        self.nodes.register("start", start_node_default)
        self.nodes.register("process", process_node_default)
        self.nodes.register("validate", human_validation_node_default)
        self.nodes.register("end", end_node_default)
        
        # 3. Register default routing edge
        self.edges.register("human_validation_router", human_validation_router_default)

        # 4. Build and compile graph
        self.wrapper = StateGraphWrapper(
            node_registry=self.nodes,
            edge_registry=self.edges,
            checkpointer=self.checkpoints.get_checkpointer()
        )
        self.wrapper.assemble_default_flow()
        self.graph = self.wrapper.compile()

    async def execute_run(self, run_id: str, thread_id: str) -> AsyncGenerator[dict[str, Any], None]:
        """Initiates a new run and streams step-by-step workflow updates."""
        logger.info(f"Initiating run '{run_id}' under thread: '{thread_id}'")
        
        # Preserve active execution parameters strictly through MemoryManager (Working Memory)
        await self.memory.working.set_state(thread_id, "active_run_id", run_id)
        
        config = {"configurable": {"thread_id": thread_id}}
        initial_state = {
            "messages": [],
            "status": "started",
            "next_action": None,
            "run_id": run_id,
            "variables": {},
            "human_input": None
        }

        async for event in self.graph.astream(initial_state, config, stream_mode="updates"):
            # Stream the updates dictionary back to the caller
            yield event

    async def resume_run(self, thread_id: str, human_input: str) -> AsyncGenerator[dict[str, Any], None]:
        """Resumes a paused run, feeding operator feedback to the active interrupt node."""
        logger.info(f"Resuming paused run on thread: '{thread_id}' with response: '{human_input}'")
        
        config = {"configurable": {"thread_id": thread_id}}
        
        # Send Command(resume=...) containing the human input payload
        async for event in self.graph.astream(
            Command(resume=human_input),
            config,
            stream_mode="updates"
        ):
            yield event
            
    async def get_state(self, thread_id: str) -> dict[str, Any]:
        """Read current graph state from checkpoints."""
        config = {"configurable": {"thread_id": thread_id}}
        state = await self.graph.aget_state(config)
        return state.values if state else {}
