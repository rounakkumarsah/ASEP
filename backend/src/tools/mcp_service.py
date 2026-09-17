"""
ASEP — Model Context Protocol (MCP) Service & Unified Registry
==============================================================
Manages workspace-scoped MCP servers, connection lifecycle, tool discovery,
hallucination guard enforcement, security confirmations, and audit logging.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from src.tools.mcp_client import MCPClient
from src.tools.metadata import ToolMetadata
from src.tools.schemas import ToolExecutionOutput
from src.utils.crypto import decrypt_env_vars, encrypt_env_vars

logger = logging.getLogger(__name__)


class MCPService:
    """Central singleton managing all MCP servers, client connections,
    session approvals, and tool registry validation.
    """

    def __init__(self) -> None:
        # In-memory server configs: {server_id: dict}
        self._servers: dict[str, dict[str, Any]] = {}
        # Active connected clients: {server_id: MCPClient}
        self._clients: dict[str, MCPClient] = {}
        # Session approvals: {session_id: set(tool_names)}
        self._session_approvals: dict[str, set[str]] = {}
        self._initialized = False

    async def initialize_defaults(self) -> None:
        """Initialize default MCP configurations on workspace load."""
        if self._initialized:
            return
        self._initialized = True

        # Pre-configure official GitHub MCP server as an available default if not present
        github_id = "srv_github_default"
        if github_id not in self._servers:
            self._servers[github_id] = {
                "id": github_id,
                "project_id": None,
                "name": "github",
                "transport_type": "stdio",
                "command": "npx -y @modelcontextprotocol/server-github",
                "url": None,
                "env_vars": encrypt_env_vars({"GITHUB_PERSONAL_ACCESS_TOKEN": ""}),
                "enabled": True,
                "status": "connected",
                "error_message": None,
            }
            client = MCPClient(
                server_name="github",
                transport_type="stdio",
                command="npx -y @modelcontextprotocol/server-github",
            )
            await client.connect_with_retry(max_attempts=1)
            self._clients[github_id] = client

        logger.info("MCPService initialized with %d servers", len(self._servers))

    def list_servers(self, project_id: str | None = None) -> list[dict[str, Any]]:
        """List configured servers for workspace/project."""
        res = []
        for srv in self._servers.values():
            if project_id and srv.get("project_id") and str(srv.get("project_id")) != str(project_id):
                continue

            srv_copy = dict(srv)
            client = self._clients.get(srv["id"])
            if client:
                srv_copy["status"] = "connected" if client.connected else "error"
                srv_copy["error_message"] = client.last_error
            # Do NOT expose raw/encrypted env vars to UI list
            srv_copy.pop("env_vars", None)
            # Attach tools
            srv_copy["tools"] = [
                {
                    "name": t.name,
                    "description": t.description,
                    "category": t.category,
                    "input_schema": t.input_schema,
                    "requires_confirmation": t.requires_confirmation,
                    "source": f"via MCP: {srv['name']}",
                }
                for t in (client._tools_cache if client else [])
            ]
            res.append(srv_copy)
        return res

    async def add_server(
        self,
        name: str,
        transport_type: str,
        command: str | None = None,
        url: str | None = None,
        env_vars: dict[str, str] | str | None = None,
        project_id: str | None = None,
        enabled: bool = True,
    ) -> dict[str, Any]:
        """Add and initialize a new MCP server."""
        server_id = f"mcp_{uuid.uuid4().hex[:12]}"
        
        # Parse & encrypt env vars
        parsed_env: dict[str, str] = {}
        if isinstance(env_vars, dict):
            parsed_env = env_vars
        elif isinstance(env_vars, str) and env_vars.strip():
            try:
                parsed_env = json.loads(env_vars)
            except Exception:
                for line in env_vars.splitlines():
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        parsed_env[k.strip()] = v.strip()

        encrypted_env = encrypt_env_vars(parsed_env)

        server_entry = {
            "id": server_id,
            "project_id": project_id,
            "name": name.strip(),
            "transport_type": transport_type.lower(),
            "command": command.strip() if command else None,
            "url": url.strip() if url else None,
            "env_vars": encrypted_env,
            "enabled": enabled,
            "status": "disconnected",
            "error_message": None,
        }
        self._servers[server_id] = server_entry

        if enabled:
            client = MCPClient(
                server_name=name,
                transport_type=transport_type,
                command=command,
                server_url=url,
                env_vars=parsed_env,
            )
            connected = await client.connect_with_retry(max_attempts=3)
            self._clients[server_id] = client
            server_entry["status"] = "connected" if connected else "error"
            server_entry["error_message"] = client.last_error

        return server_entry

    async def update_server(
        self,
        server_id: str,
        enabled: bool | None = None,
        command: str | None = None,
        url: str | None = None,
        env_vars: dict[str, str] | str | None = None,
    ) -> dict[str, Any]:
        """Update server configuration and reconnect if necessary."""
        if server_id not in self._servers:
            raise KeyError(f"MCP Server '{server_id}' not found.")

        srv = self._servers[server_id]
        if enabled is not None:
            srv["enabled"] = enabled

        if command is not None:
            srv["command"] = command.strip()
        if url is not None:
            srv["url"] = url.strip()

        parsed_env: dict[str, str] | None = None
        if env_vars is not None:
            if isinstance(env_vars, dict):
                parsed_env = env_vars
            elif isinstance(env_vars, str):
                try:
                    parsed_env = json.loads(env_vars)
                except Exception:
                    parsed_env = {}
                    for line in env_vars.splitlines():
                        if "=" in line:
                            k, v = line.split("=", 1)
                            parsed_env[k.strip()] = v.strip()
            srv["env_vars"] = encrypt_env_vars(parsed_env)

        # Handle client reconnect
        client = self._clients.get(server_id)
        if not srv["enabled"]:
            if client:
                await client.disconnect()
                srv["status"] = "disconnected"
        else:
            decrypted_str = decrypt_env_vars(srv.get("env_vars"))
            env_map = json.loads(decrypted_str) if decrypted_str else {}
            client = MCPClient(
                server_name=srv["name"],
                transport_type=srv["transport_type"],
                command=srv["command"],
                server_url=srv["url"],
                env_vars=env_map,
            )
            connected = await client.connect_with_retry(max_attempts=3)
            self._clients[server_id] = client
            srv["status"] = "connected" if connected else "error"
            srv["error_message"] = client.last_error

        return srv

    async def delete_server(self, server_id: str) -> bool:
        """Disconnect and delete an MCP server."""
        client = self._clients.pop(server_id, None)
        if client:
            await client.disconnect()
        return self._servers.pop(server_id, None) is not None

    async def test_server_connection(
        self,
        name: str,
        transport_type: str,
        command: str | None = None,
        url: str | None = None,
        env_vars: dict[str, str] | str | None = None,
    ) -> dict[str, Any]:
        """Test connection handshake and list discovered tools without saving."""
        parsed_env = {}
        if isinstance(env_vars, dict):
            parsed_env = env_vars
        elif isinstance(env_vars, str) and env_vars.strip():
            try:
                parsed_env = json.loads(env_vars)
            except Exception:
                for line in env_vars.splitlines():
                    if "=" in line:
                        k, v = line.split("=", 1)
                        parsed_env[k.strip()] = v.strip()

        client = MCPClient(
            server_name=name,
            transport_type=transport_type,
            command=command,
            server_url=url,
            env_vars=parsed_env,
        )
        try:
            connected = await client.connect_with_retry(max_attempts=2)
            tools = await client.list_tools() if connected else []
            return {
                "success": connected,
                "status": "connected" if connected else "error",
                "error": client.last_error,
                "server_info": client.server_info,
                "tools_count": len(tools),
                "tools": [
                    {
                        "name": t.name,
                        "description": t.description,
                        "input_schema": t.input_schema,
                        "source": f"via MCP: {name}",
                    }
                    for t in tools
                ],
            }
        finally:
            await client.disconnect()

    async def ping_all_servers(self) -> dict[str, dict[str, Any]]:
        """Ping all configured servers and return live statuses."""
        res = {}
        for server_id, client in self._clients.items():
            ok, msg = await client.ping()
            res[server_id] = {"connected": ok, "status": "connected" if ok else "error", "message": msg}
        return res

    def get_all_active_tools(self) -> list[dict[str, Any]]:
        """Collect all declared tools across all currently connected MCP servers."""
        tools_list: list[dict[str, Any]] = []
        for server_id, client in self._clients.items():
            srv = self._servers.get(server_id, {})
            if not srv.get("enabled", True) or not client.connected:
                continue

            for t in client._tools_cache:
                tools_list.append({
                    "name": t.name,
                    "description": t.description,
                    "category": t.category,
                    "input_schema": t.input_schema,
                    "requires_confirmation": t.requires_confirmation,
                    "server_id": server_id,
                    "server_name": client.server_name,
                    "source": f"via MCP: {client.server_name}",
                })
        return tools_list

    def is_tool_connected(self, tool_name: str) -> bool:
        """Check if a tool exists in any active, connected MCP server."""
        for client in self._clients.values():
            if client.connected:
                if any(t.name == tool_name for t in client._tools_cache):
                    return True
        return False

    def get_server_for_tool(self, tool_name: str) -> MCPClient | None:
        """Find the client instance responsible for a given tool."""
        for client in self._clients.values():
            if client.connected:
                if any(t.name == tool_name for t in client._tools_cache):
                    return client
        return None

    def is_tool_approved_for_session(self, session_id: str, tool_name: str) -> bool:
        """Check if user approved this tool for the session."""
        approved = self._session_approvals.get(session_id, set())
        return tool_name in approved

    def approve_tool_for_session(self, session_id: str, tool_name: str) -> None:
        """Record human approval for an MCP tool in the session."""
        if session_id not in self._session_approvals:
            self._session_approvals[session_id] = set()
        self._session_approvals[session_id].add(tool_name)

    async def execute_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        session_id: str | None = None,
    ) -> ToolExecutionOutput:
        """Execute an MCP tool with HALLUCINATION GUARD enforcement and session security."""
        # 1. HALLUCINATION GUARD: Validate against live connected tools
        if not self.is_tool_connected(name):
            logger.warning("HALLUCINATION GUARD BLOCKED unavailable tool: '%s'", name)
            return ToolExecutionOutput(
                success=False,
                error=f"Tool '{name}' not connected. Add an MCP server providing it in Settings.",
            )

        client = self.get_server_for_tool(name)
        if not client:
            return ToolExecutionOutput(
                success=False,
                error=f"Tool '{name}' not connected. Add an MCP server providing it in Settings.",
            )

        # 2. Check if tool requires confirmation and hasn't been approved yet
        tool_meta = next((t for t in client._tools_cache if t.name == name), None)
        if tool_meta and tool_meta.requires_confirmation and session_id:
            if not self.is_tool_approved_for_session(session_id, name):
                return ToolExecutionOutput(
                    success=False,
                    error=f"CONFIRMATION_REQUIRED: Permission needed to execute '{name}' via MCP: {client.server_name}.",
                    result={"requires_confirmation": True, "tool": name, "server": client.server_name, "arguments": arguments},
                )

        # 3. Execute tool via MCP client
        output = await client.execute_tool(name, arguments)

        # 4. Audit Logging
        try:
            from src.audit.service import get_audit_service
            from src.db.models.audit_log import ActorType, AuditOutcome, AuditSeverity
            audit = get_audit_service()
            await audit.log_event(
                actor_type=ActorType.AGENT,
                actor_id=session_id or "mcp_agent",
                action=f"mcp.tool_executed.{name}",
                resource_type=f"mcp_server.{client.server_name}",
                resource_id=name,
                outcome=AuditOutcome.SUCCESS if output.success else AuditOutcome.FAILURE,
                severity=AuditSeverity.INFO,
                details={
                    "server": client.server_name,
                    "tool": name,
                    "arguments": arguments,
                    "output_summary": str(output.result)[:200] if output.result else output.error,
                },
            )
        except Exception as exc:
            logger.debug("Audit log for MCP tool skipped: %s", exc)

        return output


_global_mcp_service: MCPService | None = None


def get_mcp_service() -> MCPService:
    """Return the global MCPService singleton."""
    global _global_mcp_service
    if _global_mcp_service is None:
        _global_mcp_service = MCPService()
    return _global_mcp_service
