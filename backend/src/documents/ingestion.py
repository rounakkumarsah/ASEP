from __future__ import annotations
import logging
import uuid
import time
from typing import Any, Dict, List, Optional
from src.documents.chunking import ChunkingEngine
from src.documents.embedding_service import EmbeddingProvider
from src.documents.loaders import get_loader_for_file
from src.documents.metadata import extract_file_metadata, compute_hash, DocumentMetadata, ChunkRecord
from src.graph import GraphService
from src.graph.queries import CREATE_CHUNK_QUERY, CREATE_DOCUMENT_QUERY, LINK_CHUNK_TO_DOCUMENT_QUERY
from src.vector import VectorService, VectorRecord
from src.vector.collections import DEFAULT_COLLECTION

logger = logging.getLogger(__name__)

class IngestionService:
    """Orchestrates document parsing, chunking, embedding, and storage across Graph and Vector DBs."""

    # Thread-safe/process-safe placeholders for incremental caches
    _embedding_cache: Dict[str, List[float]] = {}
    _ingested_documents: Dict[str, str] = {}  # file_path -> content_hash

    def __init__(
        self,
        graph_service: GraphService,
        vector_service: VectorService,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.graph = graph_service
        self.vector = vector_service
        self.embedder = embedding_provider
        self.chunker = ChunkingEngine()

    async def ingest_document(
        self,
        file_path: str,
        collection_name: str = DEFAULT_COLLECTION,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
    ) -> Dict[str, Any]:
        """Ingests a document from disk into Neo4j and Qdrant with change detection.
        
        Returns:
            Ingestion summary with document metadata and processing details.
        """
        logger.info(f"Starting ingestion for: {file_path}")
        
        # 1. Parse document content
        loader = get_loader_for_file(file_path)
        content = loader.load(file_path)
        
        # 2. Incremental Indexing Check
        doc_hash = compute_hash(content)
        if self._ingested_documents.get(file_path) == doc_hash:
            logger.info(f"Document already ingested and unchanged: {file_path}. Skipping.")
            return {
                "document_id": "cached",
                "chunks_ingested": 0,
                "status": "unchanged"
            }
            
        self._ingested_documents[file_path] = doc_hash
        
        # 3. Extract document-level metadata
        doc_metadata = extract_file_metadata(file_path, content)
        doc_id = compute_hash(file_path + "_" + doc_hash)[:16]
        doc_metadata["id"] = doc_id
        
        # 4. Generate hierarchical parent-child ChunkRecords
        chunk_records = self.chunker.chunk_document(
            document_id=doc_id,
            content=content,
            filename=doc_metadata["file_name"],
            file_path=file_path,
            collection=collection_name,
        )
        
        if not chunk_records:
            logger.warning(f"No chunks extracted from document: {file_path}")
            return {"document_id": doc_id, "chunks_ingested": 0, "metadata": doc_metadata}

        logger.info(f"Splitting generated {len(chunk_records)} chunks for {file_path}")
        
        # 5. Embedding Generation with Caching
        embeddings: List[List[float]] = []
        texts_to_embed: List[str] = []
        texts_indices: List[int] = []
        
        for idx, chunk in enumerate(chunk_records):
            # Check embedding cache
            cached_vec = self._embedding_cache.get(chunk.content_hash)
            if cached_vec is not None:
                embeddings.append(cached_vec)
            else:
                # Placeholder space to insert once computed
                embeddings.append([])
                texts_to_embed.append(chunk.content)
                texts_indices.append(idx)
                
        if texts_to_embed:
            new_embeddings = await self.embedder.embed_documents(texts_to_embed)
            for relative_idx, real_idx in enumerate(texts_indices):
                vec = new_embeddings[relative_idx]
                embeddings[real_idx] = vec
                # Cache embedding
                self._embedding_cache[chunk_records[real_idx].content_hash] = vec

        # 6. Insert Document Node into Neo4j
        await self.graph.execute_write(
            CREATE_DOCUMENT_QUERY,
            {"doc_id": doc_id, "properties": doc_metadata}
        )
        
        vector_records: List[VectorRecord] = []
        
        # 7. Symmetrically write Chunks and Relationships to Neo4j & prepare Qdrant records
        for i, (chunk, vector) in enumerate(zip(chunk_records, embeddings)):
            chunk_metadata_dict = chunk.metadata.dict()
            chunk_metadata_dict["id"] = chunk.chunk_id
            chunk_metadata_dict["parent_id"] = chunk.parent_id
            chunk_metadata_dict["text"] = chunk.content
            chunk_metadata_dict["content_hash"] = chunk.content_hash
            
            # Neo4j: Write chunk node
            await self.graph.execute_write(
                CREATE_CHUNK_QUERY,
                {"chunk_id": chunk.chunk_id, "properties": chunk_metadata_dict}
            )
            
            # Neo4j: Link chunk to parent document
            await self.graph.execute_write(
                LINK_CHUNK_TO_DOCUMENT_QUERY,
                {"doc_id": doc_id, "chunk_id": chunk.chunk_id, "index": i}
            )
            
            # Qdrant payload preserving full metadata fields
            vector_records.append(
                VectorRecord(
                    id=chunk.chunk_id,
                    vector=vector,
                    payload={
                        "text": chunk.content,
                        "document_id": doc_id,
                        "parent_id": chunk.parent_id,
                        "chunk_index": i,
                        "filename": chunk.metadata.filename,
                        "file_path": chunk.metadata.file_path,
                        "collection": chunk.metadata.collection,
                        "source": chunk.metadata.source,
                        "version": chunk.metadata.version,
                    }
                )
            )
            
        # 8. Upsert all embeddings in batch to Qdrant
        await self.vector.batch_upsert(collection_name, vector_records)
        
        logger.info(f"Ingestion completed successfully for '{file_path}'. Chunks: {len(chunk_records)}")
        return {
            "document_id": doc_id,
            "chunks_ingested": len(chunk_records),
            "metadata": doc_metadata,
            "status": "ingested"
        }
