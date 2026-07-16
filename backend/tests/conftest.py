"""
ASEP Backend — Test Suite
==========================
Pytest root conftest: shared fixtures and async event loop configuration.
"""

from __future__ import annotations

import os

# Override env vars for tests to point to exposed localhost ports instead of docker service names
os.environ["DATABASE_URL"] = "postgresql+asyncpg://asep:changeme@localhost:5440/asep_test"
os.environ["REDIS_URL"] = "redis://localhost:6380/0"
os.environ["QDRANT_URL"] = "http://localhost:6334"
os.environ["APP_ENV"] = "development"

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from src.api.app import create_app


@pytest.fixture(scope="session")
def app():
    """Return a freshly created FastAPI test application."""
    return create_app()


@pytest.fixture(scope="session")
def client(app):
    """Synchronous test client (for simple endpoint tests)."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client(app):
    """Async HTTPX client for async endpoint tests."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
