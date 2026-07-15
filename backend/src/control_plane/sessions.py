"""
ASEP — Control Plane Sessions
"""

import logging
from typing import Any
from datetime import datetime, timezone

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SessionMetadata(BaseModel):
    session_id: str
    status: str = "running" # running, paused, completed, failed, cancelled
    goal: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    error: str | None = None


class SessionManager:
    """Manages live session tracking and metadata."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionMetadata] = {}

    def register_session(self, session_id: str, goal: str) -> None:
        self._sessions[session_id] = SessionMetadata(session_id=session_id, goal=goal)

    def update_status(self, session_id: str, status: str, error: str | None = None) -> None:
        if session := self._sessions.get(session_id):
            session.status = status
            session.error = error
            session.updated_at = datetime.now(tz=timezone.utc)

    def get_session(self, session_id: str) -> SessionMetadata | None:
        return self._sessions.get(session_id)

    def list_sessions(self, status: str | None = None) -> list[SessionMetadata]:
        if status:
            return [s for s in self._sessions.values() if s.status == status]
        return list(self._sessions.values())
