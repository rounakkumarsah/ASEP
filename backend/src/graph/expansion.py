"""
ASEP — Graph Expansion Engine
===============================
Provides multi-hop graph traversal, neighbor expansion, community graph exploration,
and cost/depth safety bounding for Hybrid GraphRAG.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from src.graph.graph_service import GraphService

logger = logging.getLogger(__name__)


@dataclass
class GraphExpansionConfig:
    max_depth: int = 3
    max_nodes_per_hop: int = 25
    total_node_limit: int = 150
    relationship_types: Optional[List[str]] = None


@dataclass
class ExpandedGraphNode:
    node_id: str
    labels: List[str]
    properties: Dict[str, Any]
    depth: int
    parent_id: Optional[str] = None
    relationship: Optional[str] = None


class GraphExpansionEngine:
    """Multi-hop graph traversal and context expansion engine."""

    def __init__(
        self,
        graph_service: GraphService,
        config: Optional[GraphExpansionConfig] = None,
    ) -> None:
        self.graph = graph_service
        self.config = config or GraphExpansionConfig()

    async def expand_multi_hop(
        self,
        seed_node_ids: List[str],
        depth: Optional[int] = None,
    ) -> List[ExpandedGraphNode]:
        """Perform multi-hop BFS traversal from seed nodes up to max_depth."""
        if not seed_node_ids:
            return []

        target_depth = min(depth or self.config.max_depth, self.config.max_depth)
        visited_ids: Set[str] = set(seed_node_ids)
        expanded_nodes: List[ExpandedGraphNode] = []
        current_layer = seed_node_ids

        for current_depth in range(1, target_depth + 1):
            if not current_layer or len(expanded_nodes) >= self.config.total_node_limit:
                break

            cypher = """
            MATCH (n)-[r]-(neighbor)
            WHERE n.id IN $node_ids OR elementId(n) IN $node_ids
            RETURN n.id AS source_id, type(r) as rel_type, neighbor.id AS target_id,
                   labels(neighbor) AS labels, properties(neighbor) AS props
            LIMIT $limit
            """
            try:
                result = await self.graph.execute_read(
                    cypher,
                    {
                        "node_ids": current_layer,
                        "limit": self.config.max_nodes_per_hop * len(current_layer),
                    },
                )
            except Exception as exc:
                logger.warning("Graph multi-hop Cypher error at depth %d: %s", current_depth, exc)
                break

            next_layer: List[str] = []
            for rec in result.records:
                target_id = rec.get("target_id") or rec.get("source_id", "")
                if not target_id or target_id in visited_ids:
                    continue

                visited_ids.add(target_id)
                next_layer.append(target_id)

                expanded_nodes.append(
                    ExpandedGraphNode(
                        node_id=target_id,
                        labels=rec.get("labels", []),
                        properties=rec.get("props", {}),
                        depth=current_depth,
                        parent_id=rec.get("source_id"),
                        relationship=rec.get("rel_type"),
                    )
                )

                if len(expanded_nodes) >= self.config.total_node_limit:
                    break

            current_layer = next_layer

        return expanded_nodes

    async def expand_neighbors(self, node_id: str, limit: int = 20) -> List[ExpandedGraphNode]:
        """Perform 1-hop immediate neighbor expansion."""
        return await self.expand_multi_hop([node_id], depth=1)

    async def expand_community(self, community_id: str) -> List[ExpandedGraphNode]:
        """Traverse all nodes belonging to a designated community cluster."""
        cypher = """
        MATCH (n)
        WHERE n.community_id = $community_id OR n.community = $community_id
        RETURN n.id AS target_id, labels(n) AS labels, properties(n) AS props
        LIMIT $limit
        """
        try:
            res = await self.graph.execute_read(cypher, {"community_id": community_id, "limit": self.config.total_node_limit})
            return [
                ExpandedGraphNode(
                    node_id=r.get("target_id", ""),
                    labels=r.get("labels", []),
                    properties=r.get("props", {}),
                    depth=1,
                )
                for r in res.records
            ]
        except Exception as exc:
            logger.warning("Community traversal failed for '%s': %s", community_id, exc)
            return []
