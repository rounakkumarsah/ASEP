"""
ASEP — Unit Tests for GraphService
==================================
Uses mock Neo4j driver / session to verify query creation, node creation,
relationship creation, custom queries, graph deletions, and health checks.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.graph.graph_service import GraphService
from src.graph.models import GraphNode, GraphRelationship


class MockRecord:
    def __init__(self, data_dict):
        self._data = data_dict

    def data(self):
        return self._data


@pytest.mark.asyncio
async def test_graph_service_create_nodes():
    mock_driver = MagicMock()
    mock_session = AsyncMock()
    mock_driver.session.return_value = mock_session
    mock_session.__aenter__.return_value = mock_session

    # Mock dynamic write transaction work
    async def mock_execute_write(work_func, *args, **kwargs):
        mock_tx = AsyncMock()
        mock_result = AsyncMock()
        mock_result.data.return_value = [{"count": 1}]
        mock_result.consume.return_value = MagicMock()
        mock_tx.run.return_value = mock_result
        return await work_func(mock_tx)

    mock_session.execute_write.side_effect = mock_execute_write

    service = GraphService(driver=mock_driver)
    nodes = [
        GraphNode(id="n1", labels=["User"], properties={"name": "Alice"}),
        GraphNode(id="n2", labels=["User"], properties={"name": "Bob"})
    ]

    res = await service.create_nodes(nodes)
    assert res is True
    mock_session.execute_write.assert_called_once()


@pytest.mark.asyncio
async def test_graph_service_create_relationships():
    mock_driver = MagicMock()
    mock_session = AsyncMock()
    mock_driver.session.return_value = mock_session
    mock_session.__aenter__.return_value = mock_session

    async def mock_execute_write(work_func, *args, **kwargs):
        mock_tx = AsyncMock()
        mock_result = AsyncMock()
        mock_result.data.return_value = [{"count": 1}]
        mock_result.consume.return_value = MagicMock()
        mock_tx.run.return_value = mock_result
        return await work_func(mock_tx)

    mock_session.execute_write.side_effect = mock_execute_write

    service = GraphService(driver=mock_driver)
    rels = [
        GraphRelationship(
            id="r1",
            type="FRIEND",
            start_node_id="n1",
            end_node_id="n2",
            properties={"since": 2026}
        )
    ]

    res = await service.create_relationships(rels)
    assert res is True
    mock_session.execute_write.assert_called_once()


@pytest.mark.asyncio
async def test_graph_service_merge_entities():
    mock_driver = MagicMock()
    mock_session = AsyncMock()
    mock_driver.session.return_value = mock_session
    mock_session.__aenter__.return_value = mock_session

    async def mock_execute_write(work_func, *args, **kwargs):
        mock_tx = AsyncMock()
        mock_result = AsyncMock()
        mock_result.data.return_value = [{"count": 1}]
        mock_result.consume.return_value = MagicMock()
        mock_tx.run.return_value = mock_result
        return await work_func(mock_tx)

    mock_session.execute_write.side_effect = mock_execute_write

    service = GraphService(driver=mock_driver)
    res = await service.merge_entities("n1", ["User"], {"name": "Alice"})
    assert res is True
    mock_session.execute_write.assert_called_once()


@pytest.mark.asyncio
async def test_graph_service_search_related_entities():
    mock_driver = MagicMock()
    mock_session = AsyncMock()
    mock_driver.session.return_value = mock_session
    mock_session.__aenter__.return_value = mock_session

    dummy_records = [
        {
            "source_id": "n1",
            "source_labels": ["User"],
            "source_props": {"name": "Alice"},
            "target_id": "n2",
            "target_labels": ["User"],
            "target_props": {"name": "Bob"},
            "path_relationships": [{"type": "FRIEND", "properties": {"since": 2026}}]
        }
    ]

    async def mock_execute_read(work_func, *args, **kwargs):
        mock_tx = AsyncMock()
        mock_result = AsyncMock()
        mock_result.data.return_value = dummy_records
        mock_result.consume.return_value = MagicMock()
        mock_tx.run.return_value = mock_result
        return await work_func(mock_tx)

    mock_session.execute_read.side_effect = mock_execute_read

    service = GraphService(driver=mock_driver)
    res = await service.search_related_entities(["n1"])
    
    assert len(res) == 1
    assert res[0]["source_id"] == "n1"
    assert res[0]["target_id"] == "n2"
    mock_session.execute_read.assert_called_once()


@pytest.mark.asyncio
async def test_graph_service_delete_graph():
    mock_driver = MagicMock()
    mock_session = AsyncMock()
    mock_driver.session.return_value = mock_session
    mock_session.__aenter__.return_value = mock_session

    async def mock_execute_write(work_func, *args, **kwargs):
        mock_tx = AsyncMock()
        mock_result = AsyncMock()
        mock_result.data.return_value = []
        mock_result.consume.return_value = MagicMock()
        mock_tx.run.return_value = mock_result
        return await work_func(mock_tx)

    mock_session.execute_write.side_effect = mock_execute_write

    service = GraphService(driver=mock_driver)
    res = await service.delete_graph()
    
    assert res is True
    mock_session.execute_write.assert_called_once()


@pytest.mark.asyncio
async def test_graph_service_health_check_healthy():
    mock_driver = MagicMock()
    mock_session = AsyncMock()
    mock_driver.session.return_value = mock_session
    mock_session.__aenter__.return_value = mock_session

    mock_result = AsyncMock()
    mock_result.data.return_value = [{"ping": 1}]
    mock_session.run.return_value = mock_result

    service = GraphService(driver=mock_driver)
    res = await service.health_check()

    assert res is True
    mock_session.run.assert_called_once()


@pytest.mark.asyncio
async def test_graph_service_health_check_unhealthy():
    mock_driver = MagicMock()
    mock_session = AsyncMock()
    mock_driver.session.return_value = mock_session
    mock_session.__aenter__.return_value = mock_session

    mock_session.run.side_effect = Exception("Aura disconnected")

    service = GraphService(driver=mock_driver)
    res = await service.health_check()

    assert res is False
