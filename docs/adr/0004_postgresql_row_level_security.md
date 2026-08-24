# ADR 0004: PostgreSQL Row-Level Security (RLS) for Multi-Tenancy

* **Status:** Accepted  
* **Date:** 2026-08-24  
* **Deciders:** Principal Architect & Platform Lead (Rounak Kumar Sah)  
* **Context:** Implementing enterprise multi-tenant database isolation.

---

## Context and Problem Statement

In enterprise SaaS deployments, ensuring complete isolation between tenant data is critical. Relying purely on application-level filtering (`WHERE tenant_id = :id`) is prone to developer oversight, software bugs, and SQL injection vulnerabilities.

## Decision Drivers

* **Guaranteed Isolation:** Enforce security policies at the database engine level.
* **Operational Simplicity:** Avoid the operational complexity and schema migration overhead of maintaining separate database instances or separate schemas per tenant.
* **Performance:** Minimal query execution overhead.

## Decision Outcome

**Chosen Option:** **PostgreSQL Row-Level Security (RLS)** applied via Alembic migrations (`backend/alembic/versions/37c46316c0a8_enable_rls_multi_tenancy.py`).

### Policy Definition

```sql
-- Enable RLS on multi-tenant tables
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_runs ENABLE ROW LEVEL SECURITY;

-- Enforce session variable policy
CREATE POLICY project_tenant_isolation ON projects
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid);

CREATE POLICY agent_run_tenant_isolation ON agent_runs
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid);
```

### Consequences

* **Positive:**
  * Even if a backend API handler omits a tenant filter in its SQLAlchemy query, PostgreSQL automatically rejects rows belonging to other tenants.
  * Compatible with standard connection pooling when `SET LOCAL app.current_tenant` is executed per transaction.
* **Negative:**
  * Database administrative tasks require explicitly bypassing RLS (`SET row_security = off`) with superuser credentials.

---
