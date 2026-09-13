#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "    ASEP Enterprise Auto-Installer & Bootstrapper"
echo "=========================================================="
echo ""
echo "[1/4] Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "[-] Docker is not installed. Attempting automatic installation..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER || true
    echo "[+] Docker installed successfully."
else
    echo "[+] Docker is installed."
fi

# Check Docker Compose (Plugin or Standalone)
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
    echo "[+] Docker Compose plugin is installed."
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
    echo "[+] Docker Compose standalone is installed."
else
    echo "[-] Docker Compose not found. Please install Docker Compose and try again."
    exit 1
fi

echo "[2/4] Generating configuration..."
if [ ! -f .env ]; then
    echo "[-] .env file not found. Generating a default enterprise configuration..."
    
    # Try to auto-detect public IP (useful for EC2 deployments)
    PUBLIC_IP=$(curl -s http://checkip.amazonaws.com || echo "localhost")
    
    # Generate random passwords
    POSTGRES_PASSWORD=$(openssl rand -hex 16)
    REDIS_PASSWORD=$(openssl rand -hex 16)
    NEO4J_PASSWORD=$(openssl rand -hex 16)
    JWT_SECRET=$(openssl rand -hex 32)
    SECRET_KEY=$(openssl rand -hex 32)

    cat <<EOF > .env
APP_ENV=production
DOMAIN=${PUBLIC_IP}

# Security
SECRET_KEY=${SECRET_KEY}
JWT_SECRET_KEY=${JWT_SECRET}
JWT_REFRESH_SECRET_KEY=$(openssl rand -hex 32)

# Databases
DATABASE_URL=postgresql+asyncpg://asep_user:${POSTGRES_PASSWORD}@postgres:5432/asep_db
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
NEO4J_URI=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=${NEO4J_PASSWORD}
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=

# Internal networking
POSTGRES_USER=asep_user
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DB=asep_db
REDIS_PASSWORD=${REDIS_PASSWORD}

# Application
CORS_ORIGINS=http://${PUBLIC_IP},http://localhost,http://localhost:3000
FRONTEND_URL=http://${PUBLIC_IP}
PORT=8000
EOF
    echo "[+] .env generated with secure defaults (IP: ${PUBLIC_IP})."
else
    echo "[+] .env already exists. Skipping generation."
fi

echo "[3/4] Building and starting the stack..."
# Ensure any old containers are stopped and rebuilt
sudo $COMPOSE_CMD -f docker-compose.prod.yml down --remove-orphans || true
sudo $COMPOSE_CMD -f docker-compose.prod.yml up -d --build

echo ""
echo "=========================================================="
echo "    Deployment Complete!"
echo "=========================================================="
echo "Your ASEP enterprise stack is now running."
echo ""
echo "Access the endpoints:"
if [ -f .env ]; then
    DOMAIN=$(grep -E '^DOMAIN=' .env | cut -d '=' -f 2 || echo "localhost")
    echo " - Frontend: http://${DOMAIN}"
    echo " - Backend API: http://${DOMAIN}/api/v1"
    echo " - API Docs: http://${DOMAIN}/docs"
else
    echo " - Frontend: http://localhost"
fi
echo ""
echo "To view logs, run: docker compose -f docker-compose.prod.yml logs -f"
echo "=========================================================="
