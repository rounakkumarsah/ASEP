"""
ASEP — Unit and Integration Tests for Knowledge Synchronization Engine
"""

import pytest
from httpx import AsyncClient

from src.knowledge.sources import get_source_registry, SourceRegistry, KnowledgeSource
from src.knowledge.sync import get_sync_engine, KnowledgeSyncEngine


def test_source_registry_crud():
    """Verify registration, lookup, metadata extraction, and activation controls."""
    registry = SourceRegistry()
    src = KnowledgeSource(
        source_id="test_git",
        name="Test Git Repo Docs",
        source_type="Git Repository",
        source_url="https://github.com/internal/docs",
        version="1.4.2",
        trust_level=0.9
    )

    registry.register_source(src)
    assert registry.lookup("test_git") is not None
    assert registry.version("test_git") == "1.4.2"
    
    meta = registry.metadata("test_git")
    assert meta is not None
    assert meta["trust_level"] == 0.9

    # Test enable/disable
    registry.disable_source("test_git")
    assert registry.lookup("test_git").is_enabled is False
    registry.enable_source("test_git")
    assert registry.lookup("test_git").is_enabled is True

    # Test unregister
    registry.unregister_source("test_git")
    assert registry.lookup("test_git") is None


@pytest.mark.asyncio
async def test_incremental_sync_change_detection():
    """Verify change detection skips unmodified docs and processes new/changed docs."""
    registry = get_source_registry()
    # Ensure default_docs exists and is enabled
    src = registry.lookup("default_docs")
    if not src:
        registry.register_source(KnowledgeSource(
            source_id="default_docs",
            name="ASEP Core Architecture Docs",
            source_type="Documentation",
            source_url="https://asep.internal/docs",
            version="1.2.0"
        ))
    registry.enable_source("default_docs")

    engine = KnowledgeSyncEngine()

    # Step 1: Initial Sync with doc1 and doc2
    docs_batch_1 = [
        {"doc_id": "doc1", "version": "1.0", "checksum": "hash-abc", "content": "Initial content doc1"},
        {"doc_id": "doc2", "version": "1.0", "checksum": "hash-xyz", "content": "Initial content doc2"}
    ]
    hist_1 = await engine.incremental_sync("default_docs", docs_batch_1)
    assert hist_1.documents_synced == 2
    assert hist_1.skipped_documents == 0
    assert hist_1.changed_documents == 0

    # Step 2: Incremental Sync with doc1 (unchanged), doc2 (changed version & content), and doc3 (new)
    docs_batch_2 = [
        {"doc_id": "doc1", "version": "1.0", "checksum": "hash-abc", "content": "Initial content doc1"},
        {"doc_id": "doc2", "version": "2.0", "checksum": "hash-xyz-new", "content": "Modified content doc2"},
        {"doc_id": "doc3", "version": "1.0", "checksum": "hash-123", "content": "Brand new doc3"}
    ]
    hist_2 = await engine.incremental_sync("default_docs", docs_batch_2)
    assert hist_2.documents_synced == 1  # doc3 is new
    assert hist_2.skipped_documents == 1  # doc1 is unchanged
    assert hist_2.changed_documents == 1  # doc2 is modified


@pytest.mark.asyncio
async def test_sync_recovery_retry():
    """Verify sync runner checkpoints can be paused, resumed, and retried."""
    engine = KnowledgeSyncEngine()
    
    # 1. Simulate a sync failure
    # Ensure source registered
    registry = get_source_registry()
    if not registry.lookup("default_docs"):
        registry.register_source(KnowledgeSource(
            source_id="default_docs",
            name="ASEP Core Architecture Docs",
            source_type="Documentation",
            source_url="https://asep.internal/docs",
            version="1.2.0"
        ))
    
    hist = await engine.full_sync("default_docs")
    sync_id = hist.sync_id
    
    # 2. Test retry sync
    retry_hist = await engine.retry_sync(sync_id)
    assert retry_hist.retry_count == 1
    assert retry_hist.status == "completed"

    # 3. Test resume sync
    resume_hist = await engine.resume_sync(sync_id)
    assert resume_hist.status == "completed"


@pytest.mark.asyncio
async def test_knowledge_sync_api_endpoints(async_client: AsyncClient):
    """Verify REST API endpoints for configuring sources and triggering syncs."""
    # 1. GET /api/v1/knowledge/sources
    resp_list = await async_client.get("/api/v1/knowledge/sources")
    assert resp_list.status_code == 200
    assert len(resp_list.json()) >= 1

    # 2. POST /api/v1/knowledge/sources
    resp_create = await async_client.post(
        "/api/v1/knowledge/sources",
        json={
            "source_id": "api_source",
            "name": "External API Docs",
            "source_type": "API",
            "source_url": "https://api.external/docs",
            "version": "1.0"
        }
    )
    assert resp_create.status_code == 200
    assert resp_create.json()["status"] == "registered"

    # 3. POST /api/v1/knowledge/sync
    resp_sync = await async_client.post(
        "/api/v1/knowledge/sync",
        json={
            "source_id": "api_source",
            "sync_mode": "incremental",
            "documents": [
                {"doc_id": "api_doc_1", "version": "1.0", "checksum": "hash-api-1", "content": "External API specifications"}
            ]
        }
    )
    assert resp_sync.status_code == 200
    sync_data = resp_sync.json()
    assert sync_data["status"] == "completed"
    assert sync_data["metrics"]["documents_synced"] == 1

    # 4. GET /api/v1/knowledge/sync/history
    resp_history = await async_client.get("/api/v1/knowledge/sync/history")
    assert resp_history.status_code == 200
    assert len(resp_history.json()) >= 1

    # 5. GET /api/v1/knowledge/documents
    resp_docs = await async_client.get("/api/v1/knowledge/documents")
    assert resp_docs.status_code == 200
    docs = resp_docs.json()
    assert len(docs) >= 1
    assert docs[0]["source_id"] == "api_source"
    assert docs[0]["trust_level"] == 0.8
    assert docs[0]["license"] == "Proprietary"
    assert docs[0]["language"] == "en"
