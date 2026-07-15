"""
ASEP — Tool Metadata Schemas
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ToolType(str, Enum):
    LOCAL = "local"
    MCP = "mcp"


class ToolMetadata(BaseModel):
    """Declarative metadata exposing a tool's capabilities and constraints."""
    name: str = Field(description="Unique system-wide name of the tool")
    description: str = Field(description="Verbose description outlining when/how to use the tool")
    input_schema: dict[str, Any] = Field(
        description="JSON schema describing the required and optional arguments"
    )
    required_permissions: list[str] = Field(
        default_factory=list,
        description="Permission scopes required to trigger this tool (e.g. 'fs:read', 'net:out')"
    )
    tool_type: ToolType = Field(default=ToolType.LOCAL, description="Classification of tool execution route")
