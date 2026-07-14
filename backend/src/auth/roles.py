"""
ASEP — Authorization Roles
"""

from enum import Enum


class Role(str, Enum):
    """Available static roles in the system."""
    
    ADMIN = "admin"
    DEVELOPER = "developer"
    OPERATOR = "operator"
    VIEWER = "viewer"
    SYSTEM = "system"
