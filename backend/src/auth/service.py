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
from src.services.email_service import EmailService
from src.cache.redis import get_redis_client

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication, token lifecycle, and account management."""

    def __init__(self, user_service: UserService, email_service: EmailService) -> None:
        self.user_service = user_service
        self.email_service = email_service

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user using their email and password."""
        async with self.user_service._uow_factory() as uow:
            user = await uow.users.get_by_email(email)
            if not user:
                return None

            if not user.hashed_password or not verify_password(password, user.hashed_password):
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

    async def verify_email_code(self, email: Optional[str] = None, code: Optional[str] = None, token: Optional[str] = None) -> bool:
        """Verify the email activation code or token and mark user as verified."""
        redis = get_redis_client()
        
        # Check token first
        if token:
            email_bytes = await redis.get(f"email_verify_token:{token}")
            if not email_bytes:
                return False
            email = email_bytes if isinstance(email_bytes, str) else email_bytes.decode("utf-8")
            # Clear token from Redis (one-time use)
            await redis.delete(f"email_verify_token:{token}")
        elif email and code:
            stored_code_bytes = await redis.get(f"email_verify_code:{email}")
            if not stored_code_bytes:
                return False
            stored_code = stored_code_bytes if isinstance(stored_code_bytes, str) else stored_code_bytes.decode("utf-8")
            if stored_code != code:
                return False
            # Clear code from Redis (one-time use)
            await redis.delete(f"email_verify_code:{email}")
        else:
            return False
            
        # Activate and update email_verified in database
        async with self.user_service._uow_factory() as uow:
            user = await uow.users.get_by_email(email)
            if not user:
                return False
            user.email_verified = True
            await uow.commit()
            
        # Also clean up any matching code to be one-time
        if token:
            await redis.delete(f"email_verify_code:{email}")
            
        # Send welcome email
        await self.email_service.send_welcome_email(user.email, f"{user.first_name} {user.last_name}")
        return True

    async def generate_email_verify_code(self, email: str) -> str:
        """Generate verification code, store in Redis, and send verify email."""
        import random
        import uuid
        redis = get_redis_client()
        settings = get_settings()
        
        # 1. Generate code (for E2E code compatibility)
        code = str(random.randint(100000, 999999)) if settings.APP_ENV == "production" else "123456"
        await redis.setex(f"email_verify_code:{email}", 900, code)
        
        # 2. Generate token (for link-based verification)
        token = str(uuid.uuid4())
        await redis.setex(f"email_verify_token:{token}", 900, email)
        
        # Fetch username for email
        async with self.user_service._uow_factory() as uow:
            user = await uow.users.get_by_email(email)
            username = user.username if user else email

        # 3. Send verification email using token
        await self.email_service.send_verification_email(email, username, token)
        return code

    async def resend_verification_code(self, email: str) -> bool:
        """Regenerate verification code, store in Redis, and send resend email."""
        async with self.user_service._uow_factory() as uow:
            user = await uow.users.get_by_email(email)
            if not user:
                return False

        import random
        redis = get_redis_client()
        settings = get_settings()
        code = str(random.randint(100000, 999999)) if settings.APP_ENV == "production" else "123456"
        await redis.setex(f"email_verify_code:{email}", 900, code)  # 15 mins expiry

        # Send resend verification email
        await self.email_service.send_resend_verification_email(email, user.username, code)
        return True

    async def generate_password_reset_token(self, email: str) -> Optional[str]:
        """Generate and store password reset token in Redis, and send forgot password email."""
        async with self.user_service._uow_factory() as uow:
            user = await uow.users.get_by_email(email)
            if not user:
                return None
            
        token = str(uuid.uuid4())
        redis = get_redis_client()
        # Map token to email in Redis with 1 hour TTL
        await redis.setex(f"password_reset_token:{token}", 3600, email)
        
        # Send forgot password email
        await self.email_service.send_reset_password_email(email, token)
        return token

    async def reset_password(self, token: str, password: str) -> bool:
        """Verify reset token, update password, and send confirmation email."""
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
        
        # Send password changed confirmation email
        await self.email_service.send_password_changed_email(email)
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

    async def update_user(self, user_id: uuid.UUID, data: "ProfileUpdateRequest") -> User:
        """Update user profile information."""
        async with self.user_service._uow_factory() as uow:
            user = await uow.users.get(user_id)
            if not user:
                raise ValueError("User not found")
                
            if data.username and data.username != user.username:
                existing = await uow.users.get_by_username(data.username)
                if existing:
                    raise ValueError("Username already taken")
                user.username = data.username
                
            if data.first_name is not None:
                user.first_name = data.first_name
            if data.last_name is not None:
                user.last_name = data.last_name
            if data.avatar is not None:
                user.avatar_url = data.avatar
                
            await uow.commit()
            return user

    async def get_or_create_oauth_user(self, profile: object) -> "User":
        """Find or create a User from an OAuth provider profile.

        Lookup priority:
          1. Match on (oauth_provider, oauth_id) - most reliable.
          2. Match on email - links existing account to OAuth.
          3. Create a brand-new OAuth user.

        All OAuth users get email_verified=True and hashed_password=None.
        """
        from sqlalchemy import select
        from src.db.models.user import User as UserModel

        async with self.user_service._uow_factory() as uow:
            stmt = select(UserModel).where(
                UserModel.oauth_provider == profile.provider,
                UserModel.oauth_id == profile.oauth_id,
            )
            result = await uow._session.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                if profile.avatar_url and user.avatar_url != profile.avatar_url:
                    user.avatar_url = profile.avatar_url
                user.last_login = datetime.datetime.now(datetime.timezone.utc)
                await uow.commit()
                return user

            user = await uow.users.get_by_email(profile.email)
            if user:
                user.oauth_provider = profile.provider
                user.oauth_id = profile.oauth_id
                if profile.avatar_url and not user.avatar_url:
                    user.avatar_url = profile.avatar_url
                if not user.email_verified:
                    user.email_verified = True
                user.last_login = datetime.datetime.now(datetime.timezone.utc)
                await uow.commit()
                return user

            username_base = profile.email.split("@")[0]
            username = username_base
            counter = 1
            while await uow.users.get_by_username(username):
                username = f"{username_base}{counter}"
                counter += 1

            name_parts = (profile.name or "").strip().split(" ", 1)
            first_name = name_parts[0] if name_parts else None
            last_name = name_parts[1] if len(name_parts) > 1 else None

            new_user = UserModel(
                id=uuid.uuid4(),
                username=username,
                email=profile.email,
                first_name=first_name,
                last_name=last_name,
                hashed_password=None,
                oauth_provider=profile.provider,
                oauth_id=profile.oauth_id,
                avatar_url=profile.avatar_url,
                email_verified=True,
                role="developer",
                status="active",
                is_active=True,
                last_login=datetime.datetime.now(datetime.timezone.utc),
            )
            created = await uow.users.create(new_user)
            await uow.commit()

            logger.info(
                "New OAuth user created",
                extra={"provider": profile.provider, "user_id": str(created.id)},
            )

            try:
                display_name = (
                    (f"{created.first_name or ''} {created.last_name or ''}").strip()
                    or created.username
                )
                await self.email_service.send_welcome_email(created.email, display_name)
            except Exception as mail_exc:
                logger.warning("Welcome email failed for OAuth user: %s", str(mail_exc))

            return created
