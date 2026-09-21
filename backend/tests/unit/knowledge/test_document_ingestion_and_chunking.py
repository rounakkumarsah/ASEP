"""
ASEP — Unit tests for Document Ingestion 25 MB Limit, Markdown/Code Chunking, and Section Extraction
"""

import io
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.app import create_app
from src.auth.dependencies import get_current_user
from src.documents.chunking import (
    CODE_SEPARATORS,
    MARKDOWN_SEPARATORS,
    TEXT_SEPARATORS,
    ChunkingEngine,
    RecursiveCharacterTextSplitter,
)
from src.documents.ingestion import IngestionService
from src.production.ingestion_service import MAX_DOCUMENT_SIZE_BYTES, UniversalIngestionService


def test_chunking_engine_markdown_separators_and_sections():
    """Verify markdown content splits preserving headings in metadata.section."""
    engine = ChunkingEngine(chunk_size=150, chunk_overlap=30)
    markdown_content = """# Architecture Guide

This section introduces the core agentic workflow.

## Vector Database
Qdrant stores dense embeddings for high-speed similarity search across documents.

## Graph Database
Neo4j maintains multi-hop entity relationships and knowledge graph connections.

### Cypher Queries
Cypher queries traverse relations between documents and chunks effectively.
"""

    chunks = engine.chunk_document(
        document_id="doc_arch",
        content=markdown_content,
        filename="architecture.md",
        file_path="/docs/architecture.md",
        collection="knowledge",
    )

    assert len(chunks) >= 3
    # Check that section names were extracted into metadata
    sections = [c.metadata.section for c in chunks if c.metadata.section is not None]
    assert any("Architecture Guide" in s for s in sections)
    assert any("Vector Database" in s or "Graph Database" in s for s in sections)

    # Verify parent_id and hash integrity
    for c in chunks:
        assert c.parent_id is not None
        assert len(c.chunk_id) == 64
        assert len(c.content_hash) == 64
        assert c.content.strip() != ""


def test_chunking_engine_code_separators():
    """Verify code content is split using code-aware separators."""
    engine = ChunkingEngine(chunk_size=120, chunk_overlap=20)
    code_content = """class AgentRunner:
    def __init__(self, name: str):
        self.name = name

    def execute_task(self, task_id: str):
        return f"Executing {task_id}"

class CriticAuditor:
    def evaluate(self, code: str) -> bool:
        return True
"""
    chunks = engine.chunk_document(
        document_id="doc_code",
        content=code_content,
        filename="runner.py",
        file_path="/src/runner.py",
    )

    assert len(chunks) >= 2
    for c in chunks:
        assert c.metadata.filename == "runner.py"
        assert c.content.strip() != ""


def test_splitter_custom_and_default_separators():
    """Verify RecursiveCharacterTextSplitter handles custom and fallback separators."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=10)
    text = "Paragraph one.\n\nParagraph two with some extra text.\n\nParagraph three."
    chunks = splitter.split_text(text)
    assert len(chunks) >= 2

    # Verify with explicit separators
    custom_chunks = splitter.split_text(text, custom_separators=["\n\n", " "])
    assert len(custom_chunks) >= 2


@pytest.mark.asyncio
async def test_universal_ingestion_service_size_limit():
    """Verify UniversalIngestionService rejects documents exceeding MAX_DOCUMENT_SIZE_BYTES."""
    service = UniversalIngestionService()
    oversized_bytes = b"X" * (MAX_DOCUMENT_SIZE_BYTES + 1024)

    with pytest.raises(ValueError) as exc_info:
        await service.parse_document(oversized_bytes, "large_file.txt")

    assert "exceeds maximum allowed size limit" in str(exc_info.value)
    assert "25" in str(exc_info.value)


@pytest.mark.asyncio
async def test_universal_ingestion_service_valid_doc():
    """Verify UniversalIngestionService parses normal documents within the 25 MB limit."""
    service = UniversalIngestionService()
    normal_bytes = b"ASEP Universal Knowledge Engine Text Content."
    result = await service.parse_document(normal_bytes, "valid_sample.txt")
    assert "ASEP Universal Knowledge Engine" in result


@pytest.mark.asyncio
async def test_ingestion_service_file_size_check(tmp_path):
    """Verify IngestionService.ingest_document enforces max_size_bytes on disk files."""
    test_file = tmp_path / "oversized.txt"
    test_file.write_bytes(b"A" * 1024)

    mock_graph = MagicMock()
    mock_vector = MagicMock()
    mock_embed = MagicMock()
    service = IngestionService(
        graph_service=mock_graph,
        vector_service=mock_vector,
        embedding_provider=mock_embed,
    )

    with pytest.raises(ValueError) as exc_info:
        await service.ingest_document(str(test_file), max_size_bytes=512)

    assert "exceeds maximum allowed size limit" in str(exc_info.value)


@pytest.mark.asyncio
async def test_upload_document_api_rejects_oversized():
    """Verify POST /api/v1/upload/document returns HTTP 413 for files > 25 MB."""
    app = create_app()
    mock_user = MagicMock()
    mock_user.id = "test_user_id"
    mock_user.email = "test@asep.ai"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    fake_file_content = b"0" * (MAX_DOCUMENT_SIZE_BYTES + 100)
    files = {"file": ("big_manual.pdf", io.BytesIO(fake_file_content), "application/pdf")}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/upload/document", files=files)

    assert response.status_code == 413
    data = response.json()
    assert "detail" in data
    assert "exceeds maximum allowed size limit of 25.0 MB" in data["detail"]


@pytest.mark.asyncio
async def test_upload_document_api_accepts_valid_file():
    """Verify POST /api/v1/upload/document successfully accepts and indexes valid file."""
    app = create_app()
    mock_user = MagicMock()
    mock_user.id = "test_user_id"
    mock_user.email = "test@asep.ai"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    valid_content = b"# Introduction to Autonomous Software Engineering\nASEP platform specification."
    files = {"file": ("spec.txt", io.BytesIO(valid_content), "text/plain")}

    with patch("src.api.routers.knowledge.upload_to_cloudinary", return_value="https://cdn.cloudinary.com/test/spec.txt"), \
         patch("src.graph.get_neo4j_driver", return_value=MagicMock()), \
         patch("src.vector.qdrant.get_qdrant_client", return_value=MagicMock()), \
         patch("src.documents.ingestion.IngestionService.ingest_document", return_value=MagicMock()):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/api/v1/upload/document", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ingested"
    assert data["filename"] == "spec.txt"
    assert "document_id" in data
