"""
ASEP — Background Task Queue Service
====================================
Decouples agent execution from HTTP requests using APScheduler with PostgreSQL
job store persistence. Prevents serverless timeouts (e.g. Vercel 15s limit)
without requiring Redis or Celery.

Features:
  - Enqueue agent execution (<500ms response time).
  - PostgreSQL persistent job store with automatic fallback for tests.
  - Max 100 concurrent jobs enforced per workspace.
  - 2x automatic retry with exponential backoff on failure.
  - Survives server restart with crash recovery.
  - Auto-cleanup of completed/failed jobs after 7 days.
  - WebSocket & Webhook notification triggers.
"""

from __future__ import annotations

import asyncio
import datetime
import logging
import uuid
from typing import Any

from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import func, select

from src.config.settings import get_settings
from src.db.models.queue_job import QueueJob
from src.db.postgres import _get_session_factory

logger = logging.getLogger(__name__)

# Workspace concurrency limit
MAX_CONCURRENT_JOBS_PER_WORKSPACE = 100


class ConcurrencyLimitExceededError(Exception):
    """Raised when a workspace exceeds the maximum concurrent job execution limit."""
    pass


class JobNotFoundError(Exception):
    """Raised when a specified job ID is not found in the queue_jobs table."""
    pass


async def run_agent_job(job_id: str) -> None:
    """
    Top-level module function callable by APScheduler.
    Dispatches to the supervisor background task executor.
    """
    from src.agents.supervisor import execute_agent_background_task

    await execute_agent_background_task(job_id)


