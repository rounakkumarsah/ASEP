# 06 — Database & Storage Architecture: ASEP

This document provides a complete breakdown of all database models, schemas, relations, indexes, vector stores, and graph databases in the ASEP platform.

---

## 1. Relational Database (PostgreSQL 16 via SQLAlchemy 2.0 Async)

Managed with Alembic migrations located in `backend/alembic/versions/`.

### 1.1 Models & Tables (`backend/src/db/models/`)

1. **`users` (`user.py`)**:
   - Primary Key: `id` (UUIDv4)
   - Columns: `email` (Unique), `hashed_password`, `full_name`, `is_active`, `is_verified`, `role`, `created_at`, `updated_at`.
   - Relations: 1-to-many with `api_keys`, `projects`, `subscriptions`, `audit_logs`.

2. **`projects` (`project.py`)**:
   - Primary Key: `id` (UUIDv4)
   - Columns: `name`, `description`, `repository_url`, `user_id` (FK &rarr; `users.id`), `created_at`.
   - Relations: 1-to-many with `agent_runs`, `knowledge_documents`.

3. **`agent_runs` (`agent_run.py`)**:
   - Primary Key: `id` (UUIDv4)
   - Columns: `project_id` (FK &rarr; `projects.id`), `user_id` (FK &rarr; `users.id`), `goal`, `status` (`PENDING`, `RUNNING`, `SUCCESS`, `FAILED`, `CANCELLED`), `total_tokens`, `cost_usd`, `error_message`, `created_at`, `finished_at`.
   - Relations: 1-to-many with `tasks`.

4. **`tasks` (`task.py`)**:
   - Primary Key: `id` (UUIDv4)
   - Columns: `run_id` (FK &rarr; `agent_runs.id`), `agent_name`, `title`, `description`, `status`, `dependencies` (JSON array of task UUIDs), `execution_order`, `output_payload`, `started_at`, `completed_at`.

5. **`knowledge_documents` (`knowledge_document.py`)**:
   - Primary Key: `id` (UUIDv4)
   - Columns: `project_id` (FK &rarr; `projects.id`), `file_path`, `content_hash`, `chunk_count`, `vector_collection_id`, `indexed_at`.

6. **`memory_entries` (`memory_entry.py`)**:
   - Primary Key: `id` (UUIDv4)
   - Columns: `user_id` (FK &rarr; `users.id`), `memory_type` (`WORKING`, `SEMANTIC`, `EPISODIC`), `content`, `embedding_id`, `created_at`.

7. **`api_keys` (`api_key.py`)**:
   - Primary Key: `id` (UUIDv4)
   - Columns: `user_id` (FK &rarr; `users.id`), `name`, `key_prefix`, `hashed_key`, `scopes` (JSON array), `expires_at`, `last_used_at`.

8. **`subscriptions` & `payments` (`subscription.py`, `payment.py`)**:
   - Primary Key: `id` (UUIDv4)
   - Columns: `user_id` (FK &rarr; `users.id`), `stripe_customer_id`, `stripe_subscription_id`, `plan_tier` (`DEVELOPER`, `TEAM`, `ENTERPRISE`), `status`, `current_period_end`.

9. **`audit_logs` (`audit_log.py`)**:
   - Primary Key: `id` (UUIDv4)
   - Columns: `user_id` (FK &rarr; `users.id`), `action`, `resource_type`, `resource_id`, `ip_address`, `user_agent`, `payload`, `timestamp`.

---

## 2. Vector Database (Qdrant)

- **Collection Name**: `asep_knowledge_base` / `asep_memory`.
- **Vector Dimension**: 1536 (OpenAI `text-embedding-3-small`) or 768 (Gemini Embedding / Ollama Nomic-Embed-Text).
- **Distance Metric**: Cosine Similarity.
- **Payload Schema**: `{ document_id, project_id, chunk_index, text, file_path, tags }`.

---

## 3. Graph Database (Neo4j)

- **Node Labels**: `:MemoryNode`, `:CodeArtifact`, `:Agent`, `:Task`, `:PolicyGate`.
- **Edge Relationships**:
  - `(:Agent)-[:EXECUTED]->(:Task)`
  - `(:Task)-[:DEPENDS_ON]->(:Task)`
  - `(:Task)-[:MODIFIED]->(:CodeArtifact)`
  - `(:PolicyGate)-[:AUTHORIZED]->(:Task)`

---

## 4. Ephemeral Storage & Queue (Redis 7)

- **Key Spaces**:
  - `asep:auth:ratelimit:{ip}`: Sliding window rate limit counters.
  - `asep:agent:stream:{run_id}`: Redis Pub/Sub channels for live telemetry streaming.
  - `asep:cache:metrics:{cluster_id}`: 10-second cached cluster utilization stats.
