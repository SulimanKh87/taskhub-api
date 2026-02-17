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

> ⚠️ **SQL Branch**
>
> This branch runs the **PostgreSQL (SQLAlchemy) implementation** of TaskHub.
> The MongoDB version lives on the `main` branch.
>
> All tests, migrations, and pagination behavior in this branch
> are validated against **PostgreSQL with schema enforcement**.

📚 Overview
**TaskHub API** is a production-style backend service for user and task management, built with **FastAPI**, **PostgreSQL**, **Celery**, and **Redis**.

This version (**v2.0**) is a full migration from MongoDB to PostgreSQL.  
The API behavior, authentication flow, pagination contract, and background job semantics remain unchanged — only the **persistence layer** was replaced.

The project is designed to demonstrate **real backend engineering practices**, including:
- Explicit schema design
- Query-aligned indexing
- Exactly-once background job execution
- Deterministic CI with real services

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

## 🧱 System Architecture no AWS 
```text
Client
  │
  ▼
Application Load Balancer (AWS)
  │
  ▼
ECS Fargate
  ├── FastAPI API container
  └── Celery worker container
        │
        ├── RDS PostgreSQL (private subnet)
        └── ElastiCache Redis (private subnet)
```
📐 Architecture & Operational Guarantees (Current State)

This project documents **only the systems and guarantees that currently exist**.

### 📄 Core Documentation
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — Current system architecture and data flow
- [`docs/FAILURE_MODES.md`](docs/FAILURE_MODES.md) — How the system fails and recovers
- [`docs/SECURITY.md`](docs/SECURITY.md) — Authentication, authorization, and secret handling

These documents focus on **correctness, failure isolation, and predictable behavior**
rather than hypothetical infrastructure or future deployment plans.

## ☁️ AWS Infrastructure (Terraform)

This project includes a complete Infrastructure-as-Code setup using Terraform.

Provisioned resources:

- VPC with public & private subnets
- Application Load Balancer (ALB)
- ECS Fargate cluster
- API service + Celery worker service
- RDS PostgreSQL (private subnet)
- ElastiCache Redis (private subnet)
- ECR repositories (API + worker)
- CloudWatch log groups
- Least-privilege security groups

Infrastructure is defined in:

infra/terraform/

Design goals:
- Mid-level backend learning setup
- Clear networking boundaries
- Reproducible cloud environment
- No secrets baked into images

## 🐳 Container Registry (ECR)
This project uses **AWS Elastic Container Registry (ECR)** to store Docker images.

### 🚀 **Quick Start (AWS Deployment)**

> ⚠️ **Cost Warning:** Running `terraform apply` creates real AWS resources and **will incur charges**.

#### **Step 1: Create Infrastructure**
```bash
cd infra/terraform
terraform init
terraform plan    # Preview resources
terraform apply   # Create resources (say 'yes')
```

#### **Step 2: Build & Push Docker Images to ECR**
```bash
cd ../../  # Back to project root
./scripts/push-to-ecr.sh
```

#### **Step 3: Verify Images in ECR**
```bash
aws ecr describe-images --repository-name taskhub-dev-api --region eu-central-1
aws ecr describe-images --repository-name taskhub-dev-worker --region eu-central-1
```

#### **Step 4: Update ECS Services**

After images are in ECR, update `terraform.tfvars`:
```hcl
api_image    = "123456789012.dkr.ecr.eu-central-1.amazonaws.com/taskhub-dev-api:latest"
worker_image = "123456789012.dkr.ecr.eu-central-1.amazonaws.com/taskhub-dev-worker:latest"
```

Then re-apply Terraform:
```bash
cd infra/terraform
terraform apply
```

---

### 📚 **Detailed Documentation**

For complete ECR workflow and troubleshooting, see:
- [`docs/ECR.md`](docs/ECR.md) — ECR push workflow
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — Full deployment guide (coming soon)

---

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
├── infra/terraform/
│   ├── main.tf
│   ├── .terraform.lock.hcl
│   ├── terraform.tfvars.example
│   ├── .terraform
│   ├── variables.tf
│   ├── provider.tf
│   └── outputs.tf
│
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_init_schema.py
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── SECURITY.md
│   ├── FAILURE_MODES.md
│
├── pytest.ini
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## 🛠 Tech Stack

