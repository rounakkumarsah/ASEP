import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

class TestObservability:
    def test_diagnostics_endpoint(self, client: TestClient) -> None:
        response = client.get("/diagnostics")
        assert response.status_code == 200
        data = response.json()
        assert "build_version" in data
        assert "git_commit" in data
        assert "environment" in data
        assert "uptime_seconds" in data
        assert "runtime" in data

    def test_metrics_json_endpoint(self, client: TestClient) -> None:
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "requests_total" in data
        assert "request_latency_sum" in data
        assert "errors_total" in data
        assert "active_sessions" in data
        assert "pending_tasks" in data

    def test_metrics_prometheus_format(self, client: TestClient) -> None:
        response = client.get("/metrics", headers={"Accept": "text/plain"})
        assert response.status_code == 200
        assert "asep_requests_total" in response.text
        assert "asep_active_sessions" in response.text

    def test_correlation_id_middleware(self, client: TestClient) -> None:
        response = client.get("/health", headers={"X-Correlation-ID": "test-correlation-123"})
        assert response.status_code == 200
        assert response.headers.get("X-Correlation-ID") == "test-correlation-123"
        assert response.headers.get("X-Request-ID") is not None
