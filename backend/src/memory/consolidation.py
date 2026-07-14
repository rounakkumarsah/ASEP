"""
ASEP — Memory Consolidation Hooks
"""

import logging
import uuid

from src.memory.episodic import EpisodicMemory
from src.memory.semantic import SemanticMemory
from src.memory.working import WorkingMemory

logger = logging.getLogger(__name__)


class MemoryConsolidator:
    """Manages the consolidation of transient short-term memories into durable long-term storage."""

    def __init__(
        self,
        working: WorkingMemory,
        episodic: EpisodicMemory,
        semantic: SemanticMemory,
    ) -> None:
        self.working = working
        self.episodic = episodic
        self.semantic = semantic

    async def consolidate_session(self, session_id: str, run_id: uuid.UUID) -> None:
        """Consolidates working memory logs into episodic and semantic structures.
        
        This serves as a consolidation lifecycle hook. In a fully agentic setup,
        an LLM summarizer would filter and extract semantic concepts from the 
        working transcripts. Here, we implement the pipeline hooks by carrying
        out a default transaction mapping.
        """
        logger.info(f"Triggering consolidation hook for session: {session_id}")
        
        messages = await self.working.get_messages(session_id)
        if not messages:
            logger.info("Working memory transcript is empty; skipping consolidation.")
            return

        # 1. Episodic Consolidation: Persist the full transcript sequence to SQL
        combined_transcript = "\n".join([
            f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
            for msg in messages
        ])
        
        episode = await self.episodic.add_episode(
            run_id=run_id,
            content=combined_transcript,
            metadata={"source_session": session_id, "consolidated": True}
        )
        
        # 2. Semantic Consolidation Hook: Register consolidated summary nodes in Graph/Vector
        summary_text = f"Consolidated transcript summary for run {run_id}. Content size: {len(combined_transcript)} characters."
        
        await self.semantic.add_fact(
            fact_id=str(episode.id),
            text=summary_text,
            metadata={"parent_episode_id": str(episode.id), "run_id": str(run_id)}
        )
        
        # 3. Working Memory Reset
        await self.working.clear(session_id)
        logger.info(f"Consolidation complete for session: {session_id}. Cleared working state.")
        
    async def post_task_consolidate_hook(self, task_id: uuid.UUID, outcome: str) -> None:
        """Post-task hook allowing developers to trigger asynchronous consolidation checks."""
        logger.info(f"Triggered post-task consolidation check for task: {task_id}. Outcome: {outcome}")
        # Hook placeholder for scheduling task summaries
        pass
