"""add token_usage_logs table for granular token metering and cost attribution

Revision ID: t1u2s3a4g5e6
Revises: q2j3k4l5m6n7
Create Date: 2026-09-27 17:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "t1u2s3a4g5e6"
down_revision: str | Sequence[str] | None = "q2j3k4l5m6n7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create token_usage_logs table
    op.create_table(
        "token_usage_logs",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", sa.String(length=100), nullable=False, server_default="default"),
        sa.Column("provider", sa.String(length=100), nullable=False, server_default="unknown"),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 2. Add composite index on (user_id, timestamp, provider) for fast aggregation
    op.create_index(
        "ix_token_usage_logs_user_ts_provider",
        "token_usage_logs",
        ["user_id", "timestamp", "provider"],
        unique=False,
    )
    op.create_index(
        "ix_token_usage_logs_workspace_ts",
        "token_usage_logs",
        ["workspace_id", "timestamp"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_token_usage_logs_workspace_ts", table_name="token_usage_logs")
    op.drop_index("ix_token_usage_logs_user_ts_provider", table_name="token_usage_logs")
    op.drop_table("token_usage_logs")
