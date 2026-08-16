# 05 — Database & Storage Architecture Forensic Report: ASEP

**Audit Date**: August 2026  
**Methodology**: Inspection of SQLAlchemy Models (`backend/src/db/models/`), Alembic Migrations (`backend/alembic/versions/`), Qdrant Vector Schemas, and Neo4j Drivers.

---

## 1. PostgreSQL Relational Models (SQLAlchemy 2.0 Async)

All models inherit from `src.db.postgres.Base` and use UUIDv4 primary keys.

1. **`users` (`user.py`)**:
   - `id`: UUID Primary Key
   - `email`: String (Unique, Indexed)
   - `hashed_password`: String (Argon2 / Bcrypt)
   - `full_name`: String (Nullable)
   - `is_active`: Boolean (Default: True)
   - `is_verified`: Boolean (Default: False)
   - `role`: String (Default: 'user')
   - `created_at`, `updated_at`: DateTime (UTC)

2. **`projects` (`project.py`)**:
   - `id`: UUID Primary Key
   - `name`: String (Indexed)
   - `description`: String (Nullable)
   - `repository_url`: String (Nullable)
   - `user_id`: UUID (Foreign Key &rarr; `users.id`)

3. **`agent_runs` (`agent_run.py`)**:
   - `id`: UUID Primary Key
   - `project_id`: UUID (Foreign Key &rarr; `projects.id`)
   - `user_id`: UUID (Foreign Key &rarr; `users.id`)
   - `goal`: Text
   - `status`: Enum (`PENDING`, `RUNNING`, `SUCCESS`, `FAILED`, `CANCELLED`)
   - `total_tokens`: Integer
   - `cost_usd`: Float
   - `error_message`: Text (Nullable)

4. **`tasks` (`task.py`)**:
   - `id`: UUID Primary Key
   - `run_id`: UUID (Foreign Key &rarr; `agent_runs.id`)
   - `title`: String
   - `description`: Text
   - `status`: String (`pending`, `running`, `completed`, `failed`)
   - `dependencies`: JSON (Array of dependent Task UUIDs)
   - `execution_order`: Integer

5. **`knowledge_documents` (`knowledge_document.py`)**:
   - `id`: UUID Primary Key
   - `project_id`: UUID (Foreign Key &rarr; `projects.id`)
   - `file_path`: String
   - `content_hash`: String (SHA-256 for change detection)
   - `chunk_count`: Integer

6. **`memory_entries` (`memory_entry.py`)**:
   - `id`: UUID Primary Key
   - `user_id`: UUID (Foreign Key &rarr; `users.id`)
   - `memory_type`: String (`working`, `semantic`, `procedural`)
   - `content`: Text
   - `embedding_id`: String (Qdrant Point ID)

7. **`api_keys` (`api_key.py`)**:
   - `id`: UUID Primary Key
   - `user_id`: UUID (Foreign Key &rarr; `users.id`)
   - `name`: String
   - `key_prefix`: String (e.g., `asep_live_...`)
   - `hashed_key`: String (SHA-256)
   - `scopes`: JSON (List of permissions)

8. **`payments` & `subscriptions` (`payment.py`, `subscription.py`)**:
   - `payments`: `id`, `user_id`, `amount` (in paise), `currency`, `status`, `razorpay_order_id`, `razorpay_payment_id`
   - `subscriptions`: `id`, `user_id`, `plan`, `status`, `current_period_end`

9. **`audit_logs` (`audit_log.py`)**:
   - `id`: UUID Primary Key
   - `user_id`: UUID (Foreign Key &rarr; `users.id`)
   - `action`: String
   - `resource_type`, `resource_id`: String
   - `ip_address`, `user_agent`: String
   - `payload`: JSONB

---

## 2. Alembic Migrations History

Located in `backend/alembic/versions/`:
- `2802f86835b1_initial_empty_migration.py`
- `9bbb2aa58d0e_initial_schema.py`
- `751be1fd11a4_add_user_model.py`
- `04e17ad65a8b_add_user_fields.py`
- `daab246a259f_add_role_to_user.py`
- `878636c91861_add_payments_table.py`
- `a1b2c3d4e5f6_add_oauth_multitenancy_saas_tables.py`

---

## 3. Vector & Graph Subsystems

- **Qdrant Vector Database**:
  - Collection: `asep_memory` and `asep_knowledge_base`
  - Dimensions: 1536 (OpenAI `text-embedding-3-small`) or 768 (Gemini / Ollama)
  - Distance: Cosine Similarity
- **Neo4j Graph Database**:
  - Node Labels: `:MemoryNode`, `:CodeArtifact`, `:Agent`, `:Task`, `:PolicyGate`
  - Edges: `(:Agent)-[:EXECUTED]->(:Task)`, `(:Task)-[:DEPENDS_ON]->(:Task)`
