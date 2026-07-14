"""
ASEP — Provider-Independent Memory Retrieval Abstraction
"""

import logging
import uuid
from typing import Any

from src.memory.episodic import EpisodicMemory
from src.memory.procedural import ProceduralMemory
from src.memory.semantic import SemanticMemory
from src.memory.working import WorkingMemory

logger = logging.getLogger(__name__)


class MemoryRetrieval:
    """Consolidated search interface to scan working, episodic, and semantic memory layers."""

    def __init__(
        self,
        working: WorkingMemory,
        episodic: EpisodicMemory,
        semantic: SemanticMemory,
        procedural: ProceduralMemory,
    ) -> None:
        self.working = working
        self.episodic = episodic
        self.semantic = semantic
        self.procedural = procedural

    async def retrieve_context(
        self,
        query: str,
        session_id: str,
        run_id: uuid.UUID | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Query working memory, database episodes, and vector semantics to compile context."""
        logger.info(f"Retrieving context for query: '{query}'")
        
        # 1. Fetch current run's short-term working context
        working_messages = await self.working.get_messages(session_id)
        
        # 2. Fetch past episodes for the current run (if run_id provided)
        episodic_entries = []
        if run_id:
            episodic_entries = await self.episodic.get_episodes(run_id)
            
        # 3. Retrieve semantically similar facts from Qdrant
        semantic_matches = await self.semantic.query_facts(query, limit=limit)
        
        return {
            "working": working_messages,
            "episodic": [
                {
                    "id": str(entry.id),
                    "content": entry.content,
                    "importance": float(entry.importance_score),
                    "created_at": entry.created_at.isoformat() if entry.created_at else None,
                }
                for entry in episodic_entries
            ],
            "semantic": semantic_matches,
        }
