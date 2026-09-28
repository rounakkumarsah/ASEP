"""add queue_jobs table for background task runner

Revision ID: q2j3k4l5m6n7
Revises: q1u2o3t4a5l6
Create Date: 2026-09-27 16:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "q2j3k4l5m6n7"
down_revision: str | Sequence[str] | None = "q1u2o3t4a5l6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create queue_jobs table
    op.create_table(
        "queue_jobs",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", sa.String(length=100), nullable=False, server_default="default"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("spec", sa.JSON().with_variant(JSONB, "postgresql"), nullable=False, server_default="{}"),
        sa.Column("result", sa.JSON().with_variant(JSONB, "postgresql"), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("metrics", sa.JSON().with_variant(JSONB, "postgresql"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 2. Add indexes
    op.create_index(
        "ix_queue_jobs_workspace_status",
        "queue_jobs",
        ["workspace_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_queue_jobs_user_id",
        "queue_jobs",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_queue_jobs_status",
        "queue_jobs",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_queue_jobs_completed_at",
        "queue_jobs",
        ["completed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_queue_jobs_completed_at", table_name="queue_jobs")
    op.drop_index("ix_queue_jobs_status", table_name="queue_jobs")
    op.drop_index("ix_queue_jobs_user_id", table_name="queue_jobs")
    op.drop_index("ix_queue_jobs_workspace_status", table_name="queue_jobs")
    op.drop_table("queue_jobs")
