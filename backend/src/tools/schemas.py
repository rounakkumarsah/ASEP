"""
ASEP — Tool Execution Schemas
"""

from typing import Any

from pydantic import BaseModel, Field


class ToolExecutionInput(BaseModel):
    """Input payload for dispatching tool execution."""
    tool_name: str = Field(description="Name of the target tool to execute")
    arguments: dict[str, Any] = Field(
        default_factory=dict, 
        description="Key-value arguments matching the tool's input schema"
    )


class ToolExecutionOutput(BaseModel):
    """Result payload returned after tool execution."""
    success: bool = Field(description="Indicates if the tool executed successfully")
    result: dict[str, Any] = Field(
        default_factory=dict, 
        description="Structured data returned by the tool on success"
    )
    error: str | None = Field(default=None, description="Detailed error message if execution failed")
