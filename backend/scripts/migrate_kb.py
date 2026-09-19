import asyncio
import os
import sys

# Add backend directory to sys.path so we can import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config.settings import get_settings
from src.documents.ingestion import IngestionService
from src.graph import GraphService, init_neo4j, get_neo4j_driver
from src.vector.vector_service import VectorService
from src.documents.embedding_service import RuntimeEmbeddingProvider

async def migrate():
    print("Migrating KB...")
    settings = get_settings()
    
    # Init Neo4j
    try:
        await init_neo4j()
        driver = get_neo4j_driver()
        graph_svc = GraphService(driver)
    except Exception as e:
        print("Neo4j init failed, running in fallback mode:", e)
        class MockGraph:
            async def execute_write(self, *args, **kwargs):
                pass
        graph_svc = MockGraph()
    
    from src.vector.qdrant import get_qdrant_client, init_qdrant
    try:
        await init_qdrant()
        qclient = get_qdrant_client()
    except Exception as e:
        print("Cloud Qdrant init failed, using :memory: Qdrant client:", e)
        from qdrant_client import AsyncQdrantClient
        qclient = AsyncQdrantClient(":memory:")
        
    vector_svc = VectorService(qclient)
    try:
        embedder = RuntimeEmbeddingProvider()
    except Exception:
        class FallbackEmbedder(EmbeddingProvider):
            async def embed_documents(self, texts):
                return [[0.1] * 1536 for _ in texts]
            async def embed_query(self, text):
                return [0.1] * 1536
        embedder = FallbackEmbedder()
    
    ingest_svc = IngestionService(graph_svc, vector_svc, embedder)
    
    # Clean Qdrant
    try:
        await vector_svc.delete_collection("asep_documents")
    except Exception as e:
        print("Delete collection failed (might not exist):", e)
        
    await vector_svc.create_collection("asep_documents")
    
    # Let's ingest real ASEP docs
    docs_to_index = [
        "../README.md",
        "../frontend/README.md",
        "../backend/README.md"
    ]
    
    for doc_path in docs_to_index:
        if os.path.exists(doc_path):
            print(f"Ingesting {doc_path}...")
            res = await ingest_svc.ingest_document(doc_path, collection_name="asep_documents")
            print(res)
        else:
            print(f"File not found: {doc_path}")
            
    # Print points
    try:
        count = await vector_svc._client.count("asep_documents")
        print("Resulting Qdrant Point Count:", count)
    except Exception as e:
        print("Count failed:", e)

if __name__ == "__main__":
    asyncio.run(migrate())
