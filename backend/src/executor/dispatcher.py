"""
ASEP — Handler Registry & Task Dispatcher
"""

import asyncio
import logging
from typing import Any

from src.executor.context import ExecutionContext
from src.executor.result import TaskResult, TaskStatus
from src.executor.scheduler import DependencyScheduler
from src.executor.worker import TaskHandler, TaskWorker
from src.planner.models import SubTask

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# No-op default handler
# ─────────────────────────────────────────────────────────────────────────────

async def noop_handler(task: SubTask, context: ExecutionContext) -> dict[str, Any]:
    """Default placeholder handler.  Succeeds immediately with empty output."""
    logger.debug(f"noop_handler called for task '{task.id}'")
    return {"noop": True, "task_id": task.id}


# ─────────────────────────────────────────────────────────────────────────────
# Handler Registry
# ─────────────────────────────────────────────────────────────────────────────

class HandlerRegistry:
    """Maps task IDs or task types to async handler callables."""

    def __init__(self, default_handler: TaskHandler = noop_handler) -> None:
        self._handlers: dict[str, TaskHandler] = {}
        self._default = default_handler

    def register(self, task_id: str, handler: TaskHandler) -> None:
        """Register a handler for a specific task ID."""
        logger.debug(f"HandlerRegistry: registered handler for '{task_id}'")
        self._handlers[task_id] = handler

    def get(self, task_id: str) -> TaskHandler:
        """Retrieve the handler for a task ID, falling back to the default."""
        return self._handlers.get(task_id, self._default)

    def set_default(self, handler: TaskHandler) -> None:
        """Override the default fallback handler."""
        self._default = handler


# ─────────────────────────────────────────────────────────────────────────────
# Task Dispatcher
# ─────────────────────────────────────────────────────────────────────────────

class TaskDispatcher:
    """Fans out a single wave of independent tasks concurrently via asyncio.gather,
    collects their results, and reports back to the executor loop.
    """

    def __init__(self, handler_registry: HandlerRegistry, worker: TaskWorker) -> None:
        self.registry = handler_registry
        self.worker = worker

    async def dispatch_wave(
        self,
        tasks: list[SubTask],
        context: ExecutionContext,
        scheduler: DependencyScheduler,
    ) -> list[TaskResult]:
        """Execute all tasks in this wave concurrently.

        Marks each task as running before dispatch and updates the scheduler
        (complete / failed) once each coroutine settles.
        """
        if not tasks:
            return []

        for task in tasks:
            scheduler.mark_running(task.id)

        async def _run_one(task: SubTask) -> TaskResult:
            handler = self.registry.get(task.id)
            result = await self.worker.execute(task, handler, context)

            if result.status == TaskStatus.SUCCEEDED:
                scheduler.mark_complete(task.id)
            elif result.status in (TaskStatus.CANCELLED,):
                # Keep the scheduler in a consistent state
                scheduler.mark_failed(task.id)
            else:
                scheduler.mark_failed(task.id)

            return result

        task_names = [t.id for t in tasks]
        logger.info(f"Dispatching wave: {task_names}")

        results: list[TaskResult] = await asyncio.gather(*[_run_one(t) for t in tasks])
        return list(results)