class BackgroundTaskQueue:
    """
    Manages background agent executions using APScheduler backed by PostgreSQL.
    """

    _instance: BackgroundTaskQueue | None = None

    def __init__(self, scheduler: AsyncIOScheduler | None = None) -> None:
        self.settings = get_settings()
        self._scheduler = scheduler
        self._initialized = False

    def _init_scheduler(self) -> AsyncIOScheduler:
        """Initialize APScheduler with PostgreSQL job store and memory fallback."""
        if self._scheduler is not None:
            return self._scheduler

        jobstores: dict[str, Any] = {}
        raw_url = getattr(self.settings, "DATABASE_URL", "")
        sync_url = (
            raw_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
            .replace("postgres://", "postgresql://")
        )

        try:
            jobstores["default"] = SQLAlchemyJobStore(url=sync_url)
            scheduler = AsyncIOScheduler(jobstores=jobstores)
            logger.info("Configured APScheduler with PostgreSQL SQLAlchemyJobStore.")
        except Exception as exc:
            logger.warning(
                "Failed to initialize PostgreSQL job store (%s). Falling back to MemoryJobStore.",
                exc,
            )
            jobstores["default"] = MemoryJobStore()
            scheduler = AsyncIOScheduler(jobstores=jobstores)

        self._scheduler = scheduler
        return self._scheduler

    @property
    def scheduler(self) -> AsyncIOScheduler:
        if self._scheduler is None:
            self._init_scheduler()
        return self._scheduler  # type: ignore[return-value]

    def start(self) -> None:
        """Start the background task scheduler."""
        sched = self.scheduler
        if not sched.running:
            try:
                # Verify that an asyncio event loop is currently running
                asyncio.get_running_loop()
            except RuntimeError:
                logger.debug("BackgroundTaskQueue.start() deferred: no running event loop.")
                return

            try:
                sched.start()
                logger.info("BackgroundTaskQueue APScheduler started.")
            except Exception as exc:
                logger.warning(
                    "Error starting scheduler with default store (%s). Rebuilding with MemoryJobStore.",
                    exc,
                )
                self._scheduler = AsyncIOScheduler(jobstores={"default": MemoryJobStore()})
                try:
                    self._scheduler.start()
                    logger.info("BackgroundTaskQueue APScheduler started with fallback MemoryJobStore.")
                except Exception as inner_exc:
                    logger.warning("Failed to start fallback scheduler: %s", inner_exc)

        # Schedule automatic daily cleanup of jobs older than 7 days
        try:
            if sched.running and not sched.get_job("daily_job_cleanup"):
                from src.agents.supervisor import cleanup_completed_jobs

                sched.add_job(
                    cleanup_completed_jobs,
                    "interval",
                    hours=24,
                    id="daily_job_cleanup",
                    replace_existing=True,
                )
        except Exception as exc:
            logger.debug("Daily cleanup job registration deferred: %s", exc)

    def shutdown(self, wait: bool = True) -> None:
        """Gracefully shut down the background task scheduler."""
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=wait)
            logger.info("BackgroundTaskQueue APScheduler shutdown.")

    async def enqueue_agent_execution(
        self,
        user_id: uuid.UUID | str,
        spec: dict[str, Any],
        workspace_id: str = "default",
    ) -> str:
        """
        Enqueues an agent execution task. Completes in < 500ms without blocking.

        Args:
            user_id: ID of requesting user.
            spec: Input specification (prompt, model, task settings, webhook_url).
            workspace_id: Target workspace partition identifier.

        Returns:
            job_id: Unique string identifier for the enqueued job.

        Raises:
            ConcurrencyLimitExceededError: If workspace already has 100 active jobs.
        """
        if isinstance(user_id, str):
            try:
                uid = uuid.UUID(user_id)
            except ValueError:
                uid = uuid.uuid4()
        else:
            uid = user_id

        session_factory = _get_session_factory()
        job_id = uuid.uuid4()

        async with session_factory() as session:
            # 1. Enforce max 100 concurrent jobs per workspace
            count_stmt = select(func.count()).select_from(QueueJob).where(
                QueueJob.workspace_id == workspace_id,
                QueueJob.status.in_(["pending", "running"]),
            )
            count_result = await session.execute(count_stmt)
            active_jobs = count_result.scalar_one()

            if active_jobs >= MAX_CONCURRENT_JOBS_PER_WORKSPACE:
                logger.warning(
                    "Workspace %s exceeded concurrency limit: %d active jobs",
                    workspace_id,
                    active_jobs,
                )
                raise ConcurrencyLimitExceededError(
                    f"Workspace '{workspace_id}' has reached maximum concurrent jobs limit ({MAX_CONCURRENT_JOBS_PER_WORKSPACE})"
                )

            # 2. Persist new QueueJob record with status 'pending'
            new_job = QueueJob(
                id=job_id,
                user_id=uid,
                workspace_id=workspace_id,
                status="pending",
                spec=spec,
                retry_count=0,
                max_retries=2,
            )
            session.add(new_job)
            await session.commit()

        # 3. Register job in APScheduler
        self.start()
        try:
            self.scheduler.add_job(
                run_agent_job,
                args=[str(job_id)],
                id=str(job_id),
                replace_existing=True,
            )
        except Exception as exc:
            # Fallback to direct asyncio task if scheduler jobstore fails
            logger.warning("APScheduler job registration failed (%s), falling back to asyncio task", exc)
            asyncio.create_task(run_agent_job(str(job_id)))

        logger.info(
            "Enqueued agent execution job %s for workspace %s",
            job_id,
            workspace_id,
        )
        return str(job_id)

    async def get_job_status(self, job_id: str | uuid.UUID) -> str | None:
        """
        Retrieve current execution status of a job.
        Returns: 'pending' | 'running' | 'completed' | 'failed' | None.
        """
        jid = uuid.UUID(str(job_id))
        session_factory = _get_session_factory()
        async with session_factory() as session:
            stmt = select(QueueJob.status).where(QueueJob.id == jid)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def fetch_result(self, job_id: str | uuid.UUID) -> dict[str, Any] | None:
        """
        Retrieve results (code, review, tests, final_output) of a completed or partial job.
        """
        jid = uuid.UUID(str(job_id))
        session_factory = _get_session_factory()
        async with session_factory() as session:
            stmt = select(QueueJob.result).where(QueueJob.id == jid)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_job_details(self, job_id: str | uuid.UUID) -> dict[str, Any] | None:
        """
        Fetch full job metadata, execution metrics, status, error, and results.
        """
        jid = uuid.UUID(str(job_id))
        session_factory = _get_session_factory()
        async with session_factory() as session:
            stmt = select(QueueJob).where(QueueJob.id == jid)
            result = await session.execute(stmt)
            job = result.scalar_one_or_none()
            if not job:
                return None

            return {
                "job_id": str(job.id),
                "user_id": str(job.user_id),
                "workspace_id": job.workspace_id,
                "status": job.status,
                "spec": job.spec,
                "result": job.result,
                "error": job.error,
                "retry_count": job.retry_count,
                "max_retries": job.max_retries,
                "metrics": job.metrics,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "updated_at": job.updated_at.isoformat() if job.updated_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            }

    async def recover_pending_jobs(self) -> int:
        """
        Recovers jobs that were 'pending' or 'running' when the server restarted.
        Ensures persistent durability across process restarts.
        """
        session_factory = _get_session_factory()
        self.start()
        recovered_count = 0

        async with session_factory() as session:
            stmt = select(QueueJob.id).where(
                QueueJob.status.in_(["pending", "running"])
            )
            result = await session.execute(stmt)
            job_ids = result.scalars().all()

            for jid in job_ids:
                try:
                    self.scheduler.add_job(
                        run_agent_job,
                        args=[str(jid)],
                        id=str(jid),
                        replace_existing=True,
                    )
                    recovered_count += 1
                except Exception as exc:
                    logger.error("Failed to recover job %s: %s", jid, exc)

        logger.info("Recovered %d interrupted jobs on startup.", recovered_count)
        return recovered_count

    async def cleanup_old_jobs(self, retention_days: int = 7) -> int:
        """Deletes jobs completed more than retention_days ago."""
        from src.agents.supervisor import cleanup_completed_jobs

        return await cleanup_completed_jobs(retention_days=retention_days)


_task_queue: BackgroundTaskQueue | None = None


def get_task_queue() -> BackgroundTaskQueue:
    """Access the global singleton instance of BackgroundTaskQueue."""
    global _task_queue
    if _task_queue is None:
        _task_queue = BackgroundTaskQueue()
    return _task_queue
