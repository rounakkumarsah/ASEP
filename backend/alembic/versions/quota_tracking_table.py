"""add user_quota_logs table and monthly_token_quota column

Revision ID: q1u2o3t4a5l6
Revises: eea51b074ec7
Create Date: 2026-09-27 16:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "q1u2o3t4a5l6"
down_revision: str | Sequence[str] | None = "eea51b074ec7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add monthly_token_quota to users table
    op.add_column(
        "users",
        sa.Column("monthly_token_quota", sa.Integer(), nullable=True, server_default="100000"),
    )

    # 2. Create user_quota_logs table
    op.create_table(
        "user_quota_logs",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tokens_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("provider_name", sa.String(length=100), nullable=False, server_default="unknown"),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 3. Add composite index on (user_id, timestamp) for monthly aggregation
    op.create_index(
        "ix_user_quota_logs_user_timestamp",
        "user_quota_logs",
        ["user_id", "timestamp"],
        unique=False,
    )
    op.create_index(
        "ix_user_quota_logs_user_id",
        "user_quota_logs",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_user_quota_logs_user_id", table_name="user_quota_logs")
    op.drop_index("ix_user_quota_logs_user_timestamp", table_name="user_quota_logs")
    op.drop_table("user_quota_logs")
    op.drop_column("users", "monthly_token_quota")
