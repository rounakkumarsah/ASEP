"""
Tests for KnowledgeService
"""

import uuid
from decimal import Decimal
import pytest
from unittest.mock import AsyncMock

from src.db.models.knowledge_document import KnowledgeDocument, DocumentStatus, DocumentSourceType, CrawlStatus
from src.services.knowledge_service import KnowledgeService
from src.services.exceptions import InvalidStateError


@pytest.fixture
def knowledge_service(uow_factory):
    return KnowledgeService(uow_factory)


@pytest.mark.asyncio
async def test_register_document(knowledge_service, mock_uow):
    mock_uow.knowledge_documents.create.side_effect = lambda doc: doc
    
    result = await knowledge_service.register_document(
        document_name="test_doc",
        title="Test Document",
        source_type=DocumentSourceType.WEB,
        trust_score=0.8
    )
    
    assert result.document_name == "test_doc"
    assert result.title == "Test Document"
    assert result.status == DocumentStatus.PENDING
    assert result.trust_score == Decimal("0.800")
    
    mock_uow.knowledge_documents.create.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_register_document_validation(knowledge_service):
    with pytest.raises(ValueError, match="must be non-empty"):
        await knowledge_service.register_document(
            document_name="",
            title="test",
            source_type=DocumentSourceType.WEB
        )
        
    with pytest.raises(ValueError, match="trust_score must be in"):
        await knowledge_service.register_document(
            document_name="test",
            title="test",
            source_type=DocumentSourceType.WEB,
            trust_score=1.5
        )


@pytest.mark.asyncio
async def test_mark_indexing(knowledge_service, mock_uow):
    doc_id = uuid.uuid4()
    mock_doc = KnowledgeDocument(id=doc_id, status=DocumentStatus.PENDING)
    mock_uow.knowledge_documents.get_or_raise.return_value = mock_doc
    mock_uow.knowledge_documents.update.return_value = KnowledgeDocument(id=doc_id, status=DocumentStatus.INDEXING)
    
    result = await knowledge_service.mark_indexing(doc_id)
    
    assert result.status == DocumentStatus.INDEXING
    mock_uow.knowledge_documents.update.assert_awaited_once_with(mock_doc, status=DocumentStatus.INDEXING)
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_mark_ready_invalid_state(knowledge_service, mock_uow):
    doc_id = uuid.uuid4()
    # PENDING cannot go straight to READY
    mock_doc = KnowledgeDocument(id=doc_id, status=DocumentStatus.PENDING)
    mock_uow.knowledge_documents.get_or_raise.return_value = mock_doc
    
    with pytest.raises(InvalidStateError):
        await knowledge_service.mark_ready(doc_id)


@pytest.mark.asyncio
async def test_update_crawl_status(knowledge_service, mock_uow):
    doc_id = uuid.uuid4()
    mock_doc = KnowledgeDocument(id=doc_id, crawl_status=CrawlStatus.PENDING)
    mock_uow.knowledge_documents.get_or_raise.return_value = mock_doc
    mock_uow.knowledge_documents.update.return_value = KnowledgeDocument(id=doc_id, crawl_status=CrawlStatus.SUCCESS)
    
    result = await knowledge_service.update_crawl_status(doc_id, CrawlStatus.SUCCESS)
    
    assert result.crawl_status == CrawlStatus.SUCCESS
    mock_uow.knowledge_documents.update.assert_awaited_once_with(mock_doc, crawl_status=CrawlStatus.SUCCESS)
    mock_uow.commit.assert_awaited_once()
