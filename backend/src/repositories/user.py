"""
ASEP — User Repository
"""

import uuid
from typing import Any

from sqlalchemy import select

from src.db.models.user import User
from src.repositories.base import BaseRepository


class UserRepository(BaseRepository[User, uuid.UUID]):
    """PostgreSQL repository for User entities."""
    _model = User
        
    async def get_by_username(self, username: str) -> User | None:
        """Get a user by username."""
        stmt = select(User).where(User.username == username)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_by_email(self, email: str) -> User | None:
        """Get a user by email."""
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalars().first()
