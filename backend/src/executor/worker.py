"""
ASEP — Task Worker
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine

from src.executor.context import ExecutionContext
from src.executor.result import TaskResult, TaskStatus
from src.executor.retries import RetryPolicy, with_retry
from src.planner.models import SubTask

logger = logging.getLogger(__name__)

# Handler type: receives the SubTask and ExecutionContext, returns a dict
TaskHandler = Callable[[SubTask, ExecutionContext], Coroutine[Any, Any, dict[str, Any]]]


class TaskWorker:
    """Executes a single SubTask, honouring pause/cancel signals and the retry policy."""

    def __init__(self, retry_policy: RetryPolicy | None = None) -> None:
        self.retry_policy = retry_policy or RetryPolicy()

    async def execute(
        self,
        task: SubTask,
        handler: TaskHandler,
        context: ExecutionContext,
    ) -> TaskResult:
        """Run the task handler with retry / pause / cancel semantics.

        Flow:
          1. Check for cancellation — mark CANCELLED and return early.
          2. Await the pause event — blocks until execution is resumed.
          3. Mark the task RUNNING and invoke the handler via with_retry.
          4. Record the result (SUCCEEDED / FAILED / TIMED_OUT / CANCELLED).
        """
        result = context.results[task.id]

        # ── 1. Cancellation guard ────────────────────────────────────────────
        if context.is_cancelled():
            result.status = TaskStatus.CANCELLED
            result.error = "Execution was cancelled before task started"
            logger.info(f"[{task.id}] Skipped — execution cancelled")
            return result

        # ── 2. Pause gate — blocks cooperatively ────────────────────────────
        await context.pause_event.wait()

        # Re-check cancellation after resuming from pause
        if context.is_cancelled():
            result.status = TaskStatus.CANCELLED
            result.error = "Execution cancelled while paused"
            return result

        # ── 3. Mark RUNNING ──────────────────────────────────────────────────
        result.status = TaskStatus.RUNNING
        result.start_time = datetime.now(tz=timezone.utc)
        logger.info(f"[{task.id}] Starting — '{task.title}'")

        # ── 4. Execute with retry ────────────────────────────────────────────
        try:
            output, error, attempts = await with_retry(
                lambda: handler(task, context),
                self.retry_policy,
                task_id=task.id,
            )
        except asyncio.CancelledError:
            result.status = TaskStatus.CANCELLED
            result.error = "Cancelled during execution"
            result.end_time = datetime.now(tz=timezone.utc)
            logger.warning(f"[{task.id}] Cancelled during execution")
            return result

        result.attempts = attempts
        result.end_time = datetime.now(tz=timezone.utc)

        if error is None:
            result.status = TaskStatus.SUCCEEDED
            result.output = output or {}
            logger.info(f"[{task.id}] Succeeded in {attempts} attempt(s)")
        elif "Timed out" in (error or ""):
            result.status = TaskStatus.TIMED_OUT
            result.error = error
            logger.error(f"[{task.id}] Timed out: {error}")
        else:
            result.status = TaskStatus.FAILED
            result.error = error
            logger.error(f"[{task.id}] Failed after {attempts} attempt(s): {error}")

        # Write result back into context
        context.results[task.id] = result
        return result
