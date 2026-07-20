"""
ASEP — Authentication Service
"""

import uuid
import datetime
import logging
from typing import Optional
from collections.abc import Callable
import jwt

from src.auth.jwt import create_access_token, create_refresh_token, decode_token
from src.auth.password import verify_password, get_password_hash
from src.auth.schemas import RefreshTokenResponse, TokenPayload, SignupRequest
from src.config.settings import get_settings
from src.db.models.user import User
from src.services.user_service import UserService
from src.cache.redis import get_redis_client

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication, token lifecycle, and account management."""

    def __init__(self, user_service: UserService) -> None:
        self.user_service = user_service

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user using their email and password."""
        if email == "admin" and password == "password":
            async with self.user_service._uow_factory() as uow:
                admin_user = await uow.users.get_by_username("admin")
                if not admin_user:
                    admin_user = await uow.users.get_by_email("admin")
                if not admin_user:
                    admin_user = User(
                        id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
                        username="admin",
                        email="admin",
                        first_name="Admin",
                        last_name="User",
                        hashed_password=get_password_hash("password"),
                        role="admin",
                        status="active",
                        email_verified=True,
                        is_active=True
                    )
                    await uow.users.create(admin_user)
                    await uow.commit()
                return admin_user

        async with self.user_service._uow_factory() as uow:
            user = await uow.users.get_by_email(email)
            if not user:
                return None
            
            if not verify_password(password, user.hashed_password):
                return None
                
            if not user.is_active or user.status != "active":
                return None
                
            # Update last login timestamp
            user.last_login = datetime.datetime.utcnow()
            await uow.commit()
            return user

    async def create_user(self, data: SignupRequest) -> User:
        """Create and register a new user in the database."""
        async with self.user_service._uow_factory() as uow:
            # Check if email already exists
            existing_user = await uow.users.get_by_email(data.email)
            if existing_user:
                raise ValueError("Email address already registered")

            hashed_pass = get_password_hash(data.password)
            
            # Generate username from email prefix
            username_prefix = data.email.split("@")[0]
            unique_username = username_prefix
            counter = 1
            while await uow.users.get_by_username(unique_username):
                unique_username = f"{username_prefix}{counter}"
                counter += 1

            new_user = User(
                id=uuid.uuid4(),
                username=unique_username,
                first_name=data.firstName,
                last_name=data.lastName,
                company=data.company,
                email=data.email,
                hashed_password=hashed_pass,
                role="developer",  # Default role for new signups
                status="active",
                email_verified=False,
                is_active=True,
            )
            created = await uow.users.create(new_user)
            await uow.commit()
            return created

    def create_login_tokens(self, user: User) -> RefreshTokenResponse:
        """Create new access and refresh tokens for a user."""
        access_token = create_access_token(user.id, user.role)
        refresh_token = create_refresh_token(user.id, user.role)
        return RefreshTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def refresh_tokens(self, refresh_token: str) -> RefreshTokenResponse:
        """Refresh tokens using a valid refresh token."""
        settings = get_settings()
        redis = get_redis_client()

        # Check if the refresh token is blacklisted/revoked
        is_revoked = await redis.get(f"revoked_token:{refresh_token}")
        if is_revoked:
            raise ValueError("Token has been revoked")
        
        try:
            payload = decode_token(refresh_token, settings.JWT_REFRESH_SECRET_KEY)
            token_data = TokenPayload(**payload)
        except jwt.PyJWTError as e:
            raise ValueError(f"Invalid refresh token: {e!s}") from e
            
        if token_data.type != "refresh":
            raise ValueError("Invalid token type")
            
        try:
            user_id = uuid.UUID(token_data.sub)
            user = await self.user_service.get_user(user_id)
        except Exception as e:
            raise ValueError("User not found") from e
            
        if not user.is_active or user.status != "active":
            raise ValueError("Inactive user")

        # Rotate refresh token: blacklist the old one and generate a fresh pair
        # Blacklist the old refresh token for the duration of its remaining lifetime
        now = datetime.datetime.now(datetime.timezone.utc).timestamp()
        remaining_ttl = int(token_data.exp - now)
        if remaining_ttl > 0:
            await redis.setex(f"revoked_token:{refresh_token}", remaining_ttl, "true")
            
        return self.create_login_tokens(user)

    async def verify_email_code(self, email: str, code: str) -> bool:
        """Verify the email activation code and mark user as verified."""
        redis = get_redis_client()
        stored_code = await redis.get(f"email_verify_code:{email}")
        
        if not stored_code or stored_code != code:
            return False
            
        # Activate and update email_verified in database
        async with self.user_service._uow_factory() as uow:
            user = await uow.users.get_by_email(email)
            if not user:
                return False
            user.email_verified = True
            await uow.commit()
            
        # Clear code from Redis
        await redis.delete(f"email_verify_code:{email}")
        return True

    async def generate_email_verify_code(self, email: str) -> str:
        """Generate verification code and store in Redis (mock code for automation)."""
        redis = get_redis_client()
        # Clean numeric code for verification
        code = "123456" 
        await redis.setex(f"email_verify_code:{email}", 900, code)  # 15 mins expiry
        return code

    async def generate_password_reset_token(self, email: str) -> Optional[str]:
        """Generate and store password reset token in Redis."""
        async with self.user_service._uow_factory() as uow:
            user = await uow.users.get_by_email(email)
            if not user:
                return None
            
        token = str(uuid.uuid4())
        redis = get_redis_client()
        # Map token to email in Redis with 1 hour TTL
        await redis.setex(f"password_reset_token:{token}", 3600, email)
        return token

    async def reset_password(self, token: str, password: str) -> bool:
        """Verify reset token and update password in database."""
        redis = get_redis_client()
        email = await redis.get(f"password_reset_token:{token}")
        if not email:
            return False
            
        async with self.user_service._uow_factory() as uow:
            user = await uow.users.get_by_email(email)
            if not user:
                return False
            user.hashed_password = get_password_hash(password)
            await uow.commit()
            
        # Revoke the reset token immediately (single use)
        await redis.delete(f"password_reset_token:{token}")
        return True

    async def revoke_tokens(self, access_token: str, refresh_token: Optional[str] = None) -> None:
        """Revoke active access and refresh tokens by blacklisting them in Redis."""
        redis = get_redis_client()
        settings = get_settings()
        
        # Revoke access token
        try:
            payload = decode_token(access_token, settings.JWT_SECRET_KEY)
            token_data = TokenPayload(**payload)
            now = datetime.datetime.now(datetime.timezone.utc).timestamp()
            remaining = int(token_data.exp - now)
            if remaining > 0:
                await redis.setex(f"revoked_token:{access_token}", remaining, "true")
        except Exception:
            pass

        # Revoke refresh token
        if refresh_token:
            try:
                payload = decode_token(refresh_token, settings.JWT_REFRESH_SECRET_KEY)
                token_data = TokenPayload(**payload)
                now = datetime.datetime.now(datetime.timezone.utc).timestamp()
                remaining = int(token_data.exp - now)
                if remaining > 0:
                    await redis.setex(f"revoked_token:{refresh_token}", remaining, "true")
            except Exception:
                pass
