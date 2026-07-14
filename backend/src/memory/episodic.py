"""
ASEP — Episodic Memory (PostgreSQL Backend)
"""

import uuid
from decimal import Decimal
from typing import Any

from src.db.models.memory_entry import MemoryEntry, MemoryType
from src.unit_of_work.sqlalchemy import SQLAlchemyUnitOfWork


class EpisodicMemory:
    """Manages durable, chronological sequences of past agent runs and execution steps."""

    def __init__(self, uow: SQLAlchemyUnitOfWork) -> None:
        self.uow = uow

    async def add_episode(
        self,
        run_id: uuid.UUID,
        content: str,
        namespace: str = "default",
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None
    ) -> MemoryEntry:
        """Persist a new run episode to PostgreSQL database."""
        async with self.uow:
            entry = MemoryEntry(
                agent_run_id=run_id,
                memory_type=MemoryType.EPISODIC,
                content=content,
                namespace=namespace,
                importance_score=Decimal(str(importance)),
                entry_metadata=metadata or {},
            )
            created = await self.uow.memory_entries.create(entry)
            await self.uow.commit()
            return created

    async def get_episodes(self, run_id: uuid.UUID) -> list[MemoryEntry]:
        """Fetch all chronological episodic records for a specific agent run."""
        async with self.uow:
            return await self.uow.memory_entries.get_by_agent_run(run_id)
