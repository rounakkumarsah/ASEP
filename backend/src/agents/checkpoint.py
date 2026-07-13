"""
ASEP — LangGraph Checkpoint Manager (Placeholder)
===================================================
Manages LangGraph checkpointer for durable state persistence.
Checkpoints allow runs to be paused, resumed, and replayed.

TODO (Phase 0.2):
    - Implement PostgreSQL-backed checkpointer (langgraph-checkpoint-postgres)
    - Add checkpoint TTL / eviction policy
    - Add checkpoint replay API
    - Add human-in-the-loop interrupt points
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class CheckpointManager:
    """
    Placeholder for the LangGraph checkpoint manager.

    TODO (Phase 0.2):
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        self._saver = AsyncPostgresSaver.from_conn_string(database_url)
        await self._saver.setup()
    """

    def __init__(self) -> None:
        logger.info("CheckpointManager initialised (stub)")

    async def get_checkpointer(self) -> None:
        """
        Return the configured async checkpointer for LangGraph.

        TODO (Phase 0.2): return AsyncPostgresSaver instance.
        """
        raise NotImplementedError("Checkpointer not yet implemented — Phase 0.2")
