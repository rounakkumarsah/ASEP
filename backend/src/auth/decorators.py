"""
ASEP — Authorization Decorators/Dependencies
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import SecurityScopes

from src.auth.dependencies import get_current_user
from src.auth.policies import get_permissions_for_role
from src.db.models.user import User


def RequirePermission(permission: str):
    """
    Dependency factory to enforce RBAC permissions on a route.
    
    This integrates with FastAPI's SecurityScopes to seamlessly show
    required permissions in the OpenAPI docs.
    """
    async def permission_checker(
        security_scopes: SecurityScopes,
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if not current_user.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned role.",
            )
            
        user_permissions = get_permissions_for_role(current_user.role)
        
        # Check if the user has the explicitly required permission (from the factory)
        if permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required: {permission}",
            )
            
        # Also enforce any scopes declared in the Depends/Security call itself
        for scope in security_scopes.scopes:
            if scope not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Not enough permissions. Missing scope: {scope}",
                )
                
        return current_user

    return Depends(permission_checker)
