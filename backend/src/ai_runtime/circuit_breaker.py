from __future__ import annotations

import time


class CircuitBreakerError(RuntimeError):
    """Raised when circuit breaker trips after reaching consecutive failure limit."""
    pass


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, cooldown_seconds: float = 30.0) -> None:
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds

        self.state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.consecutive_failures: int = 0
        self.last_state_change: float = time.time()
        self.last_error: str | None = None

    @property
    def is_open(self) -> bool:
        return self.state == "OPEN"

    def allow_request(self) -> bool:
        now = time.time()
        if self.state == "OPEN":
            if now - self.last_state_change >= self.cooldown_seconds:
                self.transition_to("HALF_OPEN")
                return True
            return False
        return True

    def record_success(self) -> None:
        self.consecutive_failures = 0
        self.last_error = None
        if self.state != "CLOSED":
            self.transition_to("CLOSED")

    def record_failure(self, error: Exception | str) -> None:
        self.consecutive_failures += 1
        self.last_error = str(error)

        if self.state in ("CLOSED", "HALF_OPEN") and self.consecutive_failures >= self.failure_threshold:
            self.transition_to("OPEN")

    def transition_to(self, new_state: str) -> None:
        self.state = new_state
        self.last_state_change = time.time()
        # Reset counters if entering closed
        if new_state == "CLOSED":
            self.consecutive_failures = 0


_run_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_run_circuit_breaker(run_id: str, failure_threshold: int = 3) -> CircuitBreaker:
    if run_id not in _run_circuit_breakers:
        _run_circuit_breakers[run_id] = CircuitBreaker(failure_threshold=failure_threshold, cooldown_seconds=60.0)
    return _run_circuit_breakers[run_id]


def reset_run_circuit_breaker(run_id: str) -> None:
    _run_circuit_breakers.pop(run_id, None)
