"""
ASEP — Authentication Schemas
"""

import datetime
import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    email_verified: bool
    status: str
    avatar_url: str | None = None
    mfa_enabled: bool = False
    account_type: str | None = "individual"
    timezone: str | None = "UTC"
    locale: str | None = "en"
    current_plan: str | None = "free"
    last_login: datetime.datetime | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class SignupRequest(BaseModel):
    firstName: str = Field(..., min_length=1)
    lastName: str = Field(..., min_length=1)
    username: str | None = None
    company: str | None = None
    email: str
    password: str = Field(..., min_length=12)
    acceptTerms: bool = Field(..., Literal=True)
    captchaToken: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str
    code: str | None = None  # MFA OTP code if mfa_enabled
    rememberMe: bool | None = False


class VerifyEmailRequest(BaseModel):
    email: str | None = None
    code: str | None = None
    token: str | None = None


class ForgotPasswordRequest(BaseModel):
    email: str


class ResendVerificationRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(..., min_length=12)


class ProfileUpdateRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    avatar: str | None = None
    account_type: str | None = None
    timezone: str | None = None
    locale: str | None = None


class CheckUsernameResponse(BaseModel):
    valid: bool
    available: bool
    message: str
    suggestions: list[str] | None = None


class UserQuotaResponse(BaseModel):
    tier: str
    limit: int
    used: int
    remaining: int
    reset_seconds: int


class MFASetupResponse(BaseModel):
    secret: str
    otpauth_url: str
    recovery_codes: list[str]


class MFAVerifyRequest(BaseModel):
    code: str


class MFADisableRequest(BaseModel):
    password: str
