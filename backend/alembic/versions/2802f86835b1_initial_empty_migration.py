"""Initial empty migration

Revision ID: 2802f86835b1
Revises:
Create Date: 2026-07-13 17:19:46.122072

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = '2802f86835b1'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
