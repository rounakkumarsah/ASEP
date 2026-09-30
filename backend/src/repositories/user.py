"""
ASEP — User Repository
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import defer

from src.auth.utils import normalize_email
from src.db.models.user import User
from src.repositories.base import BaseRepository


class UserRepository(BaseRepository[User, uuid.UUID]):
    """PostgreSQL repository for User entities."""
    _model = User

    async def _execute_with_fallback(self, stmt: Any) -> User | None:
        """Execute query with defensive fallback if monthly_token_quota column is missing."""
        try:
            result = await self._session.execute(stmt)
            return result.scalars().first()
        except ProgrammingError as exc:
            if "monthly_token_quota" in str(exc):
                await self._session.rollback()
                fallback_stmt = stmt.options(defer(User.monthly_token_quota))
                result = await self._session.execute(fallback_stmt)
                user = result.scalars().first()
                if user is not None:
                    user.__dict__["monthly_token_quota"] = 100000
                return user
            raise

    async def get_by_username(self, username: str) -> User | None:
        """Get a user by username (case-insensitive)."""
        clean_username = username.strip().lower()
        stmt = select(User).where(func.lower(User.username) == clean_username)
        return await self._execute_with_fallback(stmt)

    async def get_by_email(self, email: str) -> User | None:
        """Get a user by email (normalized and case-insensitive)."""
        clean_email = normalize_email(email)
        raw_email = email.strip().lower() if email else ""
        if not clean_email and not raw_email:
            return None
        if clean_email != raw_email and raw_email:
            stmt = select(User).where(or_(func.lower(User.email) == clean_email, func.lower(User.email) == raw_email))
        else:
            stmt = select(User).where(func.lower(User.email) == clean_email)
        return await self._execute_with_fallback(stmt)
