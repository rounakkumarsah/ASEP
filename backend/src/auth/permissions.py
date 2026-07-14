"""
ASEP — Authorization Permissions
"""

from enum import Enum


class Permission(str, Enum):
    """Granular permissions for RBAC."""
    
    # Agent Runs
    AGENT_RUNS_READ = "agent_runs:read"
    AGENT_RUNS_CREATE = "agent_runs:create"
    AGENT_RUNS_UPDATE = "agent_runs:update"
    AGENT_RUNS_DELETE = "agent_runs:delete"
    
    # Tasks
    TASKS_READ = "tasks:read"
    TASKS_CREATE = "tasks:create"
    TASKS_UPDATE = "tasks:update"
    TASKS_DELETE = "tasks:delete"
    TASKS_EXECUTE = "tasks:execute"
    
    # Memory
    MEMORY_READ = "memory:read"
    MEMORY_WRITE = "memory:write"
    
    # Audit Logs
    AUDIT_READ = "audit:read"
    
    # Knowledge Base
    KNOWLEDGE_READ = "knowledge:read"
    KNOWLEDGE_WRITE = "knowledge:write"
    
    # Users
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"
