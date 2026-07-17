"""
ASEP — Tool Metadata Schemas
"""

from enum import Enum
from typing import Any, List

from pydantic import BaseModel, Field


class ToolType(str, Enum):
    LOCAL = "local"
    MCP = "mcp"


class ToolCategory(str, Enum):
    DEVELOPMENT = "Development"
    INFRASTRUCTURE = "Infrastructure"
    DATABASE = "Database"
    FILESYSTEM = "Filesystem"
    BROWSER = "Browser"
    NETWORKING = "Networking"
    CLOUD = "Cloud"
    SYSTEM = "System"


class ToolMetadata(BaseModel):
    """Declarative metadata exposing a tool's capabilities and constraints."""
    name: str = Field(description="Unique system-wide name of the tool")
    version: str = Field(default="1.0.0", description="SemVer string of the tool version")
    description: str = Field(description="Verbose description outlining when/how to use the tool")
    category: str = Field(description="Operational category of the tool")
    input_schema: dict[str, Any] = Field(
        description="JSON schema describing the required and optional arguments"
    )
    required_permissions: List[str] = Field(
        default_factory=list,
        description="Permission scopes required to trigger this tool"
    )
    tool_type: ToolType = Field(default=ToolType.LOCAL, description="Classification of tool execution route")
    
    # Sandbox/Safety capabilities
    sandbox_supported: bool = Field(default=True, description="Indicates if the tool can execute in a sandbox")
    destructive_operations: bool = Field(default=False, description="Indicates if the tool runs destructive commands")
    requires_confirmation: bool = Field(default=False, description="Indicates if execution needs manual verification")
