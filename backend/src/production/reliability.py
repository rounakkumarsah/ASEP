"""
ASEP — Enterprise Reliability Engine
======================================
Circuit breakers, adaptive retry policies, Dead Letter Queue (DLQ),
and automated recovery management.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class CircuitState(StrEnum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpenException(Exception):
    """Raised when circuit breaker is in OPEN state."""
    pass


class CircuitBreaker:
    """Stateful circuit breaker protecting remote calls."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_state_change = time.time()

    def record_success(self) -> None:
        self.failure_count = 0
        if self.state != CircuitState.CLOSED:
            self.state = CircuitState.CLOSED
            self.last_state_change = time.time()
            logger.info("CircuitBreaker '%s' reset to CLOSED state.", self.name)

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.last_state_change = time.time()
            logger.warning("CircuitBreaker '%s' OPENED after %d failures.", self.name, self.failure_count)

    def check_state(self) -> None:
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_state_change > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.last_state_change = time.time()
                logger.info("CircuitBreaker '%s' switched to HALF_OPEN state.", self.name)
            else:
                raise CircuitBreakerOpenException(f"CircuitBreaker '{self.name}' is OPEN.")


@dataclass
class DLQMessage:
    message_id: str
    execution_id: str
    component: str
    payload: dict[str, Any]
    error_reason: str
    timestamp: float = field(default_factory=time.time)


class DeadLetterQueue:
    """Dead Letter Queue for failed task executions requiring intervention."""

    def __init__(self) -> None:
        self._dlq: list[DLQMessage] = []

    def enqueue(
        self,
        message_id: str,
        execution_id: str,
        component: str,
        payload: dict[str, Any],
        error_reason: str,
    ) -> DLQMessage:
        dlq_msg = DLQMessage(
            message_id=message_id,
            execution_id=execution_id,
            component=component,
            payload=payload,
            error_reason=error_reason,
        )
        self._dlq.append(dlq_msg)
        logger.error("Enqueued to DLQ [%s]: %s (reason: %s)", execution_id, message_id, error_reason)
        return dlq_msg

    def list_messages(self) -> list[DLQMessage]:
        return list(self._dlq)


    def replay_message(self, message_id: str) -> DLQMessage | None:
        for idx, msg in enumerate(self._dlq):
            if msg.message_id == message_id:
                logger.info("Replaying DLQ message '%s'", message_id)
                return self._dlq.pop(idx)
        return None
