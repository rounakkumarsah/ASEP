"""
ASEP — Document Ingestion Service
"""

import logging
import uuid
from typing import Any

from src.documents.chunking import RecursiveCharacterTextSplitter
from src.documents.embedding_service import EmbeddingProvider
from src.documents.loaders import get_loader_for_file
from src.documents.metadata import extract_file_metadata
from src.graph import GraphService
from src.graph.queries import CREATE_CHUNK_QUERY, CREATE_DOCUMENT_QUERY, LINK_CHUNK_TO_DOCUMENT_QUERY
from src.vector import VectorService, VectorRecord
from src.vector.collections import DEFAULT_COLLECTION

logger = logging.getLogger(__name__)


class IngestionService:
    """Orchestrates document parsing, chunking, embedding, and storage across Graph and Vector DBs."""

    def __init__(
        self,
        graph_service: GraphService,
        vector_service: VectorService,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.graph = graph_service
        self.vector = vector_service
        self.embedder = embedding_provider

    async def ingest_document(
        self,
        file_path: str,
        collection_name: str = DEFAULT_COLLECTION,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> dict[str, Any]:
        """Ingests a document from disk into Neo4j and Qdrant.
        
        Returns:
            Ingestion summary with document metadata and processing details.
        """
        logger.info(f"Starting ingestion for: {file_path}")
        
        # 1. Parse document content
        loader = get_loader_for_file(file_path)
        content = loader.load(file_path)
        
        # 2. Extract document-level metadata
        doc_metadata = extract_file_metadata(file_path, content)
        doc_id = str(uuid.uuid4())
        doc_metadata["id"] = doc_id
        
        # 3. Perform recursive character text splitting
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunk_texts = splitter.split_text(content)
        
        if not chunk_texts:
            logger.warning(f"No chunks extracted from document: {file_path}")
            return {"document_id": doc_id, "chunks_ingested": 0, "metadata": doc_metadata}

        logger.info(f"Splitting generated {len(chunk_texts)} chunks for {file_path}")
        
        # 4. Batch generate embeddings for all chunks
        embeddings = await self.embedder.embed_documents(chunk_texts)
        
        # 5. Insert Document Node into Neo4j
        await self.graph.execute_write(
            CREATE_DOCUMENT_QUERY,
            {"doc_id": doc_id, "properties": doc_metadata}
        )
        
        vector_records: list[VectorRecord] = []
        
        # 6. Symmetrically write Chunks and Relationships to Neo4j & prepare Qdrant records
        for i, (text, vector) in enumerate(zip(chunk_texts, embeddings)):
            chunk_id = str(uuid.uuid4())
            chunk_metadata = {
                "id": chunk_id,
                "document_id": doc_id,
                "index": i,
                "text": text,
                "char_length": len(text),
                "word_count": len(text.split()),
                # Preserve parent metadata context
                "file_name": doc_metadata["file_name"],
                "file_type": doc_metadata["file_type"],
            }
            
            # Neo4j: Write chunk node
            await self.graph.execute_write(
                CREATE_CHUNK_QUERY,
                {"chunk_id": chunk_id, "properties": chunk_metadata}
            )
            
            # Neo4j: Link chunk to parent document
            await self.graph.execute_write(
                LINK_CHUNK_TO_DOCUMENT_QUERY,
                {"doc_id": doc_id, "chunk_id": chunk_id, "index": i}
            )
            
            # Qdrant payload: we keep text and relevant document keys
            vector_records.append(
                VectorRecord(
                    id=chunk_id,
                    vector=vector,
                    payload={
                        "text": text,
                        "document_id": doc_id,
                        "chunk_index": i,
                        "file_name": doc_metadata["file_name"],
                    }
                )
            )
            
        # 7. Upsert all embeddings in batch to Qdrant
        await self.vector.batch_upsert(collection_name, vector_records)
        
        logger.info(f"Ingestion completed successfully for '{file_path}'. Chunks: {len(chunk_texts)}")
        return {
            "document_id": doc_id,
            "chunks_ingested": len(chunk_texts),
            "metadata": doc_metadata
        }
