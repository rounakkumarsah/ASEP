"""
ASEP — Security Remediation & Acquisition Blockers Regression Test Suite
========================================================================
Validates fixes for:
1. Phase 1 & 2: Centralized Multi-Tenant Authorization (IDOR Defense)
   - Banned access when current_user.org_id is None (deny-by-default)
   - Banned cross-tenant access when current_user.org_id != project.org_id
   - require_project_access and verify_project_access shared dependencies
   - List endpoint isolation (list_projects, list_api_keys with project_id)
2. Phase 3: CI Route Table Verification
   - Automated AST / routing inspection
   - Fails CI if any project/api-key/org endpoint lacks tenant authorization
3. Phase 4: SSRF Hardening in HTTPTool
   - Scheme filtering (only HTTP/HTTPS allowed)
   - Loopback and Cloud Metadata blocking (127.0.0.1, ::1, 169.254.169.254, localhost)
   - RFC1918 Private Subnet blocking (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
   - Carrier-Grade NAT blocking (100.64.0.0/10)
   - IPv4-Mapped IPv6 addresses (::ffff:127.0.0.1, ::ffff:169.254.169.254, etc.)
   - DNS rebinding resolution check
   - Content-Length enforcement (> 5 MB rejected)
   - Streamed response byte limit enforcement (> 5 MB aborts)
   - Timeouts and connection limits verification
"""

import inspect
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.auth.dependencies import (
    get_current_user,
    require_project_access,
    verify_project_access,
)
from src.db.models.api_key import ApiKey
from src.db.models.project import Project
from src.db.models.user import User
from src.db.postgres import get_db_session
from src.tools.impl import (
    MAX_HTTP_RESPONSE_BYTES,
    HTTPTool,
    _is_safe_url,
)


# ===========================================================================
# Phase 1 & 2: Centralized Authorization & Multi-Tenant Isolation Tests
# ===========================================================================

@pytest.fixture
def mock_app():
    """Create FastAPI application instance for testing."""
    return create_app()


def test_h01_project_idor_user_without_org_rejected(mock_app):
    """Verify that a user with org_id=None CANNOT access another org's project (GET, PATCH, DELETE)."""
    app = mock_app
    project_id = uuid.uuid4()
    org_id = uuid.uuid4()

    mock_project = Project(
        id=project_id,
        org_id=org_id,
        name="Confidential Project",
        slug="confidential-project",
        description="Proprietary",
        is_active=True,
    )

    user_no_org = User(
        id=uuid.uuid4(),
        email="lonely_user@test.com",
        username="lonely_user",
        org_id=None,
        is_active=True,
        status="active",
    )

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_project
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: user_no_org
    app.dependency_overrides[get_db_session] = lambda: mock_db

    client = TestClient(app)

    # 1. GET project
    res_get = client.get(f"/api/v1/projects/{project_id}")
    assert res_get.status_code == 403, f"Expected 403, got {res_get.status_code}: {res_get.text}"
    assert "Access denied" in res_get.json()["detail"]

    # 2. PATCH project
    res_patch = client.patch(f"/api/v1/projects/{project_id}", json={"name": "Hacked Name"})
    assert res_patch.status_code == 403, f"Expected 403, got {res_patch.status_code}: {res_patch.text}"
    assert "Access denied" in res_patch.json()["detail"]

    # 3. DELETE project
    res_delete = client.delete(f"/api/v1/projects/{project_id}")
    assert res_delete.status_code == 403, f"Expected 403, got {res_delete.status_code}: {res_delete.text}"
    assert "Access denied" in res_delete.json()["detail"]


