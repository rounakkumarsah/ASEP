from __future__ import annotations
import time
from typing import Optional

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, cooldown_seconds: float = 30.0) -> None:
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        
        self.state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.consecutive_failures: int = 0
        self.last_state_change: float = time.time()
        self.last_error: Optional[str] = None

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
        now = time.time()
        
        if self.state in ("CLOSED", "HALF_OPEN") and self.consecutive_failures >= self.failure_threshold:
            self.transition_to("OPEN")

    def transition_to(self, new_state: str) -> None:
        self.state = new_state
        self.last_state_change = time.time()
        # Reset counters if entering closed
        if new_state == "CLOSED":
            self.consecutive_failures = 0
