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

async def _ensure_agent_run(
    uow_factory,
    run_id_str: str,
    org_id: uuid.UUID,
    goal: str = "Agent Run"
) -> uuid.UUID | None:
    """Ensure that the parent AgentRun exists in the DB so FK constraints succeed."""
    try:
        run_uuid = uuid.UUID(run_id_str)
    except (ValueError, TypeError):
        return None

    try:
        async with uow_factory() as uow:
            existing = await uow.agent_runs.get(run_uuid)
            if not existing:
                parsed_org_id = None
                if org_id:
                    try:
                        parsed_org_id = uuid.UUID(str(org_id))
                    except (ValueError, TypeError):
                        pass
                new_run = AgentRun(
                    id=run_uuid,
                    org_id=parsed_org_id,
                    goal=goal or "Agent Run",
                    status=RunStatus.RUNNING,
                )
                await uow.agent_runs.create(new_run)
                await uow.commit()
        return run_uuid
    except Exception as e:
        logger.warning(f"Could not ensure AgentRun {run_uuid} for memory linking: {e}")
        return None


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
        uow_factory = get_uow_factory()
        agent_run_uuid = await _ensure_agent_run(uow_factory, run_id, org_id, goal=content)
        memory_service = MemoryService(uow_factory)
        expires_at = datetime.now(UTC) + timedelta(hours=24)
        await memory_service.store_memory(
            content=content,
            namespace=namespace,
            org_id=org_id,
            memory_type=MemoryType.WORKING,
            agent_run_id=agent_run_uuid,
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
        uow_factory = get_uow_factory()
        agent_run_uuid = await _ensure_agent_run(uow_factory, run_id, org_id, goal=goal)
        memory_service = MemoryService(uow_factory)
        content = f"Goal: {goal}\nResponse: {final_response}\nTools: {', '.join(tools_used)}\nStatus: {'Success' if success else 'Failed'}"
        await memory_service.store_memory(
            content=content,
            namespace=namespace,
            org_id=org_id,
            memory_type=MemoryType.EPISODIC,
            agent_run_id=agent_run_uuid,
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
        resolved_model = ai_service.registry.get_default_model()
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
            model=resolved_model,
            temperature=0.0
        )
        resp = await asyncio.wait_for(ai_service.complete(req), timeout=5.0)
        
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
        uow_factory = get_uow_factory()
        agent_run_uuid = await _ensure_agent_run(uow_factory, run_id, org_id)
        memory_service = MemoryService(uow_factory)
        
        for item in items:
            mem_type = MemoryType.SEMANTIC if item.get('type') == 'SEMANTIC' else MemoryType.PROCEDURAL
            await memory_service.store_memory(
                content=item.get('content', ''),
                namespace=namespace,
                org_id=org_id,
                memory_type=mem_type,
                agent_run_id=agent_run_uuid,
                importance_score=float(item.get('importance', 0.5)),
                source="llm_extraction",
            )
            
    except Exception as e:
        logger.warning(
            "Failed to extract durable memories for run %s: exception_type=%s, message=%s",
            run_id,
            type(e).__name__,
            str(e),
            exc_info=True,
        )