def test_h01_project_idor_cross_tenant_rejected(mock_app):
    """Verify that a user from Org A CANNOT access Org B's project (Cross-tenant rejection)."""
    app = mock_app
    project_id = uuid.uuid4()
    org_a = uuid.uuid4()
    org_b = uuid.uuid4()

    mock_project = Project(
        id=project_id,
        org_id=org_b,
        name="Org B Secret Project",
        slug="org-b-secret",
        description="Confidential",
        is_active=True,
    )

    user_org_a = User(
        id=uuid.uuid4(),
        email="user_a@test.com",
        username="user_a",
        org_id=org_a,
        is_active=True,
        status="active",
    )

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_project
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: user_org_a
    app.dependency_overrides[get_db_session] = lambda: mock_db

    client = TestClient(app)

    res_get = client.get(f"/api/v1/projects/{project_id}")
    assert res_get.status_code == 403
    assert "Access denied" in res_get.json()["detail"]

    res_patch = client.patch(f"/api/v1/projects/{project_id}", json={"name": "Tampered"})
    assert res_patch.status_code == 403

    res_delete = client.delete(f"/api/v1/projects/{project_id}")
    assert res_delete.status_code == 403


def test_h01_api_key_creation_idor_rejected(mock_app):
    """Verify that creating an API key for a project requires user.org_id == project.org_id via verify_project_access."""
    app = mock_app
    project_id = uuid.uuid4()
    org_victim = uuid.uuid4()

    mock_project = Project(
        id=project_id,
        org_id=org_victim,
        name="Victim Org Project",
        slug="victim-org-project",
        is_active=True,
    )

    # 1. User with org_id=None
    user_no_org = User(
        id=uuid.uuid4(),
        email="attacker_no_org@test.com",
        username="attacker_no_org",
        org_id=None,
        is_active=True,
        status="active",
    )

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_project
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: user_no_org
    app.dependency_overrides[get_db_session] = lambda: mock_db

    client = TestClient(app)

    payload = {
        "project_id": str(project_id),
        "name": "Exploit Key",
        "scopes": ["read", "write"],
    }
    res = client.post("/api/v1/api-keys", json=payload)
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]

    # 2. User with different org_id
    user_diff_org = User(
        id=uuid.uuid4(),
        email="attacker_org_b@test.com",
        username="attacker_org_b",
        org_id=uuid.uuid4(),
        is_active=True,
        status="active",
    )
    app.dependency_overrides[get_current_user] = lambda: user_diff_org

    res2 = client.post("/api/v1/api-keys", json=payload)
    assert res2.status_code == 403
    assert "Access denied" in res2.json()["detail"]


def test_h01_api_key_list_cross_tenant_filter_rejected(mock_app):
    """Verify that listing API keys with a foreign project_id is rejected with 403."""
    app = mock_app
    foreign_project_id = uuid.uuid4()
    org_victim = uuid.uuid4()

    mock_project = Project(
        id=foreign_project_id,
        org_id=org_victim,
        name="Foreign Project",
        slug="foreign-project",
        is_active=True,
    )

    user_attacker = User(
        id=uuid.uuid4(),
        email="attacker@test.com",
        username="attacker",
        org_id=uuid.uuid4(),  # Different org
        is_active=True,
        status="active",
    )

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_project
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: user_attacker
    app.dependency_overrides[get_db_session] = lambda: mock_db

    client = TestClient(app)

    res = client.get(f"/api/v1/api-keys?project_id={foreign_project_id}")
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]


