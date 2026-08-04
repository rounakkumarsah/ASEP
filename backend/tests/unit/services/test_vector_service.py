"""
ASEP — Unit Tests for VectorService
===================================
Uses mock Qdrant clients to verify that the service layer correctly forwards
operations to the official SDK and correctly formats records.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock
from qdrant_client.http.models import Distance, UpdateStatus, UpdateResult
from src.vector.vector_service import VectorService
from src.vector.models import VectorRecord


@pytest.mark.asyncio
async def test_vector_service_create_collection():
    mock_client = AsyncMock()
    mock_client.collection_exists.return_value = False
    mock_client.create_collection.return_value = True

    service = VectorService(client=mock_client)
    res = await service.create_collection(
        collection_name="test_collection",
        vector_size=1536,
        distance=Distance.COSINE
    )

    assert res is True
    mock_client.collection_exists.assert_called_once_with(collection_name="test_collection")
    mock_client.create_collection.assert_called_once()


@pytest.mark.asyncio
async def test_vector_service_create_collection_already_exists():
    mock_client = AsyncMock()
    mock_client.collection_exists.return_value = True

    service = VectorService(client=mock_client)
    res = await service.create_collection(collection_name="test_collection")

    assert res is False
    mock_client.create_collection.assert_not_called()


@pytest.mark.asyncio
async def test_vector_service_delete_collection():
    mock_client = AsyncMock()
    mock_client.collection_exists.return_value = True
    mock_client.delete_collection.return_value = True

    service = VectorService(client=mock_client)
    res = await service.delete_collection("test_collection")

    assert res is True
    mock_client.delete_collection.assert_called_once_with(collection_name="test_collection")


@pytest.mark.asyncio
async def test_vector_service_delete_collection_not_found():
    mock_client = AsyncMock()
    mock_client.collection_exists.return_value = False

    service = VectorService(client=mock_client)
    res = await service.delete_collection("test_collection")

    assert res is False
    mock_client.delete_collection.assert_not_called()


@pytest.mark.asyncio
async def test_vector_service_upsert_documents():
    mock_client = AsyncMock()
    
    # Mock update result
    mock_result = MagicMock()
    mock_result.status = MagicMock()
    mock_result.status.name = "COMPLETED"
    mock_client.upsert.return_value = mock_result

    service = VectorService(client=mock_client)
    records = [
        VectorRecord(
            id="point-1",
            vector=[0.1, 0.2, 0.3],
            payload={"text": "hello"}
        )
    ]
    res = await service.upsert_documents("test_collection", records)

    assert res is True
    mock_client.upsert.assert_called_once()


@pytest.mark.asyncio
async def test_vector_service_search():
    mock_client = AsyncMock()
    
    # Mock query_points response (Qdrant v1.7+)
    mock_hit = MagicMock()
    mock_hit.id = "point-1"
    mock_hit.score = 0.95
    mock_hit.payload = {"text": "hello"}
    mock_hit.version = 1
    
    mock_response = MagicMock()
    mock_response.points = [mock_hit]
    mock_client.query_points.return_value = mock_response

    service = VectorService(client=mock_client)
    results = await service.search(
        collection_name="test_collection",
        query_vector=[0.1, 0.2, 0.3],
        limit=5,
        payload_filters={"key": "val"},
        score_threshold=0.8
    )

    assert len(results) == 1
    assert results[0].id == "point-1"
    assert results[0].score == 0.95
    assert results[0].payload == {"text": "hello"}
    mock_client.query_points.assert_called_once()



@pytest.mark.asyncio
async def test_vector_service_delete_points():
    mock_client = AsyncMock()
    mock_result = MagicMock()
    mock_result.status = MagicMock()
    mock_result.status.name = "COMPLETED"
    mock_client.delete.return_value = mock_result

    service = VectorService(client=mock_client)
    res = await service.delete_points("test_collection", ["point-1"])

    assert res is True
    mock_client.delete.assert_called_once()


@pytest.mark.asyncio
async def test_vector_service_health_check_healthy():
    mock_client = AsyncMock()
    mock_client.get_collections.return_value = MagicMock()

    service = VectorService(client=mock_client)
    res = await service.health_check()

    assert res is True
    mock_client.get_collections.assert_called_once()


@pytest.mark.asyncio
async def test_vector_service_health_check_unhealthy():
    mock_client = AsyncMock()
    mock_client.get_collections.side_effect = Exception("connection failed")

    service = VectorService(client=mock_client)
    res = await service.health_check()

    assert res is False
