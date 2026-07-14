"""
Knowledge Router
"""

import uuid
from fastapi import APIRouter, Depends, status

from src.api.dependencies import KnowledgeServiceDep
from src.api.schemas import (
    KnowledgeDocumentRegister,
    KnowledgeDocumentResponse,
    PaginatedResponse,
    PaginationParams
)
from src.auth.decorators import RequirePermission
from src.auth.permissions import Permission


router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


@router.post("/", response_model=KnowledgeDocumentResponse, status_code=status.HTTP_201_CREATED, dependencies=[RequirePermission(Permission.KNOWLEDGE_WRITE)])
async def create_document(
    payload: KnowledgeDocumentRegister,
    service: KnowledgeServiceDep,
) -> KnowledgeDocumentResponse:
    """Register a new knowledge document."""
    return await service.register_document(
        source_uri=str(payload.source_uri),
        title=payload.title,
        doc_metadata=payload.doc_metadata
    )


@router.post("/{doc_id}/indexing", response_model=KnowledgeDocumentResponse, dependencies=[RequirePermission(Permission.KNOWLEDGE_WRITE)])
async def mark_indexing(
    doc_id: uuid.UUID,
    service: KnowledgeServiceDep,
) -> KnowledgeDocumentResponse:
    """Mark a document as currently being indexed."""
    return await service.mark_indexing(doc_id)


@router.get("/", response_model=PaginatedResponse[KnowledgeDocumentResponse], dependencies=[RequirePermission(Permission.KNOWLEDGE_READ)])
async def list_documents(
    service: KnowledgeServiceDep,
    pagination: PaginationParams = Depends(),
) -> PaginatedResponse[KnowledgeDocumentResponse]:
    """List pending knowledge documents for crawl."""
    # Since KnowledgeService only has get_pending_crawl, we use that for the listing endpoint.
    docs = await service.get_pending_crawl(limit=pagination.limit)
    
    return PaginatedResponse(
        items=docs,
        total=len(docs),
        limit=pagination.limit,
        offset=pagination.offset
    )
