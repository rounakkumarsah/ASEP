"""
ASEP — Reflection Policies
"""

from enum import StrEnum

from pydantic import BaseModel, Field


class ReflectionTrigger(StrEnum):
    ON_SUCCESS = "on_success"
    ON_FAILURE = "on_failure"
    ALWAYS = "always"
    NEVER = "never"

class ReflectionPolicy(BaseModel):
    trigger: ReflectionTrigger = Field(default=ReflectionTrigger.ON_FAILURE)
    min_confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    update_procedural_memory: bool = Field(default=True)
