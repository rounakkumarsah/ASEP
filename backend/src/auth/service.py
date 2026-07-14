"""
ASEP — Authentication Service
"""

import uuid

from fastapi.security import OAuth2PasswordRequestForm
import jwt

from src.auth.jwt import create_access_token, create_refresh_token, decode_token
from src.auth.password import verify_password
from src.auth.schemas import RefreshTokenResponse, TokenPayload
from src.config.settings import get_settings
from src.db.models.user import User
from src.services.user_service import UserService


class AuthService:
    """Authentication and token lifecycle management."""

    def __init__(self, user_service: UserService) -> None:
        self.user_service = user_service

    async def authenticate_user(self, form_data: OAuth2PasswordRequestForm) -> User | None:
        """Authenticate a user using OAuth2 password flow."""
        user = await self.user_service.get_user_by_username(form_data.username)
        if not user:
            return None
            
        if not verify_password(form_data.password, user.hashed_password):
            return None
            
        if not user.is_active:
            return None
            
        return user

    def create_login_tokens(self, user: User) -> RefreshTokenResponse:
        """Create new access and refresh tokens for a user."""
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        return RefreshTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def refresh_tokens(self, refresh_token: str) -> RefreshTokenResponse:
        """Refresh tokens using a valid refresh token."""
        settings = get_settings()
        
        try:
            payload = decode_token(refresh_token, settings.JWT_REFRESH_SECRET_KEY)
            token_data = TokenPayload(**payload)
        except jwt.PyJWTError as e:
            # Re-raise as ValueError to let API layer map it to 400 Bad Request
            # Or map it to something specific
            raise ValueError(f"Invalid refresh token: {e!s}") from e
            
        if token_data.type != "refresh":
            raise ValueError("Invalid token type")
            
        try:
            user_id = uuid.UUID(token_data.sub)
            user = await self.user_service.get_user(user_id)
        except Exception as e:
            raise ValueError("User not found") from e
            
        if not user.is_active:
            raise ValueError("Inactive user")
            
        return self.create_login_tokens(user)
