"""
ASEP — Memory Manager Facade
"""

from src.cache import CacheService
from src.documents.embedding_service import EmbeddingProvider
from src.graph.graph_service import GraphService
from src.memory.consolidation import MemoryConsolidator
from src.memory.episodic import EpisodicMemory
from src.memory.procedural import ProceduralMemory
from src.memory.retrieval import MemoryRetrieval
from src.memory.semantic import SemanticMemory
from src.memory.working import WorkingMemory
from src.unit_of_work.sqlalchemy import SQLAlchemyUnitOfWork
from src.vector import VectorService


class MemoryManager:
    """Facade orchestrating the working, episodic, semantic, and procedural memory submodules."""

    def __init__(
        self,
        uow: SQLAlchemyUnitOfWork,
        cache_service: CacheService,
        vector_service: VectorService,
        graph_service: GraphService,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.working = WorkingMemory(cache_service)
        self.episodic = EpisodicMemory(uow)
        self.semantic = SemanticMemory(
            vector_service=vector_service,
            graph_service=graph_service,
            embedding_provider=embedding_provider,
        )
        self.procedural = ProceduralMemory(uow, graph_service)
        
        self.retrieval = MemoryRetrieval(
            working=self.working,
            episodic=self.episodic,
            semantic=self.semantic,
            procedural=self.procedural,
        )
        
        self.consolidator = MemoryConsolidator(
            working=self.working,
            episodic=self.episodic,
            semantic=self.semantic,
        )
