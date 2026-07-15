"""
ASEP — Agent Session Lifecycle Management
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from src.agent.state import AgentSessionStatus, AgentState

if TYPE_CHECKING:
    from src.memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

# Working-memory key prefix for session records
_SESSION_KEY_PREFIX = "agent:session:"
_SESSION_TTL_SECONDS = 86400  # 24 hours


class AgentSession(BaseModel):
    """Lightweight persistent session record stored in working memory."""
    session_id: str
    run_id: str
    goal: str
    status: AgentSessionStatus = AgentSessionStatus.IDLE
    # thread_id equals session_id — used as the LangGraph checkpoint key
    thread_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class SessionManager:
    """Creates, updates, and loads agent sessions via the MemoryManager working layer."""

    def __init__(self, memory_manager: "MemoryManager") -> None:
        self._memory = memory_manager

    # ──────────────────────────────────────────────────────────────────────────
    # Public interface
    # ──────────────────────────────────────────────────────────────────────────

    async def create_session(self, goal: str) -> AgentSession:
        """Allocate a new session with a UUID, persist it to working memory, and return it."""
        session_id = str(uuid.uuid4())
        session = AgentSession(
            session_id=session_id,
            run_id=str(uuid.uuid4()),
            goal=goal,
            thread_id=session_id,   # 1:1 mapping with LangGraph thread_id
        )
        await self._persist(session)
        logger.info(f"Created agent session: {session_id}")
        return session

    async def update_status(self, session: AgentSession, status: AgentSessionStatus) -> None:
        """Update the session status in working memory."""
        session.status = status
        await self._persist(session)
        logger.debug(f"Session {session.session_id}: status → {status.value}")

    async def load_session(self, session_id: str) -> AgentSession | None:
        """Retrieve a session record from working memory. Returns None if not found."""
        key = _SESSION_KEY_PREFIX + session_id
        raw = await self._memory.working.cache.get_json(key)
        if not raw:
            return None
        return AgentSession.model_validate(raw)

    def to_state(self, session: AgentSession, plan_task_count: int | None = None) -> AgentState:
        """Construct a full AgentState from a session record."""
        return AgentState(
            session_id=session.session_id,
            run_id=session.run_id,
            thread_id=session.thread_id,
            goal=session.goal,
            status=session.status,
            plan_task_count=plan_task_count,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Internal
    # ──────────────────────────────────────────────────────────────────────────

    async def _persist(self, session: AgentSession) -> None:
        key = _SESSION_KEY_PREFIX + session.session_id
        await self._memory.working.cache.set_json(
            key, session.model_dump(mode="json"), ttl=_SESSION_TTL_SECONDS
        )
