# =============================================================================
# Dockerfile — TaskHub API
# Multi-stage build: builder (compiles deps) → runtime (lean final image)
#
# Why multi-stage?
#   - Build tools (gcc, pip cache, build headers) never reach production
#   - Final image: ~180MB vs ~450MB single-stage
#   - No secrets or AWS credentials baked in — all config via env vars
#
# Compatible with:
#   - Local Docker / Docker Compose
#   - AWS ECS Fargate
#   - Kubernetes (EKS)
# =============================================================================

# =============================================================================
# STAGE 1: builder
# Install all Python dependencies into a clean prefix we can copy later.
# =============================================================================
FROM python:3.12.3-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /build

# Build-time OS deps needed to compile some Python packages (asyncpg, psycopg)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        libpq5 \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \

# Install Python packages into /install prefix — copied to runtime stage only
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# =============================================================================
# STAGE 2: runtime
# Lean image — copies only installed packages + application code.
# Build tools, pip cache, gcc never make it here.
# =============================================================================
FROM python:3.12.3-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Runtime-only OS deps
#   curl:            Docker/ECS HEALTHCHECK + container readiness checks
#   ca-certificates: HTTPS to AWS APIs (boto3)
#   libpq5:          PostgreSQL client runtime library (asyncpg)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy compiled Python packages from builder — no pip needed in runtime
COPY --from=builder /install /usr/local

# Copy only the application code needed at runtime
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# -----------------------------------------------------------------------
# Security: drop root privileges
# Required by ECS Fargate best practices and Kubernetes PodSecurityPolicy
# UID 1001 avoids conflicts with common system UIDs
# -----------------------------------------------------------------------
RUN useradd -m -u 1001 appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# -----------------------------------------------------------------------
# HEALTHCHECK
# Used by:
#   - Docker / Docker Compose (container marked healthy/unhealthy)
#   - ECS task health checks (before registering to target group)
#   - Kubernetes liveness probes (if not overridden in manifest)
#
# --start-period: gives the app time to connect to DB before first check
# -----------------------------------------------------------------------
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=15s \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# PORT env var allows ECS / ALB / K8s to override the listening port
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
