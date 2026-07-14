"""
ASEP — Checkpoint Abstraction Wrapper
"""

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver


class CheckpointManager:
    """Wrapper class managing thread-safe workflow checkpoint savers."""

    def __init__(self) -> None:
        # Defaults to in-memory checkpointer. Can be extended to Postgres/Redis.
        self._saver = MemorySaver()

    def get_checkpointer(self) -> BaseCheckpointSaver:
        """Retrieve the compiled checkpoint saver instance."""
        return self._saver
