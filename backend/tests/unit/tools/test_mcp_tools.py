from __future__ import annotations
import os
import pytest
import asyncio
from unittest.mock import MagicMock

from src.tools import (
    ToolRegistry,
    ToolDispatcher,
    ToolErrorCode,
    ToolPermission,
    FilesystemTool,
    TerminalTool,
    GitTool,
    DockerTool,
    PostgresTool,
    Neo4jTool,
    QdrantTool,
    RedisTool,
    EnvironmentTool,
    ConfigurationTool,
    BrowserTool
)

@pytest.mark.asyncio
async def test_tool_registry_lifecycle():
    registry = ToolRegistry()
    config_tool = ConfigurationTool()
    
    # Register
    registry.register(config_tool)
    assert registry.lookup("configuration") == config_tool
    assert registry.version("configuration") == "1.0.0"
    
    # Health checks
    h_states = registry.health()
    assert h_states["configuration"]["status"] == "healthy"
    
    # Disable and discover
    registry.disable("configuration")
    assert registry.is_enabled("configuration") is False
    assert len(registry.discover()) == 0
    
    # Enable and discover
    registry.enable("configuration")
    assert registry.is_enabled("configuration") is True
    assert len(registry.discover()) == 1
    
    # Unregister
    registry.unregister("configuration")
    assert registry.lookup("configuration") is None

@pytest.mark.asyncio
async def test_dispatcher_permission_enforcement(tmp_path):
    registry = ToolRegistry()
    fs_tool = FilesystemTool()
    registry.register(fs_tool)
    
    dispatcher = ToolDispatcher(registry)
    
    # Write sample file
    test_file = tmp_path / "hello.txt"
    
    # Execute without required permission
    resp = await dispatcher.execute(
        tool_name="filesystem",
        arguments={
            "action": "write",
            "path": str(test_file),
            "content": "Hello World"
        },
        granted_permissions=[ToolPermission.READ] # missing filesystem permission
    )
    assert resp.success is False
    assert resp.error == ToolErrorCode.PERMISSION_DENIED
    
    # Execute with required permission
    resp = await dispatcher.execute(
        tool_name="filesystem",
        arguments={
            "action": "write",
            "path": str(test_file),
            "content": "Hello World"
        },
        granted_permissions=[ToolPermission.FILESYSTEM]
    )
    assert resp.success is True
    assert os.path.exists(test_file)
    
    # Read the file using the tool
    resp_read = await dispatcher.execute(
        tool_name="filesystem",
        arguments={
            "action": "read",
            "path": str(test_file)
        },
        granted_permissions=[ToolPermission.FILESYSTEM]
    )
    assert resp_read.success is True
    assert resp_read.result["content"] == "Hello World"

@pytest.mark.asyncio
async def test_dispatcher_disabled_and_missing():
    registry = ToolRegistry()
    dispatcher = ToolDispatcher(registry)
    
    # Test missing tool
    resp = await dispatcher.execute(
        tool_name="missing_tool",
        arguments={},
        granted_permissions=[]
    )
    assert resp.success is False
    assert resp.error == ToolErrorCode.TOOL_NOT_FOUND
    
    # Test disabled tool
    config_tool = ConfigurationTool()
    registry.register(config_tool)
    registry.disable("configuration")
    
    resp_disabled = await dispatcher.execute(
        tool_name="configuration",
        arguments={},
        granted_permissions=[ToolPermission.READ]
    )
    assert resp_disabled.success is False
    assert resp_disabled.error == ToolErrorCode.TOOL_DISABLED

@pytest.mark.asyncio
async def test_dispatcher_validation_failure():
    registry = ToolRegistry()
    fs_tool = FilesystemTool()
    registry.register(fs_tool)
    
    dispatcher = ToolDispatcher(registry)
    
    # Invalid argument validation
    resp = await dispatcher.execute(
        tool_name="filesystem",
        arguments={
            "action": "write"
            # path is missing
        },
        granted_permissions=[ToolPermission.FILESYSTEM]
    )
    assert resp.success is False
    assert ToolErrorCode.INVALID_INPUT in resp.error

@pytest.mark.asyncio
async def test_terminal_tool_sandboxing():
    registry = ToolRegistry()
    term_tool = TerminalTool()
    registry.register(term_tool)
    
    dispatcher = ToolDispatcher(registry)
    
    # Forbidden command block
    resp = await dispatcher.execute(
        tool_name="terminal",
        arguments={
            "command": "rm -rf /"
        },
        granted_permissions=[ToolPermission.EXECUTE]
    )
    assert resp.success is False
    assert "blocked" in resp.error

@pytest.mark.asyncio
async def test_all_initial_tools_registration():
    registry = ToolRegistry()
    tools = [
        FilesystemTool(),
        TerminalTool(),
        GitTool(),
        DockerTool(),
        PostgresTool(),
        Neo4jTool(),
        QdrantTool(),
        RedisTool(),
        EnvironmentTool(),
        ConfigurationTool(),
        BrowserTool()
    ]
    for t in tools:
        registry.register(t)
        
    for t in tools:
        assert registry.lookup(t.name) == t
        assert registry.is_enabled(t.name) is True