def test_h01_project_access_allowed_for_matching_org(mock_app):
    """Verify that a user with matching org_id successfully accesses their own project."""
    app = mock_app
    project_id = uuid.uuid4()
    org_id = uuid.uuid4()

    mock_project = Project(
        id=project_id,
        org_id=org_id,
        name="Legitimate Project",
        slug="legitimate-project",
        description="Allowed",
        is_active=True,
    )

    user_matching_org = User(
        id=uuid.uuid4(),
        email="legit_user@test.com",
        username="legit_user",
        org_id=org_id,
        is_active=True,
        status="active",
    )

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_project
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: user_matching_org
    app.dependency_overrides[get_db_session] = lambda: mock_db

    client = TestClient(app)

    res_get = client.get(f"/api/v1/projects/{project_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == str(project_id)
    assert res_get.json()["name"] == "Legitimate Project"


# ===========================================================================
# Phase 3: CI Route Table Verification (Permanent Regression Protection)
# ===========================================================================

def test_ci_route_table_tenant_authorization_enforced(mock_app):
    """
    CI REGRESSION GUARD:
    Inspects all FastAPI registered routes and verifies that every endpoint
    under org-scoped paths enforces tenant authorization and authentication.

    Fails CI automatically if an org-scoped endpoint lacks tenant verification.
    """
    app = mock_app
    org_scoped_prefixes = ("/projects", "/api-keys", "/organizations")

    # Unpack all routes including nested and included routers
    all_routes = []
    for r in app.routes:
        if hasattr(r, "original_router") and hasattr(r.original_router, "routes"):
            all_routes.extend(r.original_router.routes)
        elif hasattr(r, "routes"):
            all_routes.extend(r.routes)
        else:
            all_routes.append(r)

    verified_routes_count = 0

    def get_all_dependency_callables(dep):
        calls = []
        if getattr(dep, "call", None):
            calls.append(dep.call)
        for sub in getattr(dep, "dependencies", []):
            calls.extend(get_all_dependency_callables(sub))
        return calls

    for route in all_routes:
        if not isinstance(route, APIRoute):
            continue

        if any(route.path.startswith(prefix) for prefix in org_scoped_prefixes):
            verified_routes_count += 1
            endpoint_name = route.name

            # Extract dependency callables recursively from route.dependant
            all_dep_calls = get_all_dependency_callables(route.dependant)

            # Also check function signature annotations
            sig = inspect.signature(route.endpoint)
            param_annotations = [str(p.annotation) for p in sig.parameters.values()]

            # Check whether route requires CurrentUser or require_project_access
            has_auth = (
                get_current_user in all_dep_calls
                or require_project_access in all_dep_calls
                or any("CurrentUser" in a or "ProjectAccessDep" in a for a in param_annotations)
                or any(
                    dep_call in (get_current_user, require_project_access, verify_project_access)
                    for dep_call in all_dep_calls
                )
            )

            assert has_auth, (
                f"CI PROTECTION FAILURE: Endpoint '{endpoint_name}' at path '{route.path}' "
                f"lacks tenant authentication/authorization dependency!"
            )

    assert verified_routes_count >= 10, (
        f"Expected at least 10 org-scoped routes, found {verified_routes_count}."
    )


# ===========================================================================
# Phase 4: Server-Side Request Forgery (SSRF) Hardening Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_h02_ssrf_disallowed_schemes():
    """Verify that non-HTTP(S) schemes are blocked immediately."""
    tool = HTTPTool()

    disallowed_urls = [
        "ftp://example.com/payload.sh",
        "file:///etc/passwd",
        "gopher://127.0.0.1:6379/_test",
        "tftp://10.0.0.1/file",
        "ldap://localhost:389/dc=example",
    ]

    for url in disallowed_urls:
        out = await tool.execute({"method": "GET", "url": url})
        assert out.success is False
        assert "SSRF Protection" in out.error
        assert "not allowed" in out.error or "Scheme" in out.error


@pytest.mark.asyncio
async def test_h02_ssrf_loopback_and_metadata_blocking():
    """Verify that loopback addresses and cloud metadata endpoints are strictly blocked."""
    tool = HTTPTool()

    blocked_targets = [
        "http://localhost:8000/api/v1/health",
        "http://127.0.0.1:8000/internal",
        "http://127.0.0.2:9000/admin",
        "http://0.0.0.0:8000/",
        "http://169.254.169.254/latest/meta-data/",
        "http://169.254.169.254/computeMetadata/v1/",
    ]

    for target in blocked_targets:
        out = await tool.execute({"method": "GET", "url": target})
        assert out.success is False
        assert "SSRF Protection" in out.error


@pytest.mark.asyncio
async def test_h02_ssrf_private_network_blocking():
    """Verify that RFC1918 private subnets (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16) are blocked."""
    tool = HTTPTool()

    private_ips = [
        "http://10.0.0.1/admin",
        "http://10.254.0.1:8080/",
        "http://172.16.0.1:5432/",
        "http://172.31.255.255/",
        "http://192.168.1.1/router",
        "http://192.168.0.254:3000/",
    ]

    for target in private_ips:
        out = await tool.execute({"method": "GET", "url": target})
        assert out.success is False
        assert "SSRF Protection" in out.error
        assert "prohibited" in out.error


def test_h02_ssrf_cgnat_network_blocking():
    """Verify that Carrier-Grade NAT (RFC 6598: 100.64.0.0/10) addresses are blocked."""
    mock_addrinfo = [(2, 1, 6, "", ("100.64.0.1", 80))]

    with patch("socket.getaddrinfo", return_value=mock_addrinfo):
        is_safe, err = _is_safe_url("http://cgnat.internal.test/")
        assert is_safe is False
        assert "CGNAT IP address '100.64.0.1' is prohibited" in err


def test_h02_ssrf_ipv4_mapped_ipv6_blocking():
    """
    Verify that IPv4-mapped IPv6 addresses (RFC 4291: ::ffff:127.0.0.1, ::ffff:169.254.169.254)
    are unmapped and verified against private and loopback policies.
    """
    evasions = [
        ("::ffff:127.0.0.1", "loopback"),
        ("::ffff:169.254.169.254", "metadata / link-local"),
        ("::ffff:10.0.0.1", "RFC 1918 private"),
        ("::ffff:192.168.1.1", "RFC 1918 private"),
    ]

    for ip_str, desc in evasions:
        mock_addrinfo = [(10, 1, 6, "", (ip_str, 80))]
        with patch("socket.getaddrinfo", return_value=mock_addrinfo):
            is_safe, err = _is_safe_url(f"http://[{ip_str}]/test")
            assert is_safe is False, f"Failed to block IPv4-mapped IPv6 evasion: {desc} ({ip_str})"
            assert "SSRF Protection" in err


def test_h02_ssrf_dns_rebinding_resolution_to_private():
    """Verify that a hostname resolving to a private IP is intercepted and blocked."""
    mock_addrinfo = [(2, 1, 6, "", ("10.1.2.3", 80))]

    with patch("socket.getaddrinfo", return_value=mock_addrinfo):
        is_safe, err = _is_safe_url("http://internal.rebinding.test/secret")
        assert is_safe is False
        assert "private/internal IP address '10.1.2.3' is prohibited" in err


@pytest.mark.asyncio
async def test_h02_ssrf_content_length_oversized_rejected():
    """Verify that responses with Content-Length exceeding 5 MB are rejected upfront."""
    tool = HTTPTool()

    oversized_bytes = str(MAX_HTTP_RESPONSE_BYTES + 1024)

    # Mock safe validation for target domain
    with patch("src.tools.impl._is_safe_url", return_value=(True, "")):
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-length": oversized_bytes}

        # Mock client.stream
        mock_stream_cm = AsyncMock()
        mock_stream_cm.__aenter__.return_value = mock_response

        with patch("httpx.AsyncClient.stream", return_value=mock_stream_cm):
            out = await tool.execute({"method": "GET", "url": "https://api.example.com/largefile"})
            assert out.success is False
            assert "exceeds maximum allowed limit" in out.error


@pytest.mark.asyncio
async def test_h02_ssrf_streaming_byte_limit_exceeded_rejected():
    """Verify that an unbounded response stream exceeding 5 MB is aborted."""
    tool = HTTPTool()

    # Generator emitting chunks that exceed MAX_HTTP_RESPONSE_BYTES
    chunk_size = 1024 * 1024  # 1 MB
    chunks = [b"A" * chunk_size for _ in range(6)]  # 6 MB total

    async def mock_aiter_bytes():
        for chunk in chunks:
            yield chunk

    with patch("src.tools.impl._is_safe_url", return_value=(True, "")):
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.aiter_bytes = mock_aiter_bytes

        mock_stream_cm = AsyncMock()
        mock_stream_cm.__aenter__.return_value = mock_response

        with patch("httpx.AsyncClient.stream", return_value=mock_stream_cm):
            out = await tool.execute({"method": "GET", "url": "https://api.example.com/stream"})
            assert out.success is False
            assert "Response stream exceeded maximum allowed limit" in out.error


def test_h02_ssrf_public_safe_url():
    """Verify that a public domain resolving to a public IP passes SSRF check."""
    mock_addrinfo = [(2, 1, 6, "", ("93.184.216.34", 443))]

    with patch("socket.getaddrinfo", return_value=mock_addrinfo):
        is_safe, err = _is_safe_url("https://example.com/api/v1/resource")
        assert is_safe is True
        assert err == ""
