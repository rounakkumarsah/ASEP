"""
ASEP — Base Tool Abstraction & Placeholder Local Tools
"""

import sys
from abc import ABC, abstractmethod
from typing import Any, Type

from pydantic import BaseModel, Field

from src.tools.metadata import ToolMetadata, ToolType
from src.tools.permissions import ToolPermission
from src.tools.schemas import ToolExecutionOutput


class BaseTool(ABC):
    """Abstract base class for all local system tools."""

    name: str
    description: str
    input_model: Type[BaseModel]
    required_permissions: list[str] = []

    def get_metadata(self) -> ToolMetadata:
        """Dynamically generate tool metadata, converting input Pydantic model to JSON schema."""
        return ToolMetadata(
            name=self.name,
            description=self.description,
            input_schema=self.input_model.model_json_schema(),
            required_permissions=self.required_permissions,
            tool_type=ToolType.LOCAL
        )

    @abstractmethod
    async def run(self, arguments: dict[str, Any]) -> ToolExecutionOutput:
        """Asynchronously execute tool logic with type-validated arguments."""
        pass


# --- Placeholder Local Tool Implementations ---

class ReadLocalFileInput(BaseModel):
    path: str = Field(description="Absolute or relative file path to read")


class ReadLocalFileTool(BaseTool):
    """Simulates reading content from local disk."""
    name = "read_local_file"
    description = "Read raw string content from a local text or code file."
    input_model = ReadLocalFileInput
    required_permissions = [ToolPermission.FS_READ]

    async def run(self, arguments: dict[str, Any]) -> ToolExecutionOutput:
        try:
            # Validate input arguments through Pydantic
            inputs = self.input_model.model_validate(arguments)
            # Placeholder implementation (infrastructure-only phase)
            return ToolExecutionOutput(
                success=True,
                result={"path": inputs.path, "content": f"Placeholder content read from {inputs.path}."}
            )
        except Exception as e:
            return ToolExecutionOutput(success=False, error=str(e))


class SysInfoTool(BaseTool):
    """Retrieves mock platform/runtime info."""
    name = "system_info"
    description = "Retrieve details about the execution host runtime environment."
    input_model = BaseModel  # No parameters needed
    required_permissions = [ToolPermission.SYS_INFO]

    async def run(self, arguments: dict[str, Any]) -> ToolExecutionOutput:
        try:
            return ToolExecutionOutput(
                success=True,
                result={
                    "platform": sys.platform,
                    "python_version": sys.version,
                    "mock_memory_usage_mb": 142.5
                }
            )
        except Exception as e:
            return ToolExecutionOutput(success=False, error=str(e))
