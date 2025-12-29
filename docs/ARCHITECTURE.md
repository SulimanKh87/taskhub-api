# 🧱 TaskHub API — System Architecture

This document describes the **current architecture** of TaskHub API as it exists today.

The focus is on **clarity, correctness, and production realism**, not future or hypothetical infrastructure.

---

## 🎯 Design Goals

- Stateless, scalable API
- Clear separation of responsibilities
- Strong data consistency guarantees
- Async processing for reliability
- Predictable behavior under failure

---

## 🧠 High-Level Overview

```text
Client
  ↓
FastAPI (Async)
  ↓
PostgreSQL (Primary Data Store)
  ↓
Redis / Celery (Async Jobs)
```
Each component exists for one clear responsibility.

1️⃣ API Layer (FastAPI)

Role: Synchronous request handling

Responsibilities:

Authentication (JWT)

Request validation (Pydantic)

Business logic

Database reads and writes

Emitting background jobs

Characteristics:

Stateless

Horizontally scalable

Safe to restart at any time

Rule:

Any request can be served by any API instance.

2️⃣ Data Layer (PostgreSQL)

Role: Single source of truth

Stores:

Users

Tasks

Job execution records (idempotency)

Characteristics:

ACID transactions

Explicit schema enforcement

Query-aligned indexes

Relational integrity

Rule:

If data conflicts exist, PostgreSQL always wins.

3️⃣ Async Processing (Celery + Redis)

Role: Background and non-blocking work

Used for:

Emails

Retryable jobs

Long-running or failure-prone tasks

Guarantees:

Tasks are retryable

Idempotency is enforced at the database level

No duplicate execution across retries

Redis is used for:

Task brokering

Temporary state

Redis is not a source of truth.

4️⃣ Containerization

The application is containerized using Docker.

Same image used locally and in CI

No environment-specific logic in code

All configuration injected via environment variables

🎯 Summary

This architecture emphasizes:

Explicit data ownership

Failure isolation

Predictable behavior

Production-aligned simplicity

It is intentionally minimal and suitable for mid-level to entry-senior backend systems.


---

# 💥 `docs/FAILURE_MODES.md` (FINAL VERSION)

```md
# 💥 Failure Modes & Recovery

This document describes **how TaskHub API fails**, **what the impact is**, and **how the system recovers**.

Failures are expected. Correct systems **handle them predictably**.
```
---

## 🎯 Design Philosophy

- Failures are inevitable
- Data correctness is never compromised
- Failures degrade functionality, not integrity
- Recovery is automated where possible

---

## 1️⃣ API Process Failure

**What fails**
- API container crash
- Memory or CPU exhaustion

**Impact**
- Temporary loss of capacity
- No data loss

**Why it’s safe**
- API is stateless
- Requests can be retried

**Recovery**
- Process restart
- Traffic routed to healthy instances

---

## 2️⃣ Background Worker Failure

**What fails**
- Worker crashes mid-task
- Task timeout or exception

**Impact**
- Delayed background work
- No duplicate execution

**Why it’s safe**
- Tasks are retryable
- Idempotency enforced via PostgreSQL

**Recovery**
- Automatic retry
- Job state stored in DB

---

## 3️⃣ PostgreSQL Failure

**What fails**
- Temporary DB unavailability
- Connection errors

**Impact**
- API requests fail fast
- Writes are blocked

**Why it’s safe**
- ACID guarantees
- No partial writes

**Recovery**
- Application retries
- Service resumes when DB is available

Rule:
> If PostgreSQL is unavailable, the system is degraded but consistent.

---

## 4️⃣ Redis Failure

**What fails**
- Redis restart
- Broker unavailable

**Impact**
- Background jobs pause
- Rate limiting unavailable

**Why it’s safe**
- Redis is not a source of truth
- Core data stored in PostgreSQL

**Recovery**
- Redis restart
- Jobs resume automatically

---

## 5️⃣ Rate Limiting Failure

**What fails**
- Redis-based rate limit keys lost

**Impact**
- Temporary loss of rate limiting

**Why it’s acceptable**
- Rate limiting is a protection layer
- Not required for correctness

---

## 🧠 Key Takeaway

TaskHub is designed so that:
- State is protected by PostgreSQL
- Async systems absorb instability
- Failures are isolated by layer

Correct systems are defined not by avoiding failure, but by **recovering without corruption**.