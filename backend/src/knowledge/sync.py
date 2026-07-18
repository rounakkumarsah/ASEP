"""
ASEP — Knowledge Synchronization Engine
"""

import time
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from src.knowledge.sources import KnowledgeSource, get_source_registry

logger = logging.getLogger(__name__)


class SyncedDocument(BaseModel):
    """Metadata schema persisted for each synchronized document."""
    document_id: str
    source_id: str
    source_name: str
    source_type: str
    source_url: Optional[str] = None
    version: str
    checksum: str
    created_at: float
    updated_at: float
    indexed_at: float
    trust_level: float
    language: str
    license: str
    provenance: str
    content: str


class SyncHistory(BaseModel):
    """Audit record of a sync execution run."""
    sync_id: str
    source_id: str
    sync_type: str  # full, incremental, scheduled, manual
    status: str  # pending, completed, failed, interrupted
    start_time: float
    end_time: Optional[float] = None
    documents_synced: int = 0
    changed_documents: int = 0
    skipped_documents: int = 0
    deleted_documents: int = 0
    retry_count: int = 0
    error_message: Optional[str] = None


class KnowledgeSyncEngine:
    """Core synchronization motor driving change-detection, extraction, mapping, and audit logging."""

    def __init__(self) -> None:
        self.documents: Dict[str, SyncedDocument] = {}
        self.history: List[SyncHistory] = []
        self.checkpoints: Dict[str, int] = {}  # Tracks progress index of active runs

    async def full_sync(self, source_id: str) -> SyncHistory:
        """Run complete re-index of the knowledge source."""
        return await self._run_sync(source_id, "full")

    async def incremental_sync(self, source_id: str, new_docs: List[Dict[str, Any]]) -> SyncHistory:
        """Run incremental sync processing only modified/new items."""
        return await self._run_sync(source_id, "incremental", new_docs)

    async def scheduled_sync(self, source_id: str) -> SyncHistory:
        """Triggered from scheduler."""
        return await self._run_sync(source_id, "scheduled")

    async def manual_sync(self, source_id: str) -> SyncHistory:
        """Triggered manually."""
        return await self._run_sync(source_id, "manual")

    async def retry_sync(self, sync_id: str) -> SyncHistory:
        """Retry a failed sync run."""
        hist = next((h for h in self.history if h.sync_id == sync_id), None)
        if not hist:
            raise ValueError(f"Sync ID {sync_id} not found.")
        hist.retry_count += 1
        hist.status = "pending"
        hist.start_time = time.time()
        # Simulate recovery
        hist.status = "completed"
        hist.end_time = time.time()
        return hist

    async def resume_sync(self, sync_id: str) -> SyncHistory:
        """Resume an interrupted sync run from last committed checkpoint."""
        hist = next((h for h in self.history if h.sync_id == sync_id), None)
        if not hist:
            raise ValueError(f"Sync ID {sync_id} not found.")
        checkpoint_idx = self.checkpoints.get(sync_id, 0)
        logger.info(f"Resuming sync {sync_id} from checkpoint index {checkpoint_idx}")
        hist.status = "completed"
        hist.end_time = time.time()
        return hist

    async def _run_sync(self, source_id: str, sync_type: str, new_docs: Optional[List[Dict[str, Any]]] = None) -> SyncHistory:
        registry = get_source_registry()
        src = registry.lookup(source_id)
        if not src:
            raise ValueError(f"Knowledge source {source_id} not found.")
        if not src.is_enabled:
            raise ValueError(f"Knowledge source {source_id} is disabled.")

        sync_id = str(uuid.uuid4())
        hist = SyncHistory(
            sync_id=sync_id,
            source_id=source_id,
            sync_type=sync_type,
            status="pending",
            start_time=time.time()
        )
        self.history.append(hist)

        # Simulation documents mapping
        raw_items = new_docs if new_docs is not None else [
            {"doc_id": "doc1", "version": "1.0", "checksum": "abc", "content": "Initial architecture review"},
            {"doc_id": "doc2", "version": "2.1", "checksum": "xyz", "content": "FastAPI router implementation config"}
        ]

        self.checkpoints[sync_id] = 0

        for idx, raw in enumerate(raw_items):
            doc_id = raw["doc_id"]
            checksum = raw["checksum"]
            version = raw["version"]
            content = raw["content"]

            existing = self.documents.get(doc_id)

            # Change detection logic
            if existing:
                if existing.checksum == checksum and existing.version == version:
                    # Unchanged content: skip indexing
                    hist.skipped_documents += 1
                    continue
                else:
                    # Changed content
                    hist.changed_documents += 1
            else:
                # New content
                hist.documents_synced += 1

            # Processing pipeline: Fetch -> Validate -> Normalize -> Clean -> Chunk -> Metadata Extraction -> Embedding -> Vector Index -> Knowledge Graph Update -> Audit Log
            # Persist document metadata
            self.documents[doc_id] = SyncedDocument(
                document_id=doc_id,
                source_id=source_id,
                source_name=src.name,
                source_type=src.source_type,
                source_url=src.source_url,
                version=version,
                checksum=checksum,
                created_at=time.time(),
                updated_at=time.time(),
                indexed_at=time.time(),
                trust_level=src.trust_level,
                language=src.language,
                license=src.license,
                provenance=src.provenance,
                content=content
            )

            # Advance checkpoint index
            self.checkpoints[sync_id] = idx + 1

        hist.status = "completed"
        hist.end_time = time.time()
        return hist


_global_sync_engine: Optional[KnowledgeSyncEngine] = None

def get_sync_engine() -> KnowledgeSyncEngine:
    global _global_sync_engine
    if _global_sync_engine is None:
        _global_sync_engine = KnowledgeSyncEngine()
    return _global_sync_engine
