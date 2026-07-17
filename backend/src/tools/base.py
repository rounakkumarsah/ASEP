"""
ASEP — Base Tool Abstraction
"""

import sys
from abc import ABC, abstractmethod
from typing import Any, Type, Optional, List

from pydantic import BaseModel, Field

from src.tools.metadata import ToolMetadata, ToolType, ToolCategory
from src.tools.permissions import ToolPermission
from src.tools.schemas import ToolExecutionOutput


class BaseTool(ABC):
    """Abstract base class for all local system and MCP-compatible tools."""

    name: str
    version: str = "1.0.0"
    description: str
    category: str  # ToolCategory
    input_model: Type[BaseModel]
    required_permissions: List[str] = []

    # Sandbox / safety metadata declarations
    sandbox_supported: bool = True
    destructive_operations: bool = False
    requires_confirmation: bool = False

    def schema(self) -> dict[str, Any]:
        """Returns the JSON schema describing input arguments."""
        return self.input_model.model_json_schema()

    def permissions(self) -> List[str]:
        """Returns the required permissions list."""
        return self.required_permissions

    def capabilities(self) -> dict[str, Any]:
        """Returns the tool's sandbox and confirmation capabilities."""
        return {
            "sandbox_supported": self.sandbox_supported,
            "destructive_operations": self.destructive_operations,
            "requires_confirmation": self.requires_confirmation
        }

    def metadata(self) -> ToolMetadata:
        """Returns a detailed ToolMetadata configuration object."""
        return ToolMetadata(
            name=self.name,
            version=self.version,
            description=self.description,
            category=self.category,
            input_schema=self.schema(),
            required_permissions=self.permissions(),
            tool_type=ToolType.LOCAL,
            sandbox_supported=self.sandbox_supported,
            destructive_operations=self.destructive_operations,
            requires_confirmation=self.requires_confirmation
        )

    def validate(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Validates arguments against Pydantic schema and returns parsed dictionary."""
        validated = self.input_model.model_validate(arguments)
        return validated.model_dump()

    def health(self) -> dict[str, Any]:
        """Verifies tool dependency status and general health."""
        return {
            "status": "healthy",
            "available": True,
            "error": None
        }

    @abstractmethod
    async def execute(self, arguments: dict[str, Any], session_id: Optional[str] = None) -> ToolExecutionOutput:
        """Asynchronously execute the tool logic with validated arguments."""
        pass
