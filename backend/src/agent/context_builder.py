"""
ASEP — Agent Context Builder

Assembles a rich ContextSnapshot from four memory layers plus the live tool catalog.
This snapshot is the agent's complete situational awareness before planning begins.
"""

import logging
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from src.memory.memory_manager import MemoryManager
    from src.tools.discovery import ToolDiscovery

logger = logging.getLogger(__name__)

# How many episodic/semantic/procedural items to pull
_MAX_EPISODES = 5
_MAX_CONCEPTS = 5
_MAX_PROCEDURES = 3


class ContextSnapshot(BaseModel):
    """Complete situational context assembled for a single agent invocation."""
    session_id: str

    # ── Memory layers ────────────────────────────────────────────────────────
    working_vars: dict[str, Any] = Field(
        default_factory=dict,
        description="Current working-memory key/value state for this session",
    )
    recent_episodes: list[dict[str, Any]] = Field(
        default_factory=list,
        description=f"Up to {_MAX_EPISODES} most recent episodic memory entries",
    )
    relevant_concepts: list[dict[str, Any]] = Field(
        default_factory=list,
        description=f"Up to {_MAX_CONCEPTS} semantically relevant knowledge facts",
    )
    relevant_procedures: list[dict[str, Any]] = Field(
        default_factory=list,
        description=f"Up to {_MAX_PROCEDURES} applicable procedural memory entries",
    )

    # ── Tool catalog ─────────────────────────────────────────────────────────
    available_tools: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Summarised catalog of tools available to the agent (name + description + permissions)",
    )

    @property
    def tool_names(self) -> list[str]:
        return [t.get("name", "") for t in self.available_tools]


class ContextBuilder:
    """Hydrates a ContextSnapshot from MemoryManager + ToolDiscovery before each agent run."""

    def __init__(
        self,
        memory_manager: "MemoryManager",
        tool_discovery: "ToolDiscovery",
    ) -> None:
        self._memory = memory_manager
        self._tools = tool_discovery

    async def build(self, goal: str, session_id: str) -> ContextSnapshot:
        """Assemble context by querying all four memory layers and the tool catalog."""

        working_vars: dict[str, Any] = {}
        recent_episodes: list[dict[str, Any]] = []
        relevant_concepts: list[dict[str, Any]] = []
        relevant_procedures: list[dict[str, Any]] = []

        # 1. Fetch memory context via MemoryRetrieval subsystem
        try:
            import uuid
            try:
                run_uuid = uuid.UUID(session_id)
            except ValueError:
                run_uuid = uuid.uuid4()

            retrieved = await self._memory.retrieval.retrieve_context(
                query=goal,
                session_id=session_id,
                run_id=run_uuid,
                limit=_MAX_EPISODES
            )
            working_vars = {"messages": retrieved.get("working", [])}
            recent_episodes = retrieved.get("episodic", [])
            relevant_concepts = retrieved.get("semantic", [])
        except Exception as exc:
            logger.warning(f"[{session_id}] Memory retrieval failed: {exc}")

        # 2. Tool catalog
        available_tools: list[dict[str, Any]] = []
        try:
            all_tools = await self._tools.list_available_tools()
            available_tools = [
                {
                    "name": t.name,
                    "description": t.description,
                    "required_permissions": t.required_permissions,
                    "tool_type": getattr(t, "tool_type", "python"),
                }
                for t in all_tools
            ]
        except Exception as exc:
            logger.warning(f"[{session_id}] Tool catalog fetch failed: {exc}")

        snapshot = ContextSnapshot(
            session_id=session_id,
            working_vars=working_vars,
            recent_episodes=recent_episodes,
            relevant_concepts=relevant_concepts,
            relevant_procedures=relevant_procedures,
            available_tools=available_tools,
        )
        return snapshot
