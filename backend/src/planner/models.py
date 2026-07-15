"""
ASEP — Structured Planning Models
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Complexity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Goal(BaseModel):
    """Structured representation of a parsed user request."""
    raw_goal: str = Field(description="The original unstructured user goal")
    parsed_title: str = Field(description="A clean, descriptive title for the target execution")
    success_criteria: list[str] = Field(
        default_factory=list, 
        description="Explicit parameters verifying that the goal has been met"
    )


class SubTask(BaseModel):
    """A single logical step of execution in a decomposed plan."""
    id: str = Field(description="A unique alphanumeric key for the subtask (e.g. 'setup_db', 'write_api')")
    title: str = Field(description="Descriptive short name of the task")
    description: str = Field(description="Detailed explanation of what needs to be performed")
    depends_on: list[str] = Field(
        default_factory=list,
        description="List of subtask IDs that must complete before this task can start"
    )
    complexity: Complexity = Field(default=Complexity.MEDIUM, description="Task execution complexity")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task execution priority")
    tool_name: str | None = Field(
        default=None,
        description="Optional name of the tool to invoke when executing this task via the ToolRouter"
    )


class DecomposedPlan(BaseModel):
    """The full structured execution plan representing a Directed Acyclic Graph (DAG) of tasks."""
    tasks: list[SubTask] = Field(
        default_factory=list,
        description="Topologically ordered list of execution subtasks"
    )
    rationale: str = Field(description="LLM's high-level planning approach and logic summary")
