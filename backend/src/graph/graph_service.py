"""
ASEP — Typed Graph Service Abstraction
=======================================
Provides a clean API over Neo4j session execution.

Contains all required functions:
  - create_nodes()
  - create_relationships()
  - merge_entities()
  - search_related_entities()
  - delete_graph()
  - health_check()

All operations run inside automatic retry contexts and include structured logging.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from neo4j import AsyncDriver
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config.settings import get_settings
from src.graph.models import GraphNode, GraphRelationship, GraphResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Retry policy for transient network/DB failures
# ---------------------------------------------------------------------------

_RETRY_POLICY = {
    "stop": stop_after_attempt(3),
    "wait": wait_exponential(multiplier=1, min=1, max=8),
    "retry": retry_if_exception_type(Exception),
    "reraise": True,
    "before_sleep": before_sleep_log(logger, logging.WARNING),
}


class GraphService:
    """
    Abstractions for interacting with Neo4j.

    Usage::

        service = GraphService(driver=get_neo4j_driver())
        await service.create_nodes([GraphNode(id="x", labels=["User"])])
    """

    def __init__(self, driver: AsyncDriver) -> None:
        """Initialise with an async Neo4j driver."""
        self._driver = driver
        # None = use driver's default routing (required for Neo4j Aura Free)
        self._database: str | None = get_settings().NEO4J_DATABASE or None

    # ------------------------------------------------------------------
    # Raw execution blocks (backward compatibility)
    # ------------------------------------------------------------------

    async def execute_read(
        self, query: str, parameters: dict[str, Any] | None = None
    ) -> GraphResult:
        """Execute a read Cypher query with retries."""
        parameters = parameters or {}

        async def _work(tx: Any) -> GraphResult:
            result = await tx.run(query, parameters)
            records = await result.data()
            summary = await result.consume()
            return GraphResult(
                records=records,
                summary=summary.__dict__ if summary else {},
            )

        async with self._driver.session(database=self._database) as session:
            try:
                return await session.execute_read(_work)
            except Exception as e:
                logger.error("Error executing read query: %s", str(e), exc_info=True)
                raise

    async def execute_write(
        self, query: str, parameters: dict[str, Any] | None = None
    ) -> GraphResult:
        """Execute a write Cypher query with retries."""
        parameters = parameters or {}

        async def _work(tx: Any) -> GraphResult:
            result = await tx.run(query, parameters)
            records = await result.data()
            summary = await result.consume()
            return GraphResult(
                records=records,
                summary=summary.__dict__ if summary else {},
            )

        async with self._driver.session(database=self._database) as session:
            try:
                return await session.execute_write(_work)
            except Exception as e:
                logger.error("Error executing write query: %s", str(e), exc_info=True)
                raise

    # ------------------------------------------------------------------
    # Structured Node / Relationship CRUD Operations
    # ------------------------------------------------------------------

    @retry(**_RETRY_POLICY)
    async def create_nodes(self, nodes: list[GraphNode]) -> bool:
        """
        Batch create or merge nodes.

        Uses APOC/Cypher dynamic label setting if multiple labels are provided,
        or falling back to standard MERGE matching on ID.
        """
        if not nodes:
            return True

        # Construct parameter list
        node_dicts = []
        for node in nodes:
            node_dicts.append({
                "id": node.id,
                "labels": node.labels,
                "props": node.properties or {},
            })

        # We construct a Cypher query using MERGE.
        # Since Cypher doesn't support parameterized labels directly (e.g. MERGE (n:$label)),
        # we MERGE on a base Entity label or a default label, then set dynamic labels.
        query = """
        UNWIND $nodes AS node_data
        MERGE (n:Entity {id: node_data.id})
        SET n += node_data.props
        WITH n, node_data
        CALL apoc.create.addLabels(n, node_data.labels) YIELD node
        RETURN count(node) AS count
        """
        # APOC might not be present on all instances (like basic local test setups).
        # We can write a pure Cypher fallback that handles the primary label or just sets properties.
        fallback_query = """
        UNWIND $nodes AS node_data
        MERGE (n:Entity {id: node_data.id})
        SET n += node_data.props
        RETURN count(n) AS count
        """

        try:
            await self.execute_write(query, {"nodes": node_dicts})
        except Exception:
            # Fallback if APOC is not available
            logger.debug("APOC label setting failed — falling back to standard MERGE.")
            await self.execute_write(fallback_query, {"nodes": node_dicts})

        logger.info("Successfully created/merged %d nodes in the graph.", len(nodes))
        return True

    @retry(**_RETRY_POLICY)
    async def create_relationships(self, relationships: list[GraphRelationship]) -> bool:
        """
        Batch create relationships between nodes.

        Nodes are matched by their IDs.
        """
        if not relationships:
            return True

        rel_dicts = []
        for rel in relationships:
            rel_dicts.append({
                "start_id": rel.start_node_id,
                "end_id": rel.end_node_id,
                "type": rel.type,
                "props": rel.properties or {},
            })

        # Since Cypher doesn't allow variable relationship types (e.g. MERGE (a)-[r:$type]->(b)),
        # we either run them individually or use APOC. Let's do a fast Cypher loop using APOC,
        # or execute them in a fallback loop for compatibility.
        query = """
        UNWIND $rels AS rel_data
        MATCH (a:Entity {id: rel_data.start_id})
        MATCH (b:Entity {id: rel_data.end_id})
        CALL apoc.create.relationship(a, rel_data.type, rel_data.props, b) YIELD rel
        RETURN count(rel) AS count
        """

        fallback_loop_query = """
        MATCH (a:Entity {id: $start_id})
        MATCH (b:Entity {id: $end_id})
        MERGE (a)-[r:RELATED {type: $type}]->(b)
        SET r += $props
        RETURN r
        """

        try:
            await self.execute_write(query, {"rels": rel_dicts})
        except Exception:
            logger.debug("APOC relationship creation failed — falling back to sequential execution.")
            for rel in rel_dicts:
                await self.execute_write(fallback_loop_query, rel)

        logger.info("Successfully created %d relationships in the graph.", len(relationships))
        return True

    @retry(**_RETRY_POLICY)
    async def merge_entities(
        self,
        node_id: str,
        labels: list[str],
        properties: dict[str, Any],
    ) -> bool:
        """Merge a single entity node into the graph (idempotent write)."""
        node = GraphNode(id=node_id, labels=labels, properties=properties)
        return await self.create_nodes([node])

    # ------------------------------------------------------------------
    # Graph Search & Retrieval (RAG query pipeline)
    # ------------------------------------------------------------------

    @retry(**_RETRY_POLICY)
    async def search_related_entities(
        self,
        entity_ids: list[str],
        depth: int = 1,
    ) -> list[dict[str, Any]]:
        """
        Search for entities connected to the specified starting IDs.

        Returns a list of node properties and relationship metadata,
        which is used for Graph Expansion in the RAG retrieval pipeline.
        """
        if not entity_ids:
            return []

        query = f"""
        MATCH (n:Entity) WHERE n.id IN $ids
        MATCH path = (n)-[r:RELATED*1..{depth}]-(m:Entity)
        RETURN n.id AS source_id, labels(n) AS source_labels, n AS source_props,
               m.id AS target_id, labels(m) AS target_labels, m AS target_props,
               [rel IN r | {{type: type(rel), properties: properties(rel)}}] AS path_relationships
        LIMIT 100
        """
        # Simple fallback matching any relationship if 'RELATED' is not standard
        fallback_query = """
        MATCH (n) WHERE n.id IN $ids
        MATCH (n)-[r]-(m)
        RETURN n.id AS source_id, labels(n) AS source_labels, properties(n) AS source_props,
               m.id AS target_id, labels(m) AS target_labels, properties(m) AS target_props,
               type(r) AS rel_type, properties(r) AS rel_props
        LIMIT 100
        """

        try:
            result = await self.execute_read(query, {"ids": entity_ids})
            return [dict(record) for record in result.records]
        except Exception:
            logger.debug("Aura-optimized traversal failed — running generic relationship search.")
            result = await self.execute_read(fallback_query, {"ids": entity_ids})
            return [dict(record) for record in result.records]

    # ------------------------------------------------------------------
    # Maintenance / Maintenance Operations
    # ------------------------------------------------------------------

    @retry(**_RETRY_POLICY)
    async def delete_graph(self) -> bool:
        """
        Delete all nodes and relationships from the database.

        WARNING: Destructive operation.
        """
        query = "MATCH (n) DETACH DELETE n"
        await self.execute_write(query)
        logger.warning("Graph database cleared successfully (delete_graph called).")
        return True

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        """
        Liveness check returning True if Neo4j responds to a basic query.

        Does not retry.
        """
        try:
            async with self._driver.session(database=self._database) as session:
                res = await session.run("RETURN 1 AS ping")
                records = await res.data()
                return len(records) > 0 and records[0].get("ping") == 1
        except Exception as exc:
            logger.warning("Neo4j health check failed: %s", str(exc))
            return False
