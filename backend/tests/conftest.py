"""
ASEP Backend — Test Suite
==========================
Pytest root conftest: shared fixtures and async event loop configuration.
"""

from __future__ import annotations

import os

# Override env vars for tests to point to exposed localhost ports instead of docker service names
# os.environ["DATABASE_URL"] = "postgresql+asyncpg://asep:changeme@localhost:5440/asep_test"
# os.environ["REDIS_URL"] = "redis://localhost:6380/0"
# os.environ["QDRANT_URL"] = "http://localhost:6334"
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


@pytest.fixture(autouse=True)
def reset_db_singletons():
    """Reset database and cache singletons to prevent event loop leakage."""
    import src.db.postgres
    import src.cache.redis
    src.db.postgres._engine = None
    src.db.postgres._session_factory = None
    src.cache.redis._redis_client = None
    yield
    src.db.postgres._engine = None
    src.db.postgres._session_factory = None
    src.cache.redis._redis_client = None


@pytest.fixture
async def async_client(app):
    """Async HTTPX client for async endpoint tests."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

import socket

def is_db_running():
    try:
        with socket.create_connection(("localhost", 5432), timeout=0.3):
            return True
    except OSError:
        try:
            with socket.create_connection(("localhost", 5440), timeout=0.3):
                return True
        except OSError:
            return False

def is_redis_running():
    try:
        with socket.create_connection(("localhost", 6379), timeout=0.2):
            return True
    except OSError:
        try:
            with socket.create_connection(("localhost", 6380), timeout=0.2):
                return True
        except OSError:
            return False

def is_qdrant_running():
    try:
        with socket.create_connection(("localhost", 6333), timeout=0.2):
            return True
    except OSError:
        try:
            with socket.create_connection(("localhost", 6334), timeout=0.2):
                return True
        except OSError:
            return False

def is_neo4j_running():
    try:
        with socket.create_connection(("localhost", 7687), timeout=0.2):
            return True
    except OSError:
        return False

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark test as requiring live database or external services"
    )
    config.addinivalue_line(
        "markers", "requires_qdrant: mark test as requiring live Qdrant instance"
    )
    config.addinivalue_line(
        "markers", "requires_redis: mark test as requiring live Redis instance"
    )
    config.addinivalue_line(
        "markers", "requires_neo4j: mark test as requiring live Neo4j instance"
    )

def pytest_collection_modifyitems(config, items):
    db_running = is_db_running()
    redis_running = is_redis_running()
    qdrant_running = is_qdrant_running()
    neo4j_running = is_neo4j_running()

    skip_db = pytest.mark.skip(reason="integration tests skipped (no DB)")
    skip_redis = pytest.mark.skip(reason="skipped (Redis not running)")
    skip_qdrant = pytest.mark.skip(reason="skipped (Qdrant not running)")
    skip_neo4j = pytest.mark.skip(reason="skipped (Neo4j not running)")
    
    skipped_count = 0
    for item in items:
        fspath_str = str(item.fspath).lower()
        name_str = item.name.lower()

        # 1. Qdrant checks
        if item.get_closest_marker("requires_qdrant") or "qdrant" in fspath_str or "qdrant" in name_str:
            if not qdrant_running:
                item.add_marker(skip_qdrant)
                skipped_count += 1
                continue

        # 2. Redis checks
        if item.get_closest_marker("requires_redis") or "redis" in fspath_str or "redis" in name_str:
            if not redis_running:
                item.add_marker(skip_redis)
                skipped_count += 1
                continue

        # 3. Neo4j checks
        if item.get_closest_marker("requires_neo4j") or "neo4j" in fspath_str or "neo4j" in name_str:
            if not neo4j_running:
                item.add_marker(skip_neo4j)
                skipped_count += 1
                continue

        # 4. General DB / integration checks
        if "integration" in fspath_str or item.get_closest_marker("integration"):
            if not db_running:
                item.add_marker(skip_db)
                skipped_count += 1
                continue
                
    if skipped_count > 0:
        config.stash["skipped_integration_count"] = skipped_count

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    skipped_count = config.stash.get("skipped_integration_count", 0)
    if skipped_count > 0:
        terminalreporter.write_line(f"\\n{skipped_count} integration / service tests skipped", yellow=True)
