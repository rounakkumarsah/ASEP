from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    reasoning: str | None = None
    reasoning_details: list[dict[str, Any]] | None = None

class UsageInfo(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_tokens: int = 0
    reasoning_tokens: int = 0
    thought_tokens: int = 0
    tool_use_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    latency_ms: float = 0.0
    cache_status: str | None = None

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
    tools: list[dict[str, Any]] | None = None
    tool_choice: str | dict[str, Any] | None = None
    parallel_tool_calls: bool | None = None
    tool_callables: dict[str, Any] | None = None
    user: str | None = None
    session_id: str | None = None
    trace: dict[str, Any] | None = None
    reasoning: dict[str, Any] | None = None
    preferred_max_latency: dict[str, Any] | None = None
    preferred_min_throughput: dict[str, Any] | None = None
    router_metadata: dict[str, Any] | None = None
    service_tier: str | None = None
    seed: int | None = None

class CompletionResponse(BaseModel):
    text: str
    usage: UsageInfo
    provider: str
    model: str
    finish_reason: str | None = None
    tool_calls: list[ToolCall] | None = None
    router_metadata: dict[str, Any] | None = None
    reasoning: str | None = None
    reasoning_details: list[dict[str, Any]] | None = None

class StreamChunk(BaseModel):
    text: str
    usage: UsageInfo | None = None
    finish_reason: str | None = None
    tool_calls: list[ToolCall] | None = None
    router_metadata: dict[str, Any] | None = None
    reasoning: str | None = None
    reasoning_details: list[dict[str, Any]] | None = None

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
