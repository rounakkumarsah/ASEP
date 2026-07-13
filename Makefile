# =============================================================================
# ASEP — Makefile
# Developer experience shortcuts
# =============================================================================

.PHONY: help install dev test lint format typecheck docker-up docker-down \
        docker-logs migrate clean

PYTHON  := python3.12
PIP     := pip
BACKEND := backend

help:
	@echo ""
	@echo "  ASEP — Autonomous Software Engineering Platform"
	@echo "  ================================================"
	@echo ""
	@echo "  make install      Install all backend dependencies"
	@echo "  make dev          Start FastAPI dev server (hot-reload)"
	@echo "  make test         Run pytest test suite"
	@echo "  make lint         Run Ruff linter"
	@echo "  make format       Run Black formatter"
	@echo "  make typecheck    Run MyPy type checker"
	@echo "  make docker-up    Start full Docker Compose stack"
	@echo "  make docker-down  Stop Docker Compose stack"
	@echo "  make docker-logs  Tail backend logs"
	@echo "  make migrate      Run Alembic migrations"
	@echo "  make clean        Remove build artefacts"
	@echo ""

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
install:
	cd $(BACKEND) && $(PIP) install -e ".[dev]"
	pre-commit install

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------
dev:
	cd $(BACKEND) && uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# ---------------------------------------------------------------------------
# Quality
# ---------------------------------------------------------------------------
test:
	cd $(BACKEND) && pytest

lint:
	cd $(BACKEND) && ruff check src/ tests/

format:
	cd $(BACKEND) && black src/ tests/

typecheck:
	cd $(BACKEND) && mypy src/

check: lint typecheck test

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------
docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-down-v:
	docker compose down -v

docker-logs:
	docker compose logs -f asep

docker-build:
	docker compose build

docker-ps:
	docker compose ps

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
migrate:
	cd $(BACKEND) && alembic upgrade head

migrate-create:
	cd $(BACKEND) && alembic revision --autogenerate -m "$(name)"

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov"     -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc"               -delete 2>/dev/null || true
	@echo "Clean complete."
