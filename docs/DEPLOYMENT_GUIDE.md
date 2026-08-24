# ASEP — Production Deployment Guide

**One-command production deployment for ASEP v0.1.3**

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Docker | 24.0+ | With Docker Compose v2 (`docker compose` not `docker-compose`) |
| OS | Ubuntu 22.04 LTS | Recommended; any Linux with Docker works |
| RAM | 8 GB minimum | 16 GB recommended for running local Ollama LLM |
| CPU | 4 vCPU | More = faster agent sandboxes |
| Disk | 40 GB SSD | For Docker images, databases, vector embeddings |
| Domain | Required | e.g. `asep.yourdomain.com` pointed at server IP (A record) |
| Ports | 80, 443 open | For Traefik + Let's Encrypt TLS |

---

## One-Command Deployment

```bash
# 1. Clone the repository
git clone https://github.com/rounakkumarsah/ASEP.git
cd ASEP

# 2. Configure environment
cp .env.example .env
nano .env    # Fill in ALL required values (see Environment Variables section)

# 3. Deploy everything (one command)
docker compose -f docker-compose.prod.yml up -d --build

# Done. ASEP is running at https://yourdomain.com
```

**The single `docker compose` command:**
- Builds frontend (Next.js standalone) and backend (FastAPI uvicorn) Docker images
- Starts Traefik reverse proxy with automatic Let's Encrypt TLS certificates
- Starts PostgreSQL 16, Redis 7, Neo4j 5, and Qdrant
- Runs Alembic database migrations (`alembic upgrade head`)
- Routes `https://yourdomain.com` → frontend
- Routes `https://yourdomain.com/api` → backend
- Routes `wss://yourdomain.com/ws` → WebSocket (PTY terminal)

---

## Environment Variable Configuration

Before running, copy `.env.example` to `.env` and fill in **every** value marked `REQUIRED`:

```bash
cp .env.example .env
```

**Minimum required values for production:**

```bash
# Your domain
DOMAIN=asep.yourdomain.com
ACME_EMAIL=your@email.com

# Secrets (generate with: openssl rand -hex 32)
SECRET_KEY=<64-char hex string>
POSTGRES_PASSWORD=<strong password>
REDIS_PASSWORD=<strong password>
NEO4J_PASSWORD=<strong password>

# At least one LLM key
GEMINI_API_KEY=<from Google AI Studio>

# Payments (required for billing)
RAZORPAY_KEY_ID=<from Razorpay dashboard>
RAZORPAY_KEY_SECRET=<from Razorpay dashboard>
RAZORPAY_WEBHOOK_SECRET=<from Razorpay dashboard>

# Email (required for verification emails)
RESEND_API_KEY=<from resend.com>

# Bot protection (recommended)
ENABLE_TURNSTILE=true
TURNSTILE_SECRET_KEY=<from Cloudflare dashboard>
NEXT_PUBLIC_TURNSTILE_SITE_KEY=<from Cloudflare dashboard>
```

---

## Deployment Steps (Detailed)

### Step 1: Server Setup

```bash
# Install Docker (Ubuntu 22.04)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version          # Docker 24.x+
docker compose version    # Docker Compose v2.x
```

### Step 2: Clone and Configure

```bash
git clone https://github.com/rounakkumarsah/ASEP.git
cd ASEP

# Generate strong secrets
SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -hex 16)
REDIS_PASSWORD=$(openssl rand -hex 16)
NEO4J_PASSWORD=$(openssl rand -hex 16)

# Create .env from template
cp .env.example .env

# Fill in the values
sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PASSWORD/" .env
sed -i "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=$REDIS_PASSWORD/" .env
sed -i "s/NEO4J_PASSWORD=.*/NEO4J_PASSWORD=$NEO4J_PASSWORD/" .env

# Set your domain and email
read -p "Enter your domain (e.g. asep.yourdomain.com): " DOMAIN
read -p "Enter your email (for Let's Encrypt): " ACME_EMAIL
echo "DOMAIN=$DOMAIN" >> .env
echo "ACME_EMAIL=$ACME_EMAIL" >> .env
echo "APP_ENV=production" >> .env
```

### Step 3: Configure DNS

Point your domain at the server IP:
```
A record:  asep.yourdomain.com → <server IP>
TTL:       300 (5 minutes)
```

Wait for DNS propagation (use `dig asep.yourdomain.com` to verify).

### Step 4: Deploy

```bash
# Build images and start all services
docker compose -f docker-compose.prod.yml up -d --build

# Watch startup logs
docker compose -f docker-compose.prod.yml logs -f

# Verify all services are healthy
docker compose -f docker-compose.prod.yml ps
```

