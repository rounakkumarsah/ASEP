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
from httpx import ASGITransport, AsyncClient

from src.api.app import create_app


@pytest.fixture
def app():
    """Return a freshly created FastAPI test application."""
    return create_app()


@pytest.fixture
def client(app):
    """Synchronous test client (for simple endpoint tests)."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client(app):
    """Async HTTPX client for async endpoint tests."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

import socket

def is_db_running():
    try:
        # Check if we can connect to the postgres port
        with socket.create_connection(("localhost", 5440), timeout=1):
            return True
    except OSError:
        return False

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark test as requiring live database"
    )

def pytest_collection_modifyitems(config, items):
    db_running = is_db_running()
    skipped_count = 0
    skip_db = pytest.mark.skip(reason="integration tests skipped (no DB)")
    
    for item in items:
        # If the test is in the integration directory or marked as integration
        if "integration" in str(item.fspath) or item.get_closest_marker("integration"):
            if not db_running:
                item.add_marker(skip_db)
                skipped_count += 1
                
    if skipped_count > 0:
        config.stash["skipped_integration_count"] = skipped_count

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    skipped_count = config.stash.get("skipped_integration_count", 0)
    if skipped_count > 0:
        terminalreporter.write_line(f"\\n{skipped_count} integration tests skipped (no DB)", yellow=True)
