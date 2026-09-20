import asyncio
import logging
import uuid
from datetime import datetime, timedelta, UTC
from typing import Any

from src.api.dependencies import get_uow_factory
from src.db.models.memory_entry import MemoryType
from src.services.memory_service import MemoryService
from src.ai_runtime.service import AIRuntimeService
from src.ai_runtime.contracts import CompletionRequest, Message

logger = logging.getLogger(__name__)

# Config flag - can be moved to settings if needed
MEMORY_ENABLED = True

def is_memory_enabled() -> bool:
    return MEMORY_ENABLED

async def store_working_memory(
    run_id: str,
    org_id: uuid.UUID,
    content: str,
    namespace: str = "default",
    source: str = "run_start"
) -> None:
    """Store short-lived working memory (24h TTL) in the background."""
    if not is_memory_enabled():
        return
    try:
        memory_service = MemoryService(get_uow_factory())
        expires_at = datetime.now(UTC) + timedelta(hours=24)
        await memory_service.store_memory(
            content=content,
            namespace=namespace,
            org_id=org_id,
            memory_type=MemoryType.WORKING,
            agent_run_id=uuid.UUID(run_id),
            importance_score=0.5,
            source=source,
            expires_at=expires_at
        )
    except Exception as e:
        logger.error(f"Failed to store working memory for run {run_id}: {e}", exc_info=True)


async def store_episodic_memory(
    run_id: str,
    org_id: uuid.UUID,
    goal: str,
    final_response: str,
    tools_used: list[str],
    success: bool,
    namespace: str = "default"
) -> None:
    if not is_memory_enabled():
        return
    try:
        memory_service = MemoryService(get_uow_factory())
        content = f"Goal: {goal}\nResponse: {final_response}\nTools: {', '.join(tools_used)}\nStatus: {'Success' if success else 'Failed'}"
        await memory_service.store_memory(
            content=content,
            namespace=namespace,
            org_id=org_id,
            memory_type=MemoryType.EPISODIC,
            agent_run_id=uuid.UUID(run_id),
            importance_score=0.8,
            source="run_end",
        )
    except Exception as e:
        logger.error(f"Failed to store episodic memory for run {run_id}: {e}", exc_info=True)


async def extract_and_store_durable_memories(
    run_id: str,
    org_id: uuid.UUID,
    transcript: str,
    namespace: str = "default"
) -> None:
    """Extract durable Semantic and Procedural memories using an LLM after run completes."""
    if not is_memory_enabled():
        return
    try:
        ai_service = AIRuntimeService()
        prompt = (
            "Analyze the following agent transcript and extract 2-5 durable facts (Semantic) "
            "and any highly reusable 'how-to' sequences (Procedural). "
            "Format the output strictly as a JSON array of objects with keys: "
            "'type' (either 'SEMANTIC' or 'PROCEDURAL'), 'content' (the fact or instruction), "
            "and 'importance' (a float between 0.0 and 1.0).\n\n"
            f"Transcript:\n{transcript}"
        )
        
        req = CompletionRequest(
            messages=[Message(role="user", content=prompt)],
            model="gpt-4o-mini",  # Adjust model as needed
            temperature=0.0
        )
        resp = await ai_service.complete(req)
        
        # parse json from text
        import json
        import re
        
        text = resp.text
        # extract json array using regex in case of markdown formatting
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if not match:
            logger.warning(f"Failed to extract JSON from LLM response for run {run_id}")
            return
            
        items = json.loads(match.group(0))
        memory_service = MemoryService(get_uow_factory())
        
        for item in items:
            mem_type = MemoryType.SEMANTIC if item.get('type') == 'SEMANTIC' else MemoryType.PROCEDURAL
            await memory_service.store_memory(
                content=item.get('content', ''),
                namespace=namespace,
                org_id=org_id,
                memory_type=mem_type,
                agent_run_id=uuid.UUID(run_id),
                importance_score=float(item.get('importance', 0.5)),
                source="llm_extraction",
            )
            
    except Exception as e:
        logger.error(f"Failed to extract durable memories for run {run_id}: {e}", exc_info=True)
