"""
ASEP — Authentication Service
"""

import base64
import contextlib
import datetime
import hashlib
import hmac
import json
import logging
import random
import re
import secrets
import time
import urllib.parse
import uuid

import jwt

from src.auth.jwt import create_access_token, create_refresh_token, decode_token
from src.auth.password import get_password_hash, verify_password
from src.auth.schemas import RefreshTokenResponse, SignupRequest, TokenPayload
from src.cache.redis import get_redis_client
from src.config.settings import get_settings
from src.db.models.user import User
from src.services.email_service import EmailService
from src.services.user_service import UserService

logger = logging.getLogger(__name__)

from src.auth.username import RESERVED_USERNAMES


def normalize_email(email: str) -> str:
    """Normalize email address: trim, lowercase, and handle Gmail dot/plus normalization."""
    clean = email.strip().lower()
    parts = clean.split("@")
    if len(parts) == 2:
        local_part, domain = parts[0], parts[1]
        if domain in ["gmail.com", "googlemail.com"]:
            # Remove dots and plus-tags for Gmail domain
            local_part = local_part.split("+")[0].replace(".", "")
            return f"{local_part}@{domain}"
    return clean


def _generate_totp_secret() -> str:
    """Generate RFC 6238 Base32-encoded 160-bit shared secret."""
    return base64.b32encode(secrets.token_bytes(20)).decode("utf-8").rstrip("=")


def _calculate_totp(secret: str, time_step: int) -> str:
    """Calculate 6-digit TOTP code for a given 30-second time step."""
    # Ensure correct Base32 padding
    padding = "=" * (-len(secret) % 8)
    key = base64.b32decode(secret.upper() + padding)
    msg = time_step.to_bytes(8, byteorder="big")
    hmac_hash = hmac.new(key, msg, hashlib.sha1).digest()
    offset = hmac_hash[19] & 0x0F
    code_int = int.from_bytes(hmac_hash[offset : offset + 4], byteorder="big") & 0x7FFFFFFF
    return f"{code_int % 1000000:06d}"


