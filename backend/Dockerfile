# =============================================================================
# ASEP Backend — Dockerfile
# Multi-stage build for production-ready container
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: dependency builder
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system deps needed for compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install pip and hatch
RUN pip install --no-cache-dir --upgrade pip hatchling

# Copy only dependency manifest and readme (layer cache optimisation)
COPY pyproject.toml README.md ./

# Install project dependencies into a prefix
RUN pip install --no-cache-dir --prefix=/install ".[dev]" || \
    pip install --no-cache-dir --prefix=/install .

# ---------------------------------------------------------------------------
# Stage 2: runtime image
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

LABEL maintainer="ASEP Platform Team"
LABEL version="0.1.0"
LABEL description="ASEP Backend — Autonomous Software Engineering Platform"

# Security: non-root user
RUN groupadd --gid 1001 asep && \
    useradd --uid 1001 --gid asep --shell /bin/bash --create-home asep

WORKDIR /app

# System runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy source code
COPY --chown=asep:asep . .

# Switch to non-root user
USER asep

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Entrypoint: uvicorn in production mode
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
