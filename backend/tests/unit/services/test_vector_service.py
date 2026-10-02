"""
ASEP — Unit Tests for VectorService
===================================
Uses mock Qdrant clients to verify that the service layer correctly forwards
operations to the official SDK and correctly formats records.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from qdrant_client.http.models import Distance

from src.vector.models import VectorRecord
from src.vector.vector_service import VectorService


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


def test_normalize_qdrant_url_cloud_cases():
    from src.vector.qdrant import _normalize_qdrant_url

    # Cloud URL with port 6333 stripped
    raw = "https://a8697179-1b71-4269-89ce-13bd8a9626e2.ca-central-1-0.aws.cloud.qdrant.io:6333"
    assert _normalize_qdrant_url(raw) == "https://a8697179-1b71-4269-89ce-13bd8a9626e2.ca-central-1-0.aws.cloud.qdrant.io"

    # Cloud URL without scheme
    raw2 = "a8697179-1b71-4269-89ce-13bd8a9626e2.ca-central-1-0.aws.cloud.qdrant.io:6333/"
    assert _normalize_qdrant_url(raw2) == "https://a8697179-1b71-4269-89ce-13bd8a9626e2.ca-central-1-0.aws.cloud.qdrant.io"

    # Cloud URL with http upgraded to https
    raw3 = "http://a8697179-1b71-4269-89ce-13bd8a9626e2.ca-central-1-0.aws.cloud.qdrant.io"
    assert _normalize_qdrant_url(raw3) == "https://a8697179-1b71-4269-89ce-13bd8a9626e2.ca-central-1-0.aws.cloud.qdrant.io"

    # Local URL kept intact
    raw_local = "http://localhost:6333"
    assert _normalize_qdrant_url(raw_local) == "http://localhost:6333"

    # Bare local host gets http://
    assert _normalize_qdrant_url("localhost:6333") == "http://localhost:6333"


def test_get_qdrant_client_lazy_instantiation(monkeypatch):
    import src.vector.qdrant as qdrant_mod
    monkeypatch.setattr(qdrant_mod, "_qdrant_client", None)

    client = qdrant_mod.get_qdrant_client()
    assert client is not None
    assert qdrant_mod._qdrant_client is client

