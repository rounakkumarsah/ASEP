"""add hitl sessions table

Revision ID: f1b2c3d4e5f6
Revises: a1b2c3d4e5f6
Create Date: 2026-08-16 02:13:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "hitl_sessions",
        sa.Column("session_id", sa.String(length=50), nullable=False),
        sa.Column("execution_id", sa.Uuid(), nullable=False),
        sa.Column("correlation_id", sa.String(length=255), nullable=False),
        sa.Column("requesting_agent", sa.String(length=100), nullable=False),
        sa.Column("requesting_tool", sa.String(length=100), nullable=False),
        sa.Column("risk_level", sa.String(length=50), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "approved",
                "rejected",
                "expired",
                name="hitl_status",
                native_enum=True,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "decision",
            sa.Enum(
                "Approve",
                "Reject",
                "Modify",
                "Retry",
                "Escalate",
                "Cancel",
                "Expire",
                name="hitl_action",
                native_enum=True,
            ),
            nullable=True,
        ),
        sa.Column("reviewer", sa.String(length=255), nullable=True),
        sa.Column("reviewer_role", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "arguments_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("latency_seconds", sa.Float(), nullable=True),
        sa.Column("ttl_seconds", sa.Integer(), nullable=False, server_default="300"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["execution_id"], ["agent_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("session_id"),
    )
    op.create_index(
        "ix_hitl_sessions_execution_id",
        "hitl_sessions",
        ["execution_id"],
        unique=False,
    )
    op.create_index(
        "ix_hitl_sessions_status", "hitl_sessions", ["status"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_hitl_sessions_status", table_name="hitl_sessions")
    op.drop_index("ix_hitl_sessions_execution_id", table_name="hitl_sessions")
    op.drop_table("hitl_sessions")

    # Drop enum types
    hitl_action = postgresql.ENUM(
        "Approve",
        "Reject",
        "Modify",
        "Retry",
        "Escalate",
        "Cancel",
        "Expire",
        name="hitl_action",
    )
    hitl_action.drop(op.get_bind(), checkfirst=True)

    hitl_status = postgresql.ENUM(
        "pending", "approved", "rejected", "expired", name="hitl_status"
    )
    hitl_status.drop(op.get_bind(), checkfirst=True)
