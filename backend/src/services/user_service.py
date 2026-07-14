"""
ASEP — UserService
"""

import uuid
from collections.abc import Callable

from src.db.models.user import User
from src.unit_of_work.base import AbstractUnitOfWork

class UserService:
    """Minimal service for User operations."""

    def __init__(self, uow_factory: Callable[[], AbstractUnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def get_user(self, user_id: uuid.UUID) -> User:
        """Get user by ID."""
        async with self._uow_factory() as uow:
            return await uow.users.get_or_raise(user_id)

    async def get_user_by_username(self, username: str) -> User | None:
        """Get user by username."""
        async with self._uow_factory() as uow:
            return await uow.users.get_by_username(username)
