"""
ASEP — Plan Integrity Validator
"""

import logging

from src.planner.models import DecomposedPlan

logger = logging.getLogger(__name__)


class PlanValidator:
    """Verifies the integrity, completeness, and acyclic properties of a DecomposedPlan."""

    def validate_plan(self, plan: DecomposedPlan) -> tuple[bool, str | None]:
        """Validate that the plan has no cyclic dependencies or dangling parent references.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not plan.tasks:
            return False, "Plan contains no subtasks."

        task_ids = {t.id for t in plan.tasks}
        
        # 1. Check for duplicate task IDs and empty IDs
        seen_ids = set()
        for task in plan.tasks:
            if not task.id:
                return False, f"Task '{task.title}' has an empty ID."
            if task.id in seen_ids:
                return False, f"Duplicate task ID detected: '{task.id}'"
            seen_ids.add(task.id)

        # 2. Check for dangling parent references (dependencies that do not exist)
        for task in plan.tasks:
            for dep in task.depends_on:
                if dep not in task_ids:
                    return False, f"Task '{task.id}' depends on non-existent task '{dep}'"

        # 3. Cycle Detection using DFS (topological traversal)
        # 0 = Unvisited, 1 = Visiting (in current path), 2 = Visited (fully checked)
        state: dict[str, int] = {t.id: 0 for t in plan.tasks}
        adj = {t.id: t.depends_on for t in plan.tasks}

        def has_cycle(node: str) -> bool:
            state[node] = 1  # Mark as visiting
            for neighbor in adj[node]:
                if state[neighbor] == 1:
                    # Found a loop back to a node in the current path
                    return True
                if state[neighbor] == 0:
                    if has_cycle(neighbor):
                        return True
            state[node] = 2  # Mark as fully visited
            return False

        for task in plan.tasks:
            if state[task.id] == 0:
                if has_cycle(task.id):
                    return False, f"Cyclic dependency loop detected starting from task '{task.id}'"

        logger.info("Plan validation completed successfully. Plan is a valid DAG.")
        return True, None
