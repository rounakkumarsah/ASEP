"""
ASEP — Procedural Memory (PostgreSQL + Neo4j Backends)
"""

import json
import uuid
from decimal import Decimal
from typing import Any

from src.db.models.memory_entry import MemoryEntry, MemoryType
from src.graph.graph_service import GraphService
from src.unit_of_work.sqlalchemy import SQLAlchemyUnitOfWork


class ProceduralMemory:
    """Manages workflows, standard operating procedures, and tool usage sequences."""

    def __init__(self, uow: SQLAlchemyUnitOfWork, graph_service: GraphService) -> None:
        self.uow = uow
        self.graph = graph_service

    async def add_procedure(
        self,
        name: str,
        steps: list[str],
        namespace: str = "default",
        metadata: dict[str, Any] | None = None
    ) -> MemoryEntry:
        """Register a procedure in Postgres and optional dependency node in Neo4j."""
        content = json.dumps({"name": name, "steps": steps})
        
        async with self.uow:
            entry = MemoryEntry(
                memory_type=MemoryType.PROCEDURAL,
                content=content,
                namespace=namespace,
                importance_score=Decimal("0.800"),  # Default high importance for procedures
                entry_metadata=metadata or {},
            )
            created = await self.uow.memory_entries.create(entry)
            await self.uow.commit()
            
            # Neo4j: Write Procedure metadata node
            query = """
            MERGE (p:Procedure {id: $id})
            SET p.name = $name, p.steps = $steps
            RETURN p
            """
            await self.graph.execute_write(
                query,
                {"id": str(created.id), "name": name, "steps": steps}
            )
            
            return created

    async def get_procedure_by_id(self, procedure_id: uuid.UUID) -> MemoryEntry | None:
        """Retrieve a specific procedure by identifier."""
        async with self.uow:
            return await self.uow.memory_entries.get_or_none(procedure_id)
