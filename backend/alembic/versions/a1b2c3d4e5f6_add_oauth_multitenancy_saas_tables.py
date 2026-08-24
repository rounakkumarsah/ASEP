"""add_oauth_multitenancy_saas_tables

Revision ID: a1b2c3d4e5f6
Revises: 04e17ad65a8b
Create Date: 2026-07-27 18:00:00.000000

Adds:
  - organizations table (multi-tenant workspace boundary)
  - projects table (org-scoped project workspace)
  - subscriptions table (org-scoped SaaS subscription)
  - api_keys table (project-scoped API key with SHA-256 hash)
  - users.oauth_provider column
  - users.oauth_id column
  - users.org_id FK column
  - users.hashed_password made nullable (for OAuth-only users)
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: str | Sequence[str] | None = ('04e17ad65a8b', '878636c91861')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # organizations
    # -----------------------------------------------------------------------
    op.create_table(
        'organizations',
        sa.Column('id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('owner_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_organizations_slug', 'organizations', ['slug'], unique=True)
    op.create_index('ix_organizations_owner_id', 'organizations', ['owner_id'])

    # -----------------------------------------------------------------------
    # Extend users with oauth + org FK (AFTER organizations exists)
    # -----------------------------------------------------------------------
    op.add_column('users', sa.Column('oauth_provider', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('oauth_id', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('org_id', sa.Uuid(as_uuid=True), nullable=True))
    op.create_index('ix_users_oauth_id', 'users', ['oauth_id'])
    op.create_index('ix_users_org_id', 'users', ['org_id'])
    op.create_foreign_key(
        'fk_users_org_id_organizations',
        'users', 'organizations',
        ['org_id'], ['id'],
        ondelete='SET NULL',
    )
    # Make hashed_password nullable so OAuth-only users can exist
    op.alter_column('users', 'hashed_password', existing_type=sa.String(length=1024), nullable=True)

    # -----------------------------------------------------------------------
    # projects
    # -----------------------------------------------------------------------
    op.create_table(
        'projects',
        sa.Column('id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('org_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_projects_org_id', 'projects', ['org_id'])
    op.create_index('ix_projects_slug', 'projects', ['slug'])

    # -----------------------------------------------------------------------
    # subscriptions
    # -----------------------------------------------------------------------
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('org_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('plan', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='trialing'),
        sa.Column('razorpay_order_id', sa.String(length=255), nullable=True),
        sa.Column('razorpay_payment_id', sa.String(length=255), nullable=True),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_subscriptions_org_id', 'subscriptions', ['org_id'])
    op.create_index('ix_subscriptions_status', 'subscriptions', ['status'])
    op.create_index('ix_subscriptions_razorpay_order_id', 'subscriptions', ['razorpay_order_id'])
    op.create_index('ix_subscriptions_razorpay_payment_id', 'subscriptions', ['razorpay_payment_id'])

    # -----------------------------------------------------------------------
    # api_keys
    # -----------------------------------------------------------------------
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('project_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('key_prefix', sa.String(length=16), nullable=False),
        sa.Column('key_hash', sa.String(length=64), nullable=False),
        sa.Column('scopes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash'),
    )
    op.create_index('ix_api_keys_project_id', 'api_keys', ['project_id'])
    op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'])
    op.create_index('ix_api_keys_key_hash', 'api_keys', ['key_hash'], unique=True)
    op.create_index('ix_api_keys_is_active', 'api_keys', ['is_active'])


def downgrade() -> None:
    # Drop in reverse order of creation
    op.drop_table('api_keys')
    op.drop_table('subscriptions')
    op.drop_table('projects')

    # Remove user columns before dropping organizations (FK constraint)
    op.drop_constraint('fk_users_org_id_organizations', 'users', type_='foreignkey')
    op.drop_index('ix_users_org_id', table_name='users')
    op.drop_index('ix_users_oauth_id', table_name='users')
    op.drop_column('users', 'org_id')
    op.drop_column('users', 'oauth_id')
    op.drop_column('users', 'oauth_provider')
    op.alter_column('users', 'hashed_password', existing_type=sa.String(length=1024), nullable=False)

    op.drop_table('organizations')
