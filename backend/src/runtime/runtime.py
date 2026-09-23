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
    critic_node,
    debugger_node,
    test_phase_node,
    security_audit_phase_node,
    deploy_phase_node,
    host_manager_node,
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
    explore_node,
    start_node_default,
    end_node_default,
)

import asyncio
logger = logging.getLogger(__name__)

_background_tasks: set[asyncio.Task] = set()

def safe_fire_and_forget(coro) -> None:
    """Safely executes a background task, holding a strong reference to prevent garbage collection."""
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    
    def cleanup(t: asyncio.Task) -> None:
        _background_tasks.discard(t)
        if not t.cancelled() and t.exception():
            logger.error(f"Background task failed: {t.exception()}", exc_info=t.exception())
            
    task.add_done_callback(cleanup)


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
        self.nodes.register("explore", explore_node)
        self.nodes.register("orchestrator", orchestrator_node)
        self.nodes.register("research", research_phase_node)
        self.nodes.register("clarification_gate", clarification_gate_node)
        self.nodes.register("deploy_clarification_gate", deploy_clarification_gate_node)
        self.nodes.register("blueprint", blueprint_phase_node)
        self.nodes.register("scaffold", scaffold_phase_node)
        self.nodes.register("implement", implement_phase_node)
        self.nodes.register("critic", critic_node)
        self.nodes.register("debugger", debugger_node)
        self.nodes.register("test", test_phase_node)
        self.nodes.register("security_audit", security_audit_phase_node)
        self.nodes.register("deploy", deploy_phase_node)
        self.nodes.register("host_manager", host_manager_node)
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
        self, run_id: str, thread_id: str, goal: str = "", research_mode: str = "balanced", environment_mode: str = "local", org_id: str | None = None
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Initiates a new run and streams step-by-step workflow updates."""
        logger.info(f"Initiating run '{run_id}' under thread: '{thread_id}' with goal: '{goal}'")

        # Kill any existing hosted app from previous runs on this thread/session
        from src.utils.host_manager import host_manager
        host_manager.stop_session(thread_id)
        if run_id != thread_id:
            host_manager.stop_session(run_id)

        # Preserve active execution parameters strictly through MemoryManager (Working Memory)
        await self.memory.working.set_state(thread_id, "active_run_id", run_id)

        from langchain_core.runnables.config import RunnableConfig
        config = RunnableConfig(configurable={"thread_id": thread_id})
        
        # Retrieval Injection: Top K memories
        injected_memories_text = ""
        import uuid
        from src.runtime.memory_hooks import is_memory_enabled, store_working_memory, store_episodic_memory, extract_and_store_durable_memories
        if org_id and is_memory_enabled():
            try:
                from src.services.memory_service import MemoryService
                from src.api.dependencies import get_uow_factory
                from src.db.models.memory_entry import MemoryType
                memory_service = MemoryService(get_uow_factory())
                org_uuid = uuid.UUID(str(org_id))
                
                # Retrieve Semantic, Procedural, Episodic
                top_memories = []
                for mtype in [MemoryType.SEMANTIC, MemoryType.PROCEDURAL, MemoryType.EPISODIC]:
                    mems = await memory_service.get_top_memories(namespace="default", memory_type=mtype, org_id=org_uuid, limit=2)
                    top_memories.extend(mems)
                    
                # Sort by importance and take top 5
                top_memories.sort(key=lambda x: x.importance_score, reverse=True)
                top_memories = top_memories[:5]
                
                if top_memories:
                    injected_memories_text = "Relevant Past Memories:\n" + "\n".join(f"- [{m.memory_type}] {m.content}" for m in top_memories) + "\n\n"
                    
                # Hook: Store Working Memory (Start)
                await store_working_memory(run_id, org_uuid, f"Goal: {goal}")
            except Exception as e:
                logger.error(f"Failed to retrieve or store initial memories: {e}")

        augmented_goal = injected_memories_text + goal
        
        initial_state: dict[str, Any] = {
            "goal": augmented_goal,
            "messages": [{"role": "user", "content": augmented_goal}] if goal else [],
            "environment_mode": environment_mode,
            "credentials_status": {},
            "local_secrets": [],
            "plan": [],
            "status": "started",
            "next_action": None,
            "run_id": run_id,
            "thread_id": thread_id,
            "variables": {"research_mode": research_mode},
            "human_input": None,
        }

        # Track data for Episodic memory
        transcript_builder = [f"Goal: {goal}"]
        tools_used = set()
        final_response = ""
        success = False

        try:
            async for event in self.graph.astream(initial_state, config, stream_mode="updates"):
                # Inspect event to gather transcript and tool usages
                for node_name, node_data in event.items():
                    if "messages" in node_data and node_data["messages"]:
                        last_msg = node_data["messages"][-1]
                        if isinstance(last_msg, dict):
                            content = last_msg.get("content", "")
                            role = last_msg.get("role", "")
                            name = last_msg.get("name", "")
                        else:
                            content = getattr(last_msg, "content", "")
                            role = getattr(last_msg, "type", "")
                            name = getattr(last_msg, "name", "")
                            
                        if role == "tool" or name:
                            tools_used.add(name or role)
                            transcript_builder.append(f"Tool {name or role} Output: {str(content)[:200]}...")
                            if org_id and is_memory_enabled():
                                await store_working_memory(run_id, org_uuid, f"Tool {name or role} output: {content}", source=f"tool_{name or role}")
                        elif role == "ai" or role == "assistant":
                            transcript_builder.append(f"AI: {str(content)[:200]}...")
                            final_response = str(content)
                            if org_id and is_memory_enabled():
                                await store_working_memory(run_id, org_uuid, f"AI Thought: {content}", source="ai_step")
                                
                    if node_data.get("status") == "completed":
                        success = True
                    elif node_data.get("status") == "failed":
                        success = False

                # Stream the updates dictionary back to the caller
                yield event
        except Exception as e:
            success = False
            final_response = f"Run failed with exception: {str(e)}"
            logger.error(f"Execution stream error: {e}", exc_info=True)
            raise
        finally:
            # Hook: Episodic & Semantic/Procedural Extraction on End
            if org_id and is_memory_enabled():
                try:
                    transcript_str = "\n".join(transcript_builder)
                    await store_episodic_memory(run_id, org_uuid, goal, final_response, list(tools_used), success)
                    
                    import os
                    if os.environ.get("VERCEL") == "1" or os.environ.get("SERVERLESS") == "1":
                        await extract_and_store_durable_memories(run_id, org_uuid, transcript_str)
                    else:
                        safe_fire_and_forget(extract_and_store_durable_memories(run_id, org_uuid, transcript_str))
                except Exception as e:
                    logger.error(f"Failed to trigger end-of-run memory hooks: {e}")


    async def execute_step(
        self, run_id: str, thread_id: str, goal: str = "", research_mode: str = "balanced", environment_mode: str = "local", org_id: str | None = None, is_first: bool = False
    ) -> dict:
        """Executes exactly one step (superstep) of the LangGraph workflow and returns events."""
        from langchain_core.runnables.config import RunnableConfig
        import uuid
        import logging
        logger = logging.getLogger(__name__)
        
        config = RunnableConfig(configurable={"thread_id": thread_id})
        
        input_data = None
        if is_first:
            logger.info(f"Initiating step-by-step run '{run_id}' under thread: '{thread_id}' with goal: '{goal}'")
            from src.utils.host_manager import host_manager
            host_manager.stop_session(thread_id)
            if run_id != thread_id:
                host_manager.stop_session(run_id)

            await self.memory.working.set_state(thread_id, "active_run_id", run_id)
            
            injected_memories_text = ""
            from src.runtime.memory_hooks import is_memory_enabled, store_working_memory, store_episodic_memory, extract_and_store_durable_memories
            org_uuid = None
            if org_id and is_memory_enabled():
                try:
                    from src.services.memory_service import MemoryService
                    from src.api.dependencies import get_uow_factory
                    from src.db.models.memory_entry import MemoryType
                    memory_service = MemoryService(get_uow_factory())
                    org_uuid = uuid.UUID(str(org_id))
                    
                    top_memories = []
                    for mtype in [MemoryType.SEMANTIC, MemoryType.PROCEDURAL, MemoryType.EPISODIC]:
                        mems = await memory_service.get_top_memories(namespace="default", memory_type=mtype, org_id=org_uuid, limit=2)
                        top_memories.extend(mems)
                        
                    top_memories.sort(key=lambda x: x.importance_score, reverse=True)
                    top_memories = top_memories[:5]
                    
                    if top_memories:
                        injected_memories_text = "Relevant Past Memories:\n" + "\n".join(f"- [{m.memory_type}] {m.content}" for m in top_memories) + "\n\n"
                        
                    await store_working_memory(run_id, org_uuid, f"Goal: {goal}")
                except Exception as e:
                    logger.error(f"Failed to retrieve or store initial memories: {e}")

            augmented_goal = injected_memories_text + goal
            input_data = {
                "goal": augmented_goal,
                "messages": [{"role": "user", "content": augmented_goal}] if goal else [],
                "environment_mode": environment_mode,
                "credentials_status": {},
                "local_secrets": [],
                "plan": [],
                "status": "started",
                "next_action": None,
                "run_id": run_id,
                "thread_id": thread_id,
                "variables": {"research_mode": research_mode},
                "human_input": None,
            }
            
        events = []
        try:
            async for event in self.graph.astream(input_data, config, stream_mode="updates"):
                events.append(event)
                # Hook Working Memory for the executed step
                from src.runtime.memory_hooks import is_memory_enabled, store_working_memory
                if org_id and is_memory_enabled():
                    try:
                        org_uuid = uuid.UUID(str(org_id))
                        for node_name, node_data in event.items():
                            if "messages" in node_data and node_data["messages"]:
                                last_msg = node_data["messages"][-1]
                                if isinstance(last_msg, dict):
                                    content = last_msg.get("content", "")
                                    role = last_msg.get("role", "")
                                    name = last_msg.get("name", "")
                                else:
                                    content = getattr(last_msg, "content", "")
                                    role = getattr(last_msg, "type", "")
                                    name = getattr(last_msg, "name", "")
                                if role == "tool" or name:
                                    await store_working_memory(run_id, org_uuid, f"Tool {name or role} output: {content}", source=f"tool_{name or role}")
                                elif role == "ai" or role == "assistant":
                                    await store_working_memory(run_id, org_uuid, f"AI Thought: {content}", source="ai_step")
                    except Exception as e:
                        logger.error(f"Working memory step hook failed: {e}")
                break
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Execution step error: {e}", exc_info=True)
            return {"status": "error", "events": events, "error": str(e)}
            
        state = await self.graph.aget_state(config)
        is_done = len(state.next) == 0 if state else True
        
        if is_done:
            # End of run extraction
            from src.runtime.memory_hooks import is_memory_enabled, store_episodic_memory, extract_and_store_durable_memories
            from src.utils.safe_execute import safe_fire_and_forget
            if org_id and is_memory_enabled():
                try:
                    import logging
                    logger = logging.getLogger(__name__)
                    org_uuid = uuid.UUID(str(org_id))
                    # Reconstruct transcript
                    transcript_builder = [f"Goal: {goal}"] if goal else []
                    tools_used = set()
                    final_response = ""
                    success = False
                    
                    if state and "messages" in state.values:
                        for msg in state.values["messages"]:
                            if isinstance(msg, dict):
                                content = msg.get("content", "")
                                role = msg.get("role", "")
                                name = msg.get("name", "")
                            else:
                                content = getattr(msg, "content", "")
                                role = getattr(msg, "type", "")
                                name = getattr(msg, "name", "")
                            
                            if role == "tool" or name:
                                tools_used.add(name or role)
                                transcript_builder.append(f"Tool {name or role} Output: {str(content)[:200]}...")
                            elif role == "ai" or role == "assistant":
                                transcript_builder.append(f"AI: {str(content)[:200]}...")
                                final_response = str(content)
                                
                    if state and state.values.get("status") == "completed":
                        success = True
                        
                    transcript_str = "\n".join(transcript_builder)
                    await store_episodic_memory(run_id, org_uuid, goal, final_response, list(tools_used), success)
                    
                    import os
                    if os.environ.get("VERCEL") == "1" or os.environ.get("SERVERLESS") == "1":
                        await extract_and_store_durable_memories(run_id, org_uuid, transcript_str)
                    else:
                        safe_fire_and_forget(extract_and_store_durable_memories(run_id, org_uuid, transcript_str))
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to trigger end-of-run memory hooks: {e}")
                    
        return {"status": "done" if is_done else "running", "events": events}

    async def resume_run(
        self, thread_id: str, human_input: str
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Resumes a paused run, feeding operator feedback to the active interrupt node."""
        safe_response = human_input if human_input in ("approve", "reject", "mock") else (f"{human_input[:3]}...[REDACTED]" if len(human_input) > 6 else "[REDACTED]")
        logger.info(f"Resuming paused run on thread: '{thread_id}' with response: '{safe_response}'")

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
