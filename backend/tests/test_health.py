"""
ASEP — Health Endpoint Tests
==============================
Verifies health and readiness endpoints work correctly.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient


class TestHealthEndpoint:
    """Tests for the GET /health liveness probe."""

    def test_health_returns_200(self, client: TestClient) -> None:
        """Health endpoint must return HTTP 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_schema(self, client: TestClient) -> None:
        """Health endpoint must return the expected JSON schema."""
        response = client.get("/health")
        data = response.json()

        assert data["status"] == "ok"
        assert data["service"] == "ASEP"
        assert "version" in data
        assert "uptime_seconds" in data
        assert "environment" in data
        assert "python_version" in data

    def test_health_uptime_is_positive(self, client: TestClient) -> None:
        """Reported uptime must be a positive float."""
        response = client.get("/health")
        data = response.json()
        assert data["uptime_seconds"] >= 0.0

    def test_health_python_version_is_valid(self, client: TestClient) -> None:
        """Python version should match expected format."""
        response = client.get("/health")
        data = response.json()
        # Should be something like "3.12.0"
        assert "." in data["python_version"]


class TestReadinessEndpoint:
    """Tests for the GET /ready readiness probe."""

    def test_ready_returns_200(self, client: TestClient) -> None:
        """Readiness endpoint must return HTTP 200."""
        response = client.get("/ready")
        assert response.status_code == 200

    def test_ready_response_schema(self, client: TestClient) -> None:
        """Readiness endpoint must return the expected JSON schema."""
        response = client.get("/ready")
        data = response.json()

        assert "status" in data
        assert data["status"] in ["ready", "degraded", "not_ready"]
        assert "dependencies" in data
        assert isinstance(data["dependencies"], list)

    def test_ready_includes_postgres_dependency(self, client: TestClient) -> None:
        """Readiness response must include PostgreSQL dependency status."""
        response = client.get("/ready")
        data = response.json()

        postgres_dep = next((d for d in data["dependencies"] if d["name"] == "postgres"), None)
        assert postgres_dep is not None
        assert "status" in postgres_dep
        assert postgres_dep["status"] in ["ok", "degraded", "unavailable", "unknown"]

    def test_ready_postgres_status_ok(self, client: TestClient) -> None:
        """PostgreSQL should be marked as 'ok' when database is reachable."""
        response = client.get("/ready")
        data = response.json()

        postgres_dep = next((d for d in data["dependencies"] if d["name"] == "postgres"), None)
        assert postgres_dep is not None
        assert postgres_dep["status"] == "ok"
        assert "detail" in postgres_dep
        assert postgres_dep["latency_ms"] is not None

    def test_ready_postgres_has_latency(self, client: TestClient) -> None:
        """PostgreSQL dependency should include latency measurement."""
        response = client.get("/ready")
        data = response.json()

        postgres_dep = next((d for d in data["dependencies"] if d["name"] == "postgres"), None)
        assert postgres_dep is not None
        assert postgres_dep["latency_ms"] > 0

    def test_ready_overall_status_ready_when_all_ok(self, client: TestClient) -> None:
        """Overall status should be 'ready' when all dependencies are 'ok'."""
        response = client.get("/ready")
        data = response.json()

        all_ok = all(d["status"] == "ok" for d in data["dependencies"])
        if all_ok:
            assert data["status"] == "ready"


@pytest.mark.asyncio
class TestHealthEndpointAsync:
    """Async tests for health endpoints."""

    async def test_health_endpoint_async(self, async_client: AsyncClient) -> None:
        """Health endpoint should work with async client."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    async def test_ready_endpoint_async(self, async_client: AsyncClient) -> None:
        """Readiness endpoint should work with async client."""
        response = await async_client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ready", "degraded", "not_ready"]


class TestReadinessEndpoint:
    """Tests for the GET /ready endpoint."""

    def test_ready_returns_200(self, client: TestClient) -> None:
        """Ready endpoint must return HTTP 200."""
        response = client.get("/ready")
        assert response.status_code == 200

    def test_ready_has_dependencies_list(self, client: TestClient) -> None:
        """Ready response must include a dependencies list."""
        response = client.get("/ready")
        data = response.json()
        assert "dependencies" in data
        assert isinstance(data["dependencies"], list)
        assert len(data["dependencies"]) > 0

    def test_ready_dependencies_have_name_and_status(self, client: TestClient) -> None:
        """Each dependency entry must have name and status fields."""
        response = client.get("/ready")
        deps = response.json()["dependencies"]
        for dep in deps:
            assert "name" in dep
            assert "status" in dep
