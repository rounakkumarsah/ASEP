"""
ASEP — Authentication Schemas
"""

import uuid
import datetime
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


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
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    email_verified: bool
    status: str
    avatar_url: Optional[str] = None
    last_login: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class SignupRequest(BaseModel):
    firstName: str = Field(..., min_length=1)
    lastName: str = Field(..., min_length=1)
    company: Optional[str] = None
    email: str
    password: str = Field(..., min_length=12)
    acceptTerms: bool = Field(..., Literal=True)
    captchaToken: str


class LoginRequest(BaseModel):
    email: str
    password: str
    rememberMe: Optional[bool] = False


class VerifyEmailRequest(BaseModel):
    email: str
    code: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(..., min_length=12)
