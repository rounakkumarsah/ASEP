from __future__ import annotations

import contextvars
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StepTelemetry:
    step_index: int = 1
    active_node_name: str = "none"
    llm_provider_response_status: str = "none"  # "success", "429", "error", or "none"
    tokens_used: int = 0
    tool_calls_made: list[str] = field(default_factory=list)
    finish_reason: str = "unknown"
    provider_name: str | None = None
    error_message: str | None = None
    run_id: str | None = None

    def record_llm_success(
        self,
        provider: str,
        tokens: int = 0,
        tool_calls: list[str] | None = None,
        finish_reason: str = "stop",
    ) -> None:
        self.llm_provider_response_status = "success"
        self.provider_name = provider
        self.tokens_used += tokens
        if tool_calls:
            self.tool_calls_made.extend(tool_calls)
        if finish_reason:
            self.finish_reason = finish_reason

    def record_llm_failure(
        self,
        provider: str,
        is_429: bool = False,
        error_msg: str = "",
    ) -> None:
        self.llm_provider_response_status = "429" if is_429 else "error"
        self.provider_name = provider
        self.error_message = error_msg
        self.finish_reason = "rate_limit_429" if is_429 else "error"


_current_step_telemetry: contextvars.ContextVar[StepTelemetry | None] = contextvars.ContextVar(
    "current_step_telemetry", default=None
)


def get_current_step_telemetry() -> StepTelemetry:
    t = _current_step_telemetry.get()
    if t is None:
        t = StepTelemetry()
        _current_step_telemetry.set(t)
    return t


def set_current_step_telemetry(t: StepTelemetry | None) -> None:
    _current_step_telemetry.set(t)
