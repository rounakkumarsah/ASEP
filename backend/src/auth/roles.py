"""
ASEP — Authorization Roles
"""

from enum import StrEnum


class Role(StrEnum):
    """Available static roles in the system."""

    ADMIN = "admin"
    DEVELOPER = "developer"
    OPERATOR = "operator"
    VIEWER = "viewer"
    SYSTEM = "system"
