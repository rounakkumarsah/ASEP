"""
ASEP — Tool Permissions mapping
"""

class ToolPermission:
    """Standard permission scopes required to execute specific class tools."""
    FS_READ = "fs:read"
    FS_WRITE = "fs:write"
    SYS_INFO = "sys:info"
    WEB_SEARCH = "web:search"


def verify_tool_permissions(
    tool_required: list[str],
    user_granted: list[str],
) -> tuple[bool, str | None]:
    """Validates if the user's granted permissions satisfy all tool requirements.
    
    Returns:
        Tuple of (is_authorized, error_reason)
    """
    granted_set = set(user_granted)
    for permission in tool_required:
        if permission not in granted_set:
            return False, f"Missing required permission scope: '{permission}'"
    return True, None
