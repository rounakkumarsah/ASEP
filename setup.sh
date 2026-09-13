#!/usr/bin/env bash
# ==============================================================================
# ASEP Auto-Installer Wizard
# Description: 1-Click interactive installation for the ASEP AI Engineering Workspace
# ==============================================================================
set -e

# Define Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_info() { echo -e "${BLUE}[*] $1${NC}"; }
print_success() { echo -e "${GREEN}[+] $1${NC}"; }
print_warn() { echo -e "${YELLOW}[!] $1${NC}"; }
print_error() { echo -e "${RED}[x] $1${NC}"; }

# ASCII Art
print_banner() {
cat << "EOF"
    ___   _____ ____________ 
   /   | / ___// ____/ __  /
  / /| | \__ \/ __/ / /_/ / 
 / ___ |___/ / /___/ ____/  
/_/  |_/____/_____/_/       
                            
AI Engineering Workspace Wizard
EOF
}

print_banner
echo ""

# ==============================================================================
# Step 1: Check Prerequisites
# ==============================================================================
print_info "Step 1: Verifying Prerequisites..."

if ! command -v docker &> /dev/null; then
    print_warn "Docker is not installed."
    read -t 10 -p "Attempt automatic installation? [Y/n] (Auto-yes in 10s): " INSTALL_DOCKER || INSTALL_DOCKER="y"
    INSTALL_DOCKER=${INSTALL_DOCKER:-y}
    
    if [[ "$INSTALL_DOCKER" =~ ^[Yy]$ ]]; then
        print_info "Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER || true
        print_success "Docker installed."
    else
        print_error "Docker is required. Exiting."
        exit 1
    fi
else
    print_success "Docker is installed."
fi

if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
    print_success "Docker Compose plugin is installed."
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
    print_success "Docker Compose standalone is installed."
else
    print_error "Docker Compose not found. Exiting."
    exit 1
fi

# ==============================================================================
# Step 2: Environment Setup
# ==============================================================================
print_info "Step 2: Environment Setup..."

if [ -f .env ]; then
    print_success ".env file already exists."
else
    print_warn ".env file not found. Generating template..."
    
    # Prompt for critical keys or fallback to placeholders if non-interactive
    if [ -t 0 ]; then
        read -p "Enter GEMINI_API_KEY (leave blank for placeholder): " INPUT_GEMINI
        read -p "Enter OPENAI_API_KEY (leave blank for placeholder): " INPUT_OPENAI
    else
        INPUT_GEMINI=""
        INPUT_OPENAI=""
    fi
    
    GEMINI_API_KEY=${INPUT_GEMINI:-"your_gemini_api_key_here"}
    OPENAI_API_KEY=${INPUT_OPENAI:-"your_openai_api_key_here"}
    
    # Generate random passwords for local DBs
    POSTGRES_PASSWORD=$(openssl rand -hex 16)
    REDIS_PASSWORD=$(openssl rand -hex 16)
    NEO4J_PASSWORD=$(openssl rand -hex 16)
    JWT_SECRET=$(openssl rand -hex 32)
    SECRET_KEY=$(openssl rand -hex 32)
    PUBLIC_IP=$(curl -s http://checkip.amazonaws.com || echo "localhost")

    cat <<EOF > .env
APP_ENV=production
DOMAIN=${PUBLIC_IP}
PORT=8000
FRONTEND_URL=http://${PUBLIC_IP}:3000
CORS_ORIGINS=http://${PUBLIC_IP}:3000,http://localhost:3000

# API Keys
GEMINI_API_KEY=${GEMINI_API_KEY}
OPENAI_API_KEY=${OPENAI_API_KEY}

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
EOF
    print_success ".env generated with secure DB credentials and provided API keys."
fi

# ==============================================================================
# Step 3: Database Pre-flight Port Check
# ==============================================================================
print_info "Step 3: Database Pre-flight (Port Availability Check)..."

check_port() {
    local port=$1
    local service=$2
    # Use ss or netstat to check if port is bound on host
    if command -v ss &> /dev/null; then
        if ss -tuln | grep -q ":$port "; then
            print_error "Port $port is already in use by another service. ASEP $service requires it."
            exit 1
        fi
    elif command -v netstat &> /dev/null; then
        if netstat -tuln | grep -q ":$port "; then
            print_error "Port $port is already in use. ASEP $service requires it."
            exit 1
        fi
    else
        # Fallback if ss/netstat not found
        if grep -q "$(printf '%04X' $port)" /proc/net/tcp 2>/dev/null; then
            print_error "Port $port appears in use. ASEP $service requires it."
            exit 1
        fi
    fi
    print_success "$service port ($port) is free."
}

check_port 5432 "Postgres"
check_port 6379 "Redis"
check_port 6333 "Qdrant"
check_port 7687 "Neo4j"
check_port 3000 "Frontend"
check_port 8000 "Backend"

# ==============================================================================
# Step 4: Build & Launch
# ==============================================================================
print_info "Step 4: Building & Launching the Stack..."

# Use production compose file if it exists
if [ -f "docker-compose.prod.yml" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
else
    COMPOSE_FILE="docker-compose.yml"
fi

sudo $COMPOSE_CMD -f $COMPOSE_FILE down --remove-orphans || true
sudo $COMPOSE_CMD -f $COMPOSE_FILE up -d --build

# ==============================================================================
# Step 5: Health Check
# ==============================================================================
print_info "Step 5: Verifying Health Endpoints..."

check_health() {
    local url=$1
    local name=$2
    local retries=30
    local wait=2

    echo -n "Waiting for $name to be healthy..."
    for i in $(seq 1 $retries); do
        local status=$(curl -s -o /dev/null -w "%{http_code}" "$url" || true)
        if [ "$status" == "200" ] || [ "$status" == "307" ] || [ "$status" == "308" ]; then
            echo -e " ${GREEN}OK!${NC}"
            return 0
        fi
        echo -n "."
        sleep $wait
    done
    echo -e " ${RED}FAILED!${NC}"
    print_error "$name failed to start within $((retries * wait)) seconds."
    sudo $COMPOSE_CMD -f $COMPOSE_FILE logs
    exit 1
}

# Ping the local exposed ports to verify containers came up
check_health "http://localhost:3000" "Next.js Frontend"
check_health "http://localhost:8000/api/v1/health" "FastAPI Backend"

# ==============================================================================
# Step 6: Success
# ==============================================================================
echo ""
echo -e "${GREEN}"
cat << "EOF"
   ___   _____ ___________    _      __    ___ _   _____ 
  /   | / ___// ____/ __  \  | | /| / /   /   | | / /__ \
 / /| | \__ \/ __/ / /_/ /   | |/ |/ /   / /| | |/ /__/ /
/ ___ |___/ / /___/ ____/    | /|  /   / ___ | / // __/ 
/_/  |_/____/_____/_/        |/ |_/   /_/  |_|//_/____/  

EOF
echo -e "${NC}"
print_success "ASEP is successfully deployed at http://localhost:3000!"
print_info "API Documentation available at: http://localhost:8000/docs"
print_info "To view live logs: sudo $COMPOSE_CMD -f $COMPOSE_FILE logs -f"
echo "=========================================================="
