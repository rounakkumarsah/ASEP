"""
ASEP — Dependency-Aware Scheduler
"""

import logging

from src.planner.models import DecomposedPlan, SubTask

logger = logging.getLogger(__name__)


class DependencyScheduler:
    """Resolves the DAG execution order, yielding tasks in dependency-safe waves.

    Independent tasks within the same wave are returned together so the
    dispatcher can run them concurrently.  The next wave is only computed
    after all tasks from the current wave have been marked complete.
    """

    def __init__(self, plan: DecomposedPlan) -> None:
        # Build an index for O(1) lookup
        self._tasks: dict[str, SubTask] = {t.id: t for t in plan.tasks}
        self._completed: set[str] = set()
        self._running: set[str] = set()
        self._failed: set[str] = set()

    # ──────────────────────────────────────────────────────────────────────────
    # State updates
    # ──────────────────────────────────────────────────────────────────────────

    def mark_complete(self, task_id: str) -> None:
        """Record that a task finished successfully."""
        self._running.discard(task_id)
        self._completed.add(task_id)
        logger.debug(f"Scheduler: '{task_id}' marked complete")

    def mark_failed(self, task_id: str) -> None:
        """Record that a task failed; its dependents will be skipped."""
        self._running.discard(task_id)
        self._failed.add(task_id)
        logger.warning(f"Scheduler: '{task_id}' marked failed")

    def mark_running(self, task_id: str) -> None:
        self._running.add(task_id)

    # ──────────────────────────────────────────────────────────────────────────
    # Wave resolution
    # ──────────────────────────────────────────────────────────────────────────

    def get_ready_wave(self) -> list[SubTask]:
        """Return all tasks whose dependencies have all completed and are not yet
        running, completed, or failed.

        Tasks whose parent has failed are excluded (they will be skipped by the
        dispatcher as a downstream consequence).
        """
        ready: list[SubTask] = []

        for task in self._tasks.values():
            if task.id in self._completed:
                continue
            if task.id in self._running:
                continue
            if task.id in self._failed:
                continue

            # Check if any dependency has failed — if so, skip this task too
            if any(dep in self._failed for dep in task.depends_on):
                continue

            # All dependencies must be completed
            if all(dep in self._completed for dep in task.depends_on):
                ready.append(task)

        return ready

    def get_skippable(self) -> list[str]:
        """Return task IDs that should be skipped because a parent failed."""
        skip: list[str] = []
        for task in self._tasks.values():
            if task.id in self._completed or task.id in self._failed:
                continue
            if any(dep in self._failed for dep in task.depends_on):
                skip.append(task.id)
        return skip

    def is_complete(self) -> bool:
        """Return True when all tasks are in a terminal state."""
        terminal = self._completed | self._failed
        return terminal == set(self._tasks.keys())

    def is_stalled(self) -> bool:
        """Return True when no tasks are ready but the plan is not complete.
        This would indicate a broken DAG that slipped past validation.
        """
        if self.is_complete():
            return False
        ready = self.get_ready_wave()
        return len(ready) == 0 and len(self._running) == 0

    @property
    def completed(self) -> frozenset[str]:
        return frozenset(self._completed)

    @property
    def failed(self) -> frozenset[str]:
        return frozenset(self._failed)
