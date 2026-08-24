# ASEP — Installation & Self-Hosting Guide
==========================================
Step-by-step installation instructions for Local, Docker, and Cloud environments.

## Quickstart via Docker Compose (Recommended)

### Prerequisites
* Docker Engine 24.0+ & Docker Compose v2+
* Python 3.12+ (if running locally)
* Node.js 20+ (if running locally)

### 1. Clone & Configure
```bash
git clone https://github.com/rounakkumarsah/ASEP.git
cd ASEP
```

### 2. Set Up Environment Files
```bash
# Backend Environment
cp backend/.env.example backend/.env

# Frontend Environment
cp frontend/.env.local.example frontend/.env.local
```

### 3. Launch Services
```bash
docker-compose up -d --build
```
* **Frontend Dashboard**: `http://localhost:3000`
* **Backend API & Swagger Docs**: `http://localhost:8000/docs`
* **Health Check**: `http://localhost:8000/health`

---

## Local Development Setup (Without Docker)

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## Production Cloud Deployment Matrix

| Component | Recommended Free / Low-Cost Host |
| :--- | :--- |
| **Frontend** | Cloudflare Pages / Vercel (Pro) |
| **Backend API** | Render / Railway / Fly.io / AWS EC2 |
| **PostgreSQL** | Neon.tech (Serverless) / AWS RDS |
| **Redis** | Upstash Redis / Redis Cloud |
| **Vector DB** | Qdrant Cloud (1GB Free Cluster) |
| **Graph DB** | Neo4j AuraDB (Free Tier) |
