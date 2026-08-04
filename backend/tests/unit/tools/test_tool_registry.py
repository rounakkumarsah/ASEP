"""
ASEP — Unit Tests for Tool Registry & Validation
"""

import pytest
from pydantic import BaseModel, Field
from src.tools.base import BaseTool
from src.tools.permissions import ToolPermission, verify_tool_permissions
from src.tools.registry import ToolRegistry
from src.tools.schemas import ToolExecutionOutput


class DummyInput(BaseModel):
    query: str = Field(..., min_length=1)


class DummyTool(BaseTool):
    name = "dummy_tool"
    version = "1.0.0"
    description = "Dummy tool for unit testing"
    category = "utility"
    input_model = DummyInput
    required_permissions = [ToolPermission.READ]

    async def execute(self, arguments: dict, session_id=None) -> ToolExecutionOutput:
        args = self.validate(arguments)
        return ToolExecutionOutput(success=True, result={"output": f"Processed {args['query']}"})



def test_tool_permissions_verification():
    valid, err = verify_tool_permissions(
        tool_required=[ToolPermission.READ],
        user_granted=[ToolPermission.READ, ToolPermission.WRITE],
    )
    assert valid is True
    assert err is None

    valid, err = verify_tool_permissions(
        tool_required=[ToolPermission.EXECUTE],
        user_granted=[ToolPermission.READ],
    )
    assert valid is False
    assert "Permission Denied" in err


def test_tool_registry_management():
    registry = ToolRegistry()
    tool = DummyTool()

    registry.register(tool)
    assert registry.lookup("dummy_tool") == tool
    assert registry.is_enabled("dummy_tool") is True

    discovered = registry.discover(capability=ToolPermission.READ)
    assert len(discovered) == 1

    registry.disable("dummy_tool")
    assert registry.is_enabled("dummy_tool") is False

    registry.unregister("dummy_tool")
    assert registry.lookup("dummy_tool") is None


from pydantic import ValidationError

@pytest.mark.asyncio
async def test_tool_validation_and_execution():
    tool = DummyTool()
    
    # Valid input
    output = await tool.execute({"query": "test query"})
    assert output.success is True
    assert "Processed test query" in output.result["output"]

    # Invalid input (missing query field)
    with pytest.raises(ValidationError):
        tool.validate({})






