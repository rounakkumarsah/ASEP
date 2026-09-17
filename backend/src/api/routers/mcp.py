"""
ASEP — Model Context Protocol (MCP) Router
==========================================
FastAPI router providing management endpoints for MCP servers,
health status monitoring, live tool discovery, and tool dispatch.
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.auth.dependencies import CurrentUser
from src.tools.mcp_service import get_mcp_service

router = APIRouter(prefix="/mcp", tags=["Model Context Protocol (MCP)"])


class AddServerRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Server name (e.g. 'github')")
    transport_type: str = Field(default="stdio", description="'stdio' or 'sse'")
    command: str | None = Field(default=None, description="Command string for stdio transport")
    url: str | None = Field(default=None, description="Remote URL for HTTP/SSE transport")
    env_vars: dict[str, str] | str | None = Field(default=None, description="Environment variables or API keys")
    project_id: str | None = Field(default=None, description="Workspace project ID")
    enabled: bool = Field(default=True, description="Initial enabled status")


class TestServerRequest(BaseModel):
    name: str = Field(..., description="Server name")
    transport_type: str = Field(default="stdio", description="'stdio' or 'sse'")
    command: str | None = Field(default=None, description="Command string")
    url: str | None = Field(default=None, description="Remote URL")
    env_vars: dict[str, str] | str | None = Field(default=None, description="Environment variables")


class UpdateServerRequest(BaseModel):
    enabled: bool | None = None
    command: str | None = None
    url: str | None = None
    env_vars: dict[str, str] | str | None = None


class ExecuteToolRequest(BaseModel):
    tool_name: str = Field(..., description="Name of the MCP tool to execute")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Tool input arguments")
    session_id: str | None = Field(default=None, description="Current session/thread ID for confirmation scope")


class ApproveToolRequest(BaseModel):
    session_id: str = Field(..., description="Session ID to approve for")
    tool_name: str = Field(..., description="MCP tool name")


@router.get("/servers", summary="List configured MCP servers for workspace")
async def list_mcp_servers(
    project_id: str | None = Query(None, description="Workspace project ID"),
    current_user: CurrentUser = None,
) -> dict[str, Any]:
    svc = get_mcp_service()
    await svc.initialize_defaults()
    servers = svc.list_servers(project_id=project_id)
    return {"servers": servers, "count": len(servers)}


@router.post("/servers", status_code=status.HTTP_201_CREATED, summary="Add a new MCP server")
async def add_mcp_server(
    payload: AddServerRequest,
    current_user: CurrentUser = None,
) -> dict[str, Any]:
    svc = get_mcp_service()
    await svc.initialize_defaults()
    try:
        server = await svc.add_server(
            name=payload.name,
            transport_type=payload.transport_type,
            command=payload.command,
            url=payload.url,
            env_vars=payload.env_vars,
            project_id=payload.project_id,
            enabled=payload.enabled,
        )
        return {"server": server, "message": f"MCP server '{payload.name}' added successfully."}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/servers/test", summary="Test connection handshake to an MCP server")
async def test_mcp_server(
    payload: TestServerRequest,
    current_user: CurrentUser = None,
) -> dict[str, Any]:
    svc = get_mcp_service()
    result = await svc.test_server_connection(
        name=payload.name,
        transport_type=payload.transport_type,
        command=payload.command,
        url=payload.url,
        env_vars=payload.env_vars,
    )
    return result


@router.patch("/servers/{server_id}", summary="Update or toggle an MCP server")
async def update_mcp_server(
    server_id: str,
    payload: UpdateServerRequest,
    current_user: CurrentUser = None,
) -> dict[str, Any]:
    svc = get_mcp_service()
    try:
        updated = await svc.update_server(
            server_id=server_id,
            enabled=payload.enabled,
            command=payload.command,
            url=payload.url,
            env_vars=payload.env_vars,
        )
        return {"server": updated, "message": "MCP server updated."}
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found.")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/servers/{server_id}", summary="Delete an MCP server")
async def delete_mcp_server(
    server_id: str,
    current_user: CurrentUser = None,
) -> dict[str, Any]:
    svc = get_mcp_service()
    ok = await svc.delete_server(server_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found.")
    return {"message": "MCP server deleted."}


@router.post("/servers/{server_id}/reconnect", summary="Reconnect an MCP server with exponential backoff")
async def reconnect_mcp_server(
    server_id: str,
    current_user: CurrentUser = None,
) -> dict[str, Any]:
    svc = get_mcp_service()
    client = svc._clients.get(server_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active server client not found.")
    ok = await client.connect_with_retry(max_attempts=3)
    return {
        "connected": ok,
        "status": "connected" if ok else "error",
        "error": client.last_error,
        "server_info": client.server_info,
    }


@router.get("/tools", summary="List all declared tools across connected MCP servers")
async def list_mcp_tools(
    current_user: CurrentUser = None,
) -> dict[str, Any]:
    svc = get_mcp_service()
    await svc.initialize_defaults()
    tools = svc.get_all_active_tools()
    return {"tools": tools, "count": len(tools)}


@router.post("/tools/execute", summary="Execute an MCP tool with Hallucination Guard")
async def execute_mcp_tool(
    payload: ExecuteToolRequest,
    current_user: CurrentUser = None,
) -> dict[str, Any]:
    svc = get_mcp_service()
    output = await svc.execute_tool(
        name=payload.tool_name,
        arguments=payload.arguments,
        session_id=payload.session_id,
    )
    if not output.success and output.error and "CONFIRMATION_REQUIRED" in output.error:
        return {
            "success": False,
            "requires_confirmation": True,
            "tool": payload.tool_name,
            "message": output.error,
        }
    if not output.success:
        return {
            "success": False,
            "error": output.error,
        }
    return {
        "success": True,
        "result": output.result,
    }


@router.post("/tools/approve", summary="Approve an MCP tool for the current session")
async def approve_mcp_tool(
    payload: ApproveToolRequest,
    current_user: CurrentUser = None,
) -> dict[str, Any]:
    svc = get_mcp_service()
    svc.approve_tool_for_session(payload.session_id, payload.tool_name)
    return {
        "success": True,
        "message": f"Tool '{payload.tool_name}' approved for session '{payload.session_id}'.",
    }
