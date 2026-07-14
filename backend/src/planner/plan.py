"""
ASEP — Plan Manager
"""

import logging

from src.planner.models import DecomposedPlan, SubTask

logger = logging.getLogger(__name__)


class PlanManager:
    """Manages plans, including topological sorting of execution ordering."""

    def __init__(self) -> None:
        pass

    def get_execution_order(self, plan: DecomposedPlan) -> list[str]:
        """Resolve a topologically sorted execution order where dependencies run first.
        
        Kahn's Algorithm is used to construct a safe sequential list of task IDs.
        """
        # Map in-degrees (number of dependencies each node has)
        in_degree = {t.id: len(t.depends_on) for t in plan.tasks}
        
        # Build children mapping: parent_id -> list of child_ids
        children = {t.id: [] for t in plan.tasks}
        for task in plan.tasks:
            for parent in task.depends_on:
                if parent in children:
                    children[parent].append(task.id)

        # Start queue with nodes that have 0 dependencies
        queue = [tid for tid, degree in in_degree.items() if degree == 0]
        # Sort to keep selection order deterministic
        queue.sort()
        
        order = []
        while queue:
            curr = queue.pop(0)
            order.append(curr)
            
            for child in children[curr]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)
                    
        return order

    def reorder_plan_tasks(self, plan: DecomposedPlan) -> DecomposedPlan:
        """Return a new DecomposedPlan where tasks are sorted topologically."""
        order = self.get_execution_order(plan)
        task_map = {t.id: t for t in plan.tasks}
        
        sorted_tasks = [task_map[tid] for tid in order if tid in task_map]
        
        return DecomposedPlan(
            tasks=sorted_tasks,
            rationale=plan.rationale
        )
