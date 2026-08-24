# ASEP — Backup and Restore Guide

This guide details the procedures for backing up and restoring the four stateful databases in the ASEP platform: PostgreSQL, Redis, Neo4j, and Qdrant.

## 1. PostgreSQL (Primary Datastore)

PostgreSQL stores users, organizations, agent runs, hitl sessions, and tasks.

### Backup

To take a logical backup (pg_dump) from the running Docker container:

```bash
# Create a timestamped backup file
BACKUP_FILE="asep_pg_backup_$(date +%Y%m%d_%H%M%S).sql"

# Execute pg_dump inside the container
docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U asep -d asep -F c > ./backups/$BACKUP_FILE

echo "Database backed up to ./backups/$BACKUP_FILE"
```

### Restore

To restore a database (Warning: This will overwrite existing data):

```bash
# 1. Stop the backend to prevent concurrent writes
docker compose -f docker-compose.prod.yml stop backend

# 2. Drop and recreate the database to ensure a clean state
docker compose -f docker-compose.prod.yml exec -T postgres psql -U asep -d postgres -c "DROP DATABASE asep WITH (FORCE);"
docker compose -f docker-compose.prod.yml exec -T postgres psql -U asep -d postgres -c "CREATE DATABASE asep OWNER asep;"

# 3. Restore the dump
docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_restore -U asep -d asep -1 < ./backups/YOUR_BACKUP_FILE.sql

# 4. Restart backend
docker compose -f docker-compose.prod.yml start backend
```

---

## 2. Redis (Sessions & Rate Limits)

Redis is mostly ephemeral (rate limits, sessions, Celery/task queues), but can be backed up if required.

### Backup

Trigger a background save (BGSAVE) and copy the `.rdb` file.

```bash
# Trigger BGSAVE
docker compose -f docker-compose.prod.yml exec redis redis-cli BGSAVE

# Wait 5 seconds for save to complete, then copy the file
docker cp asep_redis:/data/dump.rdb ./backups/redis_dump_$(date +%Y%m%d).rdb
```

### Restore

1. Stop the Redis container: `docker compose stop redis`
2. Replace the `dump.rdb` in the Docker volume.
3. Start the Redis container: `docker compose start redis`

---

## 3. Neo4j (Code Knowledge Graph)

Neo4j stores the AST code graphs used by GraphRAG.

### Backup

Neo4j provides a built-in dump command. The database must be stopped or you must use the `neo4j-admin` tool on a live database.

```bash
# Stop Neo4j container
docker compose -f docker-compose.prod.yml stop neo4j

# Create a backup using a temporary container mounting the same volumes
docker run --rm \
  --volumes-from asep_neo4j \
  -v $(pwd)/backups:/backups \
  neo4j:5-community \
  neo4j-admin database dump neo4j --to-path=/backups

# Restart Neo4j
docker compose -f docker-compose.prod.yml start neo4j
```

### Restore

```bash
docker compose -f docker-compose.prod.yml stop neo4j

docker run --rm \
  --volumes-from asep_neo4j \
  -v $(pwd)/backups:/backups \
  neo4j:5-community \
  neo4j-admin database load neo4j --from-path=/backups --overwrite-destination=true

docker compose -f docker-compose.prod.yml start neo4j
```

---

## 4. Qdrant (Vector Embeddings)

Qdrant stores code embeddings for semantic search.

### Backup

Qdrant supports creating snapshots of collections via its REST API.

```bash
# Create snapshot of the 'code_nodes' collection
curl -X POST "http://localhost:6333/collections/code_nodes/snapshots"

# The snapshot is saved in the Qdrant storage volume (/qdrant/snapshots)
# You can copy it to the host:
docker cp asep_qdrant:/qdrant/snapshots/code_nodes ./backups/qdrant_snapshots/
```

### Restore

```bash
# 1. Copy snapshot into container
docker cp ./backups/qdrant_snapshots/code_nodes/YOUR_SNAPSHOT.snapshot asep_qdrant:/qdrant/snapshots/code_nodes/

# 2. Restore via API
curl -X PUT "http://localhost:6333/collections/code_nodes/snapshots/recover" \
  -H "Content-Type: application/json" \
  -d '{"location": "file:///qdrant/snapshots/code_nodes/YOUR_SNAPSHOT.snapshot"}'
```

---

## Automated Backups (Cron)

For production, create a bash script `backup.sh` combining the above commands and add it to the host's crontab to run daily.

```bash
#!/bin/bash
# /opt/asep/backup.sh

BACKUP_DIR="/opt/asep/backups/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# PostgreSQL Logical Dump
docker compose -f /opt/asep/docker-compose.prod.yml exec -T postgres pg_dump -U asep -d asep -F c > "$BACKUP_DIR/postgres.sql"

# Keep only last 7 days of backups
find /opt/asep/backups -type d -mtime +7 -exec rm -rf {} +
```

Add to cron (`crontab -e`):
`0 2 * * * /opt/asep/backup.sh >> /var/log/asep_backup.log 2>&1`
