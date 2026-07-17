from __future__ import annotations
from typing import Dict, Any, Optional
from src.multi_agent.contracts import AgentRole, AgentManifest, AgentRequest
from src.multi_agent.base_agent import BaseAgent
from src.memory.memory_manager import MemoryManager

class MemoryAgent(BaseAgent):
    """Memory Agent integrating working, episodic, and semantic memory repositories."""

    def __init__(self, memory_manager: Optional[MemoryManager] = None) -> None:
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

    async def _execute_internal(self, request: AgentRequest) -> Dict[str, Any]:
        action = request.input_data.get("action", "retrieve_memory")
        session_id = request.input_data.get("session_id", "default_session")
        data = request.input_data.get("data", {})
        
        recalled_data = {}
        summary = "No active memory manager initialized."
        
        # If real manager is injected, execute real calls
        if self.memory_manager:
            if action == "update_working":
                await self.memory_manager.working.save_state(session_id, data)
            elif action == "update_episodic":
                await self.memory_manager.episodic.save_event(session_id, "agent_execution", data)
            elif action == "retrieve_memory":
                recalled_data = await self.memory_manager.working.load_state(session_id) or {}
                summary = "Active working memory retrieved."
        else:
            summary = f"Mocked recalled memory state for session {session_id} on action {action}"

        return {
            "status": "success",
            "recalled_data": recalled_data,
            "summary": summary
        }
