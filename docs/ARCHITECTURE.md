# 🧱 TaskHub Architecture — Cloud-Native Backend (Mid-Level)
This document explains the **architecture of TaskHub API** in a **layered, text-based format**, focusing on **clarity, production realism, and backend engineering principles**.

The goal is to demonstrate **how a real backend system is designed, deployed, scaled, and operated on AWS**, without overengineering.

> **Note:**  
> This document describes the **target cloud-native architecture** of TaskHub.
> The current implementation runs locally using Docker Compose, while the AWS
> components (ECS, RDS, ElastiCache, SQS) are being introduced incrementally.

---

## 🎯 Design Goals

- Cloud-native, production-ready backend
- Clear separation of responsibilities
- Stateless APIs with scalable infrastructure
- Strong data consistency guarantees
- Asynchronous processing for reliability
- Observable and debuggable in production
- Incremental path toward microservices

---

## 🧠 High-Level Mental Model

The system is designed in **layers**, not just services:

Client
↓
Edge / Routing
↓
API Layer
↓
Async / Event Layer
↓
Data Layer
↓
Search Layer
↓
Observability


Each AWS service exists for **one clear reason**.

---

## 1️⃣ Client Layer

**Who talks to the system**

Examples:
- Web frontend
- Mobile app
- API clients
- External integrations (webhooks)

Responsibilities:
- Send HTTP requests
- Authenticate using JWT
- Receive stable, predictable API responses

Clients **never know** how many services exist internally.

---

## 2️⃣ Edge & Routing Layer

**How traffic enters AWS**

Components:
- Application Load Balancer (ALB)
- HTTPS (TLS termination)
- Route 53 (DNS)

Responsibilities:
- Terminate HTTPS
- Distribute traffic across containers
- Enable horizontal scaling
- Act as the single public entry point

Flow:
Client → HTTPS → Load Balancer

Clients never communicate directly with containers.

---

## 3️⃣ API Layer (FastAPI)

**Primary synchronous backend service**

Deployment:
- Dockerized FastAPI application
- Runs as stateless containers on ECS (Fargate)

Responsibilities:
- Authentication (JWT)
- Request validation (Pydantic)
- Business logic
- Database reads/writes
- Emitting async events

Non-responsibilities:
- Long-running tasks
- Blocking I/O
- Background processing

Stateless rule:
> Any request can be handled by any container instance.

---

## 4️⃣ Async & Event Layer

This layer enables **scalability, reliability, and decoupling**.

### 4.1 Celery + Redis (Task-Based Async)

Used for:
- Emails
- ETL jobs
- Background processing
- Retryable tasks
- Exactly-once execution (idempotency)

Flow:
API → Celery Task → Redis → Worker


Characteristics:
- Strong retry control
- Internal job execution
- SQL-backed idempotency

---

### 4.2 SQS (Event-Based Messaging)

Used for:
- Decoupling services
- Event-driven workflows
- Fan-out patterns
- Durable async messaging

Flow:
API → SQS Queue → Consumer


Distinction:
- Celery = internal job execution
- SQS = system-to-system communication

---

## 5️⃣ Data Layer

### 5.1 PostgreSQL (RDS)

**Single source of truth**

Stores:
- Users
- Tasks
- Job logs (idempotency)
- Relational data

Characteristics:
- ACID transactions
- Foreign keys
- Schema enforcement
- Indexed queries
- Strong consistency

Rule:
> If data conflicts exist, PostgreSQL always wins.

---

### 5.2 Redis (ElastiCache / Local Redis)

**Ephemeral data store**

Used for:
- Celery broker
- Rate limiting
- Caching
- Temporary state

Not used for:
- Business-critical persistence
- Source of truth

---

## 6️⃣ Search Layer (Elasticsearch)

**Optimized read model**

Purpose:
- Full-text search
- Fast querying
- Flexible filtering

Pattern:
PostgreSQL = source of truth
Elasticsearch = derived, optimized view

Indexing flow:
DB Change → Async Event → Indexer → Elasticsearch


Query flow:
Client → API → Elasticsearch

Failure rule:
> If Elasticsearch is unavailable, the system remains functional.

---

## 7️⃣ Microservices Strategy

TaskHub uses **controlled microservices**, not fragmentation.

Logical services:
taskhub-api → HTTP API
taskhub-worker → Background jobs
taskhub-search → Search indexing

Characteristics:
- Separate deployments
- Shared repository
- Shared CI/CD
- Independent scaling

Principle:
> One service = one clear responsibility

---

## 8️⃣ Observability & Operations

Visibility is mandatory in production.

Implemented:
- Structured JSON logs
- Request IDs (correlation)
- CloudWatch logging
- Health endpoints

Optional extensions:
- Prometheus metrics
- Latency and error dashboards
- Alerting policies

Rule:
> If you cannot observe it, you cannot operate it.

---

## 9️⃣ Container Orchestration Choices

### ECS (Primary)
- Managed by AWS
- Minimal operational overhead
- Ideal for mid-level backend systems

### EKS (Conceptual)
- Kubernetes-based
- Higher flexibility
- Higher complexity

Rule:
> Master ECS first, understand EKS conceptually.

---

## 🔁 End-to-End Request Flow

Client
→ HTTPS
→ Load Balancer
→ FastAPI (ECS)
→ PostgreSQL (sync)
→ Redis / SQS (async)
→ Worker (ECS)
→ Elasticsearch (optional)

---

## 🎯 Why This Architecture

This architecture demonstrates:
- Real-world backend patterns
- Cloud-native design
- Clear ownership boundaries
- Scalability without overengineering
- Strong production readiness

It is intentionally designed to reflect **mid-level backend expectations** while laying a clean path toward senior-level systems.

---