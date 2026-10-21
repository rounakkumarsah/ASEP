"""
ASEP — User API Key Repository (BYOK)
=====================================
Database repository for managing user-scoped LLM provider credentials.
"""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.user_api_key import UserApiKey


async def create_or_update(
    session: AsyncSession,
    user_id: uuid.UUID,
    provider: str,
    encrypted_key: str,
    key_preview: str,
) -> UserApiKey:
    """Create or update a user's API key for a given provider."""
    p = provider.lower().strip()
    stmt = select(UserApiKey).where(
        UserApiKey.user_id == user_id,
        UserApiKey.provider == p,
    )
    res = await session.execute(stmt)
    existing = res.scalars().first()

    now = datetime.datetime.now(datetime.timezone.utc)
    if existing is not None:
        existing.encrypted_key = encrypted_key
        existing.key_preview = key_preview
        existing.is_valid = True
        existing.last_validated_at = now
        existing.last_error = None
        existing.updated_at = now
        await session.flush()
        return existing

    new_key = UserApiKey(
        user_id=user_id,
        provider=p,
        encrypted_key=encrypted_key,
        key_preview=key_preview,
        is_valid=True,
        last_validated_at=now,
        last_error=None,
    )
    session.add(new_key)
    await session.flush()
    return new_key


async def get_by_user_and_provider(
    session: AsyncSession,
    user_id: uuid.UUID,
    provider: str,
) -> UserApiKey | None:
    """Retrieve a user's key for a specific provider."""
    p = provider.lower().strip()
    stmt = select(UserApiKey).where(
        UserApiKey.user_id == user_id,
        UserApiKey.provider == p,
    )
    res = await session.execute(stmt)
    return res.scalars().first()


async def get_all_for_user(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> list[UserApiKey]:
    """Retrieve all provider keys configured by a user."""
    stmt = (
        select(UserApiKey)
        .where(UserApiKey.user_id == user_id)
        .order_by(UserApiKey.provider.asc())
    )
    res = await session.execute(stmt)
    return list(res.scalars().all())


async def delete(
    session: AsyncSession,
    user_id: uuid.UUID,
    provider: str,
) -> bool:
    """Delete a user's key for a specific provider. Returns True if deleted."""
    p = provider.lower().strip()
    existing = await get_by_user_and_provider(session, user_id, p)
    if existing is None:
        return False
    await session.delete(existing)
    await session.flush()
    return True


async def mark_invalid(
    session: AsyncSession,
    user_id: uuid.UUID,
    provider: str,
    reason: str,
) -> None:
    """Mark a provider key as invalid after a failed validation check."""
    p = provider.lower().strip()
    existing = await get_by_user_and_provider(session, user_id, p)
    if existing is not None:
        existing.is_valid = False
        existing.last_error = reason
        existing.last_validated_at = datetime.datetime.now(datetime.timezone.utc)
        await session.flush()


class UserApiKeyRepository:
    """Repository class encapsulating UserApiKey database operations."""

    def __init__(self, session: AsyncSession | None = None) -> None:
        self._session = session

    create_or_update = staticmethod(create_or_update)
    get_by_user_and_provider = staticmethod(get_by_user_and_provider)
    get_all_for_user = staticmethod(get_all_for_user)
    delete = staticmethod(delete)
    mark_invalid = staticmethod(mark_invalid)
