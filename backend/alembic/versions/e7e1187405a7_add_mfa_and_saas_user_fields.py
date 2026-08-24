"""add_mfa_and_saas_user_fields

Revision ID: e7e1187405a7
Revises: f1b2c3d4e5f6
Create Date: 2026-08-22 16:38:13.916904

"""
import contextlib
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e7e1187405a7'
down_revision: str | Sequence[str] | None = 'f1b2c3d4e5f6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema.

    Adds MFA columns and SaaS profile fields (account_type, timezone, locale, current_plan)
    that were present in the ORM model but missing from the database.
    Also drops stale LangGraph checkpoint tables and removes duplicate unique constraints
    that will be replaced by functional lower() indexes.
    """

    conn = op.get_bind()

    # ------------------------------------------------------------------
    # Drop LangGraph checkpoint tables if they still exist
    # ------------------------------------------------------------------
    for tbl, idx in [
        ('checkpoint_writes', 'checkpoint_writes_thread_id_idx'),
        ('checkpoints',       'checkpoints_thread_id_idx'),
        ('checkpoint_blobs',  'checkpoint_blobs_thread_id_idx'),
    ]:
        conn.execute(sa.text(f'DROP INDEX IF EXISTS "{idx}"'))
        conn.execute(sa.text(f'DROP TABLE IF EXISTS "{tbl}" CASCADE'))
    conn.execute(sa.text('DROP TABLE IF EXISTS checkpoint_migrations CASCADE'))

    # ------------------------------------------------------------------
    # api_keys – remove duplicate unique constraint (already covered by PK)
    # ------------------------------------------------------------------
    try:
        op.drop_constraint('uq_api_keys_key_hash', 'api_keys', type_='unique')
    except Exception:
        pass  # already gone

    # ------------------------------------------------------------------
    # hitl_sessions – remove server_defaults (now managed at app layer)
    # ------------------------------------------------------------------
    op.alter_column('hitl_sessions', 'status',
               existing_type=postgresql.ENUM('pending', 'approved', 'rejected', 'expired', name='hitl_status'),
               server_default=None,
               existing_nullable=False)
    op.alter_column('hitl_sessions', 'ttl_seconds',
               existing_type=sa.INTEGER(),
               server_default=None,
               existing_nullable=False)
    # Remove stale indexes (will be recreated below)
    with contextlib.suppress(Exception):
        op.drop_index('ix_hitl_sessions_execution_id', table_name='hitl_sessions')
    with contextlib.suppress(Exception):
        op.drop_index('ix_hitl_sessions_status', table_name='hitl_sessions')

    # ------------------------------------------------------------------
    # organizations / projects / subscriptions – remove server_defaults
    # ------------------------------------------------------------------
    op.alter_column('organizations', 'is_active',
               existing_type=sa.BOOLEAN(),
               server_default=None,
               existing_nullable=False)
    op.alter_column('projects', 'is_active',
               existing_type=sa.BOOLEAN(),
               server_default=None,
               existing_nullable=False)
    op.alter_column('subscriptions', 'status',
               existing_type=sa.VARCHAR(length=50),
               server_default=None,
               existing_nullable=False)

    # ------------------------------------------------------------------
    # users – add MFA + SaaS profile columns (missing from DB)
    # ------------------------------------------------------------------
    op.add_column('users', sa.Column(
        'mfa_enabled', sa.Boolean(), nullable=False,
        server_default=sa.text('false'),
    ))
    op.add_column('users', sa.Column('mfa_secret', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('mfa_recovery_codes', sa.String(length=1024), nullable=True))
    op.add_column('users', sa.Column('account_type', sa.String(length=50),
                                     nullable=True, server_default=sa.text("'individual'")))
    op.add_column('users', sa.Column('timezone', sa.String(length=50),
                                     nullable=True, server_default=sa.text("'UTC'")))
    op.add_column('users', sa.Column('locale', sa.String(length=10),
                                     nullable=True, server_default=sa.text("'en'")))
    op.add_column('users', sa.Column('current_plan', sa.String(length=50),
                                     nullable=True, server_default=sa.text("'free'")))

    # ------------------------------------------------------------------
    # Case-insensitive unique indexes on email and username
    # ------------------------------------------------------------------
    try:
        op.create_index('uq_users_lower_email', 'users',
                        [sa.literal_column('lower(email)')], unique=True)
    except Exception:
        pass  # already exists
    try:
        op.create_index('uq_users_lower_username', 'users',
                        [sa.literal_column('lower(username)')], unique=True)
    except Exception:
        pass  # already exists


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('uq_users_lower_username', table_name='users')
    op.drop_index('uq_users_lower_email', table_name='users')
    op.drop_column('users', 'current_plan')
    op.drop_column('users', 'locale')
    op.drop_column('users', 'timezone')
    op.drop_column('users', 'account_type')
    op.drop_column('users', 'mfa_recovery_codes')
    op.drop_column('users', 'mfa_secret')
    op.drop_column('users', 'mfa_enabled')
    op.alter_column('subscriptions', 'status',
               existing_type=sa.VARCHAR(length=50),
               server_default=sa.text("'trialing'::character varying"),
               existing_nullable=False)
    op.alter_column('projects', 'is_active',
               existing_type=sa.BOOLEAN(),
               server_default=sa.text('true'),
               existing_nullable=False)
    op.alter_column('organizations', 'is_active',
               existing_type=sa.BOOLEAN(),
               server_default=sa.text('true'),
               existing_nullable=False)
    op.create_index(op.f('ix_hitl_sessions_status'), 'hitl_sessions', ['status'], unique=False)
    op.create_index(op.f('ix_hitl_sessions_execution_id'), 'hitl_sessions', ['execution_id'], unique=False)
    op.alter_column('hitl_sessions', 'ttl_seconds',
               existing_type=sa.INTEGER(),
               server_default=sa.text('300'),
               existing_nullable=False)
    op.alter_column('hitl_sessions', 'status',
               existing_type=postgresql.ENUM('pending', 'approved', 'rejected', 'expired', name='hitl_status'),
               server_default=sa.text("'pending'::hitl_status"),
               existing_nullable=False)
    op.create_unique_constraint(op.f('uq_api_keys_key_hash'), 'api_keys', ['key_hash'], postgresql_nulls_not_distinct=False)
    op.alter_column('api_keys', 'is_active',
               existing_type=sa.BOOLEAN(),
               server_default=sa.text('true'),
               existing_nullable=False)
    op.create_table('checkpoint_migrations',
    sa.Column('v', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('v', name=op.f('checkpoint_migrations_pkey'))
    )
    op.create_table('checkpoint_blobs',
    sa.Column('thread_id', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('checkpoint_ns', sa.TEXT(), server_default=sa.text("''::text"), autoincrement=False, nullable=False),
    sa.Column('channel', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('version', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('type', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('blob', postgresql.BYTEA(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('thread_id', 'checkpoint_ns', 'channel', 'version', name=op.f('checkpoint_blobs_pkey'))
    )
    op.create_index(op.f('checkpoint_blobs_thread_id_idx'), 'checkpoint_blobs', ['thread_id'], unique=False)
    op.create_table('checkpoints',
    sa.Column('thread_id', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('checkpoint_ns', sa.TEXT(), server_default=sa.text("''::text"), autoincrement=False, nullable=False),
    sa.Column('checkpoint_id', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('parent_checkpoint_id', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('type', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('checkpoint', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('thread_id', 'checkpoint_ns', 'checkpoint_id', name=op.f('checkpoints_pkey'))
    )
    op.create_index(op.f('checkpoints_thread_id_idx'), 'checkpoints', ['thread_id'], unique=False)
    op.create_table('checkpoint_writes',
    sa.Column('thread_id', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('checkpoint_ns', sa.TEXT(), server_default=sa.text("''::text"), autoincrement=False, nullable=False),
    sa.Column('checkpoint_id', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('task_id', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('idx', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('channel', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('type', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('blob', postgresql.BYTEA(), autoincrement=False, nullable=False),
    sa.Column('task_path', sa.TEXT(), server_default=sa.text("''::text"), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('thread_id', 'checkpoint_ns', 'checkpoint_id', 'task_id', 'idx', name=op.f('checkpoint_writes_pkey'))
    )
    op.create_index(op.f('checkpoint_writes_thread_id_idx'), 'checkpoint_writes', ['thread_id'], unique=False)
    # ### end Alembic commands ###
