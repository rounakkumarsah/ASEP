from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

class UsageInfo(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_tokens: int = 0
    reasoning_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    latency_ms: float = 0.0

class ProviderCapabilityMatrix(BaseModel):
    streaming: bool = False
    structured_output: bool = False
    json_mode: bool = False
    vision: bool = False
    tool_calling: bool = False
    embeddings: bool = False
    reasoning: bool = False
    context_window: int = 4096

class CompletionRequest(BaseModel):
    messages: list[Message]
    model: str
    temperature: float = 0.7
    max_tokens: int | None = None
    response_format: dict[str, Any] | None = None  # Structured output schema if required

class CompletionResponse(BaseModel):
    text: str
    usage: UsageInfo
    provider: str
    model: str
    finish_reason: str | None = None

class StreamChunk(BaseModel):
    text: str
    usage: UsageInfo | None = None
    finish_reason: str | None = None

class ProviderHealth(BaseModel):
    provider_name: str
    is_healthy: bool
    active_model: str
    circuit_breaker_state: str
    error_count: int
    latency_ms: float
    loaded_models: list[str] = Field(default_factory=list)
    last_error: str | None = None

# Tool Calling Scaffold for Phase 4.4
class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]

class ToolCall(BaseModel):
    id: str
    type: Literal["function"] = "function"
    name: str
    arguments: str

class ToolResult(BaseModel):
    tool_call_id: str
    content: str
    is_error: bool = False
