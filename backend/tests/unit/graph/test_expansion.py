"""
ASEP — Unit Tests for Graph Expansion Engine
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.graph.expansion import GraphExpansionConfig, GraphExpansionEngine
from src.graph.models import GraphResult


@pytest.mark.asyncio
async def test_graph_expansion_multi_hop():
    mock_graph = AsyncMock()
    mock_graph.execute_read.return_value = GraphResult(
        records=[
            {
                "source_id": "chunk-1",
                "rel_type": "CONNECTED_TO",
                "target_id": "entity-1",
                "labels": ["Entity"],
                "props": {"name": "GraphRAG"},
            }
        ],
        summary={},
    )

    engine = GraphExpansionEngine(mock_graph, GraphExpansionConfig(max_depth=1))
    nodes = await engine.expand_multi_hop(["chunk-1"])

    assert len(nodes) == 1
    assert nodes[0].node_id == "entity-1"
    assert nodes[0].relationship == "CONNECTED_TO"
    mock_graph.execute_read.assert_called_once()



@pytest.mark.asyncio
async def test_graph_expansion_empty_seeds():
    mock_graph = AsyncMock()
    engine = GraphExpansionEngine(mock_graph)

    nodes = await engine.expand_multi_hop([])
    assert nodes == []
    mock_graph.execute_read.assert_not_called()
