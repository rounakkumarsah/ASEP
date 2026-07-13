"""
ASEP Backend — Test Suite
==========================
Pytest root conftest: shared fixtures and async event loop configuration.
"""

from __future__ import annotations

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
