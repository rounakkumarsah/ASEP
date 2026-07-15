"""
ASEP — Executor Facade
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import AsyncGenerator

from src.executor.context import ExecutionContext
from src.executor.dispatcher import HandlerRegistry, TaskDispatcher
from src.executor.result import ExecutionReport, ProgressEvent, TaskStatus
from src.executor.retries import RetryPolicy
from src.executor.scheduler import DependencyScheduler
from src.executor.worker import TaskWorker
from src.memory.memory_manager import MemoryManager
from src.planner.models import DecomposedPlan

logger = logging.getLogger(__name__)


class Executor:
    """Main orchestration facade: drives the DAG execution loop, handles
    pause/resume/cancel, and streams typed ProgressEvents to the caller.

    Design constraints enforced here:
      - The plan is never modified.
      - All storage access goes through MemoryManager.
      - Independent tasks in the same wave run concurrently.
      - Dependent tasks run sequentially (next wave after current wave settles).
    """

    def __init__(
        self,
        plan: DecomposedPlan,
        memory_manager: MemoryManager,
        run_id: str,
        handler_registry: HandlerRegistry | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self._plan = plan
        self._run_id = run_id

        self.context = ExecutionContext(
            run_id=run_id,
            plan=plan,
            memory_manager=memory_manager,
        )

        self.scheduler = DependencyScheduler(plan)

        _retry = retry_policy or RetryPolicy()
        _worker = TaskWorker(retry_policy=_retry)
        _registry = handler_registry or HandlerRegistry()
        self.dispatcher = TaskDispatcher(handler_registry=_registry, worker=_worker)

    # ──────────────────────────────────────────────────────────────────────────
    # Control surface
    # ──────────────────────────────────────────────────────────────────────────

    def pause(self) -> None:
        """Cooperatively pause execution after the current task wave settles."""
        self.context.pause_event.clear()
        logger.info(f"[{self._run_id}] Executor paused")

    def resume(self) -> None:
        """Resume a paused execution."""
        self.context.pause_event.set()
        logger.info(f"[{self._run_id}] Executor resumed")

    def cancel(self) -> None:
        """Signal cancellation; workers will abort at their next checkpoint."""
        self.context.cancel_event.set()
        self.context.pause_event.set()   # Unblock any paused workers so they can observe cancellation
        logger.info(f"[{self._run_id}] Executor cancelled")

    # ──────────────────────────────────────────────────────────────────────────
    # Main execution loop
    # ──────────────────────────────────────────────────────────────────────────

    async def execute(self) -> AsyncGenerator[ProgressEvent, None]:
        """Drive the DAG execution loop, yielding ProgressEvents.

        Usage::

            async for event in executor.execute():
                print(event.event_type, event.task_id, event.status)
        """
        start_time = datetime.now(tz=timezone.utc)

        while not self.scheduler.is_complete():
            # Abort on cancellation
            if self.context.is_cancelled():
                logger.info(f"[{self._run_id}] Cancellation detected; stopping loop")
                break

            # Check for stalled graph (broken DAG that passed validation)
            if self.scheduler.is_stalled():
                logger.error(f"[{self._run_id}] Execution stalled — no ready tasks and plan incomplete")
                break

            # Skip tasks whose parents failed
            for skipped_id in self.scheduler.get_skippable():
                self.context.results[skipped_id].status = TaskStatus.SKIPPED
                self.scheduler.mark_failed(skipped_id)   # remove from pending
                yield ProgressEvent(
                    event_type="task_skipped",
                    task_id=skipped_id,
                    status=TaskStatus.SKIPPED,
                    detail="Skipped because a dependency failed",
                )

            wave = self.scheduler.get_ready_wave()
            if not wave:
                # Tasks still running in parallel; yield control
                await asyncio.sleep(0)
                continue

            # Emit started events for each task in the wave
            for task in wave:
                self.context.results[task.id].status = TaskStatus.RUNNING
                yield ProgressEvent(
                    event_type="task_started",
                    task_id=task.id,
                    status=TaskStatus.RUNNING,
                    detail=f"Starting '{task.title}'",
                )

            # Dispatch the wave concurrently; await full wave completion
            wave_results = await self.dispatcher.dispatch_wave(wave, self.context, self.scheduler)

            # Emit outcome events
            for result in wave_results:
                if result.status == TaskStatus.SUCCEEDED:
                    yield ProgressEvent(
                        event_type="task_succeeded",
                        task_id=result.task_id,
                        status=result.status,
                        detail=f"Completed in {result.duration_seconds:.2f}s" if result.duration_seconds else "Completed",
                    )
                else:
                    yield ProgressEvent(
                        event_type="task_failed",
                        task_id=result.task_id,
                        status=result.status,
                        detail=result.error or "Unknown error",
                    )

        end_time = datetime.now(tz=timezone.utc)

        # Build final report
        results_map = self.context.results
        succeeded = sum(1 for r in results_map.values() if r.status == TaskStatus.SUCCEEDED)
        failed = sum(1 for r in results_map.values() if r.status in (TaskStatus.FAILED, TaskStatus.TIMED_OUT))
        cancelled = sum(1 for r in results_map.values() if r.status in (TaskStatus.CANCELLED, TaskStatus.SKIPPED))

        overall = TaskStatus.SUCCEEDED
        if self.context.is_cancelled():
            overall = TaskStatus.CANCELLED
        elif failed > 0:
            overall = TaskStatus.FAILED

        yield ProgressEvent(
            event_type="plan_completed",
            task_id=None,
            status=overall,
            detail=f"Succeeded={succeeded}, Failed={failed}, Cancelled/Skipped={cancelled}",
        )

    def get_report(self) -> ExecutionReport:
        """Return the final typed execution report."""
        results = self.context.results
        succeeded = sum(1 for r in results.values() if r.status == TaskStatus.SUCCEEDED)
        failed = sum(1 for r in results.values() if r.status in (TaskStatus.FAILED, TaskStatus.TIMED_OUT))
        cancelled = sum(1 for r in results.values() if r.status in (TaskStatus.CANCELLED, TaskStatus.SKIPPED))

        overall = TaskStatus.SUCCEEDED
        if self.context.is_cancelled():
            overall = TaskStatus.CANCELLED
        elif failed > 0:
            overall = TaskStatus.FAILED

        return ExecutionReport(
            run_id=self._run_id,
            overall_status=overall,
            results=results,
            total_tasks=len(results),
            succeeded=succeeded,
            failed=failed,
            cancelled=cancelled,
        )
