import pytest
from fastapi import FastAPI, Response
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from src.api.middleware.license_guard import LicenseGuardMiddleware, is_path_exempt


def test_is_path_exempt():
    assert is_path_exempt("/api/v1/health") is True
    assert is_path_exempt("/api/v1/health/ready") is True
    assert is_path_exempt("/health") is True
    assert is_path_exempt("/ready") is True
    assert is_path_exempt("/docs") is True
    assert is_path_exempt("/redoc") is True
    assert is_path_exempt("/openapi.json") is True
    assert is_path_exempt("/api/v1/docs") is True
    assert is_path_exempt("/api/v1/openapi.json") is True
    assert is_path_exempt("/favicon.ico") is True
    assert is_path_exempt("/static/bundle.js") is True
    assert is_path_exempt("/assets/style.css") is True
    assert is_path_exempt("/index.html") is True
    assert is_path_exempt("/api/v1/auth/login") is True
    assert is_path_exempt("/api/v1/auth/callback") is True

    # Non-exempt paths
    assert is_path_exempt("/api/v1/terminal/execute") is False
    assert is_path_exempt("/api/v1/workflows") is False
    assert is_path_exempt("/api/v1/sandbox/start") is False
    assert is_path_exempt("/api/v1/conversations/run") is False

    # Security: Path traversal attacks must NOT bypass license checks
    assert is_path_exempt("/api/v1/health/../terminal/execute") is False
    assert is_path_exempt("/api/v1/health/%2e%2e/terminal/execute") is False
    assert is_path_exempt("/static/../api/v1/terminal/execute") is False
    assert is_path_exempt("/docs/../api/v1/workflows") is False

    # Security: Static extensions on API routes must NOT bypass license checks
    assert is_path_exempt("/api/v1/terminal/execute.js") is False
    assert is_path_exempt("/api/v1/workflows/export.html") is False



def test_license_guard_middleware_allows_whitelisted():
    app = FastAPI()
    app.add_middleware(LicenseGuardMiddleware)

    @app.get("/api/v1/health")
    def health():
        return {"status": "ok"}

    client = TestClient(app)
    # Even if license is invalid, whitelisted paths must return 200
    with patch("src.licensing.license_manager.LicenseManager.is_licensed", return_value=False):
        r = client.get("/api/v1/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


def test_license_guard_middleware_blocks_unlicensed():
    app = FastAPI()
    app.add_middleware(LicenseGuardMiddleware)

    @app.post("/api/v1/protected/action")
    def protected():
        return {"result": "success"}

    client = TestClient(app)
    with patch("src.licensing.license_manager.LicenseManager.is_licensed", return_value=False):
        r = client.post("/api/v1/protected/action")
        assert r.status_code == 402
        assert r.json() == {"detail": "License required. Set ASEP_LICENSE_KEY in .env."}


def test_license_guard_middleware_allows_licensed():
    app = FastAPI()
    app.add_middleware(LicenseGuardMiddleware)

    @app.post("/api/v1/protected/action")
    def protected():
        return {"result": "success"}

    client = TestClient(app)
    with patch("src.licensing.license_manager.LicenseManager.is_licensed", return_value=True):
        r = client.post("/api/v1/protected/action")
        assert r.status_code == 200
        assert r.json() == {"result": "success"}


def test_license_guard_middleware_disabled_by_config():
    app = FastAPI()
    app.add_middleware(LicenseGuardMiddleware)

    @app.post("/api/v1/protected/action")
    def protected():
        return {"result": "success"}

    client = TestClient(app)
    with patch.dict("os.environ", {"ENABLE_LICENSE_MIDDLEWARE": "false"}):
        with patch("src.licensing.license_manager.LicenseManager.is_licensed", return_value=False):
            r = client.post("/api/v1/protected/action")
            assert r.status_code == 200
            assert r.json() == {"result": "success"}
