"""
ASEP — Agent Execution Router Re-export
=======================================
Re-exports the agents router from src.routes.agents for unified routing.
"""

from src.routes.agents import router, job_connection_manager

__all__ = ["router", "job_connection_manager"]
