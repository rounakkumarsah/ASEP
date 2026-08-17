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
        
        # 4. Hybrid Fusion and Memory Ranking / Scoring Engine
        # We combine episodic and semantic memories, scoring each based on relevancy, importance, and recency.
        scored_memories = []
        
        # Score semantic matches (relevance is based on vector match score)
        for match in semantic_matches:
            # semantic similarity score (Qdrant payload hit score typically between 0.0 and 1.0)
            relevance = float(match.get("score", 0.70))
            # parse importance if registered in payload metadata, default to 0.5
            importance = float(match.get("payload", {}).get("importance", 0.5))
            
            # Semantic weight score fusion: 60% relevance + 40% importance
            final_score = (relevance * 0.6) + (importance * 0.4)
            scored_memories.append({
                "type": "semantic",
                "id": match.get("id"),
                "content": match.get("text", ""),
                "score": round(final_score, 4),
                "metadata": match.get("payload", {})
            })

        # Score episodic entries
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        for entry in episodic_entries:
            importance = float(entry.importance_score)
            
            # Heuristic relevancy: keyword overlap between query and content
            query_words = set(query.lower().split())
            content_words = set(entry.content.lower().split())
            overlap = query_words.intersection(content_words)
            relevance = (len(overlap) / max(len(query_words), 1))
            
            # Recency decay calculation: decay score over time (half-life representation)
            time_decay = 1.0
            if entry.created_at:
                # Ensure entry created_at has timezone
                entry_time = entry.created_at
                if entry_time.tzinfo is None:
                    entry_time = entry_time.replace(tzinfo=timezone.utc)
                diff_hours = (now - entry_time).total_seconds() / 3600.0
                # Exponential decay factor (halves every 24 hours)
                time_decay = 0.5 ** (diff_hours / 24.0)

            # Episodic weight score fusion: 40% relevance + 30% importance + 30% recency
            final_score = (relevance * 0.4) + (importance * 0.3) + (time_decay * 0.3)
            
            scored_memories.append({
                "type": "episodic",
                "id": str(entry.id),
                "content": entry.content,
                "score": round(final_score, 4),
                "metadata": {
                    "importance": importance,
                    "created_at": entry.created_at.isoformat() if entry.created_at else None,
                    "time_decay_factor": round(time_decay, 4)
                }
            })

        # Rank all compiled episodic and semantic memories by their fused score descending
        scored_memories.sort(key=lambda x: x["score"], reverse=True)
        top_ranked = scored_memories[:limit]
        
        return {
            "working": working_messages,
            "episodic": [
                {
                    "id": m["id"],
                    "content": m["content"],
                    "importance": m["metadata"].get("importance", 0.5),
                    "created_at": m["metadata"].get("created_at"),
                    "score": m["score"]
                }
                for m in top_ranked if m["type"] == "episodic"
            ],
            "semantic": [
                {
                    "id": m["id"],
                    "score": m["score"],
                    "text": m["content"],
                    "payload": m["metadata"]
                }
                for m in top_ranked if m["type"] == "semantic"
            ],
            "ranked_fusion": top_ranked
        }
