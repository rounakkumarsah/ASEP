"""
ASEP — User Repository
"""

import uuid

from sqlalchemy import select

from src.auth.utils import normalize_email
from src.db.models.user import User
from src.repositories.base import BaseRepository


class UserRepository(BaseRepository[User, uuid.UUID]):
    """PostgreSQL repository for User entities."""
    _model = User

    async def get_by_username(self, username: str) -> User | None:
        """Get a user by username (case-insensitive)."""
        from sqlalchemy import func
        clean_username = username.strip().lower()
        stmt = select(User).where(func.lower(User.username) == clean_username)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_by_email(self, email: str) -> User | None:
        """Get a user by email (normalized and case-insensitive)."""
        from sqlalchemy import func, or_
        clean_email = normalize_email(email)
        raw_email = email.strip().lower() if email else ""
        if not clean_email and not raw_email:
            return None
        if clean_email != raw_email and raw_email:
            stmt = select(User).where(or_(func.lower(User.email) == clean_email, func.lower(User.email) == raw_email))
        else:
            stmt = select(User).where(func.lower(User.email) == clean_email)
        result = await self._session.execute(stmt)
        return result.scalars().first()
