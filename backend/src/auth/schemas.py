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
    mfa_enabled: bool = False
    account_type: Optional[str] = "individual"
    timezone: Optional[str] = "UTC"
    locale: Optional[str] = "en"
    current_plan: Optional[str] = "free"
    last_login: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class SignupRequest(BaseModel):
    firstName: str = Field(..., min_length=1)
    lastName: str = Field(..., min_length=1)
    username: Optional[str] = None
    company: Optional[str] = None
    email: str
    password: str = Field(..., min_length=12)
    acceptTerms: bool = Field(..., Literal=True)
    captchaToken: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str
    code: Optional[str] = None  # MFA OTP code if mfa_enabled
    rememberMe: Optional[bool] = False


class VerifyEmailRequest(BaseModel):
    email: Optional[str] = None
    code: Optional[str] = None
    token: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: str


class ResendVerificationRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(..., min_length=12)


class ProfileUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    avatar: Optional[str] = None
    account_type: Optional[str] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None


class CheckUsernameResponse(BaseModel):
    available: bool
    suggestions: list[str] = []


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
