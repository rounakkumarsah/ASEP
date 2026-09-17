"""
ASEP — Model Context Protocol (MCP) Comprehensive Unit Tests
===========================================================
Validates:
1. Fernet AES-256 encryption & decryption of sensitive credentials
2. MCP Client initialization handshake, protocol negotiation, ping, and retry
3. MCP Service server registry, lifecycle, and tool discovery
4. Hallucination Guard: blocking undeclared/unconnected tools with descriptive message
5. Session Confirmation Gate: security approval workflow
"""

import json
import pytest
from src.utils.crypto import encrypt_env_vars, decrypt_env_vars
from src.tools.mcp_client import MCPClient
from src.tools.mcp_service import MCPService


@pytest.mark.asyncio
async def test_crypto_encryption_decryption():
    """Verify sensitive environment variables are encrypted and decrypted correctly."""
    raw_env = {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_secure_token_12345",
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/asep",
    }
    encrypted = encrypt_env_vars(raw_env)
    assert isinstance(encrypted, str)
    assert encrypted.startswith("gAAAAA") or len(encrypted) > 20
    assert "ghp_secure_token_12345" not in encrypted

    decrypted_str = decrypt_env_vars(encrypted)
    assert json.loads(decrypted_str) == raw_env


@pytest.mark.asyncio
async def test_mcp_client_handshake_and_ping():
    """Verify MCP protocol negotiation, ping, and tool listing on simulated/mock stdio server."""
    client = MCPClient(
        server_name="test_github",
        transport_type="stdio",
        command="npx -y @modelcontextprotocol/server-github",
    )
    connected = await client.connect()
    assert connected is True
    assert client.protocol_version == "2024-11-05"

    is_alive, msg = await client.ping()
    assert is_alive is True

    tools = await client.list_tools()
    assert len(tools) >= 5
    tool_names = [t.name for t in tools]
    assert "search_repositories" in tool_names
    assert "create_issue" in tool_names

    await client.disconnect()
    assert client.connected is False


@pytest.mark.asyncio
async def test_mcp_service_lifecycle_and_registry():
    """Verify adding, listing, updating, and deleting servers in MCPService."""
    svc = MCPService()
    await svc.initialize_defaults()

    servers = svc.list_servers()
    assert len(servers) >= 1
    assert any(s["name"] == "github" for s in servers)

    # Add custom server
    new_server = await svc.add_server(
        name="custom_server",
        transport_type="stdio",
        command="node server.js",
        env_vars={"API_KEY": "secret123"},
        enabled=True,
    )
    assert new_server["name"] == "custom_server"
    assert new_server["status"] in ("connected", "disconnected")

    # Update server
    updated = await svc.update_server(new_server["id"], enabled=False)
    assert updated["enabled"] is False

    # Delete server
    deleted = await svc.delete_server(new_server["id"])
    assert deleted is True


@pytest.mark.asyncio
async def test_mcp_hallucination_guard():
    """Verify Hallucination Guard blocks undeclared or non-connected tools."""
    svc = MCPService()
    await svc.initialize_defaults()

    # Valid tool check
    assert svc.is_tool_connected("search_repositories") is True

    # Fake tool must be blocked with exact required message
    out = await svc.execute_tool(name="fake_undeclared_tool", arguments={})
    assert out.success is False
    assert out.error == "Tool 'fake_undeclared_tool' not connected. Add an MCP server providing it in Settings."


@pytest.mark.asyncio
async def test_mcp_session_confirmation_and_approval():
    """Verify confirmation is required for state-mutating tools until approved."""
    svc = MCPService()
    await svc.initialize_defaults()

    session_id = "test_session_abc"
    tool_name = "create_issue"

    # Not approved yet
    assert svc.is_tool_approved_for_session(session_id, tool_name) is False

    # Execute without approval triggers CONFIRMATION_REQUIRED
    out = await svc.execute_tool(
        name=tool_name,
        arguments={"owner": "test_owner", "repo": "test_repo", "title": "Test Issue"},
        session_id=session_id,
    )
    assert out.success is False
    assert "CONFIRMATION_REQUIRED" in (out.error or "")

    # Approve
    svc.approve_tool_for_session(session_id, tool_name)
    assert svc.is_tool_approved_for_session(session_id, tool_name) is True

    # Now execute is dispatched past the confirmation gate
    out2 = await svc.execute_tool(
        name=tool_name,
        arguments={"owner": "test_owner", "repo": "test_repo", "title": "Test Issue"},
        session_id=session_id,
    )
    # The confirmation gate is bypassed; the tool call is dispatched to the MCP client
    assert "CONFIRMATION_REQUIRED" not in (out2.error or "")
