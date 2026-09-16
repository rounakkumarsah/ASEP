"""
ASEP — Unified LangGraph Runtime Orchestrator
"""

import logging
from collections.abc import AsyncGenerator
from typing import Any

from langgraph.types import Command

from src.memory.memory_manager import MemoryManager
from src.runtime.checkpoints import CheckpointManager
from src.runtime.edges import EdgeRegistry, human_validation_router_default
from src.runtime.graph import StateGraphWrapper
from src.runtime.nodes import (
    NodeRegistry,
    orchestrator_node,
    clarification_gate_node,
    deploy_clarification_gate_node,
    research_phase_node,
    blueprint_phase_node,
    scaffold_phase_node,
    implement_phase_node,
    test_phase_node,
    security_audit_phase_node,
    deploy_phase_node,
    capability_blueprint_phase_node,
    tool_design_phase_node,
    agent_loop_implementation_phase_node,
    memory_state_design_phase_node,
    sandbox_tests_phase_node,
    evaluation_runs_phase_node,
    goal_decomposition_design_phase_node,
    planner_executor_critic_architecture_phase_node,
    tool_integration_phase_node,
    multi_step_test_scenarios_phase_node,
    failure_recovery_tests_phase_node,
    workflow_mapping_phase_node,
    trigger_action_design_phase_node,
    integration_points_phase_node,
    end_to_end_automation_tests_phase_node,
    error_handling_paths_phase_node,
    start_node_default,
    end_node_default,
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

        # 2. Register agent node behaviors
        self.nodes.register("start", start_node_default)
        self.nodes.register("orchestrator", orchestrator_node)
        self.nodes.register("research", research_phase_node)
        self.nodes.register("clarification_gate", clarification_gate_node)
        self.nodes.register("deploy_clarification_gate", deploy_clarification_gate_node)
        self.nodes.register("blueprint", blueprint_phase_node)
        self.nodes.register("scaffold", scaffold_phase_node)
        self.nodes.register("implement", implement_phase_node)
        self.nodes.register("test", test_phase_node)
        self.nodes.register("security_audit", security_audit_phase_node)
        self.nodes.register("deploy", deploy_phase_node)
        self.nodes.register("capability_blueprint", capability_blueprint_phase_node)
        self.nodes.register("tool_design", tool_design_phase_node)
        self.nodes.register("agent_loop_implementation", agent_loop_implementation_phase_node)
        self.nodes.register("memory_state_design", memory_state_design_phase_node)
        self.nodes.register("sandbox_tests", sandbox_tests_phase_node)
        self.nodes.register("evaluation_runs", evaluation_runs_phase_node)
        self.nodes.register("goal_decomposition_design", goal_decomposition_design_phase_node)
        self.nodes.register("planner_executor_critic_architecture", planner_executor_critic_architecture_phase_node)
        self.nodes.register("tool_integration", tool_integration_phase_node)
        self.nodes.register("multi_step_test_scenarios", multi_step_test_scenarios_phase_node)
        self.nodes.register("failure_recovery_tests", failure_recovery_tests_phase_node)
        self.nodes.register("workflow_mapping", workflow_mapping_phase_node)
        self.nodes.register("trigger_action_design", trigger_action_design_phase_node)
        self.nodes.register("integration_points", integration_points_phase_node)
        self.nodes.register("end_to_end_automation_tests", end_to_end_automation_tests_phase_node)
        self.nodes.register("error_handling_paths", error_handling_paths_phase_node)
        self.nodes.register("end", end_node_default)

        # 3. Register default routing edge
        self.edges.register("human_validation_router", human_validation_router_default)

        # 4. Build and compile graph
        self.wrapper = StateGraphWrapper(
            node_registry=self.nodes,
            edge_registry=self.edges,
            checkpointer=self.checkpoints.get_checkpointer(),
        )
        self.wrapper.assemble_default_flow()
        self.graph = self.wrapper.compile()

    async def execute_run(
        self, run_id: str, thread_id: str, goal: str = "", research_mode: str = "balanced", environment_mode: str = "local"
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Initiates a new run and streams step-by-step workflow updates."""
        logger.info(f"Initiating run '{run_id}' under thread: '{thread_id}' with goal: '{goal}'")

        # Preserve active execution parameters strictly through MemoryManager (Working Memory)
        await self.memory.working.set_state(thread_id, "active_run_id", run_id)

        from langchain_core.runnables.config import RunnableConfig
        config = RunnableConfig(configurable={"thread_id": thread_id})
        initial_state: dict[str, Any] = {
            "goal": goal,
            "messages": [{"role": "user", "content": goal}] if goal else [],
            "environment_mode": environment_mode,
            "credentials_status": {},
            "local_secrets": {},
            "plan": [],
            "status": "started",
            "next_action": None,
            "run_id": run_id,
            "variables": {"research_mode": research_mode},
            "human_input": None,
        }

        async for event in self.graph.astream(initial_state, config, stream_mode="updates"):
            # Stream the updates dictionary back to the caller
            yield event

    async def resume_run(
        self, thread_id: str, human_input: str
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Resumes a paused run, feeding operator feedback to the active interrupt node."""
        logger.info(f"Resuming paused run on thread: '{thread_id}' with response: '{human_input}'")

        from langchain_core.runnables.config import RunnableConfig
        config = RunnableConfig(configurable={"thread_id": thread_id})

        # Send Command(resume=...) containing the human input payload
        async for event in self.graph.astream(
            Command(resume=human_input), config, stream_mode="updates"
        ):
            yield event

    async def get_state(self, thread_id: str) -> dict[str, Any]:
        """Read current graph state from checkpoints."""
        from langchain_core.runnables.config import RunnableConfig
        config = RunnableConfig(configurable={"thread_id": thread_id})
        state = await self.graph.aget_state(config)
        return state.values if state else {}


_global_runtime: LangGraphRuntime | None = None


def get_langgraph_runtime() -> LangGraphRuntime:
    """Return the global LangGraphRuntime singleton, instantiating it dynamically."""
    global _global_runtime
    if _global_runtime is None:
        # Create a lightweight mock MemoryManager to fulfill runtime facade requirements
        class DummyWorkingMemory:
            async def set_state(self, *args: Any, **kwargs: Any) -> None:
                pass

        class DummyMemoryManager:
            def __init__(self) -> None:
                self.working = DummyWorkingMemory()

        # Let the package lazy-import MemoryManager if needed
        dummy_mgr = DummyMemoryManager()
        from typing import cast

        from src.memory.memory_manager import MemoryManager

        _global_runtime = LangGraphRuntime(cast(MemoryManager, dummy_mgr))
    return _global_runtime
