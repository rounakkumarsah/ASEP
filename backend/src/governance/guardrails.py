"""
ASEP — Static Guardrails
"""

from abc import ABC, abstractmethod

from src.governance.intent import ActionIntent
from src.governance.decision import DecisionResult


class Guardrail(ABC):
    """Abstract base class for static boundary checks."""
    
    @abstractmethod
    def evaluate(self, intent: ActionIntent) -> DecisionResult | None:
        """Return DENY if the boundary is breached, otherwise None."""
        pass


class SystemPromptGuardrail(Guardrail):
    """Blocks any attempt to modify system prompts."""
    
    def evaluate(self, intent: ActionIntent) -> DecisionResult | None:
        if intent.action_type == "write" and "system_prompt" in intent.target.lower():
            return DecisionResult.DENY
        return None


class WorkspaceGuardrail(Guardrail):
    """Blocks file system access outside the workspace."""
    
    def evaluate(self, intent: ActionIntent) -> DecisionResult | None:
        # Simplified string checking; a real implementation would use os.path.abspath
        if intent.action_type in ("read_file", "write_file", "run_command"):
            target = intent.target.lower()
            if ".." in target or target.startswith("/etc") or target.startswith("c:\\windows"):
                return DecisionResult.DENY
        return None
