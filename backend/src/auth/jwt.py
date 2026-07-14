"""
ASEP — JWT Token Utilities
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from src.config.settings import get_settings


def create_token(
    subject: str | uuid.UUID,
    role: str,
    token_type: str,
    secret_key: str,
    expires_delta: timedelta,
) -> str:
    """Create a JWT token."""
    settings = get_settings()
    expire = datetime.now(timezone.utc) + expires_delta
    
    to_encode = {
        "sub": str(subject),
        "role": role,
        "type": token_type,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),
    }
    
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_access_token(subject: str | uuid.UUID, role: str) -> str:
    """Create an access token."""
    settings = get_settings()
    expires_delta = timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
    return create_token(
        subject=subject,
        role=role,
        token_type="access",
        secret_key=settings.JWT_SECRET_KEY,
        expires_delta=expires_delta,
    )


def create_refresh_token(subject: str | uuid.UUID, role: str) -> str:
    """Create a refresh token."""
    settings = get_settings()
    expires_delta = timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
    return create_token(
        subject=subject,
        role=role,
        token_type="refresh",
        secret_key=settings.JWT_REFRESH_SECRET_KEY,
        expires_delta=expires_delta,
    )


def decode_token(token: str, secret_key: str) -> dict[str, Any]:
    """Decode and validate a JWT token."""
    settings = get_settings()
    return jwt.decode(token, secret_key, algorithms=[settings.JWT_ALGORITHM])
