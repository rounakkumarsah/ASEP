"""enable_rls_multi_tenancy

Revision ID: 37c46316c0a8
Revises: e7e1187405a7
Create Date: 2026-08-23 21:58:31.128303

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '37c46316c0a8'
down_revision: str | Sequence[str] | None = 'e7e1187405a7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Enable RLS on core multi-tenant tables
    op.execute("ALTER TABLE projects ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE agent_runs ENABLE ROW LEVEL SECURITY;")

    # 2. Create the policy for projects
    # A user can access a project if the project's org_id matches the current session tenant,
    # OR if they are a superuser (where current_tenant is set to 'admin').
    op.execute('''
        CREATE POLICY tenant_isolation_projects
        ON projects
        AS PERMISSIVE
        FOR ALL
        USING (
            current_setting('app.current_tenant', true) = org_id::text
            OR current_setting('app.current_tenant', true) = 'admin'
        );
    ''')

    # 3. Create the policy for agent_runs
    op.execute('''
        CREATE POLICY tenant_isolation_agent_runs
        ON agent_runs
        AS PERMISSIVE
        FOR ALL
        USING (
            current_setting('app.current_tenant', true) = org_id::text
            OR current_setting('app.current_tenant', true) = 'admin'
        );
    ''')

    # Note: RLS policies do not apply to table owners (the user that created the tables) by default,
    # so we must enable FORCE ROW LEVEL SECURITY if the API user is the table owner.
    op.execute("ALTER TABLE projects FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE agent_runs FORCE ROW LEVEL SECURITY;")


def downgrade() -> None:
    op.execute("ALTER TABLE projects DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE agent_runs DISABLE ROW LEVEL SECURITY;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_projects ON projects;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_agent_runs ON agent_runs;")
