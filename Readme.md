# 🚀 TaskHub API — PostgreSQL Edition (v2.0)

![CI](https://github.com/sulimankh87/taskhub-api/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.120.0-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

> **Version:** 2.0.0  
> **Status:** Production-grade backend (SQL)  
> **Release Type:** Storage-layer migration (MongoDB → PostgreSQL)

📚 Overview
**TaskHub API** is a production-style backend service for user and task management, built with **FastAPI**, **PostgreSQL**, **Celery**, and **Redis**.

This version (**v2.0**) is a full migration from MongoDB to PostgreSQL.  
The API behavior, authentication flow, pagination contract, and background job semantics remain unchanged — only the **persistence layer** was replaced.

The project is designed to demonstrate **real backend engineering practices**, including:
- Explicit schema design
- Query-aligned indexing
- Exactly-once background job execution
- Deterministic CI with real services

# This version (v2.0) is a full migration from MongoDB to PostgreSQL, preserving:
### v2.0 Migration Summary

This version preserves:
- API contracts
- Pagination behavior
- Authentication flow
- Idempotent background jobs

While introducing:
- Schema enforcement
- Relational integrity
- Alembic migrations
- SQL-level guarantees
- 
The goal of this project is to demonstrate real backend engineering, not just CRUD functionality.

## 🎯 Key Features

- JWT-based authentication (access + refresh tokens)
- Task CRUD operations
- Typed, paginated API responses (`Page[T]`)
- Async PostgreSQL access via SQLAlchemy
- Background jobs using Celery + Redis
- **Exactly-once** background job execution (idempotency)
- Dockerized local and CI environments
- Database schema migrations with Alembic
- Clean separation between API, domain, and persistence layers

## 🧱 System Architecture
```text
Client
  │
  ▼
FastAPI (async)
  │
  ├── PostgreSQL (SQLAlchemy async)
  │     ├── users
  │     ├── tasks
  │     └── job_log (idempotency)
  │
  ├── Redis
  │     └── Celery broker & result backend
  │
  └── Celery Workers
        └── idempotent background tasks
```
## 📐 Architecture & Cloud Design (Mid-Level)

This project includes explicit documentation describing how the system is
designed, deployed, scaled, and secured in a production-style AWS environment.

These documents reflect **mid-level backend engineering expectations** and
focus on clarity, correctness, and real-world tradeoffs.

### 📄 Documentation
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — Layered backend architecture (API, async, data)
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — Local → Docker → AWS ECS deployment flow
- [`docs/SECURITY.md`](docs/SECURITY.md) — JWT auth, password hashing, secrets handling
- [`docs/SCALING.md`](docs/SCALING.md) — Horizontal scaling strategy and bottlenecks
- [`docs/FAILURE_MODES.md`](docs/FAILURE_MODES.md) — Failure scenarios and recovery behavior
- [`docs/TERRAFORM_ALIGNMENT.md`](docs/TERRAFORM_ALIGNMENT.md) — AWS resource mapping (IaC-aligned)

### ☁️ AWS Proof of Deployment Knowledge
- [`docs/aws/ecs-task-definition.json`](docs/aws/ecs-task-definition.json) — Example ECS Fargate task definition with:
  - Environment variable injection
  - AWS-managed secrets
  - Health checks
  - CloudWatch logging
  
```md
🗂 Project Structure
```text
taskhub-api/
│
├── app/
│   ├── main.py                   # FastAPI entrypoint
│   ├── config.py                 # Environment & settings
│   ├── db.py                     # Async SQLAlchemy engine & session
│   ├── security.py               # Password hashing + JWT helpers
│   ├── idempotency.py            # SQL-backed idempotent job helpers
│   │
│   ├── routes/
│   │   ├── auth.py               # Register & login
│   │   └── tasks.py              # Task CRUD + pagination
│   │
│   ├── schemas/                  # API contracts (Pydantic v2)
│   │   ├── user_schema.py
│   │   ├── task_schema.py
│   │   ├── pagination_schema.py
│   │   └── token_schema.py
│   │
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── task.py
│   │   └── job_log.py
│   │
│   ├── workers/
│   │   ├── celery_app.py
│   │   └── tasks/
│   │       └── email_tasks.py
│   │
│   └── tests/
│       ├── conftest.py
│       ├── test_api.py
│       ├── test_tasks.py
│       └── test_idempotency.py
│
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 0001_init_schema.py
│
├── docs/               
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   ├── SECURITY.md
│   ├── FAILURE_MODES.md
│   ├── SCALING.md
│   ├── TERRAFORM_ALIGNMENT.md
│   └── aws/
│       └── ecs-task-definition.json
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

🛠 Tech Stack
# Backend
Python 3.12
FastAPI
Pydantic v2
# Database
PostgreSQL 16
SQLAlchemy 2.0 (async)
Alembic (migrations)
# Background Jobs
Celery
Redis
# Auth & Security
JWT (python-jose)
bcrypt / sha256_crypt (test mode)
# Tooling
Docker & Docker Compose
Pytest + pytest-asyncio
GitHub Actions CI

🔐 Authentication
JWT Bearer authentication
Short-lived access tokens
Long-lived refresh tokens
All /tasks/* endpoints are protected

📄 Pagination Contract
List endpoints return a typed pagination response:
{
  "items": [...],
  "meta": {
    "limit": 20,
    "has_more": true,
    "next_cursor": null
  }
}

This prevents unbounded queries and enforces scale-safe access.

🔁 Idempotent Background Jobs
Background jobs are exactly-once by design.

How it works:
Each job has a deterministic job_id
job_log.job_id is a PRIMARY KEY
SQL INSERT … ON CONFLICT DO NOTHING ensures:
safe retries
crash safety
parallel worker safety

🗃 Database Migrations
All schema changes are managed via Alembic.
Initial migration includes:
users table (unique usernames)
tasks table (FK → users)
Query-aligned index (owner_id, created_at DESC)
job_log table for idempotency

Run migrations:
alembic upgrade head

🐳 Run Locally (Docker)
docker-compose up --build
This starts:
FastAPI → http://localhost:8000
PostgreSQL
Redis
Celery worker

## This starts:
# Services:
FastAPI → http://localhost:8000
PostgreSQL
Redis
Celery worker
# Health check:
GET /health

🧪 Testing
pytest -v

# Tests run against:
Real PostgreSQL
Real Redis
SQL transactions with rollback isolation

🔄 Version History
# v1.5.0 — MongoDB Edition
Async MongoDB (Motor)
Runtime index creation
Document-based models

# v2.0.0 — PostgreSQL Edition (Current)
Async SQLAlchemy
Alembic migrations
Relational integrity
Schema-enforced idempotency

🎯 Design Philosophy
This project demonstrates:
Backend correctness over convenience
API stability across storage migrations
Explicit schema & index design
Exactly-once background execution
Real-world backend tradeoffs

### 🔄 Dual-Backend Support During Migration
This repository intentionally supports two backends during the migration phase:
- `main` branch runs **v1.5 (MongoDB)**
- `feature/sql-*` branches run **v2.0 (PostgreSQL)**

A single CI pipeline adapts automatically based on branch,
ensuring both implementations remain correct and isolated
until the migration is finalized.

## 📝 Release Notes

### 🔹 v2.0.0 — PostgreSQL Edition (Current)

**Release Type:** Major (Storage-layer migration)  
**Release Date:** 2025

#### 🚨 Breaking Changes
- Persistence layer migrated from **MongoDB** to **PostgreSQL**
- MongoDB-specific runtime index creation removed
- Database schema is now enforced via migrations

> ⚠️ API behavior, endpoints, pagination response shape, and authentication flow remain unchanged.

---

#### ✅ Added
- Async **SQLAlchemy 2.0** integration
- **PostgreSQL 16** as primary datastore
- **Alembic migrations** for schema and index management
- Relational integrity (primary keys, foreign keys)
- Query-aligned composite SQL indexes
- DB-enforced idempotency using `ON CONFLICT DO NOTHING`
- Transaction-scoped SQL sessions for test isolation

---

#### 🔄 Changed
- `database.py` → replaced with `db.py` (SQLAlchemy async engine)
- MongoDB document models → SQLAlchemy ORM models
- Runtime index creation → migration-defined indexes
- Idempotency logic now enforced structurally at the DB level

---

#### 🛡 Improved Guarantees
- Strong consistency (ACID)
- Predictable query performance
- Safer retries and worker restarts
- Clear schema ownership via migrations

---

### 🔹 v1.5.0 — MongoDB Edition

**Release Type:** Stable  
**Release Date:** 2024–2025

#### Features
- Async MongoDB (Motor) persistence
- Runtime compound index creation on startup
- JWT-based authentication
- Offset-based pagination (`limit` / `skip`)
- Idempotent Celery background jobs (Mongo-backed)
- Dockerized local & CI environments
- GitHub Actions CI with real services

---

#### Notes
- This version prioritized development velocity and schema flexibility
- Idempotency and indexing were handled at the application layer


📄 License
MIT License © 2025
Suleiman Khasheboun
Backend Software Engineer | FastAPI · PostgreSQL · Celery · Docker