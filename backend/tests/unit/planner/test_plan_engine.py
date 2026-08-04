"""
ASEP — Unit Tests for Planner Module
"""

import pytest
from src.planner.plan import (
    DependencyGraph,
    DynamicReplanner,
    ExecutionPlan,
    PlanGenerator,
    PlanTask,
    TaskStatus,
)


def test_dependency_graph_batches():
    t1 = PlanTask(id="1", title="Task 1", description="")
    t2 = PlanTask(id="2", title="Task 2", description="")
    t3 = PlanTask(id="3", title="Task 3", description="", dependencies=["1", "2"])

    graph = DependencyGraph([t1, t2, t3])
    assert graph.validate_dag() is True

    batches = graph.get_executable_batches()
    assert len(batches) == 2
    assert set(t.id for t in batches[0]) == {"1", "2"}
    assert [t.id for t in batches[1]] == ["3"]


def test_dependency_graph_cycle_detection():
    t1 = PlanTask(id="1", title="Task 1", description="", dependencies=["2"])
    t2 = PlanTask(id="2", title="Task 2", description="", dependencies=["1"])

    graph = DependencyGraph([t1, t2])
    assert graph.validate_dag() is False


def test_plan_generator():
    gen = PlanGenerator()
    plan = gen.create_plan("Research RAG optimization")

    assert len(plan.tasks) == 3
    assert plan.goal == "Research RAG optimization"


def test_dynamic_replanner():
    gen = PlanGenerator()
    plan = gen.create_plan("General task goal")
    initial_version = plan.version

    t2 = plan.tasks[1]
    replanner = DynamicReplanner()
    updated_plan = replanner.handle_task_failure(plan, t2.id, "API timeout")

    assert updated_plan.version == initial_version + 1
    assert t2.status == TaskStatus.FAILED
    assert any("Recover from" in t.title for t in updated_plan.tasks)