Expected output after ~2 minutes:
```
NAME            STATUS          PORTS
asep_traefik    Up (healthy)    0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
asep_backend    Up (healthy)    8000/tcp
asep_frontend   Up (healthy)    3000/tcp
asep_postgres   Up (healthy)    5432/tcp
asep_redis      Up (healthy)    6379/tcp
asep_neo4j      Up              7474/tcp, 7687/tcp
asep_qdrant     Up              6333/tcp, 6334/tcp
asep_migrate    Exited (0)      # Migration completed successfully
```

### Step 5: Verify Deployment

```bash
# Check API health
curl -s https://asep.yourdomain.com/api/v1/health | python -m json.tool

# Expected response:
# {
#   "status": "ok",
#   "version": "0.1.3",
#   "environment": "production"
# }

# Check frontend
curl -I https://asep.yourdomain.com
# Expected: HTTP/2 200
```

---

## Using Managed Cloud Services (Recommended for Production)

Instead of running databases in Docker, use managed services for better reliability:

### Option A: Neon (PostgreSQL)

1. Create a project at [neon.tech](https://neon.tech) (free tier available)
2. Copy the connection string
3. In `.env`, set:
   ```bash
   DATABASE_URL=postgresql+asyncpg://user:password@ep-xxx.neon.tech/neondb?sslmode=require
   ```
4. In `docker-compose.prod.yml`, comment out the `postgres:` service

### Option B: Upstash (Redis)

1. Create a Redis database at [upstash.com](https://upstash.com) (free tier available)
2. Copy the Redis URL
3. In `.env`, set:
   ```bash
   REDIS_URL=rediss://:password@xxx.upstash.io:6380/0
   ```
4. In `docker-compose.prod.yml`, comment out the `redis:` service

---

## Makefile Commands

```bash
# Development
make dev          # Start all services for local development
make dev-stop     # Stop all development services
make migrate      # Run Alembic migrations
make test         # Run full test suite
make lint         # Run ruff + tsc

# Production
make prod-up      # docker compose -f docker-compose.prod.yml up -d --build
make prod-down    # docker compose -f docker-compose.prod.yml down
make prod-logs    # Follow production logs
make prod-ps      # Show service status

# Database
make db-migrate   # Run pending migrations
make db-rollback  # Roll back last migration
make db-shell     # Open psql shell

# Maintenance
make backup-db    # Backup PostgreSQL to ./backups/
make update       # git pull + rebuild + restart (zero-downtime rolling update)
```

---

## Updating ASEP

```bash
# Pull latest code
git pull origin main

# Rebuild and restart (zero-downtime: Traefik handles in-flight requests)
docker compose -f docker-compose.prod.yml up -d --build --no-deps backend frontend

# Run any new migrations
docker compose -f docker-compose.prod.yml run --rm migrate
```

---

## Monitoring & Logs

```bash
# View all logs
docker compose -f docker-compose.prod.yml logs -f

# Backend only
docker compose -f docker-compose.prod.yml logs -f backend

# Check resource usage
docker stats

# Check disk usage
docker system df
```

---

## Security Hardening (Post-Deploy)

```bash
# Restrict SSH access
ufw allow from <your-ip> to any port 22
ufw allow 80
ufw allow 443
ufw enable

# Auto-update Docker images for security patches
# Add to crontab:
# 0 3 * * 0 docker compose -f /opt/asep/docker-compose.prod.yml pull && docker compose -f /opt/asep/docker-compose.prod.yml up -d --build

# Rotate secrets every 90 days
openssl rand -hex 32   # new SECRET_KEY
# Update .env, then: docker compose -f docker-compose.prod.yml up -d --no-deps backend
```

---

## Troubleshooting

| Problem | Diagnosis | Fix |
|---|---|---|
| TLS certificate not issued | `docker compose logs traefik` — check ACME errors | Verify DNS A record points to server IP; port 80 must be open |
| Backend unhealthy | `docker compose logs backend` | Check `DATABASE_URL` and `REDIS_URL` in `.env` |
| Migration failed | `docker compose logs migrate` | Check `POSTGRES_*` env vars; ensure PostgreSQL is healthy |
| Frontend 502 Bad Gateway | `docker compose logs frontend` | Wait 30s for Next.js build; check `NEXT_PUBLIC_API_URL` |
| Agent sandbox fails | `docker compose logs backend \| grep sandbox` | Backend needs `/var/run/docker.sock` mounted (already in compose) |
| Neo4j out of memory | `docker stats asep_neo4j` | Increase heap: set `NEO4J_dbms_memory_heap_max__size=1g` |

---

## Architecture Reference

See [`docs/Architecture.md`](Architecture.md) for full system, data flow, and deployment diagrams.

---

## Support

- GitHub Issues: https://github.com/rounakkumarsah/ASEP/issues
- Security Vulnerabilities: See [`SECURITY.md`](../SECURITY.md)
