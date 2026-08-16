"""
ASEP — HITLSession Repository
"""

from __future__ import annotations

from sqlalchemy import select

from src.db.models.hitl_session import HITLSession
from src.repositories.base import BaseRepository


class HITLSessionRepository(BaseRepository[HITLSession, str]):
    """PostgreSQL repository for HITLSession entities."""

    _model = HITLSession

    async def get_by_execution_id(self, execution_id: str) -> list[HITLSession]:
        """Retrieve all review sessions associated with a specific run execution ID."""
        import uuid

        try:
            exec_uuid = uuid.UUID(execution_id)
        except ValueError:
            return []

        stmt = select(HITLSession).where(HITLSession.execution_id == exec_uuid)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
