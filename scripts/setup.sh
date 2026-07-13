#!/usr/bin/env bash
# =============================================================================
# ASEP — Setup Script
# Bootstraps a fresh development environment.
# =============================================================================
set -euo pipefail

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }

echo ""
echo "  ╔═══════════════════════════════════════╗"
echo "  ║  ASEP — Dev Environment Setup         ║"
echo "  ╚═══════════════════════════════════════╝"
echo ""

# 1. Copy .env if not present
if [ ! -f .env ]; then
    info "Copying .env.example → .env"
    cp .env.example .env
    warn "Please review .env and update secrets before proceeding."
fi

# 2. Backend Python environment
info "Installing backend Python dependencies..."
cd backend
pip install -e ".[dev]" --quiet
cd ..
success "Backend dependencies installed."

# 3. Pre-commit hooks
info "Installing pre-commit hooks..."
pre-commit install
success "Pre-commit hooks installed."

# 4. Frontend
if command -v node &>/dev/null; then
    info "Installing frontend dependencies..."
    cd frontend
    npm install --silent
    cd ..
    success "Frontend dependencies installed."
else
    warn "Node.js not found. Skipping frontend setup."
fi

# 5. Docker Compose health check
if command -v docker &>/dev/null; then
    info "Pulling Docker images (this may take a while)..."
    docker compose pull --quiet
    success "Docker images ready."
else
    warn "Docker not found. Skipping image pull."
fi

echo ""
success "Setup complete! Run 'make docker-up && make dev' to start developing."
echo ""
