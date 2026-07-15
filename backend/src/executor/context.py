"""
ASEP — Execution Context
"""

import asyncio
from typing import TYPE_CHECKING

from src.executor.result import TaskResult
from src.planner.models import DecomposedPlan

if TYPE_CHECKING:
    from src.memory.memory_manager import MemoryManager


class ExecutionContext:
    """Shared runtime scope injected into every worker.

    Holds the run identity, the immutable plan, cooperative
    pause/cancel signals, and the live result map.  Workers
    MUST NOT modify the plan; they only read it.
    """

    def __init__(
        self,
        run_id: str,
        plan: DecomposedPlan,
        memory_manager: "MemoryManager",
    ) -> None:
        self.run_id = run_id
        # Executor must never modify the plan — store a read-only reference
        self._plan: DecomposedPlan = plan

        # Memory access goes exclusively through MemoryManager
        self.memory = memory_manager

        # Mutable live result map — keyed by task_id
        self.results: dict[str, TaskResult] = {
            task.id: TaskResult(task_id=task.id) for task in plan.tasks
        }

        # Cooperative pause: cleared = paused, set = running
        self._pause_event: asyncio.Event = asyncio.Event()
        self._pause_event.set()  # Start in running state

        # Cooperative cancellation: set = cancelled
        self._cancel_event: asyncio.Event = asyncio.Event()

    @property
    def plan(self) -> DecomposedPlan:
        """Read-only access to the execution plan."""
        return self._plan

    @property
    def pause_event(self) -> asyncio.Event:
        return self._pause_event

    @property
    def cancel_event(self) -> asyncio.Event:
        return self._cancel_event

    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()

    def is_paused(self) -> bool:
        return not self._pause_event.is_set()