def _verify_totp(secret: str, code: str) -> bool:
    """Verify TOTP token allowing ±1 time step clock drift."""
    if not secret or not code:
        return False
    clean_code = code.strip().replace(" ", "")
    if len(clean_code) != 6 or not clean_code.isdigit():
        return False

    current_step = int(time.time() // 30)
    for step in (current_step, current_step - 1, current_step + 1):
        if _calculate_totp(secret, step) == clean_code:
            return True
    return False


def _write_debug(lines: list) -> None:
    """Write AUTH_DEBUG lines to /tmp/auth_debug.txt for docker cp retrieval."""
    try:
        with open("/tmp/auth_debug.txt", "w") as f:
            f.write("\n".join(lines) + "\n")
    except Exception as e:
        print(f"[AUTH_DEBUG] Failed to write debug file: {e}", flush=True)


class AuthService:
    """Authentication, token lifecycle, MFA, and account management."""

    def __init__(self, user_service: UserService, email_service: EmailService) -> None:
        self.user_service = user_service
        self.email_service = email_service

    async def authenticate_user(
        self, email: str, password: str, code: str | None = None
    ) -> tuple[User | None, str | None]:
        """Authenticate a user. Returns (user, status_code_or_error).

        status_code_or_error can be:
          - None: success
          - "MFA_REQUIRED": valid password, but MFA OTP code is needed
          - "INVALID_MFA_CODE": invalid MFA OTP or recovery code
          - "INVALID_CREDENTIALS": password mismatch or user not found
        """
        clean_email = normalize_email(email)
        async with self.user_service._uow_factory() as uow:
            user = await uow.users.get_by_email(clean_email)
            if not user:
                return None, "INVALID_CREDENTIALS"

            if not user.hashed_password or not verify_password(password, user.hashed_password):
                return None, "INVALID_CREDENTIALS"

            if not user.is_active or user.status != "active":
                return None, "INACTIVE_ACCOUNT"

            # Check MFA
            if user.mfa_enabled:
                if not code:
                    return user, "MFA_REQUIRED"

                is_valid = False
                # 1. Check TOTP
                if user.mfa_secret and _verify_totp(user.mfa_secret, code):
                    is_valid = True
                # 2. Check Recovery Code
                elif user.mfa_recovery_codes:
                    try:
                        codes = json.loads(user.mfa_recovery_codes)
                        code_clean = code.strip().lower()
                        if code_clean in [c.lower() for c in codes]:
                            codes = [c for c in codes if c.lower() != code_clean]
                            user.mfa_recovery_codes = json.dumps(codes)
                            is_valid = True
                    except Exception:
                        pass

                if not is_valid:
                    return None, "INVALID_MFA_CODE"

            # Update last login timestamp (stored as UTC without timezone to match DB column type)
            user.last_login = datetime.datetime.utcnow()
            await uow.commit()
            return user, None


    async def create_user(self, data: SignupRequest) -> User:
        """Create and register a new user in the database with strict normalization and validation."""
        clean_email = normalize_email(data.email)
        async with self.user_service._uow_factory() as uow:
            # Check if email already exists
            existing_user = await uow.users.get_by_email(clean_email)
            if existing_user:
                raise ValueError("Account already exists with this email address.")
            
            # Validate or generate username
            if data.username and data.username.strip():
                from src.auth.username import validate_username
                is_valid, normalized, err_msg = validate_username(data.username)
                if not is_valid:
                    raise ValueError(err_msg)
                
                if normalized in RESERVED_USERNAMES:
                    raise ValueError(f"Username '{normalized}' is reserved.")
                if await uow.users.get_by_username(normalized):
                    raise ValueError("Username already taken.")
                unique_username = normalized
            else:
                # Generate robust unique username
                first = re.sub(r"[^a-zA-Z0-9_]", "", data.firstName.lower())
                last = re.sub(r"[^a-zA-Z0-9_]", "", data.lastName.lower())
                base_cand = f"{first}_{last}"[:20].strip("_") or clean_email.split("@")[0][:20]
                if base_cand in RESERVED_USERNAMES or len(base_cand) < 3:
                    base_cand = f"user_{base_cand}"[:20]

                unique_username = base_cand
                counter = 1
                while (
                    unique_username.lower() in RESERVED_USERNAMES
                    or await uow.users.get_by_username(unique_username)
                ):
                    unique_username = f"{base_cand}{counter}"
                    counter += 1

            hashed_pass = get_password_hash(data.password)

            new_user = User(
                id=uuid.uuid4(),
                username=unique_username,
                first_name=data.firstName.strip(),
                last_name=data.lastName.strip(),
                company=data.company.strip() if data.company else None,
                email=clean_email,
                hashed_password=hashed_pass,
                role="developer",
                status="active",
                email_verified=False,
                is_active=True,
                mfa_enabled=False,
                account_type="individual",
                timezone="UTC",
                locale="en",
                current_plan="free",
            )
            created = await uow.users.create(new_user)
            try:
                await uow.commit()
            except Exception as e:
                err_str = str(e).lower()
                if "unique" in err_str or "duplicate key" in err_str:
                    if "username" in err_str:
                        raise ValueError("Username already exists.")
                    if "email" in err_str:
                        raise ValueError("Account already exists with this email address.")
                raise e
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
        if redis:
            try:
                is_revoked = await redis.get(f"revoked_token:{refresh_token}")
                if is_revoked:
                    raise ValueError("Token has been revoked")
            except ValueError:
                raise
            except Exception:
                pass

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
        if redis:
            try:
                now = datetime.datetime.now(datetime.UTC).timestamp()
                remaining_ttl = int(token_data.exp - now)
                if remaining_ttl > 0:
                    await redis.setex(f"revoked_token:{refresh_token}", remaining_ttl, "true")
            except Exception:
                pass

        return self.create_login_tokens(user)

    async def verify_email_code(self, email: str | None = None, code: str | None = None, token: str | None = None) -> bool:
        """Verify the email activation code or token and mark user as verified."""
        clean_email = email.strip().lower() if email else None
        clean_code = str(code).strip() if code is not None else None
        clean_token = token.strip() if token else None

        redis = None
        try:
            redis = get_redis_client()
        except Exception as exc:
            logger.warning("Redis client unavailable during email verification: %s", exc)

        is_mock_provider = not self.email_service.api_key or self.email_service.api_key in ("mock", "", "None")
        resolved_email: str | None = None

        # 1. Check Token First
        if clean_token:
            if redis:
                try:
                    email_bytes = await redis.get(f"email_verify_token:{clean_token}")
                    if email_bytes:
                        resolved_email = (
                            email_bytes if isinstance(email_bytes, str) else email_bytes.decode("utf-8")
                        ).strip().lower()
                        await redis.delete(f"email_verify_token:{clean_token}")
                except Exception as exc:
                    logger.warning("Redis token lookup failed: %s", exc)
            if not resolved_email and clean_email:
                resolved_email = clean_email

        # 2. Check 6-digit Code
        elif clean_email and clean_code:
            resolved_email = clean_email
            stored_code: str | None = None
            if redis:
                try:
                    stored_code_bytes = await redis.get(f"email_verify_code:{clean_email}")
                    if stored_code_bytes:
                        stored_code = (
                            stored_code_bytes
                            if isinstance(stored_code_bytes, str)
                            else stored_code_bytes.decode("utf-8")
                        ).strip()
                except Exception as exc:
                    logger.warning("Redis code lookup failed: %s", exc)

            logger.info(
                "Email verification check: email=%s, code_received=%s, stored_code=%s, is_mock=%s",
                clean_email,
                clean_code,
                stored_code,
                is_mock_provider,
            )

            # Match criteria:
            # - Exact match with stored code
            # - Default code "123456" or "000000" ONLY if mock email provider OR if not in production
            settings = get_settings()
            is_production = settings.APP_ENV == "production"
            if stored_code is not None:
                code_matches = (stored_code == clean_code)
            else:
                code_matches = (
                    clean_code in ("123456", "000000")
                    and (is_mock_provider or not is_production)
                )

            if not code_matches:
                logger.warning(
                    "Email verification code mismatch: email=%s, received=%s, expected=%s",
                    clean_email,
                    clean_code,
                    stored_code,
                )
                return False

            if redis:
                with contextlib.suppress(Exception):
                    await redis.delete(f"email_verify_code:{clean_email}")
        else:
            logger.warning("Email verification called without token or email+code")
            return False

        if not resolved_email:
            return False

        # 3. Activate User in Database
        async with self.user_service._uow_factory() as uow:
            user = await uow.users.get_by_email(resolved_email)
            if not user:
                logger.error("User not found during email activation: %s", resolved_email)
                return False
            user.email_verified = True
            await uow.commit()
            logger.info("User successfully activated: email=%s, user_id=%s", resolved_email, user.id)

        # 4. Clean up any remaining code in Redis
        if redis:
            with contextlib.suppress(Exception):
                await redis.delete(f"email_verify_code:{resolved_email}")

        # 5. Send Welcome Email
        try:
            await self.email_service.send_welcome_email(user.email, f"{user.first_name} {user.last_name}")
        except Exception as exc:
            logger.warning("Failed to send welcome email: %s", exc)

        return True

    async def generate_email_verify_code(self, email: str) -> str:
        """Generate verification code, store in Redis, and send verify email."""
        import uuid
        clean_email = email.strip().lower()
        settings = get_settings()

        redis = None
        try:
            redis = get_redis_client()
        except Exception as exc:
            logger.warning("Redis client unavailable during code generation: %s", exc)

        has_real_email = bool(self.email_service.api_key and self.email_service.api_key not in ("mock", "", "None"))
        code = str(random.randint(100000, 999999)) if (settings.APP_ENV == "production" and has_real_email) else "123456"
        token = str(uuid.uuid4())

        if redis:
            try:
                await redis.setex(f"email_verify_code:{clean_email}", 900, code)
                await redis.setex(f"email_verify_token:{token}", 900, clean_email)
            except Exception as exc:
                logger.warning("Failed to store verification code in Redis: %s", exc)

        logger.info(
            "Verification code generated: email=%s, code=%s, has_real_email=%s, app_env=%s",
            clean_email,
            code,
            has_real_email,
            settings.APP_ENV,
        )

        # Fetch username for email
        async with self.user_service._uow_factory() as uow:
            user = await uow.users.get_by_email(clean_email)
            username = user.username if user else clean_email

        # Send verification email with both token and code
        await self.email_service.send_verification_email(clean_email, username, token, code)
        return code

    async def resend_verification_code(self, email: str) -> bool:
        """Regenerate verification code, store in Redis, and send resend email."""
        clean_email = email.strip().lower()
        async with self.user_service._uow_factory() as uow:
            user = await uow.users.get_by_email(clean_email)
            if not user or user.email_verified:
                logger.info("Resend verification bypassed (user not found or already verified): %s", clean_email)
                return False

        import uuid
        settings = get_settings()
        redis = None
        try:
            redis = get_redis_client()
        except Exception as exc:
            logger.warning("Redis client unavailable during code resend: %s", exc)

        has_real_email = bool(self.email_service.api_key and self.email_service.api_key not in ("mock", "", "None"))
        code = str(random.randint(100000, 999999)) if (settings.APP_ENV == "production" and has_real_email) else "123456"
        token = str(uuid.uuid4())

        if redis:
            try:
                await redis.setex(f"email_verify_code:{clean_email}", 900, code)
                await redis.setex(f"email_verify_token:{token}", 900, clean_email)
            except Exception as exc:
                logger.warning("Failed to update verification code in Redis: %s", exc)

        logger.info(
            "Verification code regenerated: email=%s, code=%s, has_real_email=%s",
            clean_email,
            code,
            has_real_email,
        )

        # Send resend verification email with both code and token
        await self.email_service.send_resend_verification_email(clean_email, user.username, code, token)
        return True

    async def generate_password_reset_token(self, email: str) -> str | None:
        """Generate and store password reset token in Redis, and send forgot password email."""
        clean_email = email.strip().lower()
        async with self.user_service._uow_factory() as uow:
            user = await uow.users.get_by_email(clean_email)
            if not user:
                return None

        token = str(uuid.uuid4())
        redis = get_redis_client()
        if redis:
            try:
                # Map token to email in Redis with 1 hour TTL
                await redis.setex(f"password_reset_token:{token}", 3600, clean_email)
            except Exception as exc:
                logger.warning("Failed to store password reset token in Redis: %s", exc)

        # Send forgot password email
        await self.email_service.send_reset_password_email(clean_email, token)
        return token

    async def reset_password(self, token: str, password: str) -> bool:
        """Verify reset token, update password, and send confirmation email."""
        redis = get_redis_client()
        email: str | None = None
        if redis:
            try:
                email_bytes = await redis.get(f"password_reset_token:{token}")
                if email_bytes:
                    email = email_bytes if isinstance(email_bytes, str) else email_bytes.decode("utf-8")
            except Exception:
                pass

        if not email:
            return False

        async with self.user_service._uow_factory() as uow:
            user = await uow.users.get_by_email(email)
            if not user:
                return False
            user.hashed_password = get_password_hash(password)
            await uow.commit()

        # Revoke the reset token immediately (single use)
        if redis:
            with contextlib.suppress(Exception):
                await redis.delete(f"password_reset_token:{token}")

        # Send password changed confirmation email
        await self.email_service.send_password_changed_email(email)
        return True

    async def revoke_tokens(self, access_token: str, refresh_token: str | None = None) -> None:
        """Revoke active access and refresh tokens by blacklisting them in Redis."""
        redis = get_redis_client()
        settings = get_settings()

        if not redis:
            return

        # Revoke access token
        try:
            payload = decode_token(access_token, settings.JWT_SECRET_KEY)
            token_data = TokenPayload(**payload)
            now = datetime.datetime.now(datetime.UTC).timestamp()
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
                now = datetime.datetime.now(datetime.UTC).timestamp()
                remaining = int(token_data.exp - now)
                if remaining > 0:
                    await redis.setex(f"revoked_token:{refresh_token}", remaining, "true")
            except Exception:
                pass

    async def check_username_availability(self, username: str, current_user_id: uuid.UUID | None = None) -> tuple[bool, list[str]]:
        """Validate format, check reserved names, and check uniqueness of username. Returns (is_available, suggestions)."""
        from src.auth.username import validate_username
        is_valid, normalized, _ = validate_username(username)
        if not is_valid:
            return False, []

        if normalized in RESERVED_USERNAMES:
            suggestions = [
                f"{normalized}_dev",
                f"{normalized}_user",
                f"{normalized}{random.randint(100, 9999)}",
            ]
            return False, suggestions

        async with self.user_service._uow_factory() as uow:
            existing = await uow.users.get_by_username(normalized)
            if not existing or (current_user_id and existing.id == current_user_id):
                return True, []

            # Generate valid suggestions
            suggestions: list[str] = []
            current_year = datetime.datetime.now().year
            candidates = [
                f"{normalized}01",
                f"{normalized}_07",
                f"{normalized}.dev",
                f"{normalized}{current_year}",
                f"{normalized}{random.randint(10, 99)}",
            ]
            for cand in candidates:
                if len(suggestions) >= 4:
                    break
                if (
                    len(cand) <= 30
                    and cand not in RESERVED_USERNAMES
                    and not await uow.users.get_by_username(cand)
                ):
                    suggestions.append(cand)

            return False, suggestions

    async def update_user(self, user_id: uuid.UUID, data: "ProfileUpdateRequest") -> User:
        """Update user profile and account preferences."""
        import re
        async with self.user_service._uow_factory() as uow:
            user = await uow.users.get(user_id)
            if not user:
                raise ValueError("User not found")

            if data.username is not None:
                cleaned_username = data.username.strip()
                if not re.match(r"^[a-zA-Z0-9_]{3,30}$", cleaned_username):
                    raise ValueError("Username must be between 3 and 30 characters and contain only letters, numbers, and underscores.")

                if cleaned_username.lower() in RESERVED_USERNAMES:
                    raise ValueError(f"Username '{cleaned_username}' is reserved.")

                if cleaned_username.lower() != user.username.lower():
                    existing = await uow.users.get_by_username(cleaned_username)
                    if existing and existing.id != user.id:
                        raise ValueError("Username already taken")
                    user.username = cleaned_username

            if data.first_name is not None:
                user.first_name = data.first_name.strip()
            if data.last_name is not None:
                user.last_name = data.last_name.strip()
            if data.avatar is not None:
                user.avatar_url = data.avatar
            if data.account_type is not None:
                user.account_type = data.account_type.strip().lower()
            if data.timezone is not None:
                user.timezone = data.timezone.strip()
            if data.locale is not None:
                user.locale = data.locale.strip().lower()

            await uow.commit()
            return user

    async def setup_mfa(self, user_id: uuid.UUID) -> tuple[str, str, list[str]]:
        """Initialize MFA setup for a user. Generates secret, otpauth URL, and recovery codes."""
        async with self.user_service._uow_factory() as uow:
            user = await uow.users.get(user_id)
            if not user:
                raise ValueError("User not found")

            secret = _generate_totp_secret()
            recovery_codes = [f"{secrets.token_hex(4)}-{secrets.token_hex(4)}" for _ in range(8)]
            user.mfa_secret = secret
            user.mfa_recovery_codes = json.dumps(recovery_codes)
            await uow.commit()

            encoded_email = urllib.parse.quote(user.email)
            otpauth_url = f"otpauth://totp/ASEP:{encoded_email}?secret={secret}&issuer=ASEP&algorithm=SHA1&digits=6&period=30"
            return secret, otpauth_url, recovery_codes

    async def enable_mfa(self, user_id: uuid.UUID, code: str) -> bool:
        """Verify the user's OTP code to finalize MFA enablement."""
        async with self.user_service._uow_factory() as uow:
            user = await uow.users.get(user_id)
            if not user or not user.mfa_secret:
                raise ValueError("MFA setup has not been initiated")

            if not _verify_totp(user.mfa_secret, code):
                raise ValueError("Invalid verification code")

            user.mfa_enabled = True
            await uow.commit()
            return True

    async def disable_mfa(self, user_id: uuid.UUID, password: str) -> bool:
        """Disable MFA for a user after verifying current password."""
        async with self.user_service._uow_factory() as uow:
            user = await uow.users.get(user_id)
            if not user:
                raise ValueError("User not found")

            if not user.hashed_password or not verify_password(password, user.hashed_password):
                raise ValueError("Invalid password")

            user.mfa_enabled = False
            user.mfa_secret = None
            user.mfa_recovery_codes = None
            await uow.commit()
            return True

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
                user.last_login = datetime.datetime.now(datetime.UTC)
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
                user.last_login = datetime.datetime.now(datetime.UTC)
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
                last_login=datetime.datetime.now(datetime.UTC),
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
