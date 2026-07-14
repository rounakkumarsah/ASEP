"""
Integration Tests for KnowledgeDocumentRepository
"""

import uuid
from decimal import Decimal
import pytest

from src.db.models.knowledge_document import KnowledgeDocument, DocumentStatus, DocumentSourceType, CrawlStatus
from src.repositories.knowledge_document import KnowledgeDocumentRepository


@pytest.fixture
def repo(db_session):
    return KnowledgeDocumentRepository(db_session)


@pytest.mark.asyncio
async def test_get_ready(repo, db_session):
    doc1 = KnowledgeDocument(
        id=uuid.uuid4(),
        document_name="doc1",
        title="Doc 1",
        source_type=DocumentSourceType.WEB,
        status=DocumentStatus.READY,
        trust_score=Decimal("0.8")
    )
    doc2 = KnowledgeDocument(
        id=uuid.uuid4(),
        document_name="doc2",
        title="Doc 2",
        source_type=DocumentSourceType.WEB,
        status=DocumentStatus.PENDING,
        trust_score=Decimal("0.5")
    )
    await repo.create(doc1)
    await repo.create(doc2)
    await db_session.flush()
    
    ready_docs = await repo.get_ready()
    # Ensure doc1 is in ready, but doc2 is not
    assert doc1.id in [d.id for d in ready_docs]
    assert doc2.id not in [d.id for d in ready_docs]


@pytest.mark.asyncio
async def test_get_by_checksum(repo, db_session):
    checksum = "abcdef123456"
    doc = KnowledgeDocument(
        id=uuid.uuid4(),
        document_name="doc_checksum",
        title="Doc Checksum",
        source_type=DocumentSourceType.WEB,
        status=DocumentStatus.PENDING,
        trust_score=Decimal("0.5"),
        checksum_sha256=checksum
    )
    await repo.create(doc)
    await db_session.flush()
    
    fetched = await repo.get_by_checksum(checksum)
    assert fetched is not None
    assert fetched.id == doc.id
    
    not_found = await repo.get_by_checksum("invalid")
    assert not_found is None


@pytest.mark.asyncio
async def test_get_pending_crawl(repo, db_session):
    doc = KnowledgeDocument(
        id=uuid.uuid4(),
        document_name="doc_crawl",
        title="Doc Crawl",
        source_type=DocumentSourceType.WEB,
        status=DocumentStatus.PENDING,
        crawl_status=CrawlStatus.PENDING,
        trust_score=Decimal("0.5")
    )
    await repo.create(doc)
    await db_session.flush()
    
    pending = await repo.get_pending_crawl()
    assert doc.id in [d.id for d in pending]
