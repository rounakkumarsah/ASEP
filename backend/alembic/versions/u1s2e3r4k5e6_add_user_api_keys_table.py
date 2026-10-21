"""add user_api_keys table for byok credentials

Revision ID: u1s2e3r4k5e6
Revises: t1u2s3a4g5e6
Create Date: 2026-10-11 15:40:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "u1s2e3r4k5e6"
down_revision: str | Sequence[str] | None = "t1u2s3a4g5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_api_keys",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("provider", sa.String(length=32), nullable=False, index=True),
        sa.Column("encrypted_key", sa.Text(), nullable=False),
        sa.Column("key_preview", sa.String(length=16), nullable=False),
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("user_id", "provider", name="uq_user_api_keys_user_id_provider"),
    )


def downgrade() -> None:
    op.drop_table("user_api_keys")