### Backend
- Python 3.12
- FastAPI
- Pydantic v2

### Database
- PostgreSQL 16 (RDS-compatible)
- SQLAlchemy 2.0 (async)
- Alembic (migrations)

### Background Jobs
- Celery
- Redis (ElastiCache-compatible)

### Infrastructure (AWS)
- ECS Fargate
- Application Load Balancer (ALB)
- RDS (PostgreSQL)
- ElastiCache (Redis)
- ECR (container registry)
- CloudWatch Logs
- Terraform (Infrastructure as Code)

### DevOps & Tooling
- Docker & Docker Compose
- Pytest + pytest-asyncio
- GitHub Actions CI


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


## 🗃 Database Migrations (Alembic)

TaskHub uses **Alembic as the single source of truth** for database schema
management. Runtime schema creation (`create_all`) is intentionally **not used**.

### Migration Rules

- All schema changes are managed via Alembic migrations
- Application startup never modifies the database schema
- Migrations are generated against an empty database for the initial schema
- Production databases are upgraded explicitly and deterministically

### Common Commands

```bash
# Create a new migration after changing models
docker compose exec api alembic revision --autogenerate -m "describe change"

# Apply migrations
docker compose exec api alembic upgrade head

# Check migration state
docker compose exec api alembic current
docker compose exec api alembic history


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

## 🚀 Deployment (AWS)
Terraform is used to provision infrastructure:

cd infra/terraform
terraform init
terraform plan
terraform apply

After provisioning:
- Push Docker images to ECR
- Update ECS services with new image tags


🧪 Testing
# Run the full test suite:
```bash
pytest -v
```
# Tests include:
Async API tests
SQL-backed idempotency verification
Pagination contract validation
Transaction-safe database isolation

**Testing Guarantees** box

This is short but screams *senior engineer*.

```md
### ✅ Testing Guarantees

- No background jobs run during API tests
- No Redis dependency for request/response validation
- No shared event loops across threads
- No flaky timing-based assertions

If tests pass, production behavior is reproducible.
```

# Tests run against:
Real PostgreSQL
Real Redis
SQL transactions with rollback isolation

## 🧪 Testing Strategy (Production-Grade)

This project uses a **layered async testing strategy** designed to mirror
real-world FastAPI production systems.

### Test Types

- **Async API tests (httpx.AsyncClient)**
  - Full request lifecycle
  - Real dependency injection
  - Single event loop (no sync/async mixing)
  - Matches FastAPI + async SQLAlchemy behavior

- **Database-backed tests**
  - Real PostgreSQL engine
  - Transaction-scoped sessions
  - Deterministic cleanup between tests

- **Idempotency logic tests**
  - SQL-backed job_log table
  - Exactly-once execution guarantees
  - Safe retries and race-condition protection

### Why NOT TestClient?

FastAPI’s synchronous `TestClient` runs the application in a separate thread.
When combined with async SQLAlchemy and pytest, this can cause:

- Event-loop deadlocks
- Connection pool starvation
- Flaky CI behavior

This project **intentionally avoids TestClient** in favor of
`httpx.AsyncClient(app=app)` to ensure correctness and stability.

### Background Jobs in Tests

Celery tasks are **explicitly disabled in test runs**.

Reason:
- API tests must be deterministic
- Redis must not be required for API correctness
- Background retries can cause hanging test suites

Implementation:
- Celery `send_task()` is mocked at test runtime
- Business logic is tested separately from infrastructure
- Redis is only required for integration or worker tests

This separation reflects how production teams test async systems safely.


## 🤖 CI Pipeline (Branch-Aware & Deterministic)

TaskHub uses a **single GitHub Actions pipeline** that adapts automatically
based on the active branch.

### Backend Selection Logic

- `main` branch → **MongoDB (v1.5)**
- `main-sql` / `feature/sql-*` branches → **PostgreSQL (v2.0)**

This is controlled via a branch-aware environment variable in CI:

```bash
BACKEND = mongo | postgres
```

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