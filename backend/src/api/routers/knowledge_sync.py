"""
ASEP — API Router for Knowledge Synchronization Engine
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.knowledge.sources import get_source_registry, KnowledgeSource
from src.knowledge.sync import get_sync_engine, SyncedDocument, SyncHistory

router = APIRouter(prefix="/knowledge", tags=["Knowledge Synchronization"])


class SourceCreateRequest(BaseModel):
    source_id: str
    name: str
    source_type: str
    source_url: Optional[str] = None
    version: str = "1.0"
    trust_level: float = 0.8
    license: str = "Proprietary"
    language: str = "en"
    provenance: str = "User Conf"


class SyncTriggerRequest(BaseModel):
    source_id: str
    sync_mode: str = "incremental"  # full, incremental
    documents: Optional[List[Dict[str, Any]]] = None


@router.get("/sources", response_model=List[Dict[str, Any]])
async def list_sources() -> List[Dict[str, Any]]:
    """Retrieve all configured knowledge sources."""
    registry = get_source_registry()
    sources = registry.discover_sources()
    return [registry.metadata(s.source_id) for s in sources if registry.metadata(s.source_id)]


@router.post("/sources")
async def create_source(req: SourceCreateRequest) -> Dict[str, Any]:
    """Configure a new trusted knowledge source."""
    registry = get_source_registry()
    if registry.lookup(req.source_id):
        raise HTTPException(status_code=400, detail="Source ID already exists.")
    
    source = KnowledgeSource(
        source_id=req.source_id,
        name=req.name,
        source_type=req.source_type,
        source_url=req.source_url,
        version=req.version,
        trust_level=req.trust_level,
        license=req.license,
        language=req.language,
        provenance=req.provenance
    )
    registry.register_source(source)
    return {"status": "registered", "source_id": req.source_id}


@router.post("/sync")
async def trigger_sync(req: SyncTriggerRequest) -> Dict[str, Any]:
    """Execute full or incremental synchronization runner."""
    engine = get_sync_engine()
    try:
        if req.sync_mode == "full":
            history = await engine.full_sync(req.source_id)
        else:
            history = await engine.incremental_sync(req.source_id, req.documents or [])
        return {
            "status": "completed",
            "sync_id": history.sync_id,
            "metrics": history.model_dump()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sync/history")
async def get_sync_history() -> List[Dict[str, Any]]:
    """Get history log of all synchronization operations."""
    engine = get_sync_engine()
    return [h.model_dump() for h in engine.history]


@router.get("/documents")
async def list_documents() -> List[Dict[str, Any]]:
    """Retrieve all currently synchronized document records."""
    engine = get_sync_engine()
    return [doc.model_dump() for doc in engine.documents.values()]
