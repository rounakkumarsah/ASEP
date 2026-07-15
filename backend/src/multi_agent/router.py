"""
ASEP — Message Router
"""

from src.multi_agent.contracts import AgentRole


class MessageRouter:
    """Helper class for the Supervisor to determine the next agent in the pipeline."""

    @staticmethod
    def get_next_role(current_role: AgentRole) -> AgentRole | None:
        """Deterministic routing for the standard pipeline."""
        pipeline = [
            AgentRole.SUPERVISOR,
            AgentRole.PLANNER,
            AgentRole.EXECUTOR,
            AgentRole.EVALUATOR,
            AgentRole.REFLECTOR,
        ]
        
        try:
            idx = pipeline.index(current_role)
            if idx + 1 < len(pipeline):
                return pipeline[idx + 1]
        except ValueError:
            pass
            
        return None
