"""add_user_fields

Revision ID: 04e17ad65a8b
Revises: daab246a259f
Create Date: 2026-07-20 06:55:53.401450

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '04e17ad65a8b'
down_revision: Union[str, Sequence[str], None] = 'daab246a259f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns to users table
    op.add_column('users', sa.Column('first_name', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('company', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('status', sa.String(length=50), nullable=False, server_default='active'))
    op.add_column('users', sa.Column('avatar_url', sa.String(length=1024), nullable=True))
    op.add_column('users', sa.Column('last_login', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'last_login')
    op.drop_column('users', 'avatar_url')
    op.drop_column('users', 'status')
    op.drop_column('users', 'email_verified')
    op.drop_column('users', 'company')
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')
