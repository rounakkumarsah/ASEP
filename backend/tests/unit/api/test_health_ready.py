import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routers.health_ready import router


@pytest.fixture
def health_ready_app():
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return app


def test_health_ready_all_ok(health_ready_app):
    client = TestClient(health_ready_app)
    with patch("src.api.routers.health_ready.check_db_health", new_callable=AsyncMock, return_value=(True, "ok", 1.0)), \
         patch("src.api.routers.health_ready.qdrant_health_check", new_callable=AsyncMock, return_value=True), \
         patch("src.api.routers.health_ready.neo4j_health_check", new_callable=AsyncMock, return_value=True), \
         patch("src.licensing.license_manager.LicenseManager.is_licensed", return_value=True):
        r = client.get("/api/v1/health/ready")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ready"
        assert data["checks"]["postgres"] is True
        assert data["checks"]["qdrant"] is True
        assert data["checks"]["neo4j"] is True
        assert data["checks"]["license"] is True


def test_health_ready_db_down(health_ready_app):
    client = TestClient(health_ready_app)
    with patch("src.api.routers.health_ready.check_db_health", new_callable=AsyncMock, return_value=(False, "down", None)), \
         patch("src.api.routers.health_ready.qdrant_health_check", new_callable=AsyncMock, return_value=True), \
         patch("src.api.routers.health_ready.neo4j_health_check", new_callable=AsyncMock, return_value=True), \
         patch("src.licensing.license_manager.LicenseManager.is_licensed", return_value=True):
        r = client.get("/api/v1/health/ready")
        assert r.status_code == 503
        data = r.json()
        assert data["status"] == "not_ready"
        assert data["checks"]["postgres"] is False
        assert data["checks"]["qdrant"] is True


def test_health_ready_qdrant_down(health_ready_app):
    client = TestClient(health_ready_app)
    with patch("src.api.routers.health_ready.check_db_health", new_callable=AsyncMock, return_value=(True, "ok", 1.0)), \
         patch("src.api.routers.health_ready.qdrant_health_check", new_callable=AsyncMock, return_value=False), \
         patch("src.api.routers.health_ready.neo4j_health_check", new_callable=AsyncMock, return_value=True), \
         patch("src.licensing.license_manager.LicenseManager.is_licensed", return_value=True):
        r = client.get("/api/v1/health/ready")
        assert r.status_code == 503
        data = r.json()
        assert data["status"] == "not_ready"
        assert data["checks"]["qdrant"] is False


def test_health_ready_neo4j_down(health_ready_app):
    client = TestClient(health_ready_app)
    with patch("src.api.routers.health_ready.check_db_health", new_callable=AsyncMock, return_value=(True, "ok", 1.0)), \
         patch("src.api.routers.health_ready.qdrant_health_check", new_callable=AsyncMock, return_value=True), \
         patch("src.api.routers.health_ready.neo4j_health_check", new_callable=AsyncMock, return_value=False), \
         patch("src.licensing.license_manager.LicenseManager.is_licensed", return_value=True):
        r = client.get("/api/v1/health/ready")
        assert r.status_code == 503
        data = r.json()
        assert data["status"] == "not_ready"
        assert data["checks"]["neo4j"] is False


def test_health_ready_license_disabled_by_config(health_ready_app):
    client = TestClient(health_ready_app)
    with patch("src.api.routers.health_ready.check_db_health", new_callable=AsyncMock, return_value=(True, "ok", 1.0)), \
         patch("src.api.routers.health_ready.qdrant_health_check", new_callable=AsyncMock, return_value=True), \
         patch("src.api.routers.health_ready.neo4j_health_check", new_callable=AsyncMock, return_value=True), \
         patch.dict("os.environ", {"ENABLE_LICENSE_MIDDLEWARE": "false"}), \
         patch("src.licensing.license_manager.LicenseManager.is_licensed", return_value=False):
        r = client.get("/api/v1/health/ready")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ready"
        assert data["checks"]["license"] is True
