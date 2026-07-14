"""
ASEP — Authentication Schemas
"""

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict


class TokenResponse(BaseModel):
    """OAuth2 compatible token response."""
    access_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Request payload for refreshing an access token."""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Response containing new access and refresh tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Internal JWT payload representation."""
    sub: str
    role: str
    type: Literal["access", "refresh"]
    exp: int
    iat: int
    jti: str


class UserResponse(BaseModel):
    """Response schema for User entity."""
    id: uuid.UUID
    username: str
    email: str
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
