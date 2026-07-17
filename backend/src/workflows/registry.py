"""
ASEP — Workflows Registry
"""

import logging
from typing import Any, Dict, List, Optional
from src.workflows.models import WorkflowDefinition

logger = logging.getLogger(__name__)


class WorkflowRegistry:
    """Thread-safe registry for dynamically managing workflow graphs and schemas."""

    def __init__(self) -> None:
        self._workflows: Dict[str, WorkflowDefinition] = {}

    def register_workflow(self, definition: WorkflowDefinition) -> None:
        """Register a new workflow definition."""
        self._workflows[definition.workflow_id] = definition
        logger.info(f"Registered workflow: {definition.workflow_id} (v{definition.version})")

    def unregister_workflow(self, workflow_id: str) -> None:
        """Unregister an existing workflow definition."""
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]
            logger.info(f"Unregistered workflow: {workflow_id}")

    def discover_workflows(self) -> List[WorkflowDefinition]:
        """List all currently registered workflow definitions."""
        return list(self._workflows.values())

    def lookup(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Fetch workflow details by unique identifier."""
        return self._workflows.get(workflow_id)

    def enable(self, workflow_id: str) -> None:
        """Enables a workflow definition for execution."""
        wf = self.lookup(workflow_id)
        if wf:
            wf.is_enabled = True
            logger.info(f"Enabled workflow: {workflow_id}")

    def disable(self, workflow_id: str) -> None:
        """Disables a workflow definition from execution."""
        wf = self.lookup(workflow_id)
        if wf:
            wf.is_enabled = False
            logger.info(f"Disabled workflow: {workflow_id}")

    def version(self, workflow_id: str) -> Optional[str]:
        """Gets semantic version of a workflow."""
        wf = self.lookup(workflow_id)
        return wf.version if wf else None

    def metadata(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Gets capability and registration metadata."""
        wf = self.lookup(workflow_id)
        if not wf:
            return None
        return {
            "workflow_id": wf.workflow_id,
            "version": wf.version,
            "required_agents": wf.required_agents,
            "required_tools": wf.required_tools,
            "permissions": wf.permissions
        }


_global_workflow_registry: Optional[WorkflowRegistry] = None

def get_workflow_registry() -> WorkflowRegistry:
    global _global_workflow_registry
    if _global_workflow_registry is None:
        _global_workflow_registry = WorkflowRegistry()
    return _global_workflow_registry
