"""
ASEP — API Router for Knowledge Synchronization Engine
"""

from typing import Any
from src.auth.dependencies import CurrentUser

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.knowledge.sources import KnowledgeSource, get_source_registry
from src.knowledge.sync import get_sync_engine

router = APIRouter(prefix="/knowledge", tags=["Knowledge Synchronization"])


class SourceCreateRequest(BaseModel):
    source_id: str
    name: str
    source_type: str
    source_url: str | None = None
    version: str = "1.0"
    trust_level: float = 0.8
    license: str = "Proprietary"
    language: str = "en"
    provenance: str = "User Conf"


class SyncTriggerRequest(BaseModel):
    source_id: str
    sync_mode: str = "incremental"  # full, incremental
    documents: list[dict[str, Any]] | None = None


@router.get("/sources", response_model=list[dict[str, Any]])
async def list_sources() -> list[dict[str, Any]]:
    """Retrieve all configured knowledge sources."""
    registry = get_source_registry()
    sources = registry.discover_sources()
    return [registry.metadata(s.source_id) for s in sources if registry.metadata(s.source_id)]


@router.post("/sources")
async def create_source(req: SourceCreateRequest) -> dict[str, Any]:
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
async def trigger_sync(req: SyncTriggerRequest) -> dict[str, Any]:
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
async def get_sync_history() -> list[dict[str, Any]]:
    """Get history log of all synchronization operations."""
    engine = get_sync_engine()
    return [h.model_dump() for h in engine.history]


@router.get("/documents")
async def list_documents(
    current_user: CurrentUser,
    query: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve all currently synchronized document records with optional query filtering."""
    from src.db.postgres import get_db_session
    from src.db.models.document import Document
    from sqlalchemy import select
    from sqlalchemy.exc import ProgrammingError
    
    docs_out = []
    try:
        async for db in get_db_session():
            stmt = select(Document)
            # Basic in-memory filter equivalent for query string
            result = await db.execute(stmt)
            for doc in result.scalars():
                if query:
                    q = query.strip().lower()
                    if not (
                        q in str(doc.source_name).lower() or
                        q in str(doc.source_type).lower() or
                        any(q in str(t).lower() for t in (doc.tags or []))
                    ):
                        continue
                
                docs_out.append({
                    "document_id": doc.id,
                    "id": doc.id,
                    "title": doc.source_name,
                    "source_name": doc.source_name,
                    "source_type": doc.source_type,
                    "tags": doc.tags or [],
                    "created_at": doc.created_at,
                    "updated_at": doc.updated_at
                })
            break
    except ProgrammingError:
        pass # Table might not exist yet if migrations haven't run
        
    return docs_out
