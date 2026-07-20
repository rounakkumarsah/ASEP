"""
ASEP — Authentication Dependencies
"""

import uuid
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
import jwt

from src.api.dependencies import get_uow_factory
from src.auth.jwt import decode_token
from src.auth.schemas import TokenPayload
from src.auth.service import AuthService
from src.config.settings import get_settings
from src.db.models.user import User
from src.services.user_service import UserService
from src.cache.redis import get_redis_client

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_user_service(
    uow: Annotated[callable, Depends(get_uow_factory)]
) -> UserService:
    """Provide a configured UserService."""
    return UserService(uow)


def get_auth_service(
    user_service: Annotated[UserService, Depends(get_user_service)]
) -> AuthService:
    """Provide a configured AuthService."""
    return AuthService(user_service)


async def get_current_user(
    request: Request,
    user_service: Annotated[UserService, Depends(get_user_service)],
    token_from_header: Annotated[Optional[str], Depends(oauth2_scheme)] = None,
) -> User:
    """Dependency to retrieve the currently authenticated user from cookie or token header."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 1. Resolve token from HttpOnly Cookie first
    token = request.cookies.get("access_token")
    
    # 2. Fall back to Authorization Header
    if not token:
        token = token_from_header

    if not token:
        raise credentials_exception

    # Check if token is blacklisted in Redis
    redis = get_redis_client()
    is_revoked = await redis.get(f"revoked_token:{token}")
    if is_revoked:
        raise credentials_exception

    settings = get_settings()
    try:
        payload = decode_token(token, settings.JWT_SECRET_KEY)
        token_data = TokenPayload(**payload)
        
        if token_data.type != "access":
            raise credentials_exception
            
        user_id = uuid.UUID(token_data.sub)
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception
        
    try:
        user = await user_service.get_user(user_id)
    except Exception:
        raise credentials_exception
        
    if not user.is_active or user.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user account")
        
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
