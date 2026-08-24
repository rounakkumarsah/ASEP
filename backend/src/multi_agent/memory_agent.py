from __future__ import annotations

from typing import Any

from src.memory.memory_manager import MemoryManager
from src.multi_agent.base_agent import BaseAgent
from src.multi_agent.contracts import AgentManifest, AgentRequest, AgentRole


class MemoryAgent(BaseAgent):
    """Memory Agent integrating working, episodic, and semantic memory repositories."""

    def __init__(self, memory_manager: MemoryManager | None = None) -> None:
        manifest = AgentManifest(
            name="MemoryAgent",
            version="1.0.0",
            description="Manages context persistence, episodic logs, and semantic summaries.",
            capabilities=["retrieve_memory", "update_working", "update_episodic", "update_semantic", "summarize_memory"],
            supported_inputs=["action", "session_id", "data"],
            supported_outputs=["status", "recalled_data", "summary"]
        )
        super().__init__(role=AgentRole.MEMORY, manifest=manifest)
        self.memory_manager = memory_manager

    async def _execute_internal(self, request: AgentRequest) -> dict[str, Any]:
        action = request.input_data.get("action", "retrieve_memory")
        session_id = request.input_data.get("session_id", "default_session")
        data = request.input_data.get("data", {})

        recalled_data: dict[str, Any] = {}
        summary = "No active memory manager initialized."

        # If real manager is injected, execute real calls
        if self.memory_manager:
            import uuid
            try:
                run_uuid = uuid.UUID(session_id)
            except ValueError:
                run_uuid = uuid.uuid4()

            if action == "update_working":
                await self.memory_manager.working.set_state(session_id, "agent_data", data)
            elif action == "update_episodic":
                await self.memory_manager.episodic.add_episode(
                    run_id=run_uuid,
                    namespace="agent_execution",
                    content="Episodic event update",
                    metadata=data
                )
            elif action == "retrieve_memory":
                state = await self.memory_manager.working.get_state(session_id, "agent_data")
                recalled_data = state if isinstance(state, dict) else {}
                summary = "Active working memory retrieved."
        else:
            summary = f"Mocked recalled memory state for session {session_id} on action {action}"

        return {
            "status": "success",
            "recalled_data": recalled_data,
            "summary": summary
        }
