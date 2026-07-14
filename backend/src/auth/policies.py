"""
ASEP — Authorization Policies
"""

from src.auth.permissions import Permission
from src.auth.roles import Role

# Viewer gets read-only access to most things
VIEWER_PERMISSIONS = frozenset({
    Permission.AGENT_RUNS_READ,
    Permission.TASKS_READ,
    Permission.MEMORY_READ,
    Permission.AUDIT_READ,
    Permission.KNOWLEDGE_READ,
})

# Operator can manage runs and tasks but not users or system settings
OPERATOR_PERMISSIONS = VIEWER_PERMISSIONS | frozenset({
    Permission.AGENT_RUNS_CREATE,
    Permission.AGENT_RUNS_UPDATE,
    Permission.AGENT_RUNS_DELETE,
    Permission.TASKS_CREATE,
    Permission.TASKS_UPDATE,
    Permission.TASKS_DELETE,
    Permission.TASKS_EXECUTE,
    Permission.MEMORY_WRITE,
    Permission.KNOWLEDGE_WRITE,
})

# Developer can do what an operator does, plus maybe some extra debugging/system actions
DEVELOPER_PERMISSIONS = OPERATOR_PERMISSIONS

# Admin can do everything
ADMIN_PERMISSIONS = frozenset(Permission)

# System has all permissions (used by internal service accounts/agents)
SYSTEM_PERMISSIONS = frozenset(Permission)


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.VIEWER: VIEWER_PERMISSIONS,
    Role.OPERATOR: OPERATOR_PERMISSIONS,
    Role.DEVELOPER: DEVELOPER_PERMISSIONS,
    Role.ADMIN: ADMIN_PERMISSIONS,
    Role.SYSTEM: SYSTEM_PERMISSIONS,
}


def get_permissions_for_role(role: str) -> frozenset[Permission]:
    """Get the set of permissions associated with a role."""
    try:
        r = Role(role)
        return ROLE_PERMISSIONS.get(r, frozenset())
    except ValueError:
        return frozenset()
