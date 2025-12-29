# 🚀 Deployment — From Local to AWS (Mid-Level)

This document describes how **TaskHub API** is deployed across environments,
from local development to AWS ECS.

The goal is to demonstrate **production readiness** without overengineering.

---

## 🎯 Deployment Philosophy

- Same application code across all environments
- Environment-specific configuration via variables
- Stateless API containers
- Zero-downtime updates where possible
- Simple, repeatable deployment flow

---

## 1️⃣ Local Development

**Purpose:** Fast feedback & debugging

Stack:
- FastAPI (async)
- PostgreSQL
- Redis
- Celery worker

Tooling:
- Docker
- Docker Compose

Startup:
```bash
docker-compose up --build
```

Characteristics:
Single API container
Single database instance
No auto-scaling
Developer-controlled lifecycle

Health check:
GET /health → 200 OK
2️⃣ Containerization (Docker)
The API is packaged as a single Docker image.

Key principles:
No environment-specific logic in code
No secrets baked into the image
Same image used locally, in CI, and in AWS
Runtime configuration is injected via environment variables.

3️⃣ AWS Deployment (ECS + Fargate)
Target environment: AWS ECS (Fargate)

Components:
ECS Cluster
ECS Service (API)
Application Load Balancer (ALB)
RDS (PostgreSQL)
ElastiCache (Redis)

Flow:
Client
→ ALB (HTTPS)
→ ECS Service (FastAPI containers)
→ RDS / Redis

Characteristics:
Stateless API containers
Horizontal scaling via ECS
Managed infrastructure (no servers)

4️⃣ Environment Variables
Configuration is environment-driven.

Examples:
DATABASE_URL
REDIS_BROKER
JWT_SECRET
APP_ENV
Rules:
Stored in .env (local)
Stored in ECS Task Definition / AWS Secrets Manager (AWS)
Never committed to Git
The application reads configuration using pydantic-settings.

5️⃣ Health Checks
The API exposes a lightweight health endpoint:

GET /health
Used by:

Docker Compose
ECS container health checks
Load Balancer target groups

Purpose:
Detect crashed containers
Enable automatic restarts
Remove unhealthy tasks from rotation

6️⃣ Zero-Downtime Deployments (Conceptual)
ECS handles rolling deployments automatically.
Deployment strategy:
New containers start
Health checks pass
Traffic gradually shifts
Old containers are terminated

Client impact:
No API downtime
In-flight requests complete normally
This provides basic zero-downtime guarantees without manual orchestration.

🎯 Summary
This deployment model:
Mirrors real production setups
Scales cleanly
Avoids unnecessary complexity
Matches mid-level backend expectations
Advanced topics (blue/green, canary, EKS) are intentionally out of scope.


---

# 🔹 2. `docs/SECURITY.md` (very short, 1 page)

```md
# 🔐 Security Overview (Mid-Level)

This document summarizes the core security decisions in **TaskHub API**.

The focus is on **correctness, clarity, and common backend best practices**.
```
---

## 1️⃣ Authentication Strategy (JWT)

TaskHub uses **JWT-based authentication**.

- Short-lived access tokens
- Long-lived refresh tokens
- Bearer tokens via `Authorization` header

JWT payload:
- `sub` (username)
- `exp` (expiration)

All protected endpoints validate:
- Token signature
- Expiration
- User existence

---

## 2️⃣ Password Hashing

Passwords are **never stored in plaintext**.

Hashing:
- `bcrypt` in production
- Faster algorithm in test environment (for CI speed)

Rules:
- Hash on registration
- Verify on login
- Never return hashes in API responses

---

## 3️⃣ Secrets Management

Sensitive values include:
- Database credentials
- JWT secret
- Redis connection URL

Rules:
- Loaded from environment variables
- Defined in `.env.example`
- Injected at runtime (Docker / ECS)
- Never committed to Git

No secrets exist in:
- Source code
- Docker images
- Git history

---

## 4️⃣ Repository Safety

The repository enforces:
- `.gitignore` for env files
- No credentials in commits
- Environment parity across stages

Security is handled **by configuration**, not by hardcoded logic.

---

## 🎯 Summary

This security model provides:
- Safe authentication
- Proper password handling
- Secret isolation
- Production-aligned defaults

It is intentionally simple and suitable for mid-level backend systems.