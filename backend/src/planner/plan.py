"""
ASEP — AI Planner & Task Decomposition Engine
=============================================
Provides high-level goal decomposition, DAG dependency graph resolution,
execution plan generation, and dynamic runtime replanning.
"""

from __future__ import annotations

import enum
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PlanManager:
    """Legacy wrapper around PlanGenerator & DynamicReplanner."""
    def __init__(self) -> None:
        self.generator = PlanGenerator()
        self.replanner = DynamicReplanner()

    def create_plan(self, goal: str) -> ExecutionPlan:
        return self.generator.create_plan(goal)


class TaskStatus(enum.StrEnum):
    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PlanTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    dependencies: list[str] = Field(default_factory=list, description="IDs of prerequisite tasks")
    assigned_agent: str | None = Field(default=None, description="Suggested agent role/name")
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class ExecutionPlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal: str
    tasks: list[PlanTask] = Field(default_factory=list)
    version: int = 1
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    def get_task(self, task_id: str) -> PlanTask | None:
        for t in self.tasks:
            if t.id == task_id:
                return t
        return None


# ---------------------------------------------------------------------------
# Dependency Graph (DAG Engine)
# ---------------------------------------------------------------------------

class DependencyGraph:
    """DAG engine for validating prerequisites and topological task ordering."""

    def __init__(self, tasks: list[PlanTask]) -> None:
        self.tasks = {t.id: t for t in tasks}

    def validate_dag(self) -> bool:
        """Verifies no circular dependencies exist."""
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def _dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            task = self.tasks.get(node_id)
            if task:
                for dep in task.dependencies:
                    if dep not in visited:
                        if not _dfs(dep):
                            return False
                    elif dep in rec_stack:
                        return False

            rec_stack.remove(node_id)
            return True

        return all(not (task_id not in visited and not _dfs(task_id)) for task_id in self.tasks)

    def get_executable_batches(self) -> list[list[PlanTask]]:
        """Returns batches of tasks that can be run concurrently in topological sequence."""
        if not self.validate_dag():
            raise ValueError("Invalid dependency graph: Cycle detected.")

        completed: set[str] = set()
        remaining = set(self.tasks.keys())
        batches: list[list[PlanTask]] = []

        while remaining:
            # Tasks whose dependencies are all completed
            ready = [
                tid for tid in remaining
                if all(dep in completed for dep in self.tasks[tid].dependencies)
            ]
            if not ready:
                raise ValueError("Dependency resolution deadlock detected.")

            batch = [self.tasks[tid] for tid in ready]
            batches.append(batch)
            for tid in ready:
                completed.add(tid)
                remaining.remove(tid)

        return batches


# ---------------------------------------------------------------------------
# Task Decomposer & Plan Generator
# ---------------------------------------------------------------------------

class TaskDecomposer:
    """Decomposes goals into logical task structures."""

    def decompose(self, goal: str) -> list[PlanTask]:
        """Rule-based / heuristic task decomposition."""
        goal_lower = goal.lower()

        if "rag" in goal_lower or "knowledge" in goal_lower:
            t1 = PlanTask(title="Fetch Relevant Context", description="Search vector database for documents", assigned_agent="research")
            t2 = PlanTask(title="Analyze Documents", description="Extract key facts from context", dependencies=[t1.id], assigned_agent="research")
            t3 = PlanTask(title="Generate Final Answer", description="Synthesize answer from facts", dependencies=[t2.id], assigned_agent="supervisor")
            return [t1, t2, t3]

        # Generic multi-step fallback
        t1 = PlanTask(title="Requirement Analysis", description=f"Analyze goal: {goal}", assigned_agent="planner")
        t2 = PlanTask(title="Execution Step", description="Execute core task logic", dependencies=[t1.id], assigned_agent="executor")
        t3 = PlanTask(title="Verification & Synthesis", description="Verify output quality", dependencies=[t2.id], assigned_agent="governance")
        return [t1, t2, t3]


class PlanGenerator:
    """Generates and validates an ExecutionPlan from a user goal."""

    def __init__(self, decomposer: TaskDecomposer | None = None) -> None:
        self.decomposer = decomposer or TaskDecomposer()

    def create_plan(self, goal: str) -> ExecutionPlan:
        tasks = self.decomposer.decompose(goal)
        plan = ExecutionPlan(goal=goal, tasks=tasks)
        graph = DependencyGraph(plan.tasks)
        if not graph.validate_dag():
            raise ValueError("Generated plan contains invalid cyclic dependencies.")
        return plan


# ---------------------------------------------------------------------------
# Dynamic Replanner
# ---------------------------------------------------------------------------

class DynamicReplanner:
    """Modifies active execution plans dynamically based on runtime feedback."""

    def handle_task_failure(self, plan: ExecutionPlan, failed_task_id: str, error_msg: str) -> ExecutionPlan:
        task = plan.get_task(failed_task_id)
        if not task:
            return plan

        task.status = TaskStatus.FAILED
        task.error = error_msg

        # Add a recovery task
        recovery_task = PlanTask(
            title=f"Recover from: {task.title}",
            description=f"Fix failure in task {failed_task_id}: {error_msg}",
            dependencies=[dep for dep in task.dependencies if dep != task.id],
            assigned_agent="executor",
        )

        # Re-route downstream dependencies to wait for recovery task
        for t in plan.tasks:
            if failed_task_id in t.dependencies:
                t.dependencies.remove(failed_task_id)
                t.dependencies.append(recovery_task.id)

        plan.tasks.append(recovery_task)
        plan.version += 1
        plan.updated_at = datetime.now(UTC).isoformat()
        logger.info("Dynamic replan applied for failed task '%s' (Plan v%d)", failed_task_id, plan.version)
        return plan
