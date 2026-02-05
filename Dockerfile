# ------------------------------------------------------------
# Dockerfile — TaskHub API (AWS / Cloud-ready)
#
# Purpose:
# - Build a production-ready container for FastAPI
# - Compatible with AWS ECS Fargate, ALB, and local Docker
#
# Design decisions:
# - The application binds to 0.0.0.0 so it is reachable inside containers
# - The PORT is configurable via environment variable (ECS/ALB standard)
# - All configuration (DB, Redis, JWT) is provided via env vars
# - No secrets or AWS credentials are baked into the image
#
# This image can run:
# - Locally (Docker / Docker Compose)
# - On AWS ECS Fargate behind an Application Load Balancer
# ------------------------------------------------------------

# ==========================
# STAGE 1: Base image
# ==========================

# Use official lightweight Python image (version 3.12-slim)
FROM python:3.12-slim

# ==========================
# Environment setup
# ==========================

# Prevent Python from writing .pyc files and buffering output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory inside the container
WORKDIR /app

# Copy dependency list first (to leverage Docker caching)
COPY requirements.txt .

# Install dependencies
# --no-cache-dir → prevents storing pip cache, keeping the image small
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the source code into the image
COPY . .

# Create non-root user for runtime (AWS / ECS best practice)
RUN useradd -m appuser \
    && chown -R appuser:appuser /app

# Drop root privileges for runtime
USER appuser


# ==========================
# Container runtime configuration
# ==========================

# Expose the port FastAPI will run on (matches app_port in .env)
EXPOSE 8000

# ------------------------------------------------------------
# Runtime command
#
# Why PORT env?
# - AWS ECS + Application Load Balancer inject the listening port
# - Default to 8000 for local development
#
# This keeps the same image usable in:
# - local Docker
# - CI pipelines
# - AWS ECS Fargate
# ------------------------------------------------------------
# ------------------------------------------------------------
# Runtime command (ECS / Docker / Local compatible)
# ------------------------------------------------------------
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
