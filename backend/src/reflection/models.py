"""
ASEP — Reflection Models
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

class LessonCategory(str, Enum):
    PLANNING = "planning"
    TOOL_USAGE = "tool_usage"
    MEMORY = "memory"
    EXECUTION = "execution"
    CONTEXT = "context"
    POLICY = "policy"
    PERFORMANCE = "performance"

class RootCauseCategory(str, Enum):
    TOOL_FAILURE = "tool_failure"
    PLANNING_ERROR = "planning_error"
    TIMEOUT = "timeout"
    PERMISSION_DENIED = "permission_denied"
    LOGIC_ERROR = "logic_error"
    UNKNOWN = "unknown"

class ReflectionItem(BaseModel):
    """A single structured lesson extracted during reflection."""
    category: LessonCategory
    failure_description: str = Field(description="Description of what went wrong or could be improved.")
    root_cause: str = Field(description="The underlying reason for the failure or inefficiency.")
    evidence: str = Field(description="Observable evidence from the trace, trajectory or metrics.")
    recommendation: str = Field(description="Actionable IF-THEN rule or recommendation to prevent this in the future.")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in this assessment (0.0 to 1.0).")

class FailureAnalysis(BaseModel):
    category: RootCauseCategory = Field(default=RootCauseCategory.UNKNOWN)
    contributing_factors: list[str] = Field(default_factory=list)

class ReflectionReport(BaseModel):
    """The complete reflection output for a single session."""
    session_id: str
    run_id: str
    passed: bool
    failure_analysis: FailureAnalysis | None = None
    items: list[ReflectionItem] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
