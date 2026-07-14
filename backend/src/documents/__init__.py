"""
ASEP — Documents Ingestion Package
"""

from src.documents.chunking import RecursiveCharacterTextSplitter
from src.documents.embedding_service import (
    EmbeddingProvider,
    OpenAICompatibleEmbeddingProvider,
)
from src.documents.health import embedding_health_check
from src.documents.ingestion import IngestionService
from src.documents.loaders import (
    BaseLoader,
    DOCXLoader,
    PDFLoader,
    TextLoader,
    get_loader_for_file,
)
from src.documents.metadata import extract_file_metadata

__all__ = [
    "RecursiveCharacterTextSplitter",
    "EmbeddingProvider",
    "OpenAICompatibleEmbeddingProvider",
    "embedding_health_check",
    "IngestionService",
    "BaseLoader",
    "DOCXLoader",
    "PDFLoader",
    "TextLoader",
    "get_loader_for_file",
    "extract_file_metadata",
]
